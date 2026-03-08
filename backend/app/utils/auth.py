"""
Authentication utilities - Unified role-based access control
"""
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any
from app.config import get_settings
from app.database import get_db
from app.models.hospital import Hospital
from app.models.admin import Admin

settings = get_settings()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Unified authentication: Extract and validate current user (admin or hospital) from JWT token
    
    Returns a dict with user information and role:
        {
            "id": user_id (hospital_id or admin_id),
            "role": "ADMIN" or "HOSPITAL",
            "name": user_name,
            "payload": full JWT payload
        }
    
    Raises:
        HTTPException: 401 if token is invalid, 404 if user not found in database
    """
    print("[AUTH] get_current_user() CALLED")
    import sys
    sys.stdout.flush()
    token = credentials.credentials
    try:
        # Try admin token first
        payload = jwt.decode(token, settings.ADMIN_SECRET_KEY, algorithms=[settings.ALGORITHM])
        role = payload.get("role")
        if role != "ADMIN":
            raise JWTError("Not an admin token")
    except JWTError:
        try:
            # Fallback to hospital token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user_id: str = payload.get("sub")
    role: str = payload.get("role", "HOSPITAL")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")
    if role not in ["ADMIN", "HOSPITAL"]:
        raise HTTPException(status_code=401, detail="Invalid token: unknown role")
    
    # Verify user exists in database
    if role == "ADMIN":
        user = db.query(Admin).filter(Admin.admin_id == user_id).first()
        user_name = user.admin_name if user else "Unknown"
    else:  # HOSPITAL
        user = db.query(Hospital).filter(Hospital.hospital_id == user_id).first()
        user_name = user.hospital_name if user else "Unknown"
    
    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    if role == "HOSPITAL" and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital account is pending verification."
        )
    
    print(f"[AUTH] get_current_user() RETURNING: role={role}, id={user_id}")
    sys.stdout.flush()
    return {
        "id": user_id,
        "role": role,
        "name": user_name,
        "payload": payload,
        "db_object": user
    }


def require_role(*required_roles: str) -> Callable:
    """
    Factory function to create role-checking dependency.
    Accepts one or more required roles (user must have one of them).
    
    Usage: 
        @router.get("/admin-only")
        async def admin_endpoint(current_user = Depends(require_role("ADMIN"))):
            # current_user is the dict returned by get_current_user
        
        @router.get("/dual-access")
        async def dual_endpoint(current_user = Depends(require_role("ADMIN", "HOSPITAL"))):
            # Accessible by ADMIN or HOSPITAL
    
    Args:
        *required_roles: One or more required roles (e.g., "ADMIN", "HOSPITAL")
    
    Returns:
        Dependency function that validates role
    
    Raises:
        HTTPException 403 if user role doesn't match any required role
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        # Note: role_checker depends on get_current_user only (no recursion).
        user_role = current_user.get('role', 'unknown')
        print(f"[AUTH] require_role({required_roles}) CALLED, user_role={user_role}")
        import sys
        sys.stdout.flush()
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(required_roles)}, your role: {user_role}"
            )
        print(f"[AUTH] require_role({required_roles}) PASSED")
        sys.stdout.flush()
        return current_user
    
    return role_checker