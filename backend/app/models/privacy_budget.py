"""Privacy budget tracking model (Phase 25 - Concurrency Safe)
Tracks epsilon consumption per hospital and round with DB-level enforcement.

GOVERNANCE CONSTRAINTS:
- Unique (hospital_id, round_number): Prevents duplicate consumption per round
- Enforced at DB layer (MySQL InnoDB) and application layer
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class PrivacyBudget(Base):
    __tablename__ = "privacy_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    
    # Privacy parameters
    epsilon = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    
    # Cumulative tracking
    epsilon_spent = Column(Float, default=0.0)
    total_epsilon_budget = Column(Float)  # Total allowed budget
    
    # Metadata
    mechanism = Column(String(100))  # e.g., 'gaussian', 'laplace'
    sensitivity = Column(Float)
    noise_multiplier = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 🔴 CONCURRENCY ENFORCEMENT: DB-level unique constraint
    # Prevents duplicate budget entries for (hospital, round) even in race conditions
    __table_args__ = (
        UniqueConstraint(
            'hospital_id',
            'round_number',
            name='uq_hospital_round_budget'
        ),
    )
    
    # Relationships
    hospital = relationship("Hospital")
    
    def __repr__(self):
        return f"<PrivacyBudget Hospital {self.hospital_id} Round {self.round_number} ε={self.epsilon_spent:.4f}>"
