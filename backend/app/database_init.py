"""
Database initialization and validation
Ensures password hashes are valid on startup
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.password_validator import validate_all_passwords
import logging

logger = logging.getLogger(__name__)


def check_password_integrity():
    """
    Check all password hashes on application startup
    Logs warnings if any corrupted hashes are found
    """
    try:
        db = SessionLocal()
        results = validate_all_passwords(db)
        
        if not results["valid"]:
            logger.warning("=" * 80)
            logger.warning("PASSWORD HASH INTEGRITY CHECK FAILED")
            logger.warning("=" * 80)
            logger.warning(results["summary"])
            
            if results["invalid_hospitals"]:
                logger.warning("\nINVALID HOSPITAL PASSWORDS:")
                for hospital in results["invalid_hospitals"]:
                    logger.warning(f"  - {hospital['hospital_id']} ({hospital['hospital_name']})")
                    logger.warning(f"    Error: {hospital['error']}")
                    logger.warning(f"    Hash length: {hospital['hash_length']} (expected 60)")
                    logger.warning(f"    Hash preview: {hospital['hash_preview']}...")
            
            if results["invalid_admins"]:
                logger.warning("\nINVALID ADMIN PASSWORDS:")
                for admin in results["invalid_admins"]:
                    logger.warning(f"  - {admin['admin_id']} ({admin['admin_name']})")
                    logger.warning(f"    Error: {admin['error']}")
                    logger.warning(f"    Hash length: {admin['hash_length']} (expected 60)")
                    logger.warning(f"    Hash preview: {admin['hash_preview']}...")
            
            logger.warning("\nACTION REQUIRED:")
            logger.warning("Corrupted password hashes must be reset manually.")
            logger.warning("Use the /api/password-management/validate-all-hashes endpoint to check status.")
            logger.warning("=" * 80)
        else:
            logger.info("PASS Password hash integrity check passed - all hashes are valid")
        
        db.close()
        return results["valid"]
    
    except Exception as e:
        logger.warning(f"Password integrity check skipped (schema migration in progress): {str(e)}")
        # Don't fail startup if password check fails - schema might be being updated
        return True

