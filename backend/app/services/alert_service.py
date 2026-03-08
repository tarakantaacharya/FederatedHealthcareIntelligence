"""
Alert service (Phase 18)
Real-time alerting and notification system
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict
from app.models.alerts import Alert, AlertType, AlertSeverity
from app.models.hospital import Hospital


class AlertService:
    """Service for managing alerts"""
    
    @staticmethod
    def create_capacity_alert(
        hospital_id: int,
        actual_occupancy: float,
        capacity: float,
        db: Session
    ) -> Alert:
        """
        Create capacity alert when threshold exceeded
        
        Args:
            hospital_id: Hospital ID
            actual_occupancy: Current occupancy
            capacity: Total capacity
            db: Database session
        
        Returns:
            Created Alert object
        """
        utilization = (actual_occupancy / capacity) * 100
        
        # Determine severity
        if utilization >= 95:
            severity = AlertSeverity.CRITICAL
            alert_type = AlertType.CAPACITY_CRITICAL
            title = "CRITICAL: Hospital at Maximum Capacity"
            message = f"Hospital is at {utilization:.1f}% capacity ({int(actual_occupancy)}/{int(capacity)} beds). Immediate action required."
        elif utilization >= 85:
            severity = AlertSeverity.WARNING
            alert_type = AlertType.CAPACITY_WARNING
            title = "WARNING: High Capacity Utilization"
            message = f"Hospital is at {utilization:.1f}% capacity ({int(actual_occupancy)}/{int(capacity)} beds). Consider surge planning."
        else:
            return None  # No alert needed
        
        alert = Alert(
            hospital_id=hospital_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            threshold_value=capacity,
            actual_value=actual_occupancy,
            is_acknowledged=False,
            is_resolved=False
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    @staticmethod
    def create_anomaly_alert(
        hospital_id: int,
        metric_name: str,
        expected_value: float,
        actual_value: float,
        deviation_percent: float,
        db: Session
    ) -> Alert:
        """
        Create anomaly detection alert
        
        Args:
            hospital_id: Hospital ID
            metric_name: Metric that deviated
            expected_value: Expected/predicted value
            actual_value: Actual observed value
            deviation_percent: Percentage deviation
            db: Database session
        
        Returns:
            Created Alert
        """
        if abs(deviation_percent) < 20:
            return None  # Small deviation, no alert
        
        severity = AlertSeverity.CRITICAL if abs(deviation_percent) > 50 else AlertSeverity.WARNING
        
        alert = Alert(
            hospital_id=hospital_id,
            alert_type=AlertType.ANOMALY_DETECTION,
            severity=severity,
            title=f"Anomaly Detected: {metric_name}",
            message=f"{metric_name} deviated {deviation_percent:.1f}% from expected. Expected: {expected_value:.1f}, Actual: {actual_value:.1f}",
            threshold_value=expected_value,
            actual_value=actual_value
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    @staticmethod
    def get_active_alerts(
        hospital_id: int,
        db: Session
    ) -> List[Alert]:
        """
        Get all active (unresolved) alerts for hospital
        
        Args:
            hospital_id: Hospital ID
            db: Database session
        
        Returns:
            List of active alerts
        """
        return db.query(Alert).filter(
            Alert.hospital_id == hospital_id,
            Alert.is_resolved == False
        ).order_by(
            Alert.severity.desc(),
            Alert.created_at.desc()
        ).all()
    
    @staticmethod
    def acknowledge_alert(
        alert_id: int,
        db: Session
    ) -> Alert:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
            db: Database session
        
        Returns:
            Updated Alert
        """
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if alert:
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        
        return alert
    
    @staticmethod
    def resolve_alert(
        alert_id: int,
        db: Session
    ) -> Alert:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert ID
            db: Database session
        
        Returns:
            Updated Alert
        """
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        
        return alert
    
    @staticmethod
    def get_alert_summary(
        hospital_id: int,
        db: Session
    ) -> Dict:
        """
        Get alert summary statistics
        
        Args:
            hospital_id: Hospital ID
            db: Database session
        
        Returns:
            Summary dictionary
        """
        all_alerts = db.query(Alert).filter(
            Alert.hospital_id == hospital_id
        ).all()
        
        active_alerts = [a for a in all_alerts if not a.is_resolved]
        
        critical_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL)
        warning_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING)
        
        return {
            'total_alerts': len(all_alerts),
            'active_alerts': len(active_alerts),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'acknowledged_count': sum(1 for a in active_alerts if a.is_acknowledged),
            'unacknowledged_count': sum(1 for a in active_alerts if not a.is_acknowledged)
        }
