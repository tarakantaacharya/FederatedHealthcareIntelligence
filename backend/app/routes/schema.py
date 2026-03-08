"""
Schema management routes (Phase 8)
Canonical schema access and validation
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from app.database import get_db
from app.utils.auth import require_role
from app.services.schema_validation_service import SchemaValidationService

router = APIRouter()

# Initialize schema service
schema_service = SchemaValidationService()


@router.get("/canonical")
async def get_canonical_schema(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get complete canonical schema definition
    
    Returns the full canonical schema v1.0 with all field categories,
    types, constraints, and validation rules.
    """
    return schema_service.get_schema()


@router.get("/fields")
async def get_all_fields(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get all canonical fields with specifications
    
    Returns dictionary of all fields across all categories
    with their types, constraints, and descriptions.
    """
    return schema_service.get_all_fields()


@router.get("/fields/required")
async def get_required_fields(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> List[str]:
    """
    Get list of required fields
    
    Returns field names that are mandatory in the canonical schema.
    """
    return schema_service.get_required_fields()


@router.get("/synonyms")
async def get_field_synonyms(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get field mapping hints and synonyms
    
    Returns common variations and synonyms for canonical fields
    to assist with automatic column mapping.
    """
    return schema_service.get_field_synonyms()


@router.get("/suggest-mapping/{column_name}")
async def suggest_field_mapping(
    column_name: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> List[Dict]:
    """
    Get mapping suggestions for a column name
    
    - **column_name**: Original column name from hospital CSV
    
    Returns suggested canonical field mappings with confidence scores.
    Used by Phase 9 mapping engine.
    """
    suggestions = schema_service.suggest_field_mapping(column_name)
    return suggestions
