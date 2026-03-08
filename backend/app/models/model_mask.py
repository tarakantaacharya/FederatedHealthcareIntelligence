"""
Model Mask tracking (Phase 41)
Stores MPC masks for encrypted model participation

GOVERNANCE INVARIANTS:
- UNIQUE (model_id): Exactly ONE mask per model
- model_id → model_weights.id: Foreign key enforcement
- mask_checksum: SHA256 of mask payload for integrity
- Only set mask_uploaded=TRUE after all validation passes
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ModelMask(Base):
    __tablename__ = "model_masks"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_weights.id"), nullable=False)
    
    # Mask metadata
    round_number = Column(Integer, nullable=False, index=True)
    mask_checksum = Column(String(128), nullable=False)  # SHA256 of mask payload
    mask_algorithm = Column(String(50), default="additive_mpc")  # Masking algorithm used
    
    # Validation
    is_verified = Column(Boolean, default=False)  # Checksum verified
    verification_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # GOVERNANCE CONSTRAINTS (Phase 41)
    __table_args__ = (
        # INVARIANT: Exactly ONE mask per model
        UniqueConstraint('model_id', name='uq_model_mask'),
    )
    
    # Relationships
    model_weights = relationship("ModelWeights", backref="mask")
    
    def __repr__(self):
        return f"<ModelMask Model {self.model_id} Round {self.round_number}>"
