"""
Notification API Schemas (Phase 44)
Request/Response models for enterprise notification system
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RecipientRoleEnum(str, Enum):
    """Recipient role for notification routing"""
    CENTRAL = 'CENTRAL'
    HOSPITAL = 'HOSPITAL'
    ALL = 'ALL'


class NotificationTypeEnum(str, Enum):
    """Notification display types"""
    info = 'info'
    success = 'success'
    warning = 'warning'
    error = 'error'
    critical = 'critical'


class NotificationEventTypeEnum(str, Enum):
    """Federated lifecycle and governance events"""
    # Round Lifecycle
    ROUND_CREATED = 'ROUND_CREATED'
    ROUND_INVITATION_SENT = 'ROUND_INVITATION_SENT'
    ROUND_STARTED = 'ROUND_STARTED'
    ROUND_COMPLETED = 'ROUND_COMPLETED'
    ROUND_FAILED = 'ROUND_FAILED'
    
    # Weights Management
    WEIGHTS_UPLOADED = 'WEIGHTS_UPLOADED'
    WEIGHTS_VALIDATED = 'WEIGHTS_VALIDATED'
    WEIGHTS_REJECTED = 'WEIGHTS_REJECTED'
    WEIGHTS_MISSING = 'WEIGHTS_MISSING'
    
    # Aggregation
    AGGREGATION_STARTED = 'AGGREGATION_STARTED'
    AGGREGATION_COMPLETED = 'AGGREGATION_COMPLETED'
    GLOBAL_MODEL_UPDATED = 'GLOBAL_MODEL_UPDATED'
    
    # Governance
    DP_APPLIED = 'DP_APPLIED'
    MPC_SECURED = 'MPC_SECURED'
    BLOCKCHAIN_HASH_RECORDED = 'BLOCKCHAIN_HASH_RECORDED'
    AUDIT_VERIFICATION_SUCCESS = 'AUDIT_VERIFICATION_SUCCESS'
    
    # Predictions
    PREDICTION_CREATED = 'PREDICTION_CREATED'
    PREDICTION_FLAGGED = 'PREDICTION_FLAGGED'
    PREDICTION_REPORT_READY = 'PREDICTION_REPORT_READY'
    
    # System
    SYSTEM_ALERT = 'SYSTEM_ALERT'
    DEADLINE_APPROACHING = 'DEADLINE_APPROACHING'


class NotificationBase(BaseModel):
    """Base notification fields"""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationTypeEnum = Field(default=NotificationTypeEnum.info, description="Display type")
    event_type: Optional[NotificationEventTypeEnum] = Field(None, description="Event type")
    redirect_url: Optional[str] = Field(None, description="Frontend route for navigation")


class NotificationResponse(NotificationBase):
    """Notification response model"""
    id: int
    recipient_role: RecipientRoleEnum
    recipient_hospital_id: Optional[int] = None
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    severity: str = 'INFO'
    is_read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    action_label: Optional[str] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationMarkReadRequest(BaseModel):
    """Request to mark notification as read"""
    notification_id: int


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_notifications: int
    unread_count: int
    by_event_type: dict
    by_severity: dict


class NotificationFilterRequest(BaseModel):
    """Filter parameters for notification queries"""
    event_type: Optional[NotificationEventTypeEnum] = None
    is_read: Optional[bool] = None
    severity: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
