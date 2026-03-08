"""
Schema mappings model (Phase 9)
Stores column mappings for datasets
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SchemaMapping(Base):
    __tablename__ = "schema_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    original_column = Column(String(255), nullable=False)
    canonical_field = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    hospital = relationship("Hospital")
    dataset = relationship("Dataset")
    
    __table_args__ = (
        UniqueConstraint('dataset_id', 'original_column', name='unique_dataset_column_mapping'),
    )
    
    def __repr__(self):
        return f"<SchemaMapping {self.original_column} → {self.canonical_field}>"
