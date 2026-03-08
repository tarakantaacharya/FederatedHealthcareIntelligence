"""
Dataset Preprocessing Routes

API endpoints for dataset preprocessing operations:
- Data type detection
- Data quality analysis
- Data cleaning
- Preview data
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.preprocessing_schema import (
    DataTypeDetectionResponse,
    DataQualityResponse,
    DataCleaningRequest,
    DataCleaningResponse,
    DataPreviewResponse,
    PreprocessingStatusResponse
)
from app.services.dataset_preprocessing_service import DatasetPreprocessingService
from app.services.dataset_service import DatasetService

router = APIRouter()


@router.get("/{dataset_id}/detect-types", response_model=DataTypeDetectionResponse)
async def detect_column_types(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Detect data types for all columns in dataset.
    
    - **dataset_id**: Dataset database ID
    
    Returns column-wise type information including:
    - Inferred data type
    - Pandas dtype
    - Null/non-null counts
    - Unique value counts
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    result = DatasetPreprocessingService.detect_column_types(dataset.file_path)
    return result


@router.get("/{dataset_id}/quality-report", response_model=DataQualityResponse)
async def get_quality_report(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate comprehensive data quality report.
    
    - **dataset_id**: Dataset database ID
    
    Returns:
    - Missing value analysis
    - Duplicate detection
    - Column statistics
    - Quality issue flags
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    report = DatasetPreprocessingService.get_data_quality_report(dataset.file_path)
    return report


@router.post("/{dataset_id}/clean", response_model=DataCleaningResponse)
async def clean_dataset(
    dataset_id: int,
    operations: DataCleaningRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Apply cleaning operations to dataset.
    
    - **dataset_id**: Dataset database ID
    - **operations**: Cleaning operations to apply
    
    Operations:
    - Remove duplicates
    - Handle missing values (drop or fill)
    - Remove columns
    - Rename columns
    - Convert data types
    
    If dataset has been trained, creates automatic backup before modification.
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    result = DatasetPreprocessingService.clean_dataset(
        db, dataset, operations.dict()
    )
    return result


@router.get("/{dataset_id}/preview", response_model=DataPreviewResponse)
async def get_dataset_preview(
    dataset_id: int,
    rows: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get preview of dataset data.
    
    - **dataset_id**: Dataset database ID
    - **rows**: Number of rows to preview (default: 10)
    
    Returns first N rows of dataset for UI display.
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    preview = DatasetPreprocessingService.get_preview_data(dataset.file_path, rows)
    return preview


@router.get("/{dataset_id}/preprocessing-status", response_model=PreprocessingStatusResponse)
async def get_preprocessing_status(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get comprehensive preprocessing status for dataset.
    
    - **dataset_id**: Dataset database ID
    
    Returns:
    - Quality report
    - Column types
    - Training status
    - Backup availability
    """
    hospital = current_user["db_object"]
    dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital.id)
    
    # Get quality report
    quality_report = DatasetPreprocessingService.get_data_quality_report(dataset.file_path)
    
    # Get column types
    type_detection = DatasetPreprocessingService.detect_column_types(dataset.file_path)
    
    # Check training status
    is_trained = dataset.times_trained > 0
    
    return {
        "dataset_id": dataset_id,
        "has_quality_issues": quality_report['has_issues'],
        "quality_report": quality_report,
        "column_types": type_detection['columns'],
        "is_trained": is_trained,
        "backup_available": is_trained
    }
