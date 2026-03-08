"""
Enterprise Notification & Event Service (Phase 44)
Event-driven, role-aware notification system for federated lifecycle tracking
Manages in-app notifications and email dispatch
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationType, NotificationEventType, RecipientRole
from app.models.notification_preferences import NotificationPreference
from app.models.hospital import Hospital
from app.services.email_service import EmailService
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        db: Session,
        hospital_id: Optional[int],
        admin_id: Optional[int],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None
    ) -> Notification:
        """
        Create in-app notification
        
        Args:
            db: Database session
            hospital_id: Hospital ID (for hospital notifications)
            admin_id: Admin ID (for admin notifications)
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            action_url: Optional action URL
            action_label: Optional action button label
        
        Returns:
            Created Notification object
        """
        recipient_role = RecipientRole.CENTRAL if admin_id else RecipientRole.HOSPITAL
        notification = Notification(
            recipient_role=recipient_role,
            recipient_hospital_id=hospital_id if recipient_role == RecipientRole.HOSPITAL else None,
            hospital_id=hospital_id,
            admin_id=admin_id,
            type=notification_type,
            title=title,
            message=message,
            redirect_url=action_url,
            action_url=action_url,
            action_label=action_label
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Created notification: {title} for hospital_id={hospital_id}, admin_id={admin_id}")
        return notification
    
    @staticmethod
    def send_capacity_alert(
        db: Session,
        hospital_id: int,
        utilization: float,
        severity: str
    ):
        """
        Send capacity alert notification (in-app + email)
        
        Args:
            db: Database session
            hospital_id: Hospital ID
            utilization: Current utilization percentage
            severity: Alert severity (WARNING or CRITICAL)
        """
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            return
        
        # Create in-app notification
        title = f"{'🚨 CRITICAL' if severity == 'CRITICAL' else '⚠️ WARNING'}: Hospital Capacity Alert"
        message = f"Current utilization: {utilization:.1f}%. Immediate action required."
        
        NotificationService.create_notification(
            db=db,
            hospital_id=hospital_id,
            admin_id=None,
            title=title,
            message=message,
            notification_type=NotificationType.ERROR if severity == 'CRITICAL' else NotificationType.WARNING,
            action_url="/dashboard",
            action_label="View Dashboard"
        )
        
        # Send email if enabled
        if settings.EMAIL_ENABLED:
            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.hospital_id == hospital_id
            ).first()
            
            if prefs and prefs.email_enabled and prefs.email_capacity_alerts:
                EmailService.send_capacity_alert_email(
                    hospital_name=hospital.hospital_name,
                    hospital_email=hospital.contact_email,
                    utilization=utilization,
                    severity=severity
                )
    
    @staticmethod
    def send_forecast_degradation_alert(
        db: Session,
        hospital_id: int,
        accuracy_drop: float
    ):
        """Send forecast degradation alert"""
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            return
        
        # Create in-app notification
        title = "📉 Model Performance Degradation Detected"
        message = f"Your model accuracy has dropped by {accuracy_drop:.1f}%. Consider retraining."
        
        NotificationService.create_notification(
            db=db,
            hospital_id=hospital_id,
            admin_id=None,
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            action_url="/training",
            action_label="Retrain Model"
        )
        
        # Send email if enabled
        if settings.EMAIL_ENABLED:
            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.hospital_id == hospital_id
            ).first()
            
            if prefs and prefs.email_enabled and prefs.email_forecast_degradation:
                EmailService.send_forecast_degradation_email(
                    hospital_name=hospital.hospital_name,
                    hospital_email=hospital.contact_email,
                    accuracy_drop=accuracy_drop
                )
    
    @staticmethod
    def get_unread_count(db: Session, hospital_id: Optional[int] = None, admin_id: Optional[int] = None) -> int:
        """Get count of unread notifications"""
        query = db.query(Notification).filter(Notification.is_read == False)
        
        if hospital_id:
            query = query.filter(Notification.hospital_id == hospital_id)
        elif admin_id:
            query = query.filter(Notification.admin_id == admin_id)
        
        return query.count()
    
    @staticmethod
    def get_notifications(
        db: Session,
        hospital_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for user"""
        query = db.query(Notification)
        
        if hospital_id:
            query = query.filter(Notification.hospital_id == hospital_id)
        elif admin_id:
            query = query.filter(Notification.admin_id == admin_id)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> bool:
        """Mark notification as read"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def mark_all_as_read(db: Session, hospital_id: Optional[int] = None, admin_id: Optional[int] = None):
        """Mark all notifications as read for user"""
        query = db.query(Notification).filter(Notification.is_read == False)
        
        if hospital_id:
            query = query.filter(Notification.hospital_id == hospital_id)
        elif admin_id:
            query = query.filter(Notification.admin_id == admin_id)
        
        count = query.update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        db.commit()
        
        return count
    
    @staticmethod
    def cleanup_old_notifications(db: Session):
        """Delete old read notifications (beyond retention period)"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.NOTIFICATION_RETENTION_DAYS)
        
        deleted = db.query(Notification).filter(
            Notification.is_read == True,
            Notification.read_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old notifications")
        return deleted
    
    # =========================================================================
    # PHASE 44: EVENT-DRIVEN NOTIFICATION SYSTEM
    # =========================================================================
    
    @staticmethod
    def emit(
        db: Session,
        event_type: NotificationEventType,
        recipient_role: RecipientRole,
        title: str,
        message: str,
        recipient_hospital_id: Optional[int] = None,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        redirect_url: Optional[str] = None,
        severity: str = 'INFO',
        deadline: Optional[datetime] = None,
        notification_type: NotificationType = NotificationType.INFO
    ) -> Notification:
        """
        Emit an event-driven notification (Core Event Emitter)
        
        Args:
            db: Database session
            event_type: Type of federated event
            recipient_role: CENTRAL or HOSPITAL or ALL
            title: Notification title
            message: Notification message
            recipient_hospital_id: Hospital ID (required if recipient_role=HOSPITAL)
            reference_id: Round ID, Prediction ID, etc.
            reference_type: 'round', 'prediction', 'weight', etc.
            redirect_url: Frontend route for navigation
            severity: INFO, WARNING, CRITICAL
            deadline: Optional deadline for SLA tracking
            notification_type: Display type (info, success, warning, error, critical)
        
        Returns:
            Created Notification object
        """
        try:
            notification = Notification(
                recipient_role=recipient_role,
                recipient_hospital_id=recipient_hospital_id,
                title=title,
                message=message,
                event_type=event_type,
                reference_id=reference_id,
                reference_type=reference_type,
                redirect_url=redirect_url,
                severity=severity,
                deadline=deadline,
                type=notification_type,
                # Legacy fields for backward compatibility
                hospital_id=recipient_hospital_id if recipient_role == RecipientRole.HOSPITAL else None
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            logger.info(
                f"✅ Event emitted: {event_type.value} → "
                f"{recipient_role.value} (hospital_id={recipient_hospital_id})"
            )
            return notification
            
        except Exception as e:
            logger.error(f"❌ Failed to emit event {event_type.value}: {str(e)}")
            db.rollback()
            raise
    
    # -------------------------------------------------------------------------
    # ROUND LIFECYCLE EVENTS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def emit_round_created(db: Session, round_number: int, target_column: str):
        """Notify central admin that a new round was created"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.ROUND_CREATED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"Round {round_number} Created",
            message=f"New federated round created. Target: {target_column}",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_round_invitation(
        db: Session, 
        round_number: int, 
        hospital_id: int, 
        target_column: str,
        deadline: Optional[datetime] = None
    ):
        """Notify hospital of round invitation"""
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        hospital_name = hospital.hospital_name if hospital else "Unknown"
        
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.ROUND_INVITATION_SENT,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"🎯 Invited to Round {round_number}",
            message=f"You have been invited to participate in Federated Round {round_number}. Target column: {target_column}",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/training/round/{round_number}",
            severity='INFO',
            deadline=deadline,
            notification_type=NotificationType.INFO
        )
        
        logger.info(f"📤 Invitation sent: Round {round_number} → {hospital_name}")
    
    @staticmethod
    def emit_round_started(db: Session, round_number: int):
        """Notify central that round has started (training phase)"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.ROUND_STARTED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"Round {round_number} Started",
            message=f"Federated round {round_number} training phase has begun",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_round_completed(db: Session, round_number: int, num_hospitals: int, accuracy: Optional[float] = None):
        """Notify central that round completed successfully"""
        metric_text = f" (Accuracy: {accuracy:.3f})" if accuracy else ""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.ROUND_COMPLETED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"✅ Round {round_number} Completed",
            message=f"Federated round {round_number} completed with {num_hospitals} hospitals{metric_text}",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_round_failed(db: Session, round_number: int, reason: str):
        """Notify central that round failed"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.ROUND_FAILED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"❌ Round {round_number} Failed",
            message=f"Federated round {round_number} failed: {reason}",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='CRITICAL',
            notification_type=NotificationType.ERROR
        )
    
    # -------------------------------------------------------------------------
    # WEIGHTS MANAGEMENT EVENTS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def emit_weights_uploaded(
        db: Session, 
        round_number: int, 
        hospital_id: int,
        weight_id: int
    ):
        """Notify central that hospital uploaded weights"""
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        hospital_name = hospital.hospital_name if hospital else f"Hospital #{hospital_id}"
        
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.WEIGHTS_UPLOADED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"📊 Weights Uploaded",
            message=f"{hospital_name} submitted weights for Round {round_number}",
            reference_id=weight_id,
            reference_type='weight',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_weights_validated(db: Session, round_number: int, hospital_id: int):
        """Notify hospital that their weights were validated"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.WEIGHTS_VALIDATED,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"✅ Weights Validated",
            message=f"Your model weights for Round {round_number} have been validated successfully",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/training/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_weights_rejected(db: Session, round_number: int, hospital_id: int, reason: str):
        """Notify hospital that their weights were rejected"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.WEIGHTS_REJECTED,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"⚠️ Weights Rejected",
            message=f"Your weights for Round {round_number} were rejected: {reason}",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/training/round/{round_number}",
            severity='WARNING',
            notification_type=NotificationType.ERROR
        )
    
    @staticmethod
    def emit_weights_missing(db: Session, round_number: int, hospital_id: int):
        """Notify hospital that they haven't submitted weights"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.WEIGHTS_MISSING,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"⏰ Weights Submission Pending",
            message=f"You haven't submitted weights for Round {round_number} yet",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/training/round/{round_number}",
            severity='WARNING',
            notification_type=NotificationType.WARNING
        )
    
    # -------------------------------------------------------------------------
    # AGGREGATION EVENTS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def emit_aggregation_started(db: Session, round_number: int, num_hospitals: int):
        """Notify central that aggregation started"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.AGGREGATION_STARTED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"⚙️ Aggregation Started",
            message=f"FedAvg aggregation started for Round {round_number} with {num_hospitals} hospitals",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.INFO
        )
    
    @staticmethod
    def emit_aggregation_completed(db: Session, round_number: int, hospital_ids: List[int] = None):
        """Notify all participants that aggregation completed"""
        # Notify central
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.AGGREGATION_COMPLETED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"✅ Aggregation Completed",
            message=f"FedAvg aggregation for Round {round_number} completed successfully",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/aggregation/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
        
        # Notify participating hospitals
        if hospital_ids:
            for hospital_id in hospital_ids:
                NotificationService.emit(
                    db=db,
                    event_type=NotificationEventType.AGGREGATION_COMPLETED,
                    recipient_role=RecipientRole.HOSPITAL,
                    recipient_hospital_id=hospital_id,
                    title=f"✅ Global Model Updated",
                    message=f"Aggregation for Round {round_number} completed. Global model is now available.",
                    reference_id=round_number,
                    reference_type='round',
                    redirect_url=f"/training/round/{round_number}",
                    severity='INFO',
                    notification_type=NotificationType.SUCCESS
                )
    
    @staticmethod
    def emit_global_model_updated(db: Session, round_number: int):
        """Notify central that global model was updated"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.GLOBAL_MODEL_UPDATED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"🌐 Global Model Updated",
            message=f"Global model updated with Round {round_number} aggregation results",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/global-model",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    # -------------------------------------------------------------------------
    # GOVERNANCE EVENTS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def emit_dp_applied(db: Session, hospital_id: int, round_number: int, epsilon: float):
        """Notify hospital that DP was applied"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.DP_APPLIED,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"🔒 Differential Privacy Applied",
            message=f"DP-SGD applied to Round {round_number} training (ε={epsilon:.2f})",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/training/round/{round_number}",
            severity='INFO',
            notification_type=NotificationType.INFO
        )
    
    @staticmethod
    def emit_blockchain_recorded(db: Session, round_number: int, block_hash: str):
        """Notify central that blockchain audit was recorded"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.BLOCKCHAIN_HASH_RECORDED,
            recipient_role=RecipientRole.CENTRAL,
            title=f"⛓️ Blockchain Audit Recorded",
            message=f"Round {round_number} audit hash recorded: {block_hash[:16]}...",
            reference_id=round_number,
            reference_type='round',
            redirect_url=f"/central/blockchain-audit",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    # -------------------------------------------------------------------------
    # PREDICTION EVENTS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def emit_prediction_created(db: Session, hospital_id: int, prediction_id: int, model_name: str):
        """Notify hospital that prediction was created"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.PREDICTION_CREATED,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"📈 Prediction Created",
            message=f"New prediction generated using {model_name}",
            reference_id=prediction_id,
            reference_type='prediction',
            redirect_url=f"/predictions/{prediction_id}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    @staticmethod
    def emit_prediction_report_ready(db: Session, hospital_id: int, prediction_id: int):
        """Notify hospital that prediction report is ready"""
        NotificationService.emit(
            db=db,
            event_type=NotificationEventType.PREDICTION_REPORT_READY,
            recipient_role=RecipientRole.HOSPITAL,
            recipient_hospital_id=hospital_id,
            title=f"📊 Report Ready",
            message=f"Prediction report is ready for download",
            reference_id=prediction_id,
            reference_type='prediction',
            redirect_url=f"/predictions/{prediction_id}",
            severity='INFO',
            notification_type=NotificationType.SUCCESS
        )
    
    # -------------------------------------------------------------------------
    # ENHANCED QUERY METHODS
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_notifications_by_role(
        db: Session,
        recipient_role: RecipientRole,
        recipient_hospital_id: Optional[int] = None,
        event_type: Optional[NotificationEventType] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications filtered by role and criteria"""
        query = db.query(Notification).filter(Notification.recipient_role == recipient_role)
        
        if recipient_role == RecipientRole.HOSPITAL and recipient_hospital_id:
            query = query.filter(Notification.recipient_hospital_id == recipient_hospital_id)
        
        if event_type:
            query = query.filter(Notification.event_type == event_type)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_unread_count_by_role(
        db: Session,
        recipient_role: RecipientRole,
        recipient_hospital_id: Optional[int] = None
    ) -> int:
        """Get unread count for role"""
        query = db.query(Notification).filter(
            Notification.recipient_role == recipient_role,
            Notification.is_read == False
        )
        
        if recipient_role == RecipientRole.HOSPITAL and recipient_hospital_id:
            query = query.filter(Notification.recipient_hospital_id == recipient_hospital_id)
        
        return query.count()

