"""
Model Governance ORM Model (Phase 29)
Tracks approval, signatures, and policy compliance for federated models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class ModelGovernance(Base):
    """
    Model governance and approval tracking
    
    Stores approval decisions, cryptographic signatures, and audit trail
    for federated global models.
    """
    __tablename__ = "model_governance"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False, index=True)
    model_hash = Column(String(256), nullable=False, index=True)
    approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String(100), nullable=True)
    signature = Column(String(512), nullable=True)
    policy_version = Column(String(50), default="v1", nullable=False)
    policy_details = Column(Text, nullable=True)  # JSON string of policy evaluation
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
