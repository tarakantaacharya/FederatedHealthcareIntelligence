"""
Hospital entity model (Phase 1)
Stores registered hospital information
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_name = Column(String(255), unique=True, nullable=False, index=True)
    hospital_id = Column(String(100), unique=True, nullable=False)  # External ID
    
    # Contact & Location
    contact_email = Column(String(255), nullable=False)
    location = Column(String(255))
    
    # Credentials
    hashed_password = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String(30), default="PENDING")
    is_allowed_federated = Column(Boolean, default=True)
    
    # Role-Based Access Control (Phase 30)
    role = Column(String(20), default="HOSPITAL", nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Hospital {self.hospital_name}>"
