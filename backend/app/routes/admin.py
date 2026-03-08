"""
Admin management routes
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.admin import Admin
from app.models.hospital import Hospital
from app.security.rbac import require_admin_role

router = APIRouter()


@router.get("/list")
async def list_admins(
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    List all admins (admin-only)
    
    Requires admin JWT
    """
    admins = db.query(Admin).all()
    return [
        {
            "id": a.id,
            "admin_id": a.admin_id,
            "admin_name": a.admin_name,
            "contact_email": a.contact_email,
            "role": a.role,
            "is_active": a.is_active,
            "is_super_admin": a.is_super_admin,
            "created_at": a.created_at,
        }
        for a in admins
    ]


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

