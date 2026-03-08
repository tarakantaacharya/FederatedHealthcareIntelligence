"""
Canonical field schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CanonicalFieldResponse(BaseModel):
    id: int
    field_name: str
    description: Optional[str] = None
    data_type: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CanonicalFieldListResponse(BaseModel):
    total: int
    fields: list[CanonicalFieldResponse]
