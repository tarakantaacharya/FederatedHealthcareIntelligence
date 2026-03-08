"""
Model update service
Handles distribution of global model to hospitals
"""
import os
import json
import shutil
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.model_weights import ModelWeights
from app.models.model_governance import ModelGovernance
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound
from app.services.federated_service import FederatedService
from app.config import get_settings
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

settings = get_settings()


class ModelUpdateService:
    """Service for updating local models with global weights"""

    @staticmethod
    def _get_approved_governance_record(
        db: Session,
        round_number: int,
        model_hash: str
    ) -> ModelGovernance | None:
        return db.query(ModelGovernance).filter(
            ModelGovernance.round_number == round_number,
            ModelGovernance.model_hash == model_hash,
            ModelGovernance.approved == True
        ).order_by(ModelGovernance.created_at.desc()).first()
    
    @staticmethod
    def download_global_model(
        round_number: int,
        db: Session,
        hospital: Hospital
    ) -> dict:
        """
        Download global model weights for a specific round
        
        Args:
            round_number: Federated round number
            db: Database session
            hospital: Hospital object
        
        Returns:
            Dictionary with global model info and local copy path
        
        Raises:
            HTTPException: If global model not found
        """
        # Get global model
        global_model = FederatedService.get_global_model(round_number, db)
        
        if not global_model.model_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Global model missing governance hash. Admin approval required before download."
            )

        governance_record = ModelUpdateService._get_approved_governance_record(
            db=db,
            round_number=round_number,
            model_hash=global_model.model_hash
        )

        if not governance_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global model not approved by governance. Admin approval required before download."
            )

        # Read global weights
        with open(global_model.model_path, 'r') as f:
            global_weights_data = json.load(f)
        
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        aggregation_strategy = (getattr(training_round, 'aggregation_strategy', 'fedavg') or 'fedavg').lower()
        is_pfl = aggregation_strategy == 'pfl'

        global_weights = global_weights_data.get('weights', global_weights_data)
        
        # ===============================
        # PFL: Merge shared weights with local head
        # ===============================
        if is_pfl:
            from app.ml.pfl_splitter import PFLParameterSplitter
            
            # Load hospital's local head from upload
            hospital_dir = os.path.join(settings.MODEL_DIR, hospital.hospital_id)
            local_head_path = os.path.join(
                hospital_dir,
                f'local_head_round_{round_number}.json'
            )
            
            if os.path.exists(local_head_path):
                with open(local_head_path, 'r') as f:
                    local_head_weights = json.load(f)
                
                # Merge shared (from global) with local head
                merged_weights = PFLParameterSplitter.merge_shared_with_local(
                    global_weights,
                    local_head_weights
                )
                
                print(f"[PFL] Merged global shared weights with local head for hospital {hospital.hospital_id}")
                
                # Store merged model
                global_weights_data['weights'] = merged_weights
                global_weights_data['pfl_merged'] = True
            else:
                print(f"[PFL WARNING] Local head not found at {local_head_path}, using shared weights only")
        
        # Copy global weights to hospital's local directory
        hospital_dir = os.path.join(settings.MODEL_DIR, hospital.hospital_id)
        os.makedirs(hospital_dir, exist_ok=True)
        
        local_global_model_path = os.path.join(
            hospital_dir, 
            f"global_model_round_{round_number}.json"
        )
        
        with open(local_global_model_path, 'w') as f:
            json.dump(global_weights_data, f, indent=2)
        
        # Create local copy record in database
        local_global_record = ModelWeights(
            hospital_id=hospital.id,
            round_number=round_number,
            model_path=local_global_model_path,
            model_type=global_model.model_type,
            local_loss=global_model.local_loss,
            local_accuracy=global_model.local_accuracy,
            is_global=False,   # ✅ FIXED
            training_type="FEDERATED",
            model_architecture=global_model.model_architecture
        )
        
        db.add(local_global_record)
        db.commit()
        db.refresh(local_global_record)
        
        return {
            'status': 'global_model_downloaded',
            'round_number': round_number,
            'global_model_id': global_model.id,
            'local_copy_id': local_global_record.id,
            'local_path': local_global_model_path,
            'accuracy': global_model.local_accuracy,
            'loss': global_model.local_loss,
            'message': f'Global model for round {round_number} successfully downloaded'
        }
    
    @staticmethod
    def update_local_with_global(
        round_number: int,
        db: Session,
        hospital: Hospital
    ) -> dict:
        """
        Update hospital's local model with global weights
        
        This performs a "pull" operation where the hospital
        replaces its local model with the aggregated global model
        
        Args:
            round_number: Federated round number
            db: Database session
            hospital: Hospital object
        
        Returns:
            Update confirmation
        """
        # First, download global model if not already present
        existing_global = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital.id,
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True
        ).first()
        
        if not existing_global:
            download_result = ModelUpdateService.download_global_model(
                round_number, db, hospital
            )
            local_copy_id = download_result['local_copy_id']
        else:
            local_copy_id = existing_global.id
        
        return {
            'status': 'local_model_updated',
            'round_number': round_number,
            'hospital_id': hospital.id,
            'hospital_name': hospital.hospital_name,
            'updated_model_id': local_copy_id,
            'message': f'Local model updated with global weights from round {round_number}'
        }
    
    @staticmethod
    def get_available_global_models(db: Session) -> list:
        """
        Get list of all available global models
        
        Args:
            db: Database session
        
        Returns:
            List of global models
        """
        global_models = db.query(ModelWeights).options(
            joinedload(ModelWeights.training_round)
        ).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None  # True global models (not hospital copies)
        ).order_by(ModelWeights.round_number.desc()).all()
        
        return global_models

    @staticmethod
    def get_approved_global_models(db: Session) -> list:
        from sqlalchemy import select
        
        # Get list of approved model hashes
        approved_hashes_query = select(ModelGovernance.model_hash).where(
            ModelGovernance.approved == True
        ).scalar_subquery()

        global_models = db.query(ModelWeights).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None,
            ModelWeights.model_hash.in_(approved_hashes_query)
        ).order_by(ModelWeights.round_number.desc()).all()

        return global_models

    @staticmethod
    def get_all_available_models_for_hospital(db: Session, hospital_id: int) -> list:
        """
        Returns:
            - Deduplicated LOCAL models for this hospital
            - APPROVED global federated models
        """

        from sqlalchemy import func
        from sqlalchemy.orm import joinedload

        round_id_safe = func.coalesce(ModelWeights.round_id, 0)

        # -------------------------
        # LOCAL MODELS (deduplicated)
        # -------------------------
        local_subq = db.query(
            ModelWeights.dataset_id,
            ModelWeights.model_architecture,
            ModelWeights.training_type,
            round_id_safe.label("round_id_safe"),
            func.max(ModelWeights.id).label("max_id")
        ).filter(
            ModelWeights.hospital_id == hospital_id
        ).group_by(
            ModelWeights.dataset_id,
            ModelWeights.model_architecture,
            ModelWeights.training_type,
            round_id_safe
        ).subquery()

        local_ids = [row.max_id for row in db.query(local_subq.c.max_id).all()]

        local_models = []
        if local_ids:
            local_models = db.query(ModelWeights).options(
                joinedload(ModelWeights.training_round)
            ).filter(
                ModelWeights.id.in_(local_ids)
            ).all()

        # -------------------------
        # APPROVED GLOBAL MODELS (Governance enforced)
        # -------------------------
        approved_global_models = ModelUpdateService.get_approved_global_models(db)

        # -------------------------
        # MERGE + SORT
        # -------------------------
        combined = local_models + approved_global_models

        combined.sort(
            key=lambda x: (x.round_number, x.created_at),
            reverse=True
        )

        return combined
    
    @staticmethod
    def get_hospital_sync_status(
        hospital_id: int,
        db: Session
    ) -> dict:
        """
        Check which rounds a hospital has synced
        
        Args:
            hospital_id: Hospital ID
            db: Database session
        
        Returns:
            Dictionary with sync status
        """
        # Get all global models
        all_global_rounds = db.query(ModelWeights.round_number).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).distinct().all()
        
        global_rounds = [r[0] for r in all_global_rounds]
        
        # Get hospital's synced rounds
        synced_rounds = db.query(ModelWeights.round_number).filter(
            ModelWeights.hospital_id == hospital_id,
            ModelWeights.is_global == True
        ).distinct().all()
        
        synced = [r[0] for r in synced_rounds]
        
        # Find missing rounds
        missing_rounds = sorted(set(global_rounds) - set(synced))
        
        return {
            'hospital_id': hospital_id,
            'total_global_rounds': len(global_rounds),
            'synced_rounds': sorted(synced),
            'missing_rounds': missing_rounds,
            'sync_percentage': (len(synced) / len(global_rounds) * 100) if global_rounds else 0
        }

    @staticmethod
    def personalize_model(
        round_number: int,
        db: Session,
        hospital: Hospital,
        mode: str = "FL",
        personalization_lr: float = 0.5
    ) -> dict:
        """
        Hospital-side model personalization: FL vs PFL
        
        FL (Federated Learning): Wf = Wagg (use global model directly)
        PFL (Personalized FL): Wf = W + lr*(W - Wagg) (personalize based on local difference)
        
        Args:
            round_number: Federated round
            db: Database session
            hospital: Hospital object
            mode: "FL" or "PFL"
            personalization_lr: Learning rate for personalization (PFL only)
        
        Returns:
            Personalization result
        """
        import json
        import numpy as np
        
        if mode not in ["FL", "PFL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mode must be 'FL' or 'PFL'"
            )
        
        # Get global model for this round
        global_model = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).first()
        
        if not global_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Global model for round {round_number} not found"
            )
        
        # Get local hospital model from previous round
        local_model = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital.id,
            ModelWeights.round_number == round_number - 1 if round_number > 1 else 0
        ).order_by(ModelWeights.created_at.desc()).first()
        
        # Load weights
        with open(global_model.model_path, 'r') as f:
            global_weights = json.load(f).get('weights', json.load(f))
        
        if mode == "FL":
            # FL: Use global model directly
            final_weights = global_weights
            message = f"FL mode: Using global model directly for round {round_number}"
        
        else:  # PFL
            # PFL: Wf = W + lr*(W - Wagg)
            if not local_model:
                # No local model yet, use global
                final_weights = global_weights
                message = f"PFL mode: No local model available, using global model for round {round_number}"
            else:
                # Load local weights
                with open(local_model.model_path, 'r') as f:
                    local_weights = json.load(f).get('weights', json.load(f))
                
                # Compute personalized weights: Wf = W + lr*(W - Wagg)
                final_weights = {}
                for key in global_weights.keys():
                    if key in local_weights:
                        w_local = np.array(local_weights[key])
                        w_global = np.array(global_weights[key])
                        
                        # PFL formula
                        w_personalized = w_local + personalization_lr * (w_local - w_global)
                        final_weights[key] = w_personalized.tolist()
                    else:
                        final_weights[key] = global_weights[key]
                
                message = f"PFL mode: Personalized with lr={personalization_lr}, formula: W + {personalization_lr}*(W-Wagg)"
        
        # Save personalized model
        hospital_dir = os.path.join(settings.MODEL_DIR, hospital.hospital_id)
        os.makedirs(hospital_dir, exist_ok=True)
        
        personalized_model_path = os.path.join(
            hospital_dir,
            f'personalized_round_{round_number}_{mode}.json'
        )
        
        with open(personalized_model_path, 'w') as f:
            json.dump({'weights': final_weights}, f)
        
        return {
            'status': 'personalization_complete',
            'round_number': round_number,
            'hospital_id': hospital.id,
            'hospital_name': hospital.hospital_name,
            'mode': mode,
            'personalization_lr': personalization_lr if mode == "PFL" else None,
            'personalized_model_path': personalized_model_path,
            'message': message
        }
    
    @staticmethod
    def get_hospital_aggregated_weights_preview(
        model_id: int,
        db: Session,
        hospital: Hospital
    ) -> dict:
        """
        Hospital-side read-only preview of approved/distributed aggregated global weights.

        Legal-governance guardrails:
        - Global model must exist for round
        - Global model must be approved in ModelGovernance
        - Model must be distributed/available to requesting hospital
        """
        requested_model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
        if not requested_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        round_number = requested_model.round_number

        # Resolve actual aggregated global model for the round.
        global_model = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).order_by(ModelWeights.id.desc()).first()

        if not global_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aggregated global model is not available for this round"
            )

        governance_record = ModelUpdateService._get_approved_governance_record(
            db=db,
            round_number=round_number,
            model_hash=global_model.model_hash
        )
        if not governance_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global model is not governance-approved"
            )

        # Distribution check: hospital must have federated availability for this round.
        distributed_record = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital.id,
            ModelWeights.round_number == round_number,
            ModelWeights.training_type == "FEDERATED"
        ).first()
        if not distributed_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global model is not distributed to this hospital yet"
            )

        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        path_candidates = [global_model.model_path]
        if not os.path.isabs(global_model.model_path):
            path_candidates.append(os.path.join(backend_root, global_model.model_path))
            path_candidates.append(os.path.join(backend_root, 'storage', 'models', 'global', os.path.basename(global_model.model_path)))

        resolved_path = next((p for p in path_candidates if os.path.exists(p)), None)
        if not resolved_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aggregated weights file not found"
            )

        try:
            with open(resolved_path, 'r') as f:
                payload = json.load(f)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read aggregated weights JSON: {str(exc)}"
            )

        return {
            "model_id": global_model.id,
            "round_number": round_number,
            "model_hash": global_model.model_hash,
            "approved": True,
            "approved_by": governance_record.approved_by,
            "signature": governance_record.signature,
            "policy_version": governance_record.policy_version,
            "distributed_to_hospital": True,
            "hospital_id": hospital.id,
            "hospital_code": hospital.hospital_id,
            "weights_json": payload,
        }

    @staticmethod
    def get_central_aggregated_weights_preview(
        model_id: int,
        db: Session
    ) -> dict:
        """
        Central admin read-only preview of approved aggregated global weights.

        Legal-governance guardrails:
        - Global model must exist for round
        - Global model must be approved in ModelGovernance
        - No hospital distribution check (admin can view all approved models)
        """
        requested_model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
        if not requested_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )

        round_number = requested_model.round_number

        # Resolve actual aggregated global model for the round.
        global_model = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).order_by(ModelWeights.id.desc()).first()

        if not global_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aggregated global model is not available for this round"
            )

        governance_record = ModelUpdateService._get_approved_governance_record(
            db=db,
            round_number=round_number,
            model_hash=global_model.model_hash
        )
        if not governance_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Global model is not governance-approved"
            )

        # Central admin can view all approved models - no distribution check needed
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        path_candidates = [global_model.model_path]
        if not os.path.isabs(global_model.model_path):
            path_candidates.append(os.path.join(backend_root, global_model.model_path))
            path_candidates.append(os.path.join(backend_root, 'storage', 'models', 'global', os.path.basename(global_model.model_path)))

        resolved_path = next((p for p in path_candidates if os.path.exists(p)), None)
        if not resolved_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aggregated weights file not found"
            )

        try:
            with open(resolved_path, 'r') as f:
                payload = json.load(f)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read aggregated weights JSON: {str(exc)}"
            )

        return {
            "model_id": global_model.id,
            "round_number": round_number,
            "model_hash": global_model.model_hash,
            "approved": True,
            "approved_by": governance_record.approved_by,
            "signature": governance_record.signature,
            "policy_version": governance_record.policy_version,
            "admin_view": True,
            "weights_json": payload,
        }
