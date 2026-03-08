"""
Pipeline Status Routes - Read-only monitoring endpoints

Provides visibility into dataset processing stages without
affecting training, privacy, or federated logic.

Endpoints:
- GET /api/pipelines/{dataset_id} - Get pipeline status for a specific dataset
- GET /api/pipelines/hospital/{hospital_id}/summary - Get all pipelines for a hospital
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.hospital import Hospital
from app.routes.auth import get_current_user
from app.services.dataset_validation_service import DatasetValidationService
from app.services.validation_results_storage import validation_storage
from app.services.data_pipeline_tracker import pipeline_tracker


router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


@router.get("/{dataset_id}", response_model=Dict[str, Any])
async def get_pipeline_status(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get pipeline status for a specific dataset.
    
    Returns all pipeline stages with status, timestamps, and actual validation metrics.
    Includes persisted validation results from storage.
    
    Permissions: Hospital can only view own datasets
    """
    from app.models.dataset import Dataset
    
    # Verify hospital ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == current_hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get pipeline status
    status = pipeline_tracker.get_pipeline_status(dataset_id)
    
    if not status:
        status = pipeline_tracker.initialize_pipeline(
            dataset_id=dataset_id,
            hospital_id=current_hospital.id
        )
        pipeline_tracker.mark_upload_complete(
            dataset_id,
            metrics={
                "rows": dataset.num_rows,
                "columns": dataset.num_columns,
            }
        )
    
    result = status.to_dict()
    
    # Include validation results from storage if available
    validation_result = validation_storage.get_result(dataset_id)
    if validation_result:
        result["validation_metrics"] = {
            "rows": validation_result.get("shape", {}).get("rows"),
            "columns": validation_result.get("shape", {}).get("columns"),
            "missing_values": validation_result.get("missing_analysis", {}).get("total_missing_values"),
            "missing_percentage": validation_result.get("missing_analysis", {}).get("overall_missing_percentage"),
            "duplicate_rows": validation_result.get("duplicates", {}).get("total_duplicates"),
            "duplicate_percentage": validation_result.get("duplicates", {}).get("duplicate_percentage"),
            "time_index_valid": validation_result.get("time_index", {}).get("valid"),
            "time_index_column": validation_result.get("time_index", {}).get("column"),
            "target_valid": validation_result.get("target", {}).get("valid"),
            "target_column": validation_result.get("target", {}).get("column"),
            "numeric_columns": validation_result.get("numeric_columns"),
            "categorical_columns": validation_result.get("categorical_columns"),
            "outlier_summary": validation_result.get("outlier_summary"),
            "ready_for_training": validation_result.get("ready_for_training")
        }
    
    return result


