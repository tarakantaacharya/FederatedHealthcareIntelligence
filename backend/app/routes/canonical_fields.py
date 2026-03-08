"""
Canonical fields routes (Phase 45)
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import require_role
from app.services.canonical_field_service import CanonicalFieldService
from app.schemas.canonical_field_schema import CanonicalFieldResponse, CanonicalFieldListResponse
from typing import List, Dict, Any

router = APIRouter()


@router.get("/canonical-fields", response_model=CanonicalFieldListResponse)
async def get_canonical_fields(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL"))
):
    """
    Get list of approved canonical fields for target column selection
    
    Returns all active canonical fields with descriptions, data types, and metadata.
    Used by admin for round creation and hospitals for schema understanding.
    """
    fields = CanonicalFieldService.get_all_active_fields(db)
    
    return {
        "total": len(fields),
        "fields": [
            CanonicalFieldResponse.from_attributes(field) if hasattr(CanonicalFieldResponse, 'from_attributes')
            else CanonicalFieldResponse(
                id=field.id,
                field_name=field.field_name,
                description=field.description,
                data_type=field.data_type,
                category=field.category,
                unit=field.unit,
                is_active=field.is_active,
                created_at=field.created_at
            )
            for field in fields
        ]
    }
