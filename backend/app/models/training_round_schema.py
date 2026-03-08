"""
Training Round Schema Model
===========================
CRITICAL: Federated training governance contract

This model defines the schema that hospitals MUST follow
for federated training rounds.

Central server controls:
- Target column
- Feature schema (exact columns required)
- Feature types
- Lookback window (for TFT)
- Prediction horizon (for TFT)
- Model architecture

Hospitals CANNOT change these during federated training.
"""
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class TrainingRoundSchema(Base):
    """
    Schema governance for federated training rounds.
    
    ARCHITECTURAL ROLE:
    - Enforces consistent feature schema across hospitals
    - Prevents feature mismatch during aggregation
    - Locks target column per round
    - Defines sequence parameters for TFT
    
    OWNERSHIP:
    - Central server creates this when starting round
    - Hospitals VALIDATE against this, cannot modify
    """
    __tablename__ = "training_round_schemas"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to training round
    round_id = Column(Integer, ForeignKey("training_rounds.id"), unique=True, nullable=False, index=True)
    
    # Model architecture (ML_REGRESSION or TFT)
    model_architecture = Column(String(50), nullable=False, index=True)
    # Allowed: ML_REGRESSION, TFT
    
    # Target column (LOCKED for this round)
    target_column = Column(String(100), nullable=False)
    
    # Feature schema (ORDERED list of required columns)
    # Example: ["er_visits", "admissions", "discharges", "icu_sedation_level_avg", ...]
    feature_schema = Column(JSON, nullable=False)
    
    # Feature types mapping
    # Example: {"er_visits": "float", "admissions": "int", ...}
    feature_types = Column(JSON, nullable=True)
    
    # Sequence parameters (for TFT only)
    sequence_required = Column(Boolean, default=False)
    lookback = Column(Integer, nullable=True)  # Encoder length for TFT
    horizon = Column(Integer, nullable=True)   # Prediction horizon for TFT
    
    # Model hyperparameters (LOCKED for federated)
    # Example: {"hidden_size": 64, "num_layers": 2, "dropout": 0.1}
    model_hyperparameters = Column(JSON, nullable=True)
    
    # Validation rules
    # Example: {"min_samples": 100, "max_missing_rate": 0.05}
    validation_rules = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_round = relationship("TrainingRound", back_populates="round_schema")
    
    def __repr__(self):
        return (
            f"<TrainingRoundSchema(round_id={self.round_id}, "
            f"architecture={self.model_architecture}, "
            f"target={self.target_column}, "
            f"features={len(self.feature_schema or [])})>"
        )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "round_id": self.round_id,
            "model_architecture": self.model_architecture,
            "target_column": self.target_column,
            "feature_schema": self.feature_schema,
            "feature_types": self.feature_types,
            "sequence_required": self.sequence_required,
            "lookback": self.lookback,
            "horizon": self.horizon,
            "model_hyperparameters": self.model_hyperparameters,
            "validation_rules": self.validation_rules,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_feature_count(self) -> int:
        """Get number of required features."""
        return len(self.feature_schema) if self.feature_schema else 0
    
    def is_ml_architecture(self) -> bool:
        """Check if this is ML regression architecture."""
        return self.model_architecture == "ML_REGRESSION"
    
    def is_tft_architecture(self) -> bool:
        """Check if this is TFT architecture."""
        return self.model_architecture == "TFT"
    
    def validate_feature_columns(self, provided_columns: list) -> tuple[bool, list, list]:
        """
        Validate that provided columns match required schema.
        
        Args:
            provided_columns: List of column names from hospital dataset
        
        Returns:
            Tuple of (is_valid, missing_columns, extra_columns)
        """
        required = set(self.feature_schema or [])
        provided = set(provided_columns)
        
        missing = list(required - provided)
        extra = list(provided - required)
        
        is_valid = len(missing) == 0 and len(extra) == 0
        
        return is_valid, missing, extra