@router.post("/{dataset_id}/process")
async def process_dataset_pipeline(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process dataset through the validation pipeline.
    
    Runs validation on the dataset and updates pipeline status.
    Returns updated pipeline status with validation results.
    """
    from app.models.dataset import Dataset
    import os
    
    # Verify hospital ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == current_hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get dataset file path
    file_path = dataset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")
    
    try:
        # Initialize pipeline if not already done
        status = pipeline_tracker.get_pipeline_status(dataset_id)
        if not status:
            pipeline_tracker.initialize_pipeline(
                dataset_id=dataset_id,
                hospital_id=current_hospital.id
            )
            pipeline_tracker.mark_upload_complete(
                dataset_id,
                metrics={
                    "rows": dataset.num_rows,
                    "columns": dataset.num_columns,
                }
            )

        pipeline_tracker.mark_validation_start(dataset_id)
        
        # Run validation
        validation_result = DatasetValidationService.validate_dataset(file_path, dataset_id)
        
        if not validation_result:
            pipeline_tracker.mark_validation_failed(dataset_id, "Validation service returned no results")
            raise HTTPException(status_code=500, detail="Validation failed - unable to process dataset")
        
        # Prepare metrics from validation result
        metrics = {
            "rows": validation_result.get("shape", {}).get("rows"),
            "columns": validation_result.get("shape", {}).get("columns"),
            "missing_percentage": validation_result.get("missing_analysis", {}).get("overall_missing_percentage"),
            "duplicate_rows": validation_result.get("duplicates", {}).get("total_duplicates"),
            "time_index_valid": validation_result.get("time_index", {}).get("valid"),
            "target_valid": validation_result.get("target", {}).get("valid"),
            "ready_for_training": validation_result.get("ready_for_training")
        }
        
        # Mark validation complete with metrics
        pipeline_tracker.mark_validation_complete(dataset_id, metrics=metrics)
        
        # Get updated status
        updated_status = pipeline_tracker.get_pipeline_status(dataset_id)
        result = updated_status.to_dict() if updated_status else {}

        # Include validation results from storage if available
        if validation_result:
            result["validation_metrics"] = {
                "rows": validation_result.get("shape", {}).get("rows"),
                "columns": validation_result.get("shape", {}).get("columns"),
                "missing_values": validation_result.get("missing_analysis", {}).get("total_missing_values"),
                "missing_percentage": validation_result.get("missing_analysis", {}).get("overall_missing_percentage"),
                "duplicate_rows": validation_result.get("duplicates", {}).get("total_duplicates"),
                "duplicate_percentage": validation_result.get("duplicates", {}).get("duplicate_percentage"),
                "time_index_valid": validation_result.get("time_index", {}).get("valid"),
                "time_index_column": validation_result.get("time_index", {}).get("column"),
                "target_valid": validation_result.get("target", {}).get("valid"),
                "target_column": validation_result.get("target", {}).get("column"),
                "numeric_columns": validation_result.get("numeric_columns"),
                "categorical_columns": validation_result.get("categorical_columns"),
                "outlier_summary": validation_result.get("outlier_summary"),
                "ready_for_training": validation_result.get("ready_for_training")
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        pipeline_tracker.mark_validation_failed(dataset_id, str(e))
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")


@router.get("/hospital/{hospital_id}/summary", response_model=Dict[str, Any])
async def get_hospital_pipeline_summary(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get pipeline summary for all datasets in a hospital.
    
    Returns aggregated metrics and stage distribution.
    
    Permissions: Hospital can only view own pipelines
    """
    # Verify hospital access
    if current_hospital.id != hospital_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.dataset import Dataset
    
    # Get all datasets for this hospital
    datasets = db.query(Dataset).filter(
        Dataset.hospital_id == hospital_id
    ).all()
    
    # Get pipeline statuses
    pipelines = []
    for dataset in datasets:
        status = pipeline_tracker.get_pipeline_status(dataset.id)
        if not status:
            # Initialize if not yet tracked
            status = pipeline_tracker.initialize_pipeline(
                dataset_id=dataset.id,
                hospital_id=hospital_id
            )
            pipeline_tracker.mark_upload_complete(
                dataset.id,
                metrics={
                    "rows": dataset.num_rows,
                    "columns": dataset.num_columns,
                }
            )
        pipelines.append(status)
    
    # Calculate aggregates
    total_datasets = len(datasets)
    ready_for_training = sum(1 for p in pipelines if p.is_ready)
    failed_pipelines = sum(
        1 for p in pipelines
        if any([
            p.upload.status.value == "failed",
            p.validation.status.value == "failed",
            p.cleaning.status.value == "failed",
            p.feature_engineering.status.value == "failed",
            p.harmonization.status.value == "failed"
        ])
    )
    
    avg_progress = (
        sum(p.overall_progress for p in pipelines) / total_datasets
        if total_datasets > 0
        else 0
    )
    
    # Stage distribution
    stages_distribution = {
        "upload": sum(1 for p in pipelines if p.upload.status.value == "complete"),
        "validation": sum(1 for p in pipelines if p.validation.status.value == "complete"),
        "cleaning": sum(1 for p in pipelines if p.cleaning.status.value == "complete"),
        "feature_engineering": sum(1 for p in pipelines if p.feature_engineering.status.value == "complete"),
        "harmonization": sum(1 for p in pipelines if p.harmonization.status.value == "complete"),
        "ready_for_training": ready_for_training,
    }
    
    return {
        "hospital_id": hospital_id,
        "total_datasets": total_datasets,
        "ready_for_training": ready_for_training,
        "failed_pipelines": failed_pipelines,
        "average_progress": int(avg_progress),
        "stages_distribution": stages_distribution,
        "pipelines": [p.to_dict() for p in pipelines]
    }


@router.get("/summary/quick", response_model=Dict[str, Any])
async def get_quick_pipeline_summary(
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Quick pipeline summary for current hospital dashboard.
    
    Lightweight endpoint returning only aggregated metrics.
    """
    from app.models.dataset import Dataset
    
    datasets = db.query(Dataset).filter(
        Dataset.hospital_id == current_hospital.id
    ).all()
    
    pipelines = [
        pipeline_tracker.get_pipeline_status(d.id) or
        pipeline_tracker.initialize_pipeline(d.id, current_hospital.id)
        for d in datasets
    ]
    
    ready_count = sum(1 for p in pipelines if p.is_ready)
    
    return {
        "total_datasets": len(datasets),
        "ready_for_training": ready_count,
        "in_progress": len([p for p in pipelines if 0 < p.overall_progress < 100]),
        "average_progress": int(
            sum(p.overall_progress for p in pipelines) / len(pipelines)
            if pipelines
            else 0
        )
    }


@router.post("/{dataset_id}/process", response_model=Dict[str, Any])
async def process_dataset_pipeline(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_hospital: Hospital = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger real dataset validation pipeline.
    
    Performs comprehensive data quality checks:
    - Row/column counts
    - Missing value analysis
    - Duplicate detection
    - Data type inference
    - Time index validation
    - Target column validation
    - Outlier detection
    
    Results are persisted for retrieval across page reloads.
    
    Returns: Structured validation report with readiness status.
    """
    from app.models.dataset import Dataset
    from app.config import settings
    import os
    
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.hospital_id == current_hospital.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Construct file path
    file_path = os.path.join(settings.UPLOAD_DIR, dataset.filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")
    
    # Execute real validation
    try:
        validation_result = DatasetValidationService.validate_dataset(file_path, dataset_id)
        
        if not validation_result.get("valid"):
            error_msg = validation_result.get("error", "Validation failed")
            logger.error(f"[PIPELINE] Validation failed for dataset {dataset_id}: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Dataset validation failed: {error_msg}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PIPELINE] Unexpected error during validation for dataset {dataset_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )
    
    # Persist results
    validation_storage.save_result(dataset_id, validation_result)
    
    # Update pipeline tracker with real validation data
    pipeline = pipeline_tracker.get_pipeline_status(dataset_id)
    if pipeline:
        if validation_result.get("ready_for_training"):
            pipeline_tracker.mark_ready_for_training(
                dataset_id,
                metrics={
                    "rows": validation_result["shape"]["rows"],
                    "columns": validation_result["shape"]["columns"],
                    "missing_percentage": validation_result["missing_analysis"]["overall_missing_percentage"],
                    "duplicates": validation_result["duplicates"]["total_duplicates"],
                    "time_index_valid": validation_result["time_index"]["valid"],
                    "target_valid": validation_result["target"]["valid"]
                }
            )
        else:
            # Mark as complete but not ready
            pipeline_tracker.mark_validation_complete(
                dataset_id,
                metrics={
                    "rows": validation_result["shape"]["rows"],
                    "columns": validation_result["shape"]["columns"],
                    "missing_percentage": validation_result["missing_analysis"]["overall_missing_percentage"]
                }
            )
    
    return {
        "message": "Dataset validation complete",
        "dataset_id": dataset_id,
        "validation_result": validation_result
    }
