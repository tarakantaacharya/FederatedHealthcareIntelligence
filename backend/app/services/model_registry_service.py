"""
Model Registry Service (Phase 34)
Multi-model federation with version control
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from app.models.model_registry import ModelRegistry
import logging

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Service for managing multiple federated models"""
    
    MODEL_TYPES = {
        'baseline_rf': 'Random Forest Baseline',
        'tft': 'Temporal Fusion Transformer',
        'lstm': 'Long Short-Term Memory',
        'xgboost': 'XGBoost Regressor',
        'category_specific': 'Category-Specific Model'
    }
    
    @staticmethod
    def register_model(
        db: Session,
        model_name: str,
        model_type: str,
        version: str,
        hospital_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> ModelRegistry:
        """
        Register a new model in the registry
        
        Args:
            db: Database session
            model_name: Model identifier
            model_type: Type of model (baseline_rf, tft, etc.)
            version: Model version (e.g., "1.0.0")
            hospital_id: Hospital ID (for local models)
            metadata: Additional metadata
        
        Returns:
            Created ModelRegistry object
        """
        model = ModelRegistry(
            model_name=model_name,
            model_type=model_type,
            version=version,
            hospital_id=hospital_id,
            is_active=True,
            is_global=hospital_id is None,
            metadata=metadata or {}
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"Registered model: {model_name} v{version} (type: {model_type})")
        return model
    
    @staticmethod
    def get_active_models(
        db: Session,
        model_type: Optional[str] = None,
        hospital_id: Optional[int] = None
    ) -> List[ModelRegistry]:
        """Get all active models, optionally filtered"""
        query = db.query(ModelRegistry).filter(ModelRegistry.is_active == True)
        
        if model_type:
            query = query.filter(ModelRegistry.model_type == model_type)
        
        if hospital_id:
            query = query.filter(ModelRegistry.hospital_id == hospital_id)
        
        return query.all()
    
    @staticmethod
    def get_latest_global_model(
        db: Session,
        model_type: str = 'baseline_rf'
    ) -> Optional[ModelRegistry]:
        """Get latest global model of specified type"""
        return db.query(ModelRegistry).filter(
            ModelRegistry.is_global == True,
            ModelRegistry.is_active == True,
            ModelRegistry.model_type == model_type
        ).order_by(ModelRegistry.created_at.desc()).first()
    
    @staticmethod
    def deactivate_model(db: Session, model_id: int) -> bool:
        """Deactivate a model"""
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        
        if model:
            model.is_active = False
            db.commit()
            logger.info(f"Deactivated model: {model.model_name} v{model.version}")
            return True
        
        return False
    
    @staticmethod
    def update_model_metrics(
        db: Session,
        model_id: int,
        accuracy: Optional[float] = None,
        loss: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """Update model performance metrics"""
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        
        if model:
            if accuracy is not None:
                model.accuracy = accuracy
            if loss is not None:
                model.loss = loss
            if metadata:
                model.model_metadata = {**model.model_metadata, **metadata}
            
            db.commit()
