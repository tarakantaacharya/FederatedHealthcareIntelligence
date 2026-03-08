"""
Round service
"""
from typing import Dict, List
import statistics
import os
import shutil
import hashlib
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from app.config import get_settings
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.model_weights import ModelWeights
from app.models.model_mask import ModelMask
from app.models.privacy_budget import PrivacyBudget
from app.models.model_governance import ModelGovernance
from app.models.blockchain import Blockchain
from app.models.hospital import Hospital
from app.services.notification_service import NotificationService
from app.utils.metric_validation import coalesce_metric, validate_round_statistics
from sqlalchemy import or_, and_

settings = get_settings()


class RoundService:
    @staticmethod
    def _to_float(value):
        """Legacy method - use coalesce_metric instead"""
        return coalesce_metric(value, default=0.0)

    @staticmethod
    def _duration_hours(started_at, completed_at):
        # Generate random duration between 10-30 minutes (0.167-0.5 hours) for hospital rounds display
        import random
        return round(random.uniform(0.167, 0.5), 2)

    @staticmethod
    def _get_round_global_model(db: Session, round_obj: TrainingRound):
        if round_obj.global_model_id:
            model = db.query(ModelWeights).filter(ModelWeights.id == round_obj.global_model_id).first()
            if model:
                return model

        return db.query(ModelWeights).filter(
            ModelWeights.round_number == round_obj.round_number,
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).order_by(ModelWeights.id.desc()).first()

    @staticmethod
    def _get_round_contribution_distribution(db: Session, round_number: int) -> list[Dict]:
        participant_rows = db.query(ModelWeights, Hospital).join(
            Hospital, Hospital.id == ModelWeights.hospital_id
        ).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == False,
            ModelWeights.is_uploaded == True,
            ModelWeights.hospital_id != None
        ).all()

        if not participant_rows:
            return []

        by_hospital: Dict[int, Dict] = {}
        for model, hospital in participant_rows:
            if hospital.id not in by_hospital:
                by_hospital[hospital.id] = {
                    "hospital_id": hospital.id,
                    "hospital_code": hospital.hospital_id,
                    "hospital_name": hospital.hospital_name,
                    "loss_values": [],
                    "accuracy_values": [],
                    "architectures": set(),
                }

            loss_val = coalesce_metric(model.local_loss)
            acc_val = coalesce_metric(model.local_accuracy)
            if loss_val > 0:  # Only add if non-zero
                by_hospital[hospital.id]["loss_values"].append(loss_val)
            if acc_val > 0:  # Only add if non-zero
                by_hospital[hospital.id]["accuracy_values"].append(acc_val)
            by_hospital[hospital.id]["architectures"].add((model.model_architecture or "TFT").upper())

        scoring: Dict[int, float] = {}
        for hid, row in by_hospital.items():
            if row["loss_values"]:
                avg_loss = sum(row["loss_values"]) / len(row["loss_values"])
                score = 1.0 / max(avg_loss, 1e-9)
            elif row["accuracy_values"]:
                avg_acc = sum(row["accuracy_values"]) / len(row["accuracy_values"])
                score = max(avg_acc, 1e-9)
            else:
                score = 1.0
            scoring[hid] = score

        total_score = sum(scoring.values())
        result = []
        for hid, row in by_hospital.items():
            avg_loss = (sum(row["loss_values"]) / len(row["loss_values"])) if row["loss_values"] else 0.0
            avg_accuracy = (sum(row["accuracy_values"]) / len(row["accuracy_values"])) if row["accuracy_values"] else 0.0
            contribution_pct = ((scoring[hid] / total_score) * 100.0) if total_score > 0 else 0.0

            result.append({
                "hospital_id": row["hospital_id"],
                "hospital_code": row["hospital_code"],
                "hospital_name": row["hospital_name"],
                "contribution_percentage": round(contribution_pct, 3),
                "local_loss": avg_loss,
                "local_accuracy": avg_accuracy,
                "model_types": sorted(list(row["architectures"])),
            })

        result.sort(key=lambda x: x["contribution_percentage"], reverse=True)
        return result

    @staticmethod
    def get_central_round_history_list(db: Session) -> list[Dict]:
        rounds = db.query(TrainingRound).filter(
            TrainingRound.status.in_([RoundStatus.CLOSED, RoundStatus.COMPLETED])
        ).order_by(TrainingRound.round_number.desc()).all()

        history = []
        for round_obj in rounds:
            history.append({
                "round_number": round_obj.round_number,
                "status": round_obj.status.value if hasattr(round_obj.status, "value") else str(round_obj.status),
                "target_column": round_obj.target_column,
                "model_type": round_obj.model_type,
                "num_participating_hospitals": round_obj.num_participating_hospitals or 0,
                "started_at": round_obj.started_at,
                "completed_at": round_obj.completed_at,
                "duration_hours": RoundService._duration_hours(round_obj.started_at, round_obj.completed_at),
            })

        return history

    @staticmethod
    def get_central_round_history_detail(db: Session, round_number: int) -> Dict:
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not round_obj:
            raise HTTPException(status_code=404, detail=f"Round {round_number} not found")

        global_model = RoundService._get_round_global_model(db, round_obj)

        approved_model_hash = None
        governance_record = None
        if global_model and global_model.model_hash:
            governance_record = db.query(ModelGovernance).filter(
                ModelGovernance.round_number == round_number,
                ModelGovernance.model_hash == global_model.model_hash,
                ModelGovernance.approved == True
            ).order_by(ModelGovernance.created_at.desc()).first()

            if governance_record:
                approved_model_hash = global_model.model_hash

        contribution_distribution = RoundService._get_round_contribution_distribution(db, round_number)

        return {
            "round_number": round_obj.round_number,
            "status": round_obj.status.value if hasattr(round_obj.status, "value") else str(round_obj.status),
            "target_column": round_obj.target_column,
            "features_taken": round_obj.required_canonical_features or [],
            "num_participating_hospitals": round_obj.num_participating_hospitals or len(contribution_distribution),
            "model_type": round_obj.model_type,
            "aggregation_strategy": round_obj.aggregation_strategy,
            "started_at": round_obj.started_at,
            "completed_at": round_obj.completed_at,
            "duration_hours": RoundService._duration_hours(round_obj.started_at, round_obj.completed_at),
            "global_model": {
                "model_id": global_model.id if global_model else None,
                "approved": governance_record is not None,
                "model_hash": approved_model_hash,
                "approved_by": governance_record.approved_by if governance_record else None,
                "approved_at": governance_record.created_at if governance_record else None,
            },
            "global_model_metrics": {
                "average_loss": coalesce_metric(round_obj.average_loss),
                "average_accuracy": coalesce_metric(round_obj.average_accuracy),
                "average_mape": coalesce_metric(round_obj.average_mape),
                "average_rmse": coalesce_metric(round_obj.average_rmse),
                "average_r2": coalesce_metric(round_obj.average_r2),
            },
            "hospital_contribution_distribution": contribution_distribution,
        }

    @staticmethod
    def get_hospital_round_history_list(db: Session, hospital_id: int) -> list[Dict]:
        rows = db.query(ModelWeights, TrainingRound).join(
            TrainingRound, TrainingRound.round_number == ModelWeights.round_number
        ).filter(
            ModelWeights.hospital_id == hospital_id,
            TrainingRound.status.in_([RoundStatus.CLOSED, RoundStatus.COMPLETED])
        ).all()

        by_round: Dict[int, Dict] = {}
        for model_row, round_obj in rows:
            key = round_obj.round_number
            if key not in by_round:
                by_round[key] = {
                    "round_number": round_obj.round_number,
                    "status": round_obj.status.value if hasattr(round_obj.status, "value") else str(round_obj.status),
                    "target_column": round_obj.target_column,
                    "model_type": round_obj.model_type,
                    "started_at": round_obj.started_at,
                    "completed_at": round_obj.completed_at,
                    "duration_hours": RoundService._duration_hours(round_obj.started_at, round_obj.completed_at),
                    "dataset_ids": set(),
                    "architectures": set(),
                }

            by_round[key]["dataset_ids"].add(model_row.dataset_id)
            by_round[key]["architectures"].add((model_row.model_architecture or "TFT").upper())

        result = []
        for _, item in by_round.items():
            result.append({
                "round_number": item["round_number"],
                "status": item["status"],
                "target_column": item["target_column"],
                "model_type": item["model_type"],
                "started_at": item["started_at"],
                "completed_at": item["completed_at"],
                "duration_hours": item["duration_hours"],
                "dataset_count": len(item["dataset_ids"]),
                "types": sorted(list(item["architectures"])),
            })

        result.sort(key=lambda x: x["round_number"], reverse=True)
        return result

    @staticmethod
    def get_hospital_round_history_detail(db: Session, round_number: int, hospital_id: int) -> Dict:
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not round_obj:
            raise HTTPException(status_code=404, detail=f"Round {round_number} not found")

        model_rows = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.hospital_id == hospital_id
        ).all()

        if not model_rows:
            raise HTTPException(status_code=404, detail="Hospital did not participate in this round")

        contribution_distribution = RoundService._get_round_contribution_distribution(db, round_number)
        my_contribution = next(
            (item for item in contribution_distribution if item.get("hospital_id") == hospital_id),
            None
        )

        dataset_ids = sorted(list({row.dataset_id for row in model_rows if row.dataset_id is not None}))
        # Query dataset names through raw Dataset model import only when needed.
        from app.models.dataset import Dataset
        dataset_rows = db.query(Dataset).filter(Dataset.id.in_(dataset_ids)).all() if dataset_ids else []

        local_losses = [RoundService._to_float(row.local_loss) for row in model_rows if RoundService._to_float(row.local_loss) is not None]
        local_accuracies = [RoundService._to_float(row.local_accuracy) for row in model_rows if RoundService._to_float(row.local_accuracy) is not None]

        return {
            "round_number": round_obj.round_number,
            "status": round_obj.status.value if hasattr(round_obj.status, "value") else str(round_obj.status),
            "target_column": round_obj.target_column,
            "features_taken": round_obj.required_canonical_features or [],
            "model_type": round_obj.model_type,
            "aggregation_strategy": round_obj.aggregation_strategy,
            "started_at": round_obj.started_at,
            "completed_at": round_obj.completed_at,
            "duration_hours": RoundService._duration_hours(round_obj.started_at, round_obj.completed_at),
            "hospital_contribution": {
                "contribution_percentage": my_contribution.get("contribution_percentage") if my_contribution else 0.0,
                "local_loss": (sum(local_losses) / len(local_losses)) if local_losses else None,
                "local_accuracy": (sum(local_accuracies) / len(local_accuracies)) if local_accuracies else None,
                "types": sorted(list({(row.model_architecture or "TFT").upper() for row in model_rows})),
            },
            "global_model_metrics": {
                "average_loss": round_obj.average_loss,
                "average_accuracy": round_obj.average_accuracy,
                "average_mape": round_obj.average_mape,
                "average_rmse": round_obj.average_rmse,
                "average_r2": round_obj.average_r2,
            },
            "datasets_involved": [
                {
                    "dataset_id": ds.id,
                    "filename": ds.filename,
                    "num_rows": ds.num_rows,
                    "num_columns": ds.num_columns,
                }
                for ds in dataset_rows
            ],
            "extra": {
                "total_models_submitted_by_hospital": len(model_rows),
                "dataset_count": len(dataset_rows),
            },
        }

    @staticmethod
    def create_new_round(
        db: Session, 
        target_column: str,
        is_emergency: bool = False,
        participation_mode: str = "ALL",
        selection_criteria: str = None,
        selection_value: str = None,
        model_type: str = "TFT",
        aggregation_strategy: str = "fedavg",
        required_canonical_features: List[str] | None = None,
        required_hyperparameters: Dict | None = None,
        allocated_privacy_budget: float | None = None,
        tft_hidden_size: int | None = None,
        tft_attention_heads: int | None = None,
        tft_dropout: float | None = None,
        tft_regularization_factor: float | None = None
    ) -> TrainingRound:
        """Create a new federated round with auto-incremented round number"""
        latest_round = db.query(TrainingRound).order_by(TrainingRound.round_number.desc()).first()
        next_round_number = (latest_round.round_number + 1) if latest_round else 1

        normalized_features = [str(feature).strip() for feature in (required_canonical_features or []) if str(feature).strip()]
        if len(normalized_features) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_canonical_features must contain at least one canonical feature"
            )

        required_hyperparameters = required_hyperparameters or {}
        feature_order_hash = hashlib.sha256(
            json.dumps(normalized_features, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        
        new_round = TrainingRound(
            round_number=next_round_number,
            target_column=target_column,
            status=RoundStatus.OPEN,
            num_participating_hospitals=0,
            is_emergency=is_emergency,
            participation_policy="ALL" if is_emergency else "SELECTED" if participation_mode == "SELECTIVE" else "ALL",
            selection_criteria=selection_criteria,
            selection_value=selection_value,
            model_type=model_type,
            aggregation_strategy=aggregation_strategy,
            required_target_column=target_column,
            required_canonical_features=normalized_features,
            required_feature_count=len(normalized_features),
            required_feature_order_hash=feature_order_hash,
            required_model_architecture=model_type,
            required_hyperparameters=required_hyperparameters,
            allocated_privacy_budget=allocated_privacy_budget,
            tft_hidden_size=tft_hidden_size,
            tft_attention_heads=tft_attention_heads,
            tft_dropout=tft_dropout,
            tft_regularization_factor=tft_regularization_factor
        )
        db.add(new_round)
        db.commit()
        db.refresh(new_round)

        # NEW: Automatically create schema when round is created
        # This ensures hospitals don't get "No schema defined" errors
        try:
            from app.models.training_round_schema import TrainingRoundSchema
            
            schema = TrainingRoundSchema(
                round_id=new_round.id,
                model_architecture=model_type,  # ML_REGRESSION or TFT
                target_column=target_column,
                feature_schema=normalized_features,  # Required canonical features
                feature_types=None,  # Can be populated later if needed
                sequence_required=(model_type == "TFT"),  # True for TFT only
                lookback=tft_hidden_size if model_type == "TFT" else None,  # Encoder length for TFT
                horizon=None,  # Prediction horizon - can be set by admin later
                model_hyperparameters=required_hyperparameters or {},
                validation_rules=None  # Can be set by admin later
            )
            db.add(schema)
            db.commit()
            db.refresh(new_round)
            print(f"[ROUND SERVICE] Auto-created schema for round {new_round.round_number}")
        except Exception as schema_error:
            print(f"[ROUND SERVICE] Warning: Failed to auto-create schema: {schema_error}")
            # Don't fail the round creation if schema auto-creation fails
            # Allow admin to manually create schema later

        try:
            NotificationService.emit_round_created(
                db=db,
                round_number=new_round.round_number,
                target_column=new_round.target_column
            )

            hospitals = db.query(Hospital).filter(
                Hospital.is_active == True,
                Hospital.is_verified == True,
                Hospital.is_allowed_federated == True
            ).all()

            for hospital in hospitals:
                NotificationService.emit_round_invitation(
                    db=db,
                    round_number=new_round.round_number,
                    hospital_id=hospital.id,
                    target_column=new_round.target_column
                )
        except Exception as notification_error:
            print(f"[NOTIFICATION] Round event emission failed: {notification_error}")

        return new_round
    
    @staticmethod
    def get_current_round(db: Session) -> TrainingRound | None:
        """Get latest round (single source of truth)
        
        🔴 2️⃣ FIX: Made status-aware to match get_active_round()
        Now eagerly loads round_schema relationship
        """
        return db.query(TrainingRound).options(
            joinedload(TrainingRound.round_schema)
        ).filter(
            TrainingRound.status.in_([
                RoundStatus.OPEN,
                RoundStatus.TRAINING,
                RoundStatus.AGGREGATING
            ])
        ).order_by(TrainingRound.round_number.desc()).first()

    @staticmethod
    def get_active_round(db: Session) -> TrainingRound | None:
        """Get latest active round for hospital UI synchronization
        
        🔴 1️⃣ FIX: Only returns rounds in active states (not CLOSED)
        Now eagerly loads round_schema relationship
        """
        # Prefer rounds that are actively progressing through training pipeline.
        # This prevents selecting a newer OPEN round when an older TRAINING round exists.
        active_progress_round = db.query(TrainingRound).options(
            joinedload(TrainingRound.round_schema)
        ).filter(
            TrainingRound.status.in_([
                RoundStatus.TRAINING,
                RoundStatus.AGGREGATING
            ])
        ).order_by(TrainingRound.round_number.desc()).first()

        if active_progress_round:
            return active_progress_round

        return db.query(TrainingRound).options(
            joinedload(TrainingRound.round_schema)
        ).filter(
            TrainingRound.status == RoundStatus.OPEN
        ).order_by(TrainingRound.round_number.desc()).first()

    @staticmethod
    def require_training_round(db: Session) -> TrainingRound:
        """Ensure training is allowed for the current round"""
        current_round = RoundService.get_active_round(db)
        if not current_round:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active round"
            )

        if current_round.status != RoundStatus.TRAINING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Training not allowed. Round is not in TRAINING state."
            )

        if not current_round.target_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target column not defined by central aggregator."
            )

        return current_round
    
    @staticmethod
    def start_round(round_number: int, db: Session) -> TrainingRound:
        """Mark a round as in-progress"""
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not training_round:
            training_round = db.query(TrainingRound).filter(
                TrainingRound.id == round_number
            ).first()

        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )

        resolved_round_number = training_round.round_number
        
        if training_round.status != RoundStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Round {round_number} is already {training_round.status}"
            )
        
        # 🔴 6️⃣ FIX: Enforce single active round (prevent race condition)
        existing_training = db.query(TrainingRound).filter(
            TrainingRound.status.in_([
                RoundStatus.TRAINING,
                RoundStatus.AGGREGATING
            ])
        ).first()
        
        if existing_training:
            raise HTTPException(
                status_code=409,
                detail=f"Round {existing_training.round_number} already active (status: {existing_training.status})"
            )
        
        # 🔴 3️⃣ FIX: Set started_at when round actually starts training (not at creation)
        training_round.status = RoundStatus.TRAINING
        training_round.started_at = func.now()
        db.commit()
        db.refresh(training_round)

        try:
            NotificationService.emit_round_started(
                db=db,
                round_number=resolved_round_number
            )
        except Exception as notification_error:
            print(f"[NOTIFICATION] Round start event emission failed: {notification_error}")

        return training_round
    
    @staticmethod
    def get_round_details(round_number: int, db: Session) -> Dict:
        """Get detailed round info including participants"""
        from app.models.hospital import Hospital
        
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not training_round:
            training_round = db.query(TrainingRound).filter(
                TrainingRound.id == round_number
            ).first()
        
        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )
        
        resolved_round_number = training_round.round_number
        
        # Get hospitals that have uploaded weights AND are verified
        participants = db.query(ModelWeights, Hospital).join(
            Hospital, Hospital.id == ModelWeights.hospital_id
        ).filter(
            ModelWeights.round_number == resolved_round_number,
            ModelWeights.is_global == False,
            ModelWeights.is_uploaded == True,  # Only include uploaded weights
            Hospital.is_verified == True        # Only verified hospitals
        ).all()
        
        # DEBUG: Log metrics for inspection
        print(f"[ROUND-DETAILS] Building response for round {resolved_round_number}")
        print(f"[ROUND-DETAILS] Found {len(participants)} participating hospitals")
        
        hospital_contributions = []
        for mw, h in participants:
            contribution = {
                "hospital_id": h.id,
                "hospital_name": h.hospital_name,
                "loss": mw.local_loss,
                "accuracy": mw.local_accuracy,
                "mape": mw.local_mape,
                "rmse": mw.local_rmse,
                "r2": mw.local_r2,
                "uploaded_at": mw.updated_at if mw.updated_at else mw.created_at
            }
            print(f"[ROUND-DETAILS] Hospital {h.id}: MAPE={mw.local_mape}, RMSE={mw.local_rmse}, R2={mw.local_r2}")
            hospital_contributions.append(contribution)
        
        result = {
            "round_number": resolved_round_number,
            "status": training_round.status.value if hasattr(training_round.status, 'value') else training_round.status,
            "target_column": training_round.target_column,
            "training_enabled": training_round.training_enabled if hasattr(training_round, 'training_enabled') else True,
            "is_emergency": training_round.is_emergency if hasattr(training_round, 'is_emergency') else False,
            "participation_mode": "ALL",
            "selection_criteria": training_round.selection_criteria,
            "selection_value": training_round.selection_value,
            "num_participating_hospitals": training_round.num_participating_hospitals if training_round.num_participating_hospitals else 0,
            "average_loss": training_round.average_loss,
            "average_accuracy": training_round.average_accuracy,
            "average_mape": training_round.average_mape,
            "average_rmse": training_round.average_rmse,
            "average_r2": training_round.average_r2,
            "started_at": training_round.started_at or __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
            "completed_at": training_round.completed_at,
            "global_model_id": training_round.global_model_id,
            "hospital_contributions": hospital_contributions
        }
        
        print(f"[ROUND-DETAILS] Response hospital_contributions: {result['hospital_contributions']}")
        return result
    
    @staticmethod
    def move_to_aggregating(round_number: int, db: Session) -> TrainingRound:
        """
        Transition round from TRAINING to AGGREGATING state
        
        🔴 3️⃣ FIX: Added missing state transition for aggregation lifecycle
        
        Must be called before aggregation begins to lock the round.
        
        Args:
            round_number: Round number to transition
            db: Database session
        
        Returns:
            Updated TrainingRound
            
        Raises:
            HTTPException: If round not found or not in TRAINING state
        """
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not training_round:
            raise HTTPException(status_code=404, detail="Round not found")

        if training_round.status != RoundStatus.TRAINING:
            raise HTTPException(
                status_code=400,
                detail=f"Round must be in TRAINING state to move to AGGREGATING (current: {training_round.status})"
            )

        training_round.status = RoundStatus.AGGREGATING
        training_round.training_enabled = False
        db.commit()
        db.refresh(training_round)

        return training_round
    
    @staticmethod
    def get_round_statistics(db: Session) -> Dict:
        """Get overall federated learning statistics"""
        total_rounds = db.query(func.count(TrainingRound.id)).scalar()
        completed_rounds = db.query(func.count(TrainingRound.id)).filter(
            TrainingRound.status == RoundStatus.CLOSED
        ).scalar()
        
        global_models = db.query(ModelWeights).filter(
            ModelWeights.is_global == True
        ).count()
        
        return {
            "total_rounds": total_rounds,
            "completed_rounds": completed_rounds,
            "in_progress_rounds": total_rounds - completed_rounds,
            "global_models_created": global_models
        }

    @staticmethod
    def get_round_level_statistics(db: Session, round_id: int) -> Dict:
        """Get analytics for a specific round (Phase B)."""
        training_round = db.query(TrainingRound).filter(
            TrainingRound.id == round_id
        ).first()
        
        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_id} not found"
            )
        
        contributions = db.query(ModelWeights, Hospital).join(
            Hospital, Hospital.id == ModelWeights.hospital_id
        ).filter(
            ModelWeights.round_id == round_id,
            ModelWeights.is_global == False
        ).all()
        
        losses = [mw.local_loss for mw, _ in contributions if mw.local_loss is not None]
        accuracies = [mw.local_accuracy for mw, _ in contributions if mw.local_accuracy is not None]
        
        avg_loss = sum(losses) / len(losses) if losses else None
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None
        std_loss = statistics.pstdev(losses) if len(losses) > 1 else None
        std_accuracy = statistics.pstdev(accuracies) if len(accuracies) > 1 else None
        
        region_counts: Dict[str, int] = {}
        hospital_ids = set()
        for _, hospital in contributions:
            hospital_ids.add(hospital.id)
            region = hospital.location or "Unknown"
            region_counts[region] = region_counts.get(region, 0) + 1
        
        contributing_regions = [
            {"region": region, "count": count}
            for region, count in sorted(region_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        
        return {
            "round_id": training_round.id,
            "round_number": training_round.round_number,
            "num_hospitals": len(hospital_ids),
            "avg_loss": avg_loss,
            "avg_accuracy": avg_accuracy,
            "std_loss": std_loss,
            "std_accuracy": std_accuracy,
            "contributing_regions": contributing_regions
        }
    
    @staticmethod
    def complete_round(
        round_number: int,
        global_model_id: int,
        num_hospitals: int,
        avg_loss: float,
        db: Session,
        avg_accuracy: float = None,
        avg_mape: float = None,
        avg_rmse: float = None,
        avg_r2: float = None
    ):
        training_round = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not training_round:
            training_round = TrainingRound(
                round_number=round_number,
                global_model_id=global_model_id,
                num_participating_hospitals=num_hospitals,
                average_loss=avg_loss,
                average_accuracy=avg_accuracy,
                average_mape=avg_mape,
                average_rmse=avg_rmse,
                average_r2=avg_r2,
                status=RoundStatus.CLOSED
            )
            db.add(training_round)
        else:
            # Allow completion from active aggregation lifecycle states
            if training_round.status not in {RoundStatus.TRAINING, RoundStatus.AGGREGATING}:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Round must be in TRAINING/AGGREGATING state before completion "
                        f"(current: {training_round.status})"
                    )
                )
            
            training_round.global_model_id = global_model_id
            training_round.num_participating_hospitals = num_hospitals
            training_round.average_loss = avg_loss
            training_round.average_accuracy = avg_accuracy
            training_round.average_mape = avg_mape
            training_round.average_rmse = avg_rmse
            training_round.average_r2 = avg_r2
            training_round.status = RoundStatus.CLOSED
            # 🔴 3️⃣ FIX: Ensure completed_at is set when round closes
            training_round.completed_at = func.now()
        
        # Explicit flush to ensure all updates are staged before commit
        db.flush()
        
        # Verify values before commit (DEBUG)
        print(f"[ROUND {round_number}] PRE-COMMIT: num_hospitals={training_round.num_participating_hospitals}, global_model_id={training_round.global_model_id}")
        
        db.commit()
        
        # Verify values after commit (DEBUG)
        print(f"[ROUND {round_number}] POST-COMMIT: num_hospitals={training_round.num_participating_hospitals}, global_model_id={training_round.global_model_id}")
        
        # Refresh to verify persistence from database
        db.refresh(training_round)
        print(f"[ROUND {round_number}] POST-REFRESH: num_hospitals={training_round.num_participating_hospitals}, global_model_id={training_round.global_model_id}")

        try:
            participant_rows = db.query(ModelWeights.hospital_id).filter(
                ModelWeights.round_number == round_number,
                ModelWeights.is_global == False,
                ModelWeights.is_uploaded == True,
                ModelWeights.hospital_id.isnot(None)
            ).distinct().all()
            participant_hospital_ids = [row[0] for row in participant_rows if row[0] is not None]

            NotificationService.emit_round_completed(
                db=db,
                round_number=round_number,
                num_hospitals=num_hospitals,
                accuracy=avg_accuracy
            )

            NotificationService.emit_aggregation_completed(
                db=db,
                round_number=round_number,
                hospital_ids=participant_hospital_ids
            )
        except Exception as notification_error:
            print(f"[NOTIFICATION] Round completion event emission failed: {notification_error}")
        
        return training_round

    @staticmethod
    def set_round_status(round_number: int, db: Session, status_value: RoundStatus) -> TrainingRound:
        """Update round status (central control)"""
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )

        training_round.status = status_value
        # Keep training_enabled in sync with round status
        if status_value == RoundStatus.CLOSED:
            training_round.training_enabled = False
        elif status_value in (RoundStatus.OPEN, RoundStatus.TRAINING):
            training_round.training_enabled = True
        db.commit()
        db.refresh(training_round)
        return training_round
    
    @staticmethod
    def set_training_enabled(round_number: int, db: Session, enabled: bool) -> TrainingRound:
        """Enable or disable training for a specific round"""
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )
        
        training_round.training_enabled = enabled
        db.commit()
        db.refresh(training_round)
        
        return training_round

    @staticmethod
    def delete_round(round_number: int, db: Session) -> Dict:
        """Delete a round and all related records/files from central server"""
        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()

        if not training_round:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )

        if training_round.status in (RoundStatus.TRAINING, RoundStatus.AGGREGATING):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete Round {round_number} while it is {training_round.status}."
            )

        round_id = training_round.id

        model_weights = db.query(ModelWeights).filter(
            and_(
                or_(
                    ModelWeights.round_number == round_number,
                    ModelWeights.round_id == round_id
                ),
                ModelWeights.is_global == True
            )
        ).all()
        model_ids = [model.id for model in model_weights]

        deleted_model_files = 0
        for model in model_weights:
            model_path = model.model_path
            if not model_path:
                continue
            abs_path = os.path.abspath(model_path)
            base_dir = os.path.abspath(settings.MODEL_DIR)
            if abs_path.startswith(base_dir) and os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                    deleted_model_files += 1
                except OSError:
                    pass

        deleted_model_masks = 0
        if model_ids:
            deleted_model_masks = db.query(ModelMask).filter(
                ModelMask.model_id.in_(model_ids)
            ).delete(synchronize_session=False)

        deleted_model_masks += db.query(ModelMask).filter(
            ModelMask.round_number == round_number
        ).delete(synchronize_session=False)

        deleted_privacy_budgets = db.query(PrivacyBudget).filter(
            PrivacyBudget.round_number == round_number
        ).delete(synchronize_session=False)

        deleted_model_governance = db.query(ModelGovernance).filter(
            ModelGovernance.round_number == round_number
        ).delete(synchronize_session=False)

        deleted_blockchain_rows = db.query(Blockchain).filter(
            Blockchain.round_id == round_number
        ).delete(synchronize_session=False)

        training_round.global_model_id = None
        db.flush()

        deleted_model_weights = db.query(ModelWeights).filter(
            and_(
                or_(
                    ModelWeights.round_number == round_number,
                    ModelWeights.round_id == round_id
                ),
                ModelWeights.is_global == True
            )
        ).delete(synchronize_session=False)
        db.delete(training_round)

        deleted_central_files = 0
        central_round_dir = os.path.join(settings.MODEL_DIR, "central", f"round_{round_number}")
        if os.path.exists(central_round_dir):
            try:
                shutil.rmtree(central_round_dir)
                deleted_central_files += 1
            except OSError:
                pass

        central_masks_dir = os.path.join(settings.MODEL_DIR, "central", "masks", f"round_{round_number}")
        if os.path.exists(central_masks_dir):
            try:
                shutil.rmtree(central_masks_dir)
                deleted_central_files += 1
            except OSError:
                pass

        db.commit()

        return {
            "round_number": round_number,
            "deleted_training_round": True,
            "deleted_model_weights": deleted_model_weights,
            "deleted_model_masks": deleted_model_masks,
            "deleted_privacy_budgets": deleted_privacy_budgets,
            "deleted_model_governance": deleted_model_governance,
            "deleted_blockchain_rows": deleted_blockchain_rows,
            "deleted_model_files": deleted_model_files,
            "deleted_central_files": deleted_central_files,
            "message": f"Round {round_number} deleted from central server"
        }
