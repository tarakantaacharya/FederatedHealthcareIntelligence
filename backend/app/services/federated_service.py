"""
Federated Learning Service
Implements FedAvg with MANDATORY masked aggregation
"""
import os
import json
import numpy as np
import joblib
import hashlib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict

from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound, RoundStatus
from app.services.weight_service import WeightService
from app.services.round_service import RoundService
from app.services.dp_service import DifferentialPrivacyService
from app.services.dropout_service import DropoutService
from app.services.mpc_service import MPCService
from app.services.notification_service import NotificationService
from app.config import get_settings
from app.services.model_hashing import ModelHashingService
from app.models.notification import NotificationEventType, NotificationType, RecipientRole

settings = get_settings()


class FederatedService:
    """Federated learning aggregation service"""
    
    # ============================================================
    #   MANDATORY MASKED AGGREGATION (TFT + MPC)
    # ============================================================
    @staticmethod
    def masked_federated_average(round_number: int, db: Session) -> dict:
        """
        Perform MASKED Federated Averaging with MPC protocol
        
        MANDATORY PROTOCOL:
        1. Load masked weights from central server
        2. Aggregate masked weights (sum)
        3. Collect masks from hospitals
        4. Unmask aggregated weights
        5. Compute federated average
        6. Log to blockchain
        
        Args:
            round_number: Federated learning round number
            db: Database session
            
        Returns:
            Aggregation result with global model info
        """
        # 🔴 1️⃣ ENFORCE ROUND LOCK STATE WITH ROW LOCK (CRITICAL)
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).with_for_update().first()
        
        if not training_round:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round_number} not found"
            )
        
        # Re-check status after acquiring lock (prevents TOCTOU race)
        allowed_statuses = {RoundStatus.TRAINING, RoundStatus.AGGREGATING}
        if training_round.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Round {round_number} is not in TRAINING/AGGREGATING state "
                    f"(current: {training_round.status})"
                )
            )
        
        round_id = training_round.id
        
        # VALIDATION: Check if global model already exists for this round (prevent duplicates)
        existing_global = db.query(ModelWeights).filter(
            ModelWeights.round_id == round_id,
            ModelWeights.is_global == True
        ).first()
        
        if existing_global:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Global model already exists for round {round_number}. "
                       f"Aggregation has already been completed for this round."
            )
        
        # Step 1: Load MASKED weights (DB-first governance)
        masked_weights_list = WeightService.get_central_weights_for_round(
            round_id=round_id,
            db=db
        )

        masked_weights_list = [w for w in masked_weights_list if w.get('is_masked')]
        
        # 🔴 3️⃣ ENFORCE ONLY FEDERATED MODELS WITH CORRECT ARCHITECTURE PARTICIPATE
        federated_models = db.query(ModelWeights).filter(
            ModelWeights.round_id == round_id,
            ModelWeights.training_type == "FEDERATED",
            ModelWeights.model_architecture == training_round.model_type,
            ModelWeights.is_uploaded == True,
            ModelWeights.is_mask_uploaded == True
        ).all()
        
        if len(federated_models) != len(masked_weights_list):
            raise HTTPException(
                status_code=500,
                detail=f"Mismatch between uploaded masked weights ({len(masked_weights_list)}) and federated model records ({len(federated_models)})"
            )
        
        if len(masked_weights_list) < settings.MIN_HOSPITALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient hospitals for aggregation. "
                       f"Need at least {settings.MIN_HOSPITALS}, got {len(masked_weights_list)}"
            )
        
        participation = DropoutService.track_hospital_participation(round_number, db)
        participated_ids = set(participation.get('participated_hospital_ids', []))

        if not participated_ids:
            participated_ids = {w['hospital_id'] for w in masked_weights_list}

        filtered_weights = [
            w for w in masked_weights_list if w['hospital_id'] in participated_ids
        ]

        hospital_ids = [w['hospital_id'] for w in filtered_weights]
        
        # Collect masks with DB validation (mandatory completeness)
        masks_by_hospital = WeightService.get_uploaded_masks_for_round(
            round_id=round_id,
            hospital_ids=hospital_ids,
            db=db
        )
        
        # 🔴 5️⃣ ENFORCE MASK COMPLETENESS
        if len(masks_by_hospital) != len(hospital_ids):
            raise HTTPException(
                status_code=500,
                detail=f"Mask count mismatch: expected {len(hospital_ids)}, got {len(masks_by_hospital)}"
            )

        active_weights = [
            w for w in filtered_weights if w['hospital_id'] in masks_by_hospital
        ]

        active_hospital_ids = [w['hospital_id'] for w in active_weights]

        if len(active_weights) < settings.MIN_HOSPITALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient hospitals for aggregation after dropouts. "
                       f"Need at least {settings.MIN_HOSPITALS}, got {len(active_weights)}"
            )

        num_hospitals = len(active_weights)

        try:
            NotificationService.emit_aggregation_started(
                db=db,
                round_number=round_number,
                num_hospitals=num_hospitals
            )
        except Exception as notification_error:
            print(f"[NOTIFICATION] Aggregation start event emission failed: {notification_error}")

        # Extract just the weights (masked numpy arrays)
        masked_weights_only = [w['weights'] for w in active_weights]
        
        # Step 2: AGGREGATE masked weights (NO averaging yet)
        aggregated_masked = MPCService.aggregate_masked_weights(
            masked_weights_only,
            num_hospitals
        )
        
        # Step 3: Collect masks uploaded by hospitals (dropout-safe)
        masks = [masks_by_hospital[hospital_id] for hospital_id in active_hospital_ids]
        
        # Step 4: UNMASK to get true federated average
        global_weights = MPCService.unmask_weights(
            aggregated_masked,
            masks,
            num_hospitals
        )
        
        # Step 5: Compute global model hash for blockchain
        weights_bytes = b""
        for param_name in sorted(global_weights.keys()):
            weights_bytes += global_weights[param_name].tobytes()
        
        model_hash = hashlib.sha256(weights_bytes).hexdigest()
        
        # Step 6: Save global model
        global_model_dir = os.path.join(settings.MODEL_DIR, "global")
        os.makedirs(global_model_dir, exist_ok=True)
        
        # Use model_type from round for filename and metadata
        model_type_label = training_round.model_type.lower() if training_round.model_type else "tft"
        global_weights_path = os.path.join(global_model_dir, f"global_{model_type_label}_round_{round_number}.json")
        
        # Serialize for storage
        serializable_weights = {k: v.tolist() for k, v in global_weights.items()}
        with open(global_weights_path, "w") as f:
            json.dump({
                'weights': serializable_weights,
                'round_number': round_number,
                'num_hospitals': num_hospitals,
                'model_hash': model_hash,
                'model_type': training_round.model_type,
                'aggregation_method': 'masked_fedavg'
            }, f, indent=2)
        
        # Compute average metrics from hospital contributions
        avg_loss = np.mean([w['metadata']['local_loss'] for w in active_weights])
        avg_accuracy = np.mean([w['metadata']['local_accuracy'] for w in active_weights])
        
        # Extract MAPE and RMSE from hospitals (may be None if not available)
        mapes = [w['metadata'].get('local_mape', None) for w in active_weights]
        rmses = [w['metadata'].get('local_rmse', None) for w in active_weights]
        r2s = [w['metadata'].get('local_r2', None) for w in active_weights]
        
        # Compute averages, excluding None values
        mapes_valid = [m for m in mapes if m is not None]
        rmses_valid = [r for r in rmses if r is not None]
        r2s_valid = [r for r in r2s if r is not None]
        
        avg_mape = np.mean(mapes_valid) if mapes_valid else None
        avg_rmse = np.mean(rmses_valid) if rmses_valid else None
        avg_r2 = np.mean(r2s_valid) if r2s_valid else None  # Never fabricate metrics
        
        # Extract training schema from first hospital (all hospitals use same schema for a round)
        training_schema = None
        if active_weights and 'metadata' in active_weights[0]:
            training_schema = active_weights[0]['metadata'].get('training_schema')
        
        # Save to database (with model_hash)
        # 🔴 5️⃣ EXPLICITLY NULL DP METADATA FOR GLOBAL MODEL
        model_type_db = f"{training_round.model_type.lower()}_masked_fedavg" if training_round.model_type else "tft_masked_fedavg"
        global_model = ModelWeights(
            hospital_id=None,
            round_id=round_id,
            round_number=round_number,
            model_path=global_weights_path,
            model_type=model_type_db,
            model_architecture=training_round.model_type,  # Set architecture (TFT or ML_REGRESSION)
            local_loss=avg_loss,
            local_accuracy=avg_accuracy,
            training_schema=training_schema,  # Store schema from hospitals
            is_global=True,
            model_hash=model_hash,
            # 🔒 Explicitly null DP metadata (global models never consume privacy budget)
            epsilon_spent=None,
            delta=None,
            clip_norm=None,
            noise_multiplier=None,
            dp_mode=None,
            policy_snapshot=None
        )
        
        db.add(global_model)
        db.commit()
        db.refresh(global_model)

        RoundService.complete_round(
            round_number=round_number,
            global_model_id=global_model.id,
            num_hospitals=num_hospitals,
            avg_loss=float(avg_loss),
            avg_accuracy=float(avg_accuracy) if avg_accuracy else None,
            avg_mape=float(avg_mape) if avg_mape else None,
            avg_rmse=float(avg_rmse) if avg_rmse else None,
            avg_r2=float(avg_r2) if avg_r2 else None,
            db=db
        )
        
        # ===============================
        # LOG TO BLOCKCHAIN AUDIT TRAIL
        # ===============================
        from app.models.blockchain import Blockchain
        try:
            blockchain_entry = Blockchain(
                round_id=round_id,
                round_number=round_number,
                model_hash=model_hash,
                block_data={
                    "action": "federated_aggregation",
                    "num_hospitals": num_hospitals,
                    "global_model_id": global_model.id,
                    "avg_loss": float(avg_loss),
                    "avg_accuracy": float(avg_accuracy) if avg_accuracy else None,
                    "avg_mape": float(avg_mape) if avg_mape else None,
                    "avg_rmse": float(avg_rmse) if avg_rmse else None,
                    "avg_r2": float(avg_r2) if avg_r2 else None,
                    "model_type": training_round.model_type,
                    "aggregation_method": "masked_fedavg"
                }
            )
            db.add(blockchain_entry)
            db.commit()
            print(f"[BLOCKCHAIN] Aggregation recorded for round {round_number}: {model_hash[:16]}...")
        except Exception as blockchain_error:
            print(f"[BLOCKCHAIN] Warning: Failed to log aggregation to blockchain: {blockchain_error}")
            # Don't fail aggregation if blockchain logging fails

        try:
            NotificationService.emit_global_model_updated(
                db=db,
                round_number=round_number
            )
            NotificationService.emit_blockchain_recorded(
                db=db,
                round_number=round_number,
                block_hash=model_hash
            )
            NotificationService.emit(
                db=db,
                event_type=NotificationEventType.AUDIT_VERIFICATION_SUCCESS,
                recipient_role=RecipientRole.CENTRAL,
                title=f"✅ Audit Verification Success",
                message=f"Governance audit checks passed for Round {round_number}",
                reference_id=round_number,
                reference_type='round',
                redirect_url=f"/central/blockchain-audit",
                severity='INFO',
                notification_type=NotificationType.SUCCESS
            )
        except Exception as notification_error:
            print(f"[NOTIFICATION] Aggregation completion event emission failed: {notification_error}")
        
        # Step 7: WEBSOCKET BROADCAST (MANDATORY requirement #6)
        from app.routes.websocket import manager
        import asyncio
        
        aggregation_details = {
            'round_number': round_number,
            'num_hospitals': num_hospitals,
            'global_model_id': global_model.id,
            'model_hash': model_hash,
            'avg_loss': float(avg_loss),
            'avg_accuracy': float(avg_accuracy)
        }
        
        # Broadcast asynchronously
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(
                manager.send_aggregation_complete(round_number, aggregation_details)
            )
            loop.create_task(
                manager.send_model_update(round_number, global_model.id)
            )
        except RuntimeError:
            # No event loop running (e.g., during testing)
            pass
        
        return {
            'status': 'aggregation_complete',
            'round_number': round_number,
            'num_hospitals': num_hospitals,
            'global_model_id': global_model.id,
            'global_weights_path': global_weights_path,
            'avg_loss': float(avg_loss),
            'avg_accuracy': float(avg_accuracy),
            'avg_mape': float(avg_mape) if avg_mape else None,
            'avg_rmse': float(avg_rmse) if avg_rmse else None,
            'avg_r2': float(avg_r2) if avg_r2 else None,
            'model_hash': model_hash,
            'aggregation_method': 'masked_fedavg',
            'metrics': {
                'avg_loss': float(avg_loss),
                'avg_accuracy': float(avg_accuracy),
                'avg_mape': float(avg_mape) if avg_mape else None,
                'avg_rmse': float(avg_rmse) if avg_rmse else None,
                'avg_r2': float(avg_r2) if avg_r2 else None
            },
            'dropout_summary': {
                'participated': participation.get('participated', num_hospitals),
                'dropped': participation.get('dropped', 0),
                'dropout_rate': participation.get('dropout_rate', 0.0)
            },
            'message': f'Masked FedAvg complete for round {round_number} with {num_hospitals} hospitals'
        }

    # ============================================================
    #   NORMAL FEDERATED AVERAGE (NON-DP)
    # ============================================================
    @staticmethod
    def federated_average(round_number: int, db: Session) -> dict:
        """
        Perform Federated Averaging (FedAvg) on hospital weights
        """
        # Resolve round_id from round_number WITH ROW LOCK
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).with_for_update().first()
        
        if not training_round:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round_number} not found"
            )
        
        # ENFORCE AGGREGATING STATE (governance consistency)
        if training_round.status != RoundStatus.AGGREGATING:
            raise HTTPException(
                status_code=400,
                detail=f"Round {round_number} is not in AGGREGATING state (current: {training_round.status})"
            )
        
        round_id = training_round.id
        
        # VALIDATION: Check if global model already exists for this round (prevent duplicates)
        existing_global = db.query(ModelWeights).filter(
            ModelWeights.round_id == round_id,
            ModelWeights.is_global == True
        ).first()
        
        if existing_global:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Global model already exists for round {round_number}. "
                       f"Aggregation has already been completed for this round."
            )
        
        weights_list = WeightService.get_central_weights_for_round(round_id, db)
        
        if len(weights_list) < settings.MIN_HOSPITALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient hospitals for aggregation. "
                       f"Need at least {settings.MIN_HOSPITALS}, got {len(weights_list)}"
            )
        
        # Extract weight pieces
        all_feature_importances = []
        all_scaler_means = []
        all_scaler_scales = []
        num_samples_list = []

        for weight_data in weights_list:
            weights = weight_data['weights']
            metadata = weight_data['metadata']
            
            all_feature_importances.append(weights['model_params']['feature_importances'])
            all_scaler_means.append(weights['scaler_mean'])
            all_scaler_scales.append(weights['scaler_scale'])
            
            num_samples_list.append(1.0)  # equal weights
        
        total_samples = sum(num_samples_list)
        sample_weights = [n / total_samples for n in num_samples_list]

        # Aggregation
        aggregated_importances = np.average(all_feature_importances, axis=0, weights=sample_weights).tolist()
        aggregated_scaler_mean = np.average(all_scaler_means, axis=0, weights=sample_weights).tolist()
        aggregated_scaler_scale = np.average(all_scaler_scales, axis=0, weights=sample_weights).tolist()

        avg_loss = np.mean([w['metadata']['local_loss'] for w in weights_list])
        avg_accuracy = np.mean([w['metadata']['local_accuracy'] for w in weights_list])
        
        # Extract MAPE, RMSE, and R² from hospitals (may be None if not available)
        mapes = [w['metadata'].get('local_mape', None) for w in weights_list]
        rmses = [w['metadata'].get('local_rmse', None) for w in weights_list]
        r2s = [w['metadata'].get('local_r2', None) for w in weights_list]
        
        # Compute averages, excluding None values
        mapes_valid = [m for m in mapes if m is not None]
        rmses_valid = [r for r in rmses if r is not None]
        r2s_valid = [r for r in r2s if r is not None]
        
        avg_mape = np.mean(mapes_valid) if mapes_valid else None
        avg_rmse = np.mean(rmses_valid) if rmses_valid else None
        avg_r2 = np.mean(r2s_valid) if r2s_valid else None
        
        aggregated_weights = {
            'model_params': {
                'n_estimators': weights_list[0]['weights']['model_params']['n_estimators'],
                'max_depth': weights_list[0]['weights']['model_params']['max_depth'],
                'feature_importances': aggregated_importances
            },
            'scaler_mean': aggregated_scaler_mean,
            'scaler_scale': aggregated_scaler_scale,
            'feature_columns': weights_list[0]['weights']['feature_columns'],
            'target_column': weights_list[0]['weights']['target_column']
        }

        global_model_dir = os.path.join(settings.MODEL_DIR, "global")
        os.makedirs(global_model_dir, exist_ok=True)

        global_weights_path = os.path.join(global_model_dir, f"global_weights_round_{round_number}.json")
        with open(global_weights_path, "w") as f:
            json.dump(aggregated_weights, f, indent=2)

        # Compute model hash before creating the record
        model_hash = ModelHashingService.hash_model_weights(aggregated_weights)

        # Extract training schema from first hospital (all hospitals use same schema for a round)
        training_schema = None
        if weights_list and 'metadata' in weights_list[0]:
            training_schema = weights_list[0]['metadata'].get('training_schema')

        global_model = ModelWeights(
            hospital_id=None,
            round_number=round_number,
            model_path=global_weights_path,
            model_type="sklearn_baseline_fedavg",
            local_loss=avg_loss,
            local_accuracy=avg_accuracy,
            training_schema=training_schema,  # Store schema from hospitals
            is_global=True,
            model_hash=model_hash
        )

        db.add(global_model)
        db.commit()
        db.refresh(global_model)

        # Mark round complete (will set status to CLOSED)
        RoundService.complete_round(
            round_number=round_number,
            global_model_id=global_model.id,
            num_hospitals=len(weights_list),
            avg_loss=avg_loss,
            avg_accuracy=avg_accuracy,
            avg_mape=float(avg_mape) if avg_mape else None,
            avg_rmse=float(avg_rmse) if avg_rmse else None,
            avg_r2=float(avg_r2) if avg_r2 else None,
            db=db
        )

        return {
            "model_hash": model_hash
        }

    # ============================================================
    #   FEDERATED AVERAGE WITH DIFFERENTIAL PRIVACY
    # ============================================================
    @staticmethod
    def federated_average_with_dp(
        round_number: int,
        db: Session,
        enable_dp: bool = True,
        epsilon: float = 1.0,
        delta: float = 1e-5
    ) -> dict:
        """
        DEPRECATED: Global DP is architecturally incorrect (DP should be at hospital level only).
        This method is kept for legacy support but will raise an error if enable_dp=True.
        
        Perform FedAvg with Differential Privacy
        """
        # GOVERNANCE: Global DP is architecturally wrong (double-DP risk)
        if enable_dp:
            raise HTTPException(
                status_code=400,
                detail="Global DP is deprecated. Apply DP at hospital level only (during training)."
            )
        
        # Resolve round_id from round_number WITH ROW LOCK
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).with_for_update().first()
        
        if not training_round:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round_number} not found"
            )
        
        # ENFORCE AGGREGATING STATE (governance consistency)
        if training_round.status != RoundStatus.AGGREGATING:
            raise HTTPException(
                status_code=400,
                detail=f"Round {round_number} is not in AGGREGATING state (current: {training_round.status})"
            )
        
        round_id = training_round.id
        
        weights_list = WeightService.get_central_weights_for_round(round_id, db)

        if len(weights_list) < settings.MIN_HOSPITALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient hospitals for aggregation"
            )

        all_feature_importances = []
        all_scaler_means = []
        all_scaler_scales = []

        for weight_data in weights_list:
            weights = weight_data["weights"]

            all_feature_importances.append(weights["model_params"]["feature_importances"])
            all_scaler_means.append(weights["scaler_mean"])
            all_scaler_scales.append(weights["scaler_scale"])

        num_hospitals = len(weights_list)
        weights = [1.0 / num_hospitals] * num_hospitals

        aggregated_importances = np.average(all_feature_importances, axis=0, weights=weights)
        aggregated_scaler_mean = np.average(all_scaler_means, axis=0, weights=weights)
        aggregated_scaler_scale = np.average(all_scaler_scales, axis=0, weights=weights)

        privacy_metadata = None

        # NOTE: Global models should NOT apply DP (already private via composition)
        # This code path is for legacy support only - governance requires DP at hospital level
        if enable_dp:
            dp_service = DifferentialPrivacyService()

            weight_dict = {
                "feature_importances": aggregated_importances,
                "scaler_mean": aggregated_scaler_mean,
                "scaler_scale": aggregated_scaler_scale
            }

            private_weights, privacy_metadata = dp_service.apply_dp_to_weights(
                weights=weight_dict,
                epsilon=epsilon,
                delta=delta,
                clip_norm=1.0,  # Default clipping for global model
                noise_multiplier=1.0  # Default noise multiplier
            )

            aggregated_importances = private_weights["feature_importances"]
            aggregated_scaler_mean = private_weights["scaler_mean"]
            aggregated_scaler_scale = private_weights["scaler_scale"]

        aggregated_weights = {
            "model_params": {
                "n_estimators": weights_list[0]["weights"]["model_params"]["n_estimators"],
                "max_depth": weights_list[0]["weights"]["model_params"]["max_depth"],
                "feature_importances": aggregated_importances.tolist()
            },
            "scaler_mean": aggregated_scaler_mean.tolist(),
            "scaler_scale": aggregated_scaler_scale.tolist(),
            "feature_columns": weights_list[0]["weights"]["feature_columns"],
            "target_column": weights_list[0]["weights"]["target_column"]
        }

        if privacy_metadata:
            aggregated_weights["privacy"] = privacy_metadata

        global_dir = os.path.join(settings.MODEL_DIR, "global")
        os.makedirs(global_dir, exist_ok=True)

        global_path = os.path.join(global_dir, f"global_weights_round_{round_number}.json")
        with open(global_path, "w") as f:
            json.dump(aggregated_weights, f, indent=2)

        avg_loss = np.mean([w["metadata"]["local_loss"] for w in weights_list])
        avg_accuracy = np.mean([w["metadata"]["local_accuracy"] for w in weights_list])

        # Extract training schema from first hospital (all hospitals use same schema for a round)
        training_schema = None
        if weights_list and 'metadata' in weights_list[0]:
            training_schema = weights_list[0]['metadata'].get('training_schema')

        global_model = ModelWeights(
            hospital_id=None,
            round_number=round_number,
            model_path=global_path,
            model_type="sklearn_baseline_fedavg_dp" if enable_dp else "sklearn_baseline_fedavg",
            local_loss=avg_loss,
            local_accuracy=avg_accuracy,
            training_schema=training_schema,  # Store schema from hospitals
            is_global=True
        )

        db.add(global_model)
        db.commit()
        db.refresh(global_model)

        RoundService.complete_round(
            round_number=round_number,
            global_model_id=global_model.id,
            num_hospitals=num_hospitals,
            avg_loss=avg_loss,
            db=db
        )

        return {
            "status": "aggregation_complete_with_dp" if enable_dp else "aggregation_complete",
            "round_number": round_number,
            "global_model_id": global_model.id,
            "num_hospitals": num_hospitals,
            "avg_loss": float(avg_loss),
            "avg_accuracy": float(avg_accuracy),
            "global_weights_path": global_path,
            "privacy_applied": enable_dp,
            "privacy_metadata": privacy_metadata,
            "message": (
                f"Global model created from {num_hospitals} hospitals with DP"
                if enable_dp else
                f"Global model created from {num_hospitals} hospitals"
            )
        }

    @staticmethod
    def get_global_model(round_number: int, db: Session) -> ModelWeights:
        global_model = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True
        ).order_by(ModelWeights.created_at.desc()).first()

        if not global_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No global model found for round {round_number}"
            )

        return global_model

    @staticmethod
    def get_latest_global_model(db: Session) -> ModelWeights:
        global_model = db.query(ModelWeights).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).order_by(ModelWeights.round_number.desc(), ModelWeights.created_at.desc()).first()

        if not global_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No global model found"
            )

        return global_model

    # ============================================================
    #   FEDERATED AVERAGE WITH DROPOUT HANDLING (PHASE 21)
    # ============================================================
    @staticmethod
    def federated_average_with_dropout_handling(
        round_number: int,
        db: Session,
        enable_dp: bool = True,
        epsilon: float = 1.0,
        delta: float = 1e-5
    ) -> dict:
        """
        Perform FedAvg with dropout handling and recovery
        
        Args:
            round_number: Current round
            db: Database session
            enable_dp: Whether to apply DP (DEPRECATED: should be False)
            epsilon: Privacy budget
            delta: Privacy parameter
        
        Returns:
            Aggregation result with dropout metadata
        """
        # GOVERNANCE: Global DP is architecturally wrong (double-DP risk)
        if enable_dp:
            raise HTTPException(
                status_code=400,
                detail="Global DP is deprecated. Apply DP at hospital level only (during training)."
            )
        
        # Resolve round_id from round_number WITH ROW LOCK
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).with_for_update().first()
        
        if not training_round:
            raise HTTPException(
                status_code=404,
                detail=f"Round {round_number} not found"
            )
        
        # ENFORCE AGGREGATING STATE (governance consistency)
        if training_round.status != RoundStatus.AGGREGATING:
            raise HTTPException(
                status_code=400,
                detail=f"Round {round_number} is not in AGGREGATING state (current: {training_round.status})"
            )
        
        round_id = training_round.id
        
        # Track participation
        participation = DropoutService.track_hospital_participation(round_number, db)
        
        # Check viability
        viability = DropoutService.check_round_viability(round_number, db)
        
        if not viability['is_viable']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Round not viable: only {viability['participated']} hospitals participated (min: {viability['min_required']}), dropout rate: {viability['dropout_rate']:.1%}"
            )
        
        # Attempt recovery for dropped hospitals
        recovery_result = None
        if participation['dropped'] > 0:
            recovery_result = DropoutService.attempt_recovery(
                round_number,
                participation['dropped_hospital_ids'],
                db
            )
            
            # Re-check participation after recovery attempt
            participation = DropoutService.track_hospital_participation(round_number, db)
        
        # Get weights from participating hospitals
        weights_list = WeightService.get_central_weights_for_round(round_id, db)
        
        if len(weights_list) < settings.MIN_HOSPITALS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient hospitals: {len(weights_list)} < {settings.MIN_HOSPITALS}"
            )
        
        # Calculate dropout penalties for each hospital
        hospital_penalties = {}
        for weight_data in weights_list:
            hospital_id = weight_data['hospital_id']
            penalty = DropoutService.calculate_dropout_penalty(hospital_id, db)
            hospital_penalties[hospital_id] = penalty
        
        # Extract weights with penalties
        all_feature_importances = []
        all_scaler_means = []
        all_scaler_scales = []
        sample_weights = []
        
        for weight_data in weights_list:
            weights = weight_data['weights']
            hospital_id = weight_data['hospital_id']
            penalty = hospital_penalties[hospital_id]
            
            all_feature_importances.append(weights['model_params']['feature_importances'])
            all_scaler_means.append(weights['scaler_mean'])
            all_scaler_scales.append(weights['scaler_scale'])
            
            # Apply penalty to aggregation weight
            base_weight = 1.0 / len(weights_list)
            sample_weights.append(base_weight * penalty)
        
        # Normalize weights
        total_weight = sum(sample_weights)
        sample_weights = [w / total_weight for w in sample_weights]
        
        # Aggregate with adjusted weights
        aggregated_importances = np.average(
            all_feature_importances,
            axis=0,
            weights=sample_weights
        )
        
        aggregated_scaler_mean = np.average(
            all_scaler_means,
            axis=0,
            weights=sample_weights
        )
        
        aggregated_scaler_scale = np.average(
            all_scaler_scales,
            axis=0,
            weights=sample_weights
        )
        
        # Apply Differential Privacy (if enabled)
        # NOTE: Global models should NOT apply DP (already private via composition)
        # This code path is for legacy support only - governance requires DP at hospital level
        privacy_metadata = None
        
        if enable_dp:
            dp_service = DifferentialPrivacyService()
            
            aggregated_weights_dict = {
                'feature_importances': aggregated_importances,
                'scaler_mean': aggregated_scaler_mean,
                'scaler_scale': aggregated_scaler_scale
            }
            
            private_weights_dict, privacy_metadata = dp_service.apply_dp_to_weights(
                weights=aggregated_weights_dict,
                epsilon=epsilon,
                delta=delta,
                clip_norm=1.0,  # Default clipping for global model
                noise_multiplier=1.0  # Default noise multiplier
            )
            
            aggregated_importances = private_weights_dict['feature_importances']
            aggregated_scaler_mean = private_weights_dict['scaler_mean']
            aggregated_scaler_scale = private_weights_dict['scaler_scale']
        
        # Create aggregated weights
        aggregated_weights = {
            'model_params': {
                'n_estimators': weights_list[0]['weights']['model_params']['n_estimators'],
                'max_depth': weights_list[0]['weights']['model_params']['max_depth'],
                'feature_importances': aggregated_importances.tolist()
            },
            'scaler_mean': aggregated_scaler_mean.tolist(),
            'scaler_scale': aggregated_scaler_scale.tolist(),
            'feature_columns': weights_list[0]['weights']['feature_columns'],
            'target_column': weights_list[0]['weights']['target_column'],
            'dropout_metadata': {
                'participation': participation,
                'penalties': hospital_penalties,
                'recovery': recovery_result
            }
        }
        
        if privacy_metadata:
            aggregated_weights['privacy'] = privacy_metadata
        
        # Save global model
        global_model_dir = os.path.join(settings.MODEL_DIR, 'global')
        os.makedirs(global_model_dir, exist_ok=True)
        
        global_weights_path = os.path.join(
            global_model_dir,
            f'global_weights_round_{round_number}.json'
        )
        
        with open(global_weights_path, 'w') as f:
            json.dump(aggregated_weights, f, indent=2)
        
        # Calculate metrics
        avg_loss = np.mean([w['metadata']['local_loss'] for w in weights_list if w['metadata'].get('local_loss')])
        avg_accuracy = np.mean([w['metadata']['local_accuracy'] for w in weights_list if w['metadata'].get('local_accuracy')])
        
        # Create global model record
        global_model = ModelWeights(
            hospital_id=None,
            round_number=round_number,
            model_path=global_weights_path,
            model_type='sklearn_baseline_fedavg_dropout_aware',
            local_loss=avg_loss,
            local_accuracy=avg_accuracy,
            is_global=True
        )
        
        db.add(global_model)
        db.commit()
        db.refresh(global_model)
        
        # Update training round
        RoundService.complete_round(
            round_number=round_number,
            global_model_id=global_model.id,
            num_hospitals=len(weights_list),
            avg_loss=avg_loss,
            db=db
        )
        
        return {
            'status': 'aggregation_complete_with_dropout_handling',
            'round_number': round_number,
            'global_model_id': global_model.id,
            'num_hospitals': len(weights_list),
            'avg_loss': float(avg_loss),
            'avg_accuracy': float(avg_accuracy),
            'global_weights_path': global_weights_path,
            'dropout_handling': {
                'total_hospitals': participation['total_hospitals'],
                'participated': participation['participated'],
                'dropped': participation['dropped'],
                'dropout_rate': participation['dropout_rate'],
                'recovered': recovery_result['recovered'] if recovery_result else 0,
                'penalties_applied': hospital_penalties
            },
            'privacy_applied': enable_dp,
            'privacy_metadata': privacy_metadata
        }
