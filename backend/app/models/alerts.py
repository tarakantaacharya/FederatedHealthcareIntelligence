"""
Alert model (Phase 18)
Track system alerts and notifications
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.database import Base
import enum


class AlertType(str, enum.Enum):
    """Alert types"""
    CAPACITY_WARNING = 'capacity_warning'
    CAPACITY_CRITICAL = 'capacity_critical'
    ANOMALY_DETECTION = 'anomaly_detection'
    FORECAST_DEGRADATION = 'forecast_degradation'
    DATA_QUALITY = 'data_quality'


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    
    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Metrics
    threshold_value = Column(Float)
    actual_value = Column(Float)
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    hospital = relationship("Hospital")
    
    def __repr__(self):
        return f"<Alert {self.alert_type} - {self.severity}>"
