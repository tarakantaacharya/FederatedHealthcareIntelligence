"""
Canonical Field model (Phase 45)
Stores approved target columns with metadata for governance
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class CanonicalField(Base):
    __tablename__ = "canonical_fields"

    id = Column(Integer, primary_key=True, index=True)
    field_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    data_type = Column(String(50), nullable=True)  # e.g., "integer", "float", "boolean"
    category = Column(String(100), nullable=True)  # e.g., "resource", "utilization", "outcome"
    unit = Column(String(50), nullable=True)  # e.g., "beds", "percentage", "count"
    is_active = Column(Boolean, default=True)  # Allow disabling without deletion
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<CanonicalField {self.field_name}>"
