"""
Federated intelligence layer for Copilot.
Provides deterministic analysis functions using structured platform context.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.model_weights import ModelWeights
from app.models.prediction_record import PredictionRecord
from app.models.training_rounds import TrainingRound
from app.models.privacy_budget import PrivacyBudget
from app.models.blockchain import Blockchain


class FederatedIntelligenceService:
    @staticmethod
    def list_predictions_by_round(
        db: Session,
        round_number: int,
        role: str,
        hospital_id: Optional[int],
        limit: int = 20,
    ) -> Dict[str, Any]:
        query = db.query(PredictionRecord).filter(PredictionRecord.round_number == round_number)
        if role == "HOSPITAL" and hospital_id is not None:
            query = query.filter(PredictionRecord.hospital_id == hospital_id)

        rows = query.order_by(PredictionRecord.created_at.desc()).limit(limit).all()
        return {
            "round_number": round_number,
            "count": len(rows),
            "items": [
                {
                    "id": p.id,
                    "model_type": p.model_type,
                    "prediction_timestamp": p.prediction_timestamp.isoformat() if p.prediction_timestamp else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in rows
            ],
        }

    @staticmethod
    def compare_rounds(db: Session, round1: int, round2: int) -> Dict[str, Any]:
        r1 = db.query(TrainingRound).filter(TrainingRound.round_number == round1).first()
        r2 = db.query(TrainingRound).filter(TrainingRound.round_number == round2).first()
        if not r1 or not r2:
            return {"error": "One or both rounds not found"}

        epsilon1 = db.query(PrivacyBudget).filter(PrivacyBudget.round_number == round1).order_by(PrivacyBudget.id.desc()).first()
        epsilon2 = db.query(PrivacyBudget).filter(PrivacyBudget.round_number == round2).order_by(PrivacyBudget.id.desc()).first()

        return {
            "round_1": round1,
            "round_2": round2,
            "accuracy_delta": (r2.average_accuracy or 0) - (r1.average_accuracy or 0),
            "loss_delta": (r2.average_loss or 0) - (r1.average_loss or 0),
            "participants_delta": (r2.num_participating_hospitals or 0) - (r1.num_participating_hospitals or 0),
            "dp_epsilon_delta": ((epsilon2.epsilon if epsilon2 else 0) - (epsilon1.epsilon if epsilon1 else 0)),
            "status_pair": [
                r1.status.value if hasattr(r1.status, "value") else r1.status,
                r2.status.value if hasattr(r2.status, "value") else r2.status,
            ],
        }

    @staticmethod
    def explain_prediction(db: Session, prediction_id: int, role: str, hospital_id: Optional[int]) -> Dict[str, Any]:
        query = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id)
        if role == "HOSPITAL" and hospital_id is not None:
            query = query.filter(PredictionRecord.hospital_id == hospital_id)

        pred = query.first()
        if not pred:
            return {"error": "Prediction not found or access denied"}

        model = db.query(ModelWeights).filter(ModelWeights.id == pred.model_id).first()
        dataset = db.query(Dataset).filter(Dataset.id == pred.dataset_id).first() if pred.dataset_id else None

        top_features: List[Dict[str, Any]] = []
        if isinstance(pred.feature_importance, dict):
            sorted_features = sorted(pred.feature_importance.items(), key=lambda item: item[1], reverse=True)
            top_features = [{"feature": k, "importance": v} for k, v in sorted_features[:5]]

        return {
            "prediction_id": pred.id,
            "model_type": pred.model_type,
            "round_number": pred.round_number,
            "dataset": dataset.filename if dataset else None,
            "confidence_interval": pred.confidence_interval,
            "top_features": top_features,
            "federated_training_impact": {
                "training_type": model.training_type if model else None,
                "participants": pred.aggregation_participants,
                "dp_epsilon": pred.dp_epsilon_used,
            },
        }

    @staticmethod
    def summarize_dataset(db: Session, dataset_id: int, role: str, hospital_id: Optional[int]) -> Dict[str, Any]:
        query = db.query(Dataset).filter(Dataset.id == dataset_id)
        if role == "HOSPITAL" and hospital_id is not None:
            query = query.filter(Dataset.hospital_id == hospital_id)

        dataset = query.first()
        if not dataset:
            return {"error": "Dataset not found or access denied"}

        return {
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "rows": dataset.num_rows,
            "columns": dataset.num_columns,
            "times_trained": dataset.times_trained,
            "times_federated": dataset.times_federated,
            "last_training_type": dataset.last_training_type,
            "involved_rounds": dataset.involved_rounds or [],
            "schema_status": "available" if dataset.column_names else "missing",
        }

    @staticmethod
    def audit_round(db: Session, round_number: int) -> Dict[str, Any]:
        training_round = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not training_round:
            return {"error": "Round not found"}

        block = db.query(Blockchain).filter(Blockchain.round_id == round_number).order_by(Blockchain.id.desc()).first()
        masks = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_mask_uploaded == True,
            ModelWeights.is_global == False,
        ).count()

        budget = db.query(PrivacyBudget).filter(PrivacyBudget.round_number == round_number).order_by(PrivacyBudget.id.desc()).first()

        return {
            "round_number": round_number,
            "integrity": {
                "block_hash": block.block_hash if block else None,
                "model_hash": block.model_hash if block else None,
                "immutable_recorded": block is not None,
            },
            "privacy": {
                "epsilon": budget.epsilon if budget else None,
                "delta": budget.delta if budget else None,
                "compliance_note": "Higher epsilon gives weaker privacy, often better utility" if budget else "No DP budget record",
            },
            "mpc": {
                "uploaded_masks": masks,
            },
            "round_status": training_round.status.value if hasattr(training_round.status, "value") else training_round.status,
        }

    @staticmethod
    def analyze_participation(db: Session, round_number: int, role: str, hospital_id: Optional[int]) -> Dict[str, Any]:
        round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if not round_obj:
            return {"error": "Round not found"}

        q = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == False,
        )
        if role == "HOSPITAL" and hospital_id is not None:
            q = q.filter(ModelWeights.hospital_id == hospital_id)

        models = q.all()
        uploaded = sum(1 for m in models if m.is_uploaded)
        masked = sum(1 for m in models if m.is_mask_uploaded)

        return {
            "round_number": round_number,
            "models_found": len(models),
            "weights_uploaded": uploaded,
            "masks_uploaded": masked,
            "participation_rate": (uploaded / len(models)) if models else 0,
            "expected_min_hospitals": 2,
            "eligible_for_aggregation": (round_obj.num_participating_hospitals or 0) >= 2,
        }

    @staticmethod
    def diagnose_submission_issue(db: Session, round_number: Optional[int], role: str, hospital_id: Optional[int]) -> Dict[str, Any]:
        if role != "HOSPITAL" or hospital_id is None:
            return {"summary": "Troubleshooting detail is available to hospitals for own submissions only."}

        if round_number is None:
            latest_model = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.is_global == False,
            ).order_by(ModelWeights.id.desc()).first()
            round_number = latest_model.round_number if latest_model else None

        if round_number is None:
            return {"summary": "No local submission records found for diagnosis."}

        model = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital_id,
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == False,
        ).order_by(ModelWeights.id.desc()).first()

        if not model:
            return {"summary": f"No model found for round {round_number}. Possible reason: training not completed."}

        issues = []
        if not model.is_uploaded:
            issues.append("Weights are not uploaded yet")
        if model.is_uploaded and not model.is_mask_uploaded:
            issues.append("MPC mask not uploaded yet")
        if not model.training_schema:
            issues.append("Training schema metadata missing")

        round_obj = db.query(TrainingRound).filter(TrainingRound.round_number == round_number).first()
        if round_obj and (round_obj.status.value if hasattr(round_obj.status, "value") else round_obj.status) == "CLOSED":
            issues.append("Round deadline/status already closed")

        budget = db.query(PrivacyBudget).filter(
            PrivacyBudget.hospital_id == hospital_id,
            PrivacyBudget.round_number == round_number,
        ).order_by(PrivacyBudget.id.desc()).first()
        if budget and budget.total_epsilon_budget is not None and (budget.epsilon_spent or 0) > budget.total_epsilon_budget:
            issues.append("DP budget exceeded for this round")

        if model.training_schema and isinstance(model.training_schema, dict):
            required = model.training_schema.get("required_columns")
            if required is not None and len(required) == 0:
                issues.append("Schema validation warning: required feature set is empty")

        if not issues:
            issues.append("No blocking issue detected in metadata. Check schema mapping, round deadline, and policy constraints.")

        return {
            "round_number": round_number,
            "model_id": model.id,
            "is_uploaded": model.is_uploaded,
            "is_mask_uploaded": model.is_mask_uploaded,
            "issues": issues,
        }
