"""
Admin authentication routes (Central Server)
Separate from hospital auth to enforce governance and RBAC
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.admin_schema import AdminLogin, AdminTokenResponse
from app.services.admin_auth_service import AdminAuthService

router = APIRouter()


@router.post("/login", response_model=AdminTokenResponse, status_code=status.HTTP_200_OK)
async def admin_login(
    admin_data: AdminLogin,
    db: Session = Depends(get_db)
):
    """
    Central server/admin login
    Returns JWT signed with ADMIN_SECRET_KEY and role in payload
    """
    return AdminAuthService.login_admin(db, admin_data)
