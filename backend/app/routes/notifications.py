"""
Enterprise Notification Routes (Phase 44)
Role-aware API endpoints for event-driven notification system
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.auth import require_role
from app.models.notification import Notification, NotificationEventType, RecipientRole
from app.services.notification_service import NotificationService
from app.schemas.notification_schema import (
    NotificationResponse,
    NotificationListResponse,
    NotificationStatsResponse,
    NotificationEventTypeEnum
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# =========================================================================
# HOSPITAL ENDPOINTS
# =========================================================================

@router.get("/hospital/list", response_model=NotificationListResponse)
def get_hospital_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[NotificationEventTypeEnum] = None,
    is_read: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """
    Get all notifications for current hospital
    Includes: invitations, weight validation, aggregation results, predictions
    """
    current_hospital = current_user["db_object"]
    offset = (page - 1) * page_size
    
    # Convert enum to model enum if provided
    model_event_type = NotificationEventType[event_type.value] if event_type else None
    
    notifications = NotificationService.get_notifications_by_role(
        db=db,
        recipient_role=RecipientRole.HOSPITAL,
        recipient_hospital_id=current_hospital.id,
        event_type=model_event_type,
        is_read=is_read,
        limit=page_size,
        offset=offset
    )
    
    unread_count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=RecipientRole.HOSPITAL,
        recipient_hospital_id=current_hospital.id
    )
    
    # Get total count (without pagination)
    total_query = db.query(Notification).filter(
        Notification.recipient_role == RecipientRole.HOSPITAL,
        Notification.recipient_hospital_id == current_hospital.id
    )
    if is_read is not None:
        total_query = total_query.filter(Notification.is_read == is_read)
    if model_event_type:
        total_query = total_query.filter(Notification.event_type == model_event_type)
    
    total = total_query.count()
    
    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size
    }


@router.get("/hospital/unread-count")
def get_hospital_unread_count(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Get unread notification count for hospital"""
    current_hospital = current_user["db_object"]
    count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=RecipientRole.HOSPITAL,
        recipient_hospital_id=current_hospital.id
    )
    return {"unread_count": count}


@router.patch("/hospital/{notification_id}/read")
def mark_hospital_notification_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Mark hospital notification as read"""
    current_hospital = current_user["db_object"]
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_role == RecipientRole.HOSPITAL,
        Notification.recipient_hospital_id == current_hospital.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    success = NotificationService.mark_as_read(db, notification_id)
    return {"success": success, "notification_id": notification_id}


@router.post("/hospital/mark-all-read")
def mark_all_hospital_notifications_read(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Mark all hospital notifications as read"""
    current_hospital = current_user["db_object"]
    count = NotificationService.mark_all_as_read(db, hospital_id=current_hospital.id)
    return {"marked_read": count}


# =========================================================================
# CENTRAL ADMIN ENDPOINTS
# =========================================================================

@router.get("/central/list", response_model=NotificationListResponse)
def get_central_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[NotificationEventTypeEnum] = None,
    is_read: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Get all central admin notifications
    Includes: round events, weight submissions, aggregation status, governance alerts
    """
    offset = (page - 1) * page_size
    
    # Convert enum to model enum if provided
    model_event_type = NotificationEventType[event_type.value] if event_type else None
    
    notifications = NotificationService.get_notifications_by_role(
        db=db,
        recipient_role=RecipientRole.CENTRAL,
        event_type=model_event_type,
        is_read=is_read,
        limit=page_size,
        offset=offset
    )
    
    unread_count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=RecipientRole.CENTRAL
    )
    
    # Get total count
    total_query = db.query(Notification).filter(
        Notification.recipient_role == RecipientRole.CENTRAL
    )
    if is_read is not None:
        total_query = total_query.filter(Notification.is_read == is_read)
    if model_event_type:
        total_query = total_query.filter(Notification.event_type == model_event_type)
    
    total = total_query.count()
    
    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size
    }


@router.get("/central/unread-count")
def get_central_unread_count(
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Get unread notification count for central admin"""
    count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=RecipientRole.CENTRAL
    )
    return {"unread_count": count}


@router.patch("/central/{notification_id}/read")
def mark_central_notification_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Mark central notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_role == RecipientRole.CENTRAL
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    success = NotificationService.mark_as_read(db, notification_id)
    return {"success": success, "notification_id": notification_id}


