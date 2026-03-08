"""
Password management route
Provides utilities for checking and fixing password hash issues
For admin/central server use only
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.utils.password_validator import validate_all_passwords

router = APIRouter(prefix="/api/password-management", tags=["password-management"])


@router.get("/validate-all-hashes")
def validate_all_password_hashes(
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Validate all password hashes in the system
    Admin-only endpoint for security audit
    
    Returns:
        Validation results for all hospitals and admins
    """
    admin = current_user["db_object"]
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can validate password hashes"
        )
    
    results = validate_all_passwords(db)
    
    return {
        "status": "valid" if results["valid"] else "invalid",
        "summary": results["summary"],
        "invalid_hospitals": results["invalid_hospitals"],
        "invalid_admins": results["invalid_admins"],
        "details": "All password hashes have been validated. Invalid hashes must be reset manually."
    }
