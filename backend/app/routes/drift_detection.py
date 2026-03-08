"""
Drift detection routes (Phase 24)
Data drift monitoring and auto-retraining
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.services.drift_detection_service import DriftDetectionService

router = APIRouter()


@router.post("/check-drift")
async def check_data_drift(
    reference_dataset_id: int,
    current_dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check for data drift between two datasets
    
    - **reference_dataset_id**: Reference dataset (training data)
    - **current_dataset_id**: Current dataset (new data)
    
    **Returns:**
    - Feature-level drift detection (PSI, KS test)
    - Target variable drift
    - Overall severity assessment
    - Retraining recommendation
    
    **Drift Metrics:**
    - PSI < 0.1: No drift
    - PSI 0.1-0.2: Low drift
    - PSI 0.2-0.25: Medium drift
    - PSI > 0.25: Critical drift
    """
    hospital = current_user["db_object"]
    drift_report = DriftDetectionService.comprehensive_drift_check(
        hospital_id=hospital.id,
        reference_dataset_id=reference_dataset_id,
        current_dataset_id=current_dataset_id,
        db=db
    )
    
    if 'error' in drift_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=drift_report['error']
        )
    
    return drift_report


@router.post("/auto-retrain")
async def auto_trigger_retraining(
    reference_dataset_id: int,
    current_dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check drift and automatically trigger retraining if needed
    
    - **reference_dataset_id**: Reference dataset
    - **current_dataset_id**: Current dataset
    
    **Triggers retraining when:**
    - Overall severity is MEDIUM or CRITICAL
    - >30% of features show drift
    - Target distribution shifts significantly
    
    Returns drift report and training results.
    """
    # Check drift
    hospital = current_user["db_object"]
    drift_report = DriftDetectionService.comprehensive_drift_check(
        hospital_id=hospital.id,
        reference_dataset_id=reference_dataset_id,
        current_dataset_id=current_dataset_id,
        db=db
    )
    
    if 'error' in drift_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=drift_report['error']
        )
    
    # Auto-trigger retraining
    retrain_result = DriftDetectionService.auto_trigger_retraining(
        drift_report, db
    )
    
    return {
        'drift_report': drift_report,
        'retraining': retrain_result
    }
