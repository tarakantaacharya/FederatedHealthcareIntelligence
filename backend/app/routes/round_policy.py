"""
Round Policy Routes (Phase A-Pro)
Admin endpoints for configuring round participation policies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import require_role
from app.services.round_policy_service import RoundPolicyService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/rounds", tags=["round-policy"])


class AllowedHospitalRequest(BaseModel):
    hospital_id: int


class RegionPolicyRequest(BaseModel):
    allowed_regions: List[str]


class CapacityPolicyRequest(BaseModel):
    bed_capacity_threshold: int


@router.post("/{round_id}/allowed-hospitals")
def add_allowed_hospital(
    round_id: int,
    request: AllowedHospitalRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    """Add hospital to SELECTED round allowlist."""
    
    success = RoundPolicyService.add_allowed_hospital(round_id, request.hospital_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital already in allowlist or does not exist"
        )
    
    return {"status": "added", "round_id": round_id, "hospital_id": request.hospital_id}


@router.delete("/{round_id}/allowed-hospitals/{hospital_id}")
def remove_allowed_hospital(
    round_id: int,
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    """Remove hospital from SELECTED round allowlist."""
    
    success = RoundPolicyService.remove_allowed_hospital(round_id, hospital_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not in allowlist"
        )
    
    return {"status": "removed", "round_id": round_id, "hospital_id": hospital_id}


@router.get("/{round_id}/allowed-hospitals")
def get_allowed_hospitals(
    round_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    """Get hospitals allowed for this round (SELECTED policy only)."""
    
    hospitals = RoundPolicyService.get_allowed_hospitals(round_id, db)
    return {"hospitals": hospitals}


@router.post("/{round_id}/policy/region-based")
def set_region_policy(
    round_id: int,
    request: RegionPolicyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    """Set REGION_BASED participation policy for round."""
    
    success = RoundPolicyService.set_region_policy(round_id, request.allowed_regions, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    return {"status": "updated", "policy": "REGION_BASED", "allowed_regions": request.allowed_regions}


@router.post("/{round_id}/policy/capacity-based")
def set_capacity_policy(
    round_id: int,
    request: CapacityPolicyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    """Set CAPACITY_BASED participation policy for round."""
    
    success = RoundPolicyService.set_capacity_policy(round_id, request.bed_capacity_threshold, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    return {"status": "updated", "policy": "CAPACITY_BASED", "threshold": request.bed_capacity_threshold}
