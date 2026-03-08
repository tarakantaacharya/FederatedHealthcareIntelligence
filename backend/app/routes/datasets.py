"""
Dataset upload and management routes (Phase 2)
"""
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.dataset_schema import (
    DatasetUploadResponse,
    DatasetListResponse,
    DatasetDetailResponse,
    DatasetModelSummaryResponse
)
from app.services.dataset_service import DatasetService

router = APIRouter()


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Upload hospital dataset CSV
    
    - **file**: CSV file containing hospital resource data
    
    Requires authentication. File must be in CSV format.
    Automatically extracts metadata (rows, columns, headers).
    """
    hospital = current_user["db_object"]
    dataset = await DatasetService.upload_dataset(db, file, hospital)
    
    # Parse column_names back to list for response
    response_data = DatasetUploadResponse(
        id=dataset.id,
        hospital_id=dataset.hospital_id,
        filename=dataset.filename,
        file_path=dataset.file_path,
        file_size_bytes=dataset.file_size_bytes,
        num_rows=dataset.num_rows,
        num_columns=dataset.num_columns,
        dataset_type=dataset.dataset_type,
        column_names=json.loads(dataset.column_names) if dataset.column_names else None,
        uploaded_at=dataset.uploaded_at
    )
    
    return response_data


@router.get("/", response_model=List[DatasetListResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    List all datasets for current hospital
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    
    Requires authentication. Only returns datasets owned by authenticated hospital.
    """
    datasets = DatasetService.get_hospital_datasets(
        db, 
        current_user["db_object"].id, 
        skip, 
        limit
    )
    
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get detailed information about a specific dataset
    
    - **dataset_id**: Dataset database ID
    
    Requires authentication. Only accessible by owning hospital.
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    response_data = DatasetDetailResponse(
        id=dataset.id,
        hospital_id=dataset.hospital_id,
        filename=dataset.filename,
        file_path=dataset.file_path,
        file_size_bytes=dataset.file_size_bytes,
        num_rows=dataset.num_rows,
        num_columns=dataset.num_columns,
        dataset_type=dataset.dataset_type,
        column_names=json.loads(dataset.column_names) if dataset.column_names else None,
        is_normalized=dataset.is_normalized,
        normalized_path=dataset.normalized_path,
        uploaded_at=dataset.uploaded_at
    )
    
    return response_data


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Delete a dataset and associated files
    
    - **dataset_id**: Dataset database ID
    
    Requires authentication. Only accessible by owning hospital.
    Permanently deletes file from storage and database record.
    """
    print(f"[DEBUG] DELETE endpoint reached for dataset_id={dataset_id}")
    hospital = current_user["db_object"]
    
    # Verify dataset exists and belongs to current hospital
    # Then delete DB row and commit transaction
    DatasetService.delete_dataset(db, dataset_id, hospital.id)
    
    print(f"[DEBUG] DELETE successful for dataset_id={dataset_id}")
    return {"status": "success", "deleted_id": dataset_id}


@router.get("/{dataset_id}/status")
async def get_dataset_status(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get dataset intelligence status (Phase B)
    
    Returns comprehensive training history:
    - Local training status
    - Federated training status
    - Participated rounds
    - Mask and weight upload status
    - Training counts and timestamps
    
    Only accessible by owning hospital.
    """
    from app.services.dataset_intelligence_service import DatasetIntelligenceService
    
    hospital = current_user["db_object"]
    status_data = DatasetIntelligenceService.get_dataset_status(db, dataset_id, hospital.id)
    
    if not status_data:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    return status_data


@router.get("/{dataset_id}/models", response_model=List[DatasetModelSummaryResponse])
async def get_dataset_models(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get trained models for a dataset owned by current hospital.

    Returns lightweight rows for dataset management UI:
    id, model_name, type (LOCAL/FEDERATED), architecture (TFT/ML), timestamp.
    """
    hospital = current_user["db_object"]
    return DatasetService.get_dataset_models(db, dataset_id, hospital.id)
