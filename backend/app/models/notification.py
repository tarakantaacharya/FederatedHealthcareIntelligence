"""
Enterprise Notification & Event System (Phase 44)
Event-driven, role-aware notification system for federated lifecycle tracking
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    """Notification display types"""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class NotificationEventType(str, enum.Enum):
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


class RecipientRole(str, enum.Enum):
    """Recipient role for notification routing"""
    CENTRAL = 'CENTRAL'
    HOSPITAL = 'HOSPITAL'
    ALL = 'ALL'


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient Routing (Role-Based)
    recipient_role = Column(SQLEnum(RecipientRole), nullable=False, index=True)  # CENTRAL or HOSPITAL
    recipient_hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True, index=True)  # NULL for CENTRAL
    
    # Legacy fields (for backward compatibility)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    admin_id = Column(Integer, nullable=True)  # Removed FK to non-existent admins table
    
    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.INFO)
    
    # Event Tracking
    event_type = Column(SQLEnum(NotificationEventType), nullable=True, index=True)
    reference_id = Column(Integer, nullable=True)  # Round ID, Prediction ID, etc.
    reference_type = Column(String(50), nullable=True)  # 'round', 'prediction', 'weight', etc.
    
    # Navigation
    redirect_url = Column(String(512), nullable=True)  # Frontend route
    action_url = Column(String(512), nullable=True)  # Legacy: Use redirect_url instead
    action_label = Column(String(100), nullable=True)
    
    # State Management
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Advanced Features
    severity = Column(String(20), default='INFO')  # INFO, WARNING, CRITICAL
    deadline = Column(DateTime, nullable=True)  # For SLA tracking
    acknowledged_at = Column(DateTime, nullable=True)
