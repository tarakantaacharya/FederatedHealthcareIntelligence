"""
Authentication routes (Phase 1)
Hospital registration, login, and token management
"""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.hospital_schema import (
    HospitalRegister,
    HospitalLogin,
    HospitalResponse,
    TokenResponse
)
from app.services.auth_service import AuthService
from app.utils.auth import require_role
from app.models.hospital import Hospital

# ✅ NEW IMPORT
from app.services.audit_service import AuditService, AuditEventType

router = APIRouter()


@router.post("/register", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def register_hospital(
    hospital_data: HospitalRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new hospital
    """
    hospital = AuthService.register_hospital(db, hospital_data)
    return hospital


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: HospitalLogin,
    request: Request,                      # ✅ Needed for IP logging
    db: Session = Depends(get_db)
):
    """
    Hospital login - returns JWT access token
    """

    try:
        # Attempt login
        token_response = AuthService.login_hospital(db, login_data)
        hospital = db.query(Hospital).filter(
            Hospital.hospital_id == login_data.hospital_id
        ).first()

        # ✅ SUCCESSFUL LOGIN - AUDIT EVENT
        AuditService.log_event(
            event_type=AuditEventType.LOGIN,
            user_id=None,
            hospital_id=hospital.hospital_id,
            details={
                "hospital_id": login_data.hospital_id,
                "login_method": "password"
            },
            ip_address=request.client.host,
            success=True
        )

        return token_response

    except Exception as e:
        # ❌ FAILED LOGIN - AUDIT EVENT
        AuditService.log_event(
            event_type=AuditEventType.LOGIN,
            user_id=None,
            hospital_id=None,
            details={
                "hospital_id": login_data.hospital_id,
                "failure_reason": "invalid_credentials"
            },
            ip_address=request.client.host,
            success=False
        )
        raise e


@router.get("/me", response_model=HospitalResponse)
async def get_current_user(
    current_user = Depends(require_role("HOSPITAL"))
):
    """
    Get current authenticated hospital details
    """
    return current_user["db_object"]


@router.post("/logout")
async def logout():
    """
    Client-side token deletion (stateless logout)
    """
    return {
        "message": "Logout successful. Please delete token from client storage.",
        "action": "client_token_deletion_required"
    }
