"""
Category extension routes (Phase 11)
Treatment category-specific fields
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.utils.auth import require_role
from app.services.category_service import CategoryService

router = APIRouter()

# Initialize category service
category_service = CategoryService()


@router.get("/all")
async def get_all_categories(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get all category extensions
    
    Returns complete category definitions including:
    - ICU (Intensive Care Unit)
    - Emergency Department
    - OPD (Outpatient Department)
    - IPD (Inpatient Department)
    - Surgery
    - Pediatrics
    - Cardiology
    """
    return category_service.get_all_categories()


@router.get("/list")
async def list_category_names(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> List[str]:
    """
    Get list of available category names
    
    Returns: ["icu", "emergency", "opd", "ipd", "surgery", "pediatrics", "cardiology"]
    """
    return category_service.get_all_category_names()


@router.get("/{category_name}")
async def get_category_info(
    category_name: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get detailed information about a specific category
    
    - **category_name**: Category ID (icu, emergency, opd, ipd, surgery, pediatrics, cardiology)
    
    Returns category name, description, and field definitions.
    """
    return category_service.get_category_info(category_name)


@router.get("/{category_name}/fields")
async def get_category_fields(
    category_name: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict:
    """
    Get field definitions for a category
    
    - **category_name**: Category ID
    
    Returns dictionary of field specifications.
    """
    return category_service.get_category_fields(category_name)


@router.get("/{category_name}/field-list")
async def get_category_field_list(
    category_name: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> List[str]:
    """
    Get list of prefixed field names for a category
    
    - **category_name**: Category ID
    
    Returns list like: ["icu_ventilator_usage", "icu_sedation_level_avg", ...]
    
    These prefixed names are used in CSV columns for category-specific data.
    """
    return category_service.get_category_field_list(category_name)
