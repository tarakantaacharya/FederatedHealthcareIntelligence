"""
Chat context injection service for Federated AI Copilot.
Builds role-safe, structured context from platform metadata only.
"""
from typing import Any, Dict, Optional
from collections import defaultdict
import os
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.hospital import Hospital
from app.models.model_mask import ModelMask
from app.models.model_weights import ModelWeights
from app.models.prediction_record import PredictionRecord
from app.models.privacy_budget import PrivacyBudget
from app.models.training_rounds import TrainingRound
from app.models.blockchain import Blockchain
from app.services.training_service import TrainingService
from app.services.participation_service import ParticipationService
from app.services.results_intelligence_service import ResultsIntelligenceService


class CopilotContextService:
    @staticmethod
    def build_context(
        db: Session,
        role: str,
        hospital_id: Optional[int],
        page_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "role": role,
            "hospital_id": hospital_id,
            "page": page_context.get("page", "dashboard"),
            "prediction": None,
            "round": None,
            "dataset": None,
            "governance": None,
            "recent": {},
        }

        prediction_id = page_context.get("prediction_id")
        round_number = page_context.get("round_number")
        dataset_id = page_context.get("dataset_id")

        if prediction_id:
            context["prediction"] = CopilotContextService._prediction_context(
                db=db,
                prediction_id=prediction_id,
                role=role,
                hospital_id=hospital_id,
            )

        if round_number:
            context["round"] = CopilotContextService._round_context(
                db=db,
                round_number=round_number,
                role=role,
                hospital_id=hospital_id,
            )

        if dataset_id:
            context["dataset"] = CopilotContextService._dataset_context(
                db=db,
                dataset_id=dataset_id,
                role=role,
                hospital_id=hospital_id,
            )

        context["governance"] = CopilotContextService._governance_context(
            db=db,
            round_number=round_number,
            hospital_id=hospital_id,
            role=role,
        )

        context["recent"] = CopilotContextService._recent_context(
            db=db,
            role=role,
            hospital_id=hospital_id,
        )

        return context

    @staticmethod
    def _prediction_context(db: Session, prediction_id: int, role: str, hospital_id: Optional[int]) -> Optional[Dict[str, Any]]:
        query = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id)
        if role == "HOSPITAL" and hospital_id is not None:
            query = query.filter(PredictionRecord.hospital_id == hospital_id)

        record = query.first()
        if not record:
            return None

        dataset = db.query(Dataset).filter(Dataset.id == record.dataset_id).first() if record.dataset_id else None
        model = db.query(ModelWeights).filter(ModelWeights.id == record.model_id).first() if record.model_id else None

        return {
            "id": record.id,
            "dataset": dataset.filename if dataset else None,
            "model_type": model.model_architecture if model else record.model_type,  # Use model architecture (TFT/REGRESSION) from ModelWeights
            "round": record.round_number,
            "accuracy": (record.model_accuracy_snapshot or {}).get("accuracy") if isinstance(record.model_accuracy_snapshot, dict) else None,
            "dp_epsilon": record.dp_epsilon_used,
            "prediction_timestamp": record.prediction_timestamp.isoformat() if record.prediction_timestamp else None,
            "feature_importance": record.feature_importance,
            "confidence_interval": record.confidence_interval,
            "summary_text": record.summary_text,
            "training_type": model.training_type if model else None,
        }

    @staticmethod
    def _round_context(db: Session, round_number: int, role: str, hospital_id: Optional[int]) -> Optional[Dict[str, Any]]:
        training_round = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not training_round:
            return None

        local_models_q = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == False,
        )
        if role == "HOSPITAL" and hospital_id is not None:
            local_models_q = local_models_q.filter(ModelWeights.hospital_id == hospital_id)

        local_models = local_models_q.all()
        global_model = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == True,
        ).first()

        return {
            "round_number": training_round.round_number,
            "status": training_round.status.value if hasattr(training_round.status, "value") else training_round.status,
            "target_column": training_round.target_column,
            "num_participating_hospitals": training_round.num_participating_hospitals or 0,
            "average_accuracy": training_round.average_accuracy,
            "average_loss": training_round.average_loss,
            "average_mape": training_round.average_mape,
            "average_rmse": training_round.average_rmse,
            "average_r2": training_round.average_r2,
            "local_model_count": len(local_models),
            "global_model_id": global_model.id if global_model else None,
            "global_model_hash": global_model.model_hash if global_model else None,
        }

    @staticmethod
    def _dataset_context(db: Session, dataset_id: int, role: str, hospital_id: Optional[int]) -> Optional[Dict[str, Any]]:
        query = db.query(Dataset).filter(Dataset.id == dataset_id)
        if role == "HOSPITAL" and hospital_id is not None:
            query = query.filter(Dataset.hospital_id == hospital_id)

        dataset = query.first()
        if not dataset:
            return None

        return {
            "id": dataset.id,
            "filename": dataset.filename,
            "num_rows": dataset.num_rows,
            "num_columns": dataset.num_columns,
            "column_names": dataset.column_names,
            "times_trained": dataset.times_trained,
            "times_federated": dataset.times_federated,
            "last_training_type": dataset.last_training_type,
            "involved_rounds": dataset.involved_rounds,
            "uploaded_at": dataset.uploaded_at.isoformat() if dataset.uploaded_at else None,
        }

    @staticmethod
    def _governance_context(db: Session, round_number: Optional[int], hospital_id: Optional[int], role: str) -> Dict[str, Any]:
        budgets_q = db.query(PrivacyBudget)
        if role == "HOSPITAL" and hospital_id is not None:
            budgets_q = budgets_q.filter(PrivacyBudget.hospital_id == hospital_id)
        if round_number is not None:
            budgets_q = budgets_q.filter(PrivacyBudget.round_number == round_number)

        latest_budget = budgets_q.order_by(PrivacyBudget.id.desc()).first()

        masks_q = db.query(ModelMask)
        if round_number is not None:
            masks_q = masks_q.filter(ModelMask.round_number == round_number)

        blockchain_q = db.query(Blockchain)
        if round_number is not None:
            blockchain_q = blockchain_q.filter(Blockchain.round_id == round_number)

        latest_block = blockchain_q.order_by(Blockchain.id.desc()).first()

        return {
            "dp": {
                "epsilon": latest_budget.epsilon if latest_budget else None,
                "delta": latest_budget.delta if latest_budget else None,
                "epsilon_spent": latest_budget.epsilon_spent if latest_budget else None,
                "mechanism": latest_budget.mechanism if latest_budget else None,
            },
            "mpc": {
                "mask_count": masks_q.count(),
            },
            "blockchain": {
                "last_round": latest_block.round_id if latest_block else None,
                "model_hash": latest_block.model_hash if latest_block else None,
                "block_hash": latest_block.block_hash if latest_block else None,
            },
        }

    @staticmethod
    def _recent_context(db: Session, role: str, hospital_id: Optional[int]) -> Dict[str, Any]:
        rounds = db.query(TrainingRound).order_by(TrainingRound.round_number.desc()).limit(5).all()

        predictions_q = db.query(PredictionRecord)
        if role == "HOSPITAL" and hospital_id is not None:
            predictions_q = predictions_q.filter(PredictionRecord.hospital_id == hospital_id)
        predictions = predictions_q.order_by(PredictionRecord.created_at.desc()).limit(5).all()

        all_predictions_q = db.query(PredictionRecord)
        if role == "HOSPITAL" and hospital_id is not None:
            all_predictions_q = all_predictions_q.filter(PredictionRecord.hospital_id == hospital_id)
        all_predictions = all_predictions_q.all()

        datasets_q = db.query(Dataset)
        models_q = db.query(ModelWeights).filter(ModelWeights.is_global == False)
        if role == "HOSPITAL" and hospital_id is not None:
            datasets_q = datasets_q.filter(Dataset.hospital_id == hospital_id)
            models_q = models_q.filter(ModelWeights.hospital_id == hospital_id)

        local_model_count = models_q.count()
        federated_model_count = 0
        total_model_count = 0
        if role == "HOSPITAL" and hospital_id is not None:
            try:
                deduped_models = TrainingService.get_hospital_models(
                    db=db,
                    hospital_id=hospital_id,
                    skip=0,
                    limit=1000,
                )
                local_model_count = len([
                    model for model in deduped_models
                    if (getattr(model, "training_type", None) == "LOCAL")
                    or (getattr(model, "round_number", 0) == 0)
                ])
                federated_model_count = len([
                    model for model in deduped_models
                    if (getattr(model, "training_type", None) == "FEDERATED")
                    or ((getattr(model, "round_number", 0) or 0) > 0)
                ])
                total_model_count = len(deduped_models)
            except Exception:
                # Fallback to raw count if deduplicated retrieval fails
                local_model_count = models_q.count()
                federated_model_count = db.query(ModelWeights).filter(
                    ModelWeights.hospital_id == hospital_id,
                    (ModelWeights.training_type == "FEDERATED") | (ModelWeights.round_number > 0)
                ).count()
                total_model_count = local_model_count + federated_model_count
        else:
            federated_model_count = db.query(ModelWeights).filter(ModelWeights.is_global == True).count()
            total_model_count = local_model_count + federated_model_count

        latest_prediction = predictions[0] if predictions else None
        participated_round_count = len({p.round_number for p in predictions if p.round_number is not None})

        prediction_local_count = len([
            p for p in all_predictions
            if (getattr(p, "model_type", None) or "").upper() == "LOCAL"
        ])
        prediction_global_count = len([
            p for p in all_predictions
            if (getattr(p, "model_type", None) or "").upper() in {"FEDERATED", "GLOBAL"}
        ])

        if role == "HOSPITAL" and hospital_id is not None:
            dataset_rows = datasets_q.order_by(Dataset.uploaded_at.desc()).all()
        else:
            dataset_rows = datasets_q.order_by(Dataset.uploaded_at.desc()).limit(20).all()

        dataset_details = [
            {
                "id": dataset.id,
                "name": dataset.filename,
                "uploaded_at": dataset.uploaded_at.isoformat() if dataset.uploaded_at else None,
                "times_trained": dataset.times_trained or 0,
                "times_federated": dataset.times_federated or 0,
            }
            for dataset in dataset_rows
        ]
        dataset_names = [dataset["name"] for dataset in dataset_details]
        trained_dataset_count = len([d for d in dataset_details if (d.get("times_trained") or 0) > 0])
        federated_dataset_count = len([d for d in dataset_details if (d.get("times_federated") or 0) > 0])

        local_model_names = []
        federated_model_names = []
        global_model_names = []
        model_type_counts_total: Dict[str, int] = defaultdict(int)
        model_type_counts_local: Dict[str, int] = defaultdict(int)
        model_type_counts_federated: Dict[str, int] = defaultdict(int)

        if role == "HOSPITAL" and hospital_id is not None:
            try:
                deduped_models = TrainingService.get_hospital_models(
                    db=db,
                    hospital_id=hospital_id,
                    skip=0,
                    limit=1000,
                )

                for model in deduped_models:
                    model_label = os.path.basename(getattr(model, "model_path", "") or "")
                    if not model_label:
                        model_label = f"model_{getattr(model, 'id', 'unknown')}"

                    model_family = (getattr(model, "model_type", None) or getattr(model, "model_architecture", None) or "unknown").lower()
                    model_type_counts_total[model_family] += 1

                    is_local = (getattr(model, "training_type", None) == "LOCAL") or ((getattr(model, "round_number", 0) or 0) == 0)
                    if is_local:
                        local_model_names.append(model_label)
                        model_type_counts_local[model_family] += 1
                    else:
                        federated_model_names.append(model_label)
                        model_type_counts_federated[model_family] += 1
            except Exception:
                pass

            global_models = db.query(ModelWeights).filter(ModelWeights.is_global == True).order_by(ModelWeights.round_number.desc()).limit(25).all()
            for gm in global_models:
                hash_part = (gm.model_hash or "")[:8]
                global_model_names.append(f"round_{gm.round_number}_{hash_part}" if hash_part else f"round_{gm.round_number}_global")

        local_model_names = local_model_names[:25]
        federated_model_names = federated_model_names[:25]
        global_model_names = global_model_names[:25]

        rounds_with_targets = [
            {
                "round_number": round_item.round_number,
                "target_column": round_item.target_column,
                "model_type": round_item.model_type,
                "status": round_item.status.value if hasattr(round_item.status, "value") else round_item.status,
            }
            for round_item in db.query(TrainingRound).order_by(TrainingRound.round_number.desc()).limit(20).all()
        ]

        hospital_metrics = {
            "dataset_count": datasets_q.count(),
            "dataset_uploaded_count": datasets_q.count(),
            "dataset_trained_count": trained_dataset_count,
            "dataset_federated_count": federated_dataset_count,
            "dataset_names": dataset_names,
            "dataset_details": dataset_details,
            "local_model_count": local_model_count,
            "local_model_names": local_model_names,
            "federated_model_count": federated_model_count,
            "federated_model_names": federated_model_names,
            "total_model_count": total_model_count,
            "global_model_count": len(global_model_names),
            "global_model_names": global_model_names,
            "model_type_counts_total": dict(model_type_counts_total),
            "model_type_counts_local": dict(model_type_counts_local),
            "model_type_counts_federated": dict(model_type_counts_federated),
            "prediction_count": predictions_q.count(),
            "prediction_local_count": prediction_local_count,
            "prediction_global_count": prediction_global_count,
            "latest_prediction_at": latest_prediction.created_at.isoformat() if latest_prediction and latest_prediction.created_at else None,
            "participated_round_count": participated_round_count,
            "rounds_with_targets": rounds_with_targets,
        }

        latest_round = rounds[0] if rounds else None
        if role == "HOSPITAL" and hospital_id is not None and latest_round is not None:
            is_eligible, eligibility_reason = ParticipationService.can_participate(hospital_id, latest_round.id, db)
            hospital_metrics.update({
                "latest_round_number": latest_round.round_number,
                "latest_round_status": latest_round.status.value if hasattr(latest_round.status, "value") else latest_round.status,
                "latest_round_target_column": latest_round.target_column,
                "latest_round_model_type": latest_round.model_type,
                "latest_round_training_enabled": bool(latest_round.training_enabled),
                "has_active_round": (latest_round.status.value if hasattr(latest_round.status, "value") else latest_round.status) in {"OPEN", "TRAINING"},
                "is_eligible_for_latest_round": bool(is_eligible),
                "eligibility_reason": eligibility_reason,
            })

        if role == "HOSPITAL" and hospital_id is not None:
            participated_rounds = (
                db.query(ModelWeights.round_number)
                .filter(
                    ModelWeights.hospital_id == hospital_id,
                    ModelWeights.is_global == False,
                    ModelWeights.round_number.isnot(None),
                )
                .distinct()
                .order_by(ModelWeights.round_number.desc())
                .limit(5)
                .all()
            )

            recent_rounds = [
                {
                    "round_number": r.round_number,
                    "status": None,
                }
                for r in participated_rounds
            ]

            try:
                hospital_obj = db.query(Hospital).filter(Hospital.id == hospital_id).first()
                if hospital_obj:
                    dashboard = ResultsIntelligenceService.get_hospital_dashboard(db, hospital_obj)
                    overview = dashboard.get("prediction_overview", {}) or {}
                    performance = (dashboard.get("model_performance_comparison", {}) or {}).get("metrics", {}) or {}
                    participation = dashboard.get("federated_participation_impact", {}) or {}
                    dataset_health = dashboard.get("dataset_health", {}) or {}

                    hospital_metrics.update({
                        "ri_total_predictions": overview.get("total_predictions"),
                        "ri_high_risk_count": overview.get("high_risk_count"),
                        "ri_medium_risk_count": overview.get("medium_risk_count"),
                        "ri_low_risk_count": overview.get("low_risk_count"),
                        "ri_average_confidence": overview.get("average_confidence_score"),
                        "ri_accuracy": performance.get("accuracy"),
                        "ri_precision": performance.get("precision"),
                        "ri_recall": performance.get("recall"),
                        "ri_f1": performance.get("f1_score"),
                        "ri_calibration": performance.get("calibration_score"),
                        "ri_rounds_participated": participation.get("rounds_participated"),
                        "ri_rounds_skipped": participation.get("rounds_skipped"),
                        "ri_submission_timeliness": participation.get("weight_submission_timeliness"),
                        "ri_schema_status": dataset_health.get("schema_validation_status"),
                        "ri_schema_quality": dataset_health.get("schema_quality_score"),
                    })
            except Exception:
                pass
        else:
            recent_rounds = [
                {
                    "round_number": r.round_number,
                    "status": r.status.value if hasattr(r.status, "value") else r.status,
                    "accuracy": r.average_accuracy,
                    "participants": r.num_participating_hospitals,
                }
                for r in rounds
            ]

        return {
            "latest_rounds": recent_rounds,
            "latest_predictions": [
                {
                    "id": p.id,
                    "round_number": p.round_number,
                    "model_type": p.model_type,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in predictions
            ],
            "hospital_metrics": hospital_metrics,
        }
