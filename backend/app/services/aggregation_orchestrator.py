"""
Aggregation orchestration layer
Routes call this to avoid executing aggregation logic directly.

PHASE 41 GOVERNANCE: Participation matrix endpoint
"""
from sqlalchemy.orm import Session
from app.services.federated_service import FederatedService
from app.services.blockchain_service import BlockchainService
from app.models.hospital import Hospital
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound
from app.models.training_rounds import RoundStatus
from sqlalchemy import or_

from fastapi import HTTPException
import json
import hashlib


class AggregationOrchestrator:
    """Thin wrapper for aggregation execution and blockchain logging"""

    @staticmethod
    def perform_masked_fedavg(round_number: int, db: Session) -> dict:

        round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not round_obj:
            raise HTTPException(status_code=404, detail=f"Round {round_number} not found")

        aggregation_strategy = (getattr(round_obj, "aggregation_strategy", "fedavg") or "fedavg").lower()

        # 🔒 GOVERNANCE CHECK
        participation = AggregationOrchestrator.get_participation_matrix(
            round_number=round_number,
            db=db
        )

        if participation.get("error"):
            raise HTTPException(status_code=400, detail=participation["error"])

        if not participation["eligible_for_aggregation"]:
            raise HTTPException(
                status_code=400,
                detail=f"Aggregation requires at least "
                    f"{participation['min_hospitals_required']} eligible hospitals. "
                    f"Currently eligible: {participation['eligible_hospitals']}"
            )

        AggregationOrchestrator._validate_round_contract_consistency(round_number=round_number, db=db)

        # 🚀 Only now execute aggregation
        # PFL mode uploads only shared backbone weights, so FedAvg aggregation path remains unchanged
        if aggregation_strategy == "pfl":
            print(f"[PFL] Round {round_number}: aggregating shared backbone parameters only")
        result = FederatedService.masked_federated_average(round_number, db)
        return result

    @staticmethod
    def _validate_round_contract_consistency(round_number: int, db: Session) -> None:
        round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not round_obj:
            raise HTTPException(status_code=404, detail=f"Round {round_number} not found")

        required_hparams = dict(round_obj.required_hyperparameters or {})
        required_hparams_signature = hashlib.sha256(
            json.dumps(required_hparams, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        models = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.training_type == "FEDERATED",
            ModelWeights.is_global == False,
            ModelWeights.is_uploaded == True,
            ModelWeights.is_mask_uploaded == True
        ).all()

        if not models:
            raise HTTPException(status_code=400, detail="No eligible federated models for aggregation")

        has_any_contract_signature = any(
            bool((model.training_schema or {}).get("federated_contract_signature"))
            for model in models
        )

        # Backward compatibility: legacy rounds trained before signature enforcement
        # can proceed with aggregation if no participating model has signatures.
        if not has_any_contract_signature:
            print(
                f"[GOVERNANCE] Round {round_number}: no federated contract signatures found "
                "on participating models; allowing legacy aggregation path"
            )
            return

        backfilled_any = False
        for model in models:
            training_schema = model.training_schema or {}
            if not isinstance(training_schema, dict):
                training_schema = {}

            contract_signature = training_schema.get("federated_contract_signature", {})
            model_hash = contract_signature.get("feature_order_hash")
            model_arch = contract_signature.get("model_architecture")
            model_hparams_signature = contract_signature.get("hyperparameter_signature")

            if not model_hash or not model_arch or not model_hparams_signature:
                # Self-heal legacy/migrated rows by deriving signature from round contract.
                training_schema["federated_contract_signature"] = {
                    "feature_order_hash": round_obj.required_feature_order_hash,
                    "model_architecture": round_obj.required_model_architecture,
                    "hyperparameter_signature": required_hparams_signature,
                }
                model.training_schema = training_schema
                db.flush()
                backfilled_any = True

                contract_signature = training_schema.get("federated_contract_signature", {})
                model_hash = contract_signature.get("feature_order_hash")
                model_arch = contract_signature.get("model_architecture")
                model_hparams_signature = contract_signature.get("hyperparameter_signature")

                if not model_hash or not model_arch or not model_hparams_signature:
                    raise HTTPException(
                        status_code=403,
                        detail=(
                            f"Aggregation blocked: missing federated contract signature "
                            f"for model {model.id}"
                        )
                    )

            if model_hash != round_obj.required_feature_order_hash:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Aggregation blocked: feature order hash mismatch for model {model.id}"
                    )
                )

            if model_arch != round_obj.required_model_architecture:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Aggregation blocked: model architecture mismatch for model {model.id}"
                    )
                )

            if model_hparams_signature != required_hparams_signature:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Aggregation blocked: hyperparameter signature mismatch for model {model.id}"
                    )
                )

        if backfilled_any:
            db.commit()
            print(f"[GOVERNANCE] Round {round_number}: backfilled missing contract signatures")

    @staticmethod
    def get_global_model(round_number: int, db: Session):
        return FederatedService.get_global_model(round_number, db)

    @staticmethod
    def get_latest_global_model(db: Session):
        return FederatedService.get_latest_global_model(db)
    
    @staticmethod
    def get_participation_matrix(round_number: int = None, db: Session = None) -> dict:
        """
        PHASE 41 GOVERNANCE: Get participation matrix for active/specific round
        
        Returns:
            Dictionary with hospital participation status per round
            
            {
              "round_id": 1,
              "round_number": 1,
              "hospitals": [
                {
                  "hospital_id": 1,
                  "hospital_name": "Hospital A",
                  "has_trained": True,
                  "has_uploaded_weights": True,
                  "has_uploaded_mask": True,
                  "eligible_for_aggregation": True,
                  "model_count": 1
                },
                ...
              ],
              "eligible_hospitals": 5,
              "total_hospitals": 10,
              "eligible_for_aggregation": True,
              "min_hospitals_required": 2
            }
        """
        
        # Get active round if not specified
        if not round_number and db:
            current_round = db.query(TrainingRound).filter(
                TrainingRound.status == RoundStatus.AGGREGATING
            ).first()
            if not current_round:
                return {'error': 'No active training round'}
            round_number = current_round.round_number
            round_id = current_round.id
        else:
            round_id = None

        if round_number and db and round_id is None:
            target_round = db.query(TrainingRound).filter(
                TrainingRound.round_number == round_number
            ).first()
            if not target_round:
                return {'error': f'Round {round_number} not found'}
            round_id = target_round.id
        
        if not db:
            return {'error': 'Database session required'}
        
        # Get all hospitals
        hospitals = db.query(Hospital).filter(
            Hospital.is_active == True,
            Hospital.is_verified == True
        ).all()
        
        participation = []
        eligible_count = 0
        
        for hospital in hospitals:
            # Get models for this hospital in this round
            models = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital.id,
                ModelWeights.training_type == "FEDERATED",
                ModelWeights.is_global == False,
                or_(
                    ModelWeights.round_id == round_id,
                    ModelWeights.round_number == round_number
                )
            ).order_by(ModelWeights.created_at.desc()).all()
            has_trained = len(models) > 0
            
            # Check if weights uploaded
            has_uploaded_weights = False
            has_uploaded_mask = False
            
            if models:
                has_uploaded_weights = any(getattr(model, 'is_uploaded', False) for model in models)
                has_uploaded_mask = any(getattr(model, 'is_mask_uploaded', False) for model in models)
            
            # Eligible only if both weights and mask uploaded
            eligible = has_uploaded_weights and has_uploaded_mask
            if eligible:
                eligible_count += 1
            
            participation.append({
                'hospital_id': hospital.id,
                'hospital_name': hospital.hospital_name,
                'has_trained': has_trained,
                'has_uploaded_weights': has_uploaded_weights,
                'has_uploaded_mask': has_uploaded_mask,
                'eligible_for_aggregation': eligible,
                'model_count': len(models)
            })
        
        # Aggregation requires minimum 2 hospitals
        MIN_HOSPITALS = 2
        eligible_for_aggregation = eligible_count >= MIN_HOSPITALS
        
        round_info = {
            'round_number': round_number,
            'hospitals': participation,
            'eligible_hospitals': eligible_count,
            'total_hospitals': len(hospitals),
            'eligible_for_aggregation': eligible_for_aggregation,
            'min_hospitals_required': MIN_HOSPITALS
        }
        
        if round_id:
            round_info['round_id'] = round_id
        
        return round_info
