"""
Hospital profile model (Phase A governance extension)
Stores extended biodata for each hospital
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class HospitalProfile(Base):
    __tablename__ = "hospitals_profile"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), unique=True, nullable=False)

    license_number = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    bed_capacity = Column(Integer, nullable=True)
    icu_capacity = Column(Integer, nullable=True)
    size_category = Column(String(50), nullable=True)  # SMALL or LARGE
    experience_level = Column(String(50), nullable=True)  # NEW or EXPERIENCED
    specializations = Column(Text, nullable=True)  # JSON string or comma-separated list
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    accreditation_status = Column(String(50), nullable=True)
    registration_date = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(String(30), nullable=True)
    risk_score = Column(Float, nullable=True)

    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    ownership_type = Column(String(50), nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    last_audit_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    hospital = relationship("Hospital", backref="profile")

    def __repr__(self):
        return f"<HospitalProfile hospital_id={self.hospital_id}>"
