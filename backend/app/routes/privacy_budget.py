"""
Privacy budget accounting routes (Phase 25)
Track epsilon consumption per hospital
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.services.privacy_budget_service import PrivacyBudgetService

router = APIRouter()


@router.get("/status")
async def get_budget_status(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get current privacy budget status
    
    **Returns:**
    - Total epsilon spent
    - Remaining budget
    - Consumption percentage
    - Status (HEALTHY/WARNING/CRITICAL)
    - Burn rate (epsilon per round)
    - Estimated rounds remaining
    
    **Status Levels:**
    - HEALTHY: <70% consumed
    - WARNING: 70-90% consumed
    - CRITICAL: >90% consumed
    """
    hospital = current_user["db_object"]
    status = PrivacyBudgetService.get_hospital_budget_status(hospital.id, db)
    
    return status


@router.get("/history")
async def get_privacy_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get privacy budget expenditure history
    
    Returns chronological list of epsilon spent per round.
    """
    hospital = current_user["db_object"]
    history = PrivacyBudgetService.get_privacy_history(hospital.id, db)
    
    return {
        'hospital_id': hospital.id,
        'total_records': len(history),
        'history': history
    }


@router.post("/check-availability")
async def check_budget_availability(
    required_epsilon: float,
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check if sufficient budget for operation IN SPECIFIC ROUND
    
    CRITICAL: Each round has its own fresh budget allocation.
    Budget consumed in round 1 does NOT block participation in round 2.
    
    - **required_epsilon**: Epsilon required for operation
    - **round_number**: Round to check budget for (fresh allocation per round)
    
    Returns whether hospital has enough budget remaining in THIS ROUND.
    """
    hospital = current_user["db_object"]
    result = PrivacyBudgetService.check_budget_availability(
        hospital.id, 
        required_epsilon, 
        round_number, 
        db
    )
    
    return result


@router.get("/system-summary")
async def get_system_budget_summary(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get system-wide privacy budget summary
    
    Returns budget status for all hospitals in the system.
    Admin view for privacy budget monitoring.
    """
    summary = PrivacyBudgetService.get_all_hospitals_budget_summary(db)
    
    return summary
