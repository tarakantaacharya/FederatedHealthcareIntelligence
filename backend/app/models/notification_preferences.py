"""
Notification preferences model (Phase 31)
Stores per-hospital notification settings
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), unique=True, nullable=False)
    
    # Email notifications
    email_enabled = Column(Boolean, default=True)
    email_capacity_alerts = Column(Boolean, default=True)
    email_forecast_degradation = Column(Boolean, default=True)
    email_model_updates = Column(Boolean, default=True)
    email_data_quality = Column(Boolean, default=True)
    
    # In-app notifications
    inapp_enabled = Column(Boolean, default=True)
    inapp_capacity_alerts = Column(Boolean, default=True)
    inapp_forecast_degradation = Column(Boolean, default=True)
    inapp_model_updates = Column(Boolean, default=True)
    inapp_data_quality = Column(Boolean, default=True)
