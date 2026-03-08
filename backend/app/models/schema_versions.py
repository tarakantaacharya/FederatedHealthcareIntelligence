"""
Schema version model (Phase 12)
Tracks schema versions and migrations
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "1.0", "1.1", "2.0"
    
    # Schema content
    schema_content = Column(Text, nullable=False)  # JSON string
    category_content = Column(Text)  # JSON string for categories
    
    # Status
    is_active = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)
    
    # Metadata
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SchemaVersion {self.version}>"
