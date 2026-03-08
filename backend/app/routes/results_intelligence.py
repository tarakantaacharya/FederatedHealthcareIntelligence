"""
Results & Prediction Intelligence routes.
Role-aware endpoints for hospital and central dashboards.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hospital import Hospital
from app.services.results_intelligence_service import ResultsIntelligenceService
from app.utils.auth import require_role

router = APIRouter()


@router.get("/hospital/overview")
async def hospital_overview(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
):
    hospital_obj = current_user.get("db_object")
    if not isinstance(hospital_obj, Hospital):
        raise HTTPException(status_code=404, detail="Hospital context not found")

    return ResultsIntelligenceService.get_hospital_dashboard(db, hospital_obj)


@router.get("/central/overview")
async def central_overview(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
):
    return ResultsIntelligenceService.get_central_dashboard(db)


@router.get("/central/hospitals/{hospital_id}")
async def central_hospital_detail(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
):
    detail = ResultsIntelligenceService.get_central_hospital_detail(db, hospital_id)
    if detail.get("error"):
        raise HTTPException(status_code=404, detail=detail["error"])
    return detail


@router.get("/central/hospitals/{hospital_id}/rounds/{round_number}")
async def central_hospital_round_detail(
    hospital_id: int,
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
):
    detail = ResultsIntelligenceService.get_central_round_detail(db, hospital_id, round_number)
    if detail.get("error"):
        raise HTTPException(status_code=404, detail=detail["error"])
    return detail


# ============================================================================
# NEW GOVERNANCE-ALIGNED ENDPOINTS (Phase 42+)
# ============================================================================

@router.get("/hospital/local-model-metrics")
async def hospital_local_model_metrics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN")),
    round_number: Optional[int] = None,
):
    """Get local model evaluation metrics with explicit error reasons."""
    hospital_obj = current_user.get("db_object")
    if not isinstance(hospital_obj, Hospital):
        raise HTTPException(status_code=404, detail="Hospital context not found")
    
    return ResultsIntelligenceService.get_local_model_metrics(db, hospital_obj.id, round_number)


@router.get("/hospital/global-model")
async def hospital_global_model(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN")),
    round_number: Optional[int] = None,
):
    """Get approved global model for governance transparency."""
    return ResultsIntelligenceService.get_approved_global_model(db, round_number)


@router.get("/hospital/horizon-analytics/{horizon_key}")
async def hospital_horizon_analytics(
    horizon_key: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN")),
):
    """Get TFT horizon analytics with dynamic detection and volume validation."""
    hospital_obj = current_user.get("db_object")
    if not isinstance(hospital_obj, Hospital):
        raise HTTPException(status_code=404, detail="Hospital context not found")
    
    return ResultsIntelligenceService.get_tft_horizon_analytics(db, hospital_obj.id, horizon_key)


@router.get("/hospital/drift-analysis")
async def hospital_drift_analysis(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN")),
    baseline_round: int = 1,
):
    """Compute drift using PSI against baseline round."""
    hospital_obj = current_user.get("db_object")
    if not isinstance(hospital_obj, Hospital):
        raise HTTPException(status_code=404, detail="Hospital context not found")
    
    return ResultsIntelligenceService.compute_drift_score(db, hospital_obj.id, baseline_round)


@router.get("/central/round/{round_number}/governance")
async def central_governance_summary(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
):
    """Get consolidated round governance data (DP, participation, approval)."""
    summary = ResultsIntelligenceService.get_round_governance_summary(db, round_number)
    if summary.get("error"):
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@router.get("/central/global-model")
async def central_global_model(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    round_number: Optional[int] = None,
):
    """Get latest approved global model with governance metadata."""
    return ResultsIntelligenceService.get_approved_global_model(db, round_number)
