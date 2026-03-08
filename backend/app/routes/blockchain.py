"""
Blockchain routes (Phase 18)
Local audit chain and participation stubs
Unified authentication: admin and hospital can both read, only admin can write
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.utils.auth import get_current_user, require_role
from app.services.blockchain_service import BlockchainService
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.hospital import Hospital

router = APIRouter()


@router.get("/admin-chain")
async def get_admin_blockchain_logs(
    start_index: int = 0,
    count: int = 100,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Retrieve full blockchain audit chain (admin view)

    - **start_index**: Starting index
    - **count**: Number of blocks to retrieve

    Returns complete immutable audit log from local chain.
    
    **Accessible to: ADMIN only**
    """
    blockchain_service = BlockchainService()
    return blockchain_service.get_logs_with_db(db, start_index, count)


@router.get("/my-chain")
async def get_hospital_blockchain_chain(
    start_index: int = 0,
    count: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve hospital-specific blockchain events (hospital view)

    - **start_index**: Starting index
    - **count**: Number of blocks to retrieve

    Returns only blocks related to this hospital's activities.
    
    **Accessible to: HOSPITAL and ADMIN (both can see their own scope)**
    """
    blockchain_service = BlockchainService()

    # Admin requesting /my-chain gets full view (same as central scope)
    if current_user.get("role") == "ADMIN":
        return blockchain_service.get_logs_with_db(db, start_index, count)

    hospital_obj = current_user.get("db_object")
    if not isinstance(hospital_obj, Hospital):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify hospital"
        )

    return blockchain_service.get_hospital_chain(
        hospital_id=hospital_obj.hospital_id,
        start_index=start_index,
        count=count,
        db=db,
    )


@router.get("/logs")
async def get_blockchain_logs(
    start_index: int = 0,
    count: int = 100,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Retrieve audit chain logs (legacy endpoint)

    - **start_index**: Starting index
    - **count**: Number of blocks to retrieve

    Returns immutable audit log from local chain.
    
    **Accessible to: ADMIN (read-only)**
    
    **Note**: Use /admin-chain for new implementations.
    """
    blockchain_service = BlockchainService()
    return blockchain_service.get_logs(start_index, count)


@router.get("/audit-events")
async def get_audit_events(
    start_index: int = 0,
    count: int = 10,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Retrieve audit events from local audit chain
    
    - **start_index**: Starting index
    - **count**: Number of events to retrieve
    
    Returns immutable audit log from blockchain.
    
    **Accessible to: ADMIN (read-only)**
    """
    blockchain_service = BlockchainService()
    events = blockchain_service.get_audit_events(start_index, count)
    
    return {
        'start_index': start_index,
        'count': len(events),
        'events': events
    }


@router.get("/participation-status/{hospital_address}")
async def check_participation_status(
    hospital_address: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check if hospital address is allowed to participate

    - **hospital_address**: Hospital address identifier

    Returns participation status from local policy (allow by default).
    
    **Accessible to: ADMIN and HOSPITAL (read-only)**
    """
    blockchain_service = BlockchainService()
    is_allowed = blockchain_service.check_participation_allowed(hospital_address)
    
    return {
        'hospital_address': hospital_address,
        'is_allowed': is_allowed
    }


@router.post("/allow-participation")
async def allow_hospital_participation(
    hospital_address: str,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Allow hospital to participate (admin only)

    - **hospital_address**: Hospital address to allow

    Not available in local audit mode.
    
    **Requires ADMIN role**
    """
    # TODO: Add admin role check
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Participation controls are not available in local audit mode"
    )


@router.post("/revoke-participation")
async def revoke_hospital_participation(
    hospital_address: str,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Revoke hospital participation (admin only)

    - **hospital_address**: Hospital address to revoke

    Not available in local audit mode.
    
    **Requires ADMIN role**
    """
    # TODO: Add admin role check
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Participation controls are not available in local audit mode"
    )
