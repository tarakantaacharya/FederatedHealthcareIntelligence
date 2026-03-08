"""
Dataset intelligence service (Phase B)
Tracks dataset training history and usage patterns
"""
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.model_weights import ModelWeights
from datetime import datetime
from typing import Dict, Any


class DatasetIntelligenceService:
    """Tracks and reports on dataset training history"""
    
    @staticmethod
    def update_training_intelligence(
        db: Session,
        dataset_id: int,
        training_type: str,
        round_number: int = None
    ) -> None:
        """
        Update dataset intelligence after training completion
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            training_type: LOCAL or FEDERATED
            round_number: Round number (for FEDERATED only)
        """
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return
        
        # Update training counts
        dataset.times_trained = (dataset.times_trained or 0) + 1
        
        if training_type == "FEDERATED":
            dataset.times_federated = (dataset.times_federated or 0) + 1
            
            # Update involved_rounds
            involved_rounds = dataset.involved_rounds or []
            if round_number and round_number not in involved_rounds:
                involved_rounds.append(round_number)
                dataset.involved_rounds = involved_rounds
        
        # Update last training metadata
        dataset.last_trained_at = datetime.utcnow()
        dataset.last_training_type = training_type
        
        db.commit()
    
    @staticmethod
    def get_dataset_status(db: Session, dataset_id: int, hospital_id: int) -> Dict[str, Any]:
        """
        Get comprehensive status of dataset training history
        
        Returns:
            {
                "trained_local": bool,
                "trained_federated": bool,
                "rounds": [int],
                "mask_uploaded": bool,
                "weights_uploaded": bool,
                "times_trained": int,
                "times_federated": int,
                "last_trained_at": str,
                "last_training_type": str
            }
        """
        # Verify ownership
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.hospital_id == hospital_id
        ).first()
        
        if not dataset:
            return None
        
        # Check if any models exist for this dataset
        models = db.query(ModelWeights).filter(
            ModelWeights.dataset_id == dataset_id,
            ModelWeights.hospital_id == hospital_id
        ).all()
        
        # Check for local and federated training
        local_models = [m for m in models if m.training_type == "LOCAL"]
        federated_models = [m for m in models if m.training_type == "FEDERATED"]
        
        # Check if any masks/weights uploaded
        mask_uploaded = any(m.is_mask_uploaded for m in models)
        weights_uploaded = any(m.is_uploaded for m in models)
        
        return {
            "dataset_id": dataset_id,
            "trained_local": len(local_models) > 0,
            "trained_federated": len(federated_models) > 0,
            "rounds": dataset.involved_rounds or [],
            "mask_uploaded": mask_uploaded,
            "weights_uploaded": weights_uploaded,
            "times_trained": dataset.times_trained or 0,
            "times_federated": dataset.times_federated or 0,
            "last_trained_at": dataset.last_trained_at.isoformat() if dataset.last_trained_at else None,
            "last_training_type": dataset.last_training_type
        }
