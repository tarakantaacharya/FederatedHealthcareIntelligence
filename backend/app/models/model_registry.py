"""
Model Registry Model (Phase 34)
Database schema for multi-model management
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # baseline_rf, tft, lstm, xgboost
    version = Column(String(20), nullable=False)
    
    # Ownership
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)  # NULL = global
    is_global = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    loss = Column(Float, nullable=True)
    
    # Metadata (renamed to avoid SQLAlchemy reserved name conflict)
    model_metadata = Column(JSON, nullable=True)  # Store model config, hyperparameters, etc.
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
