"""
Pydantic schemas for Hospital entity
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Literal


class HospitalRegister(BaseModel):
    hospital_id: str
    hospital_name: str
    contact_email: EmailStr
    location: Optional[str] = None
    password: str
    role: Literal["HOSPITAL", "ADMIN"] = Field(default="HOSPITAL", description="Hospital role: HOSPITAL or ADMIN for central aggregation")


class HospitalLogin(BaseModel):
    hospital_id: str
    password: str


class HospitalResponse(BaseModel):
    id: int
    hospital_id: str
    hospital_name: str
    contact_email: str
    location: Optional[str]
    is_active: bool
    is_verified: bool
    verification_status: Optional[str] = None
    is_allowed_federated: Optional[bool] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    hospital_id: str
    hospital_name: str
    verification_status: str = "VERIFIED"  # PENDING, VERIFIED, REJECTED
    pending_verification: bool = False  # Phase A-Pro: PENDING hospitals can login
