"""
Pydantic schemas for Admin authentication (Central Server)
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class AdminLogin(BaseModel):
    admin_id: str
    password: str


class AdminResponse(BaseModel):
    id: int
    admin_id: str
    admin_name: str
    contact_email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: str
    admin_name: str
