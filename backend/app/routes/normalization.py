"""
Normalization routes (Phase 10)
CSV data normalization to canonical schema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.dataset import Dataset
from app.utils.auth import require_role
from app.schemas.normalization_schema import (
    NormalizeRequest,
    NormalizeResponse,
    NormalizedPreviewResponse
)
from app.services.normalization_service import NormalizationService

router = APIRouter()

# Initialize normalization service
normalization_service = NormalizationService()


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_dataset(
    request: NormalizeRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Normalize dataset to canonical schema format
    
    - **dataset_id**: Dataset to normalize
    
    Prerequisites:
    - Dataset must be uploaded
    - Column mapping must be completed (Phase 9)
    
    Process:
    1. Applies column mappings
    2. Converts data types
    3. Cleans and validates data
    4. Saves normalized CSV
    
    Returns normalized file path and validation results.
    """
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.hospital_id == current_user["db_object"].id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    try:
        result = normalization_service.normalize_csv(request.dataset_id, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Normalization failed: {str(e)}"
        )


@router.get("/preview/{dataset_id}", response_model=NormalizedPreviewResponse)
async def preview_normalized_data(
    dataset_id: int,
    num_rows: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Preview normalized data
    
    - **dataset_id**: Dataset ID
    - **num_rows**: Number of rows to preview (default: 10)
    
    Returns sample rows from normalized CSV.
    Only works if dataset has been normalized.
    """
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == current_user["db_object"].id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    try:
        preview = normalization_service.get_normalized_preview(
            dataset_id, db, num_rows
        )
        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