@router.post("/central/mark-all-read")
def mark_all_central_notifications_read(
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Mark all central notifications as read"""
    # For central role, mark all central notifications as read
    query = db.query(Notification).filter(
        Notification.recipient_role == RecipientRole.CENTRAL,
        Notification.is_read == False
    )
    
    from datetime import datetime
    count = query.update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    
    return {"marked_read": count}


@router.get("/central/stats", response_model=NotificationStatsResponse)
def get_central_notification_stats(
    current_user: Dict[str, Any] = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Get notification statistics for central admin dashboard"""
    from sqlalchemy import func
    
    total = db.query(Notification).filter(
        Notification.recipient_role == RecipientRole.CENTRAL
    ).count()
    
    unread = db.query(Notification).filter(
        Notification.recipient_role == RecipientRole.CENTRAL,
        Notification.is_read == False
    ).count()
    
    # Group by event type
    by_event = db.query(
        Notification.event_type,
        func.count(Notification.id).label('count')
    ).filter(
        Notification.recipient_role == RecipientRole.CENTRAL
    ).group_by(Notification.event_type).all()
    
    event_dict = {str(event): count for event, count in by_event if event}
    
    # Group by severity
    by_severity = db.query(
        Notification.severity,
        func.count(Notification.id).label('count')
    ).filter(
        Notification.recipient_role == RecipientRole.CENTRAL
    ).group_by(Notification.severity).all()
    
    severity_dict = {sev: count for sev, count in by_severity if sev}
    
    return {
        "total_notifications": total,
        "unread_count": unread,
        "by_event_type": event_dict,
        "by_severity": severity_dict
    }


# =========================================================================
# LEGACY ENDPOINTS (Backward Compatibility)
# =========================================================================

@router.get("", response_model=NotificationListResponse)
def get_notifications_generic(
    role: str = Query("HOSPITAL", pattern="^(HOSPITAL|CENTRAL)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[NotificationEventTypeEnum] = None,
    is_read: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Unified endpoint: GET /api/notifications?role=HOSPITAL|CENTRAL"""
    offset = (page - 1) * page_size
    requested_role = RecipientRole.HOSPITAL if role == "HOSPITAL" else RecipientRole.CENTRAL

    if requested_role == RecipientRole.HOSPITAL and current_user["role"] != "HOSPITAL":
        raise HTTPException(status_code=403, detail="Hospitals endpoint requires hospital role")
    if requested_role == RecipientRole.CENTRAL and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Central endpoint requires admin role")

    hospital_id = current_user["db_object"].id if requested_role == RecipientRole.HOSPITAL else None
    model_event_type = NotificationEventType[event_type.value] if event_type else None

    notifications = NotificationService.get_notifications_by_role(
        db=db,
        recipient_role=requested_role,
        recipient_hospital_id=hospital_id,
        event_type=model_event_type,
        is_read=is_read,
        limit=page_size,
        offset=offset,
    )
    unread_count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=requested_role,
        recipient_hospital_id=hospital_id,
    )

    total_query = db.query(Notification).filter(Notification.recipient_role == requested_role)
    if hospital_id is not None:
        total_query = total_query.filter(Notification.recipient_hospital_id == hospital_id)
    if is_read is not None:
        total_query = total_query.filter(Notification.is_read == is_read)
    if model_event_type:
        total_query = total_query.filter(Notification.event_type == model_event_type)

    return {
        "notifications": notifications,
        "total": total_query.count(),
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/unread-count")
def get_unread_count_generic(
    role: str = Query("HOSPITAL", pattern="^(HOSPITAL|CENTRAL)$"),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Unified endpoint: GET /api/notifications/unread-count?role=..."""
    requested_role = RecipientRole.HOSPITAL if role == "HOSPITAL" else RecipientRole.CENTRAL
    if requested_role == RecipientRole.HOSPITAL and current_user["role"] != "HOSPITAL":
        raise HTTPException(status_code=403, detail="Hospitals endpoint requires hospital role")
    if requested_role == RecipientRole.CENTRAL and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Central endpoint requires admin role")

    hospital_id = current_user["db_object"].id if requested_role == RecipientRole.HOSPITAL else None
    count = NotificationService.get_unread_count_by_role(
        db=db,
        recipient_role=requested_role,
        recipient_hospital_id=hospital_id,
    )
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
def mark_notification_read_generic(
    notification_id: int,
    role: str = Query("HOSPITAL", pattern="^(HOSPITAL|CENTRAL)$"),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Unified endpoint: PATCH /api/notifications/{id}/read"""
    requested_role = RecipientRole.HOSPITAL if role == "HOSPITAL" else RecipientRole.CENTRAL
    hospital_id = current_user["db_object"].id if requested_role == RecipientRole.HOSPITAL else None

    if requested_role == RecipientRole.HOSPITAL and current_user["role"] != "HOSPITAL":
        raise HTTPException(status_code=403, detail="Hospitals endpoint requires hospital role")
    if requested_role == RecipientRole.CENTRAL and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Central endpoint requires admin role")

    query = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_role == requested_role,
    )
    if hospital_id is not None:
        query = query.filter(Notification.recipient_hospital_id == hospital_id)
    notification = query.first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    success = NotificationService.mark_as_read(db, notification_id)
    return {"success": success, "notification_id": notification_id}


@router.post("/{notification_id}/read")
def mark_as_read_legacy(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Legacy: Mark notification as read"""
    hospital = current_user["db_object"]
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.hospital_id == hospital.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    success = NotificationService.mark_as_read(db, notification_id)
    return {"success": success}


@router.post("/mark-all-read")
def mark_all_as_read_legacy(
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL")),
    db: Session = Depends(get_db)
):
    """Legacy: Mark all notifications as read"""
    hospital = current_user["db_object"]
    count = NotificationService.mark_all_as_read(db, hospital_id=hospital.id)
    return {"marked_read": count}
