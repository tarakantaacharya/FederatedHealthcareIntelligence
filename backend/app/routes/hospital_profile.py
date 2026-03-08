"""
Hospital profile routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.security.rbac import require_admin_role
from app.schemas.hospital_profile_schema import HospitalProfileCreate, HospitalProfileResponse
from app.services.hospital_profile_service import HospitalProfileService

router = APIRouter()


@router.get("/me", response_model=HospitalProfileResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    hospital = current_user["db_object"]
    return HospitalProfileService.get_or_create_profile(db, hospital.id)


@router.put("/me", response_model=HospitalProfileResponse)
async def update_my_profile(
    payload: HospitalProfileCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    hospital = current_user["db_object"]
    return HospitalProfileService.update_profile(db, hospital.id, payload.dict(exclude_unset=True))


@router.get("/{hospital_id}", response_model=HospitalProfileResponse)
async def get_profile_admin(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    return HospitalProfileService.get_or_create_profile(db, hospital_id)


@router.put("/{hospital_id}", response_model=HospitalProfileResponse)
async def update_profile_admin(
    hospital_id: int,
    payload: HospitalProfileCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    return HospitalProfileService.update_profile(db, hospital_id, payload.dict(exclude_unset=True))
