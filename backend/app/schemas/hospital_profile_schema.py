"""
Schemas for hospital profile
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HospitalProfileBase(BaseModel):
    license_number: Optional[str] = None
    region: Optional[str] = None
    bed_capacity: Optional[int] = None
    icu_capacity: Optional[int] = None
    size_category: Optional[str] = None  # SMALL or LARGE
    experience_level: Optional[str] = None  # NEW or EXPERIENCED
    specializations: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    accreditation_status: Optional[str] = None
    registration_date: Optional[datetime] = None
    verification_status: Optional[str] = None
    risk_score: Optional[float] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    ownership_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    website: Optional[str] = None
    last_audit_date: Optional[datetime] = None
    notes: Optional[str] = None


class HospitalProfileCreate(HospitalProfileBase):
    pass


class HospitalProfileResponse(HospitalProfileBase):
    id: int
    hospital_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
