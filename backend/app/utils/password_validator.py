"""
Password hash validation utility
Ensures all stored password hashes are in correct bcrypt format
"""
from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.models.admin import Admin
import logging

logger = logging.getLogger(__name__)

# Bcrypt hashes are always exactly 60 characters in format: $2a$12$... or $2b$12$... or $2y$12$...
BCRYPT_HASH_LENGTH = 60
BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def validate_bcrypt_hash(hash_value: str) -> Tuple[bool, str]:
    """
    Validate if a hash string is a valid bcrypt hash
    
    Args:
        hash_value: Hash string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hash_value or not isinstance(hash_value, str):
        return False, "Hash is empty or not a string"
    
    if not any(hash_value.startswith(prefix) for prefix in BCRYPT_PREFIXES):
        return False, f"Hash does not start with bcrypt prefix ($2a$, $2b$, or $2y$). Found: {hash_value[:10]}"
    
    if len(hash_value) != BCRYPT_HASH_LENGTH:
        return False, f"Hash length is {len(hash_value)}, expected {BCRYPT_HASH_LENGTH}. Hash may be truncated."
    
    return True, ""


def validate_hospital_passwords(db: Session) -> List[dict]:
    """
    Check all hospital passwords for validity
    
    Args:
        db: Database session
    
    Returns:
        List of hospitals with invalid password hashes
    """
    hospitals = db.query(Hospital).all()
    invalid_hospitals = []
    
    for hospital in hospitals:
        is_valid, error = validate_bcrypt_hash(hospital.hashed_password)
        if not is_valid:
            invalid_hospitals.append({
                "hospital_id": hospital.hospital_id,
                "hospital_name": hospital.hospital_name,
                "error": error,
                "hash_length": len(hospital.hashed_password) if hospital.hashed_password else 0,
                "hash_preview": hospital.hashed_password[:20] if hospital.hashed_password else "NULL"
            })
            logger.warning(
                f"Invalid password hash for hospital {hospital.hospital_id}: {error}"
            )
    
    return invalid_hospitals


def validate_admin_passwords(db: Session) -> List[dict]:
    """
    Check all admin passwords for validity
    
    Args:
        db: Database session
    
    Returns:
        List of admins with invalid password hashes
    """
    admins = db.query(Admin).all()
    invalid_admins = []
    
    for admin in admins:
        is_valid, error = validate_bcrypt_hash(admin.hashed_password)
        if not is_valid:
            invalid_admins.append({
                "admin_id": admin.admin_id,
                "admin_name": admin.admin_name,
                "error": error,
                "hash_length": len(admin.hashed_password) if admin.hashed_password else 0,
                "hash_preview": admin.hashed_password[:20] if admin.hashed_password else "NULL"
            })
            logger.warning(
                f"Invalid password hash for admin {admin.admin_id}: {error}"
            )
    
    return invalid_admins


def validate_all_passwords(db: Session) -> dict:
    """
    Validate all password hashes in the system
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with validation results
    """
    invalid_hospitals = validate_hospital_passwords(db)
    invalid_admins = validate_admin_passwords(db)
    
    return {
        "valid": len(invalid_hospitals) == 0 and len(invalid_admins) == 0,
        "invalid_hospitals": invalid_hospitals,
        "invalid_admins": invalid_admins,
        "summary": f"Found {len(invalid_hospitals)} invalid hospital passwords and {len(invalid_admins)} invalid admin passwords"
    }
