"""
Training orchestration layer
Routes call this to avoid executing training logic directly.
"""
from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.services.training_service import TrainingService


class TrainingOrchestrator:
    """Thin wrapper for training execution"""

    @staticmethod
    def start_local_training(
        db: Session,
        hospital: Hospital,
        dataset_id: int,
        target_column: str,
        epochs: int,
        training_request: object | None = None,
        privacy_policy: object | None = None,
        batch_size: int = 32
    ) -> dict:
        return TrainingService.train_local_model(
            db=db,
            hospital=hospital,
            dataset_id=dataset_id,
            target_column=target_column,
            epochs=epochs,
            training_request=training_request,
            privacy_policy=privacy_policy,
            batch_size=batch_size
        )

    @staticmethod
    def list_trained_models(
        db: Session,
        hospital_id: int,
        skip: int,
        limit: int
    ):
        return TrainingService.get_hospital_models(
            db,
            hospital_id,
            skip,
            limit
        )

    @staticmethod
    def get_model_details(
        db: Session,
        model_id: int,
        hospital_id: int
    ):
        return TrainingService.get_model_by_id(db, model_id, hospital_id)
