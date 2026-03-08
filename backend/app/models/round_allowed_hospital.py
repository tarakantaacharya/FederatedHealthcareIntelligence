"""
Round allowed hospitals junction table (Phase A-Pro)
Links hospitals to training rounds for SELECTED participation policy
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class RoundAllowedHospital(Base):
    __tablename__ = "round_allowed_hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('round_id', 'hospital_id', name='unique_round_hospital'),
    )
    
    def __repr__(self):
        return f"<RoundAllowedHospital round={self.round_id} hospital={self.hospital_id}>"
