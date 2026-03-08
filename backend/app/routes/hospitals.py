"""
Hospital management routes (Phase 1)
List and manage registered hospitals
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.schemas.hospital_schema import HospitalResponse
from app.models.hospital import Hospital
from app.utils.auth import require_role
from app.security.rbac import require_admin_role
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType

router = APIRouter()


@router.get("/all", response_model=List[HospitalResponse])
async def get_all_hospitals(
    db: Session = Depends(get_db)
):
    """
    Get list of all registered hospitals (public endpoint)
    
    Returns basic information about all hospitals in the system.
    No authentication required.
    """
    hospitals = db.query(Hospital).filter(Hospital.is_active == True).all()
    return hospitals


@router.get("/", response_model=List[HospitalResponse])
async def list_hospitals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    List all registered hospitals (protected route)
    
    Requires authentication token
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    hospital = current_user["db_object"]
    hospitals = db.query(Hospital).filter(
        Hospital.id == hospital.id
    ).offset(skip).limit(limit).all()
    return hospitals


@router.get("/admin/list", response_model=List[HospitalResponse])
async def list_hospitals_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    List all registered hospitals (admin-only route)

    Requires admin JWT

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    hospitals = db.query(Hospital).offset(skip).limit(limit).all()
    return hospitals


@router.get("/admin/{hospital_id}", response_model=HospitalResponse)
async def get_hospital_admin(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """Get specific hospital details by ID (admin-only)."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )

    return hospital


@router.post("/{hospital_id}/verify")
async def verify_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """Verify a hospital (admin-only)."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )

    hospital.is_verified = True
    hospital.verification_status = "VERIFIED"
    db.commit()
    
    NotificationService.create_notification(
        db=db,
        hospital_id=hospital.id,
        admin_id=None,
        title="Hospital Verified",
        message="Your hospital has been verified and can participate in federated rounds.",
        notification_type=NotificationType.SUCCESS,
        action_url="/dashboard",
        action_label="Go to Dashboard"
    )

    return {"status": "verified", "hospital_id": hospital_id}


@router.post("/{hospital_id}/deactivate")
async def deactivate_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """Deactivate a hospital (admin-only)."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )

    hospital.is_active = False
    db.commit()

    return {"status": "deactivated", "hospital_id": hospital_id}


@router.post("/{hospital_id}/activate")
async def activate_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """Activate a hospital (admin-only)."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )

    hospital.is_active = True
    db.commit()

    return {"status": "activated", "hospital_id": hospital_id}


@router.post("/{hospital_id}/allow-federated")
async def set_federated_access(
    hospital_id: int,
    allow: bool = True,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """Enable/disable federated participation for a hospital (admin-only)."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )

    hospital.is_allowed_federated = allow
    db.commit()

    return {
        "status": "updated",
        "hospital_id": hospital_id,
        "is_allowed_federated": hospital.is_allowed_federated
    }


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get specific hospital details by database ID
    
    Requires authentication token
    """
    from fastapi import HTTPException
    
    current_hospital = current_user["db_object"]
    if hospital_id != current_hospital.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with ID {hospital_id} not found"
        )
    
    return hospital
