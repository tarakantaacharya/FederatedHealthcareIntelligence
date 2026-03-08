"""
Admin authentication service (Central Server)
Separates admin authentication from hospital participants
"""
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.schemas.admin_schema import AdminLogin, AdminTokenResponse
from app.utils.security import verify_password, create_admin_access_token
from app.config import get_settings

settings = get_settings()


class AdminAuthService:
    @staticmethod
    def login_admin(db: Session, admin_data: AdminLogin) -> AdminTokenResponse:
        admin = db.query(Admin).filter(Admin.admin_id == admin_data.admin_id).first()

        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

        if not admin.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account is deactivated")

        # Verify password with error handling for corrupted hashes
        try:
            if not verify_password(admin_data.password, admin.hashed_password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin account has corrupted password hash. Contact system administrator."
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_admin_access_token(
            data={
                "sub": admin.admin_id,
                "admin_name": admin.admin_name,
                "role": "ADMIN"
            },
            expires_delta=access_token_expires
        )

        return AdminTokenResponse(
            access_token=access_token,
            token_type="bearer",
            admin_id=admin.admin_id,
            admin_name=admin.admin_name
        )
