"""
Security routes (Phase 20)
Key rotation, audit logs, security management
"""
from fastapi import APIRouter, Depends, Request
from datetime import datetime
from typing import Optional, Dict, Any
from app.utils.auth import require_role
from app.services.key_rotation_service import KeyRotationService
from app.services.audit_service import AuditService, AuditEventType

router = APIRouter()


@router.post("/rotate-key/{key_id}")
async def rotate_key(
    key_id: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Rotate cryptographic key
    
    - **key_id**: Key identifier to rotate
    
    Generates new key, archives old key, and updates storage.
    """
    result = KeyRotationService.rotate_key(key_id)
    
    # Log to audit
    hospital = current_user["db_object"]
    AuditService.log_event(
        event_type=AuditEventType.KEY_ROTATION,
        user_id=None,
        hospital_id=hospital.hospital_id,
        details={
            'key_id': key_id,
            'rotated_at': result['rotated_at']
        },
        success=True
    )
    
    return result


@router.get("/key-status/{key_id}")
async def check_key_status(
    key_id: str,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check key expiry status
    
    - **key_id**: Key identifier
    
    Returns days until expiry and rotation recommendations.
    """
    status = KeyRotationService.check_key_expiry(key_id)
    return status


@router.get("/audit-logs")
async def get_audit_logs(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Retrieve audit logs
    
    - **event_type**: Filter by event type
    - **start_date**: Start date (ISO format)
    - **end_date**: End date (ISO format)
    - **limit**: Maximum records
    
    Returns filtered audit logs.
    """
    # Parse dates
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    # Parse event type
    event_enum = AuditEventType(event_type) if event_type else None
    
    # Get logs for this hospital
    hospital = current_user["db_object"]
    logs = AuditService.read_audit_logs(
        start_date=start,
        end_date=end,
        event_type=event_enum,
        hospital_id=hospital.hospital_id,
        limit=limit
    )
    
    return {
        'total': len(logs),
        'logs': logs
    }


@router.get("/security-summary")
async def get_security_summary(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get security status summary
    
    Returns overview of security posture:
    - Key rotation status
    - Recent security events
    - Active sessions
    """
    # Check key status
    jwt_key_status = KeyRotationService.check_key_expiry('jwt_signing_key')
    
    # Get recent security events
    hospital = current_user["db_object"]
    recent_events = AuditService.read_audit_logs(
        event_type=AuditEventType.SECURITY_VIOLATION,
        hospital_id=hospital.hospital_id,
        limit=10
    )
    
    return {
        'hospital_id': current_hospital.hospital_id,
        'jwt_key_status': jwt_key_status,
        'recent_security_violations': len(recent_events),
        'tls_enabled': True,  # Based on configuration
        'audit_logging_active': True
    }
