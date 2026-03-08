"""
Role-Based Access Control (RBAC) utilities (Phase 30)
Enforces role-based permissions across API endpoints
Unified authentication via get_current_user
"""
from fastapi import Depends, HTTPException, status
from typing import Dict, Any
from app.utils.auth import get_current_user


# Role constants
ROLE_ADMIN = "ADMIN"
ROLE_HOSPITAL = "HOSPITAL"
ROLE_CENTRAL = "CENTRAL"


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control
    
    Args:
        *allowed_roles: Tuple of allowed role strings (ADMIN, HOSPITAL, CENTRAL)
    
    Returns:
        Dependency function that checks user role
    
    Raises:
        HTTPException 403: If user role not in allowed_roles
    
    Example:
        @router.post("/approve")
        def approve_model(user: Hospital = Depends(require_role("ADMIN"))):
            ...
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Check if current user has required role"""
        user_role = current_user.get("role", "HOSPITAL")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}. Your role: {user_role}"
            )
        
        return current_user
    
    return role_checker


def require_admin_role(*allowed_roles: str):
    """Dependency factory for admin-only access"""

    return require_role(*allowed_roles)


def require_admin():
    """Shortcut for admin-only access"""
    return require_role(ROLE_ADMIN)


def require_hospital():
    """Shortcut for hospital-only access"""
    return require_role(ROLE_HOSPITAL)


def require_central():
    """Shortcut for central system access"""
    return require_role(ROLE_CENTRAL)


def require_admin_or_central():
    """Allow both admin and central system"""
    return require_role(ROLE_ADMIN, ROLE_CENTRAL)


def require_any_role():
    """Allow any authenticated user (HOSPITAL, ADMIN, or CENTRAL)"""
    return require_role(ROLE_ADMIN, ROLE_HOSPITAL, ROLE_CENTRAL)
