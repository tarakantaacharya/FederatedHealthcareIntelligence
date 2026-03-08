"""
Dataset metadata model (Phase 2)
Tracks uploaded hospital datasets

Phase B Extensions:
- Dataset intelligence: tracks training history, federated participation
- times_trained: Total training count (local + federated)
- times_federated: Count of federated training rounds
- last_trained_at: Most recent training timestamp
- involved_rounds: JSON list of round numbers participated in
- last_training_type: LOCAL or FEDERATED
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    
    # File info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer)
    
    # Schema info
    num_rows = Column(Integer)
    num_columns = Column(Integer)
    column_names = Column(Text)  # JSON string of column names
    
    # Dataset Type Detection (Phase 42)
    dataset_type = Column(String(20), nullable=False, default='TABULAR')  # TABULAR or TIME_SERIES
    
    # Processing status
    is_normalized = Column(Boolean, default=False)
    normalized_path = Column(String(512))
    
    # Phase B: Dataset Intelligence Tracking
    times_trained = Column(Integer, default=0)  # Total training count
    times_federated = Column(Integer, default=0)  # Federated training count
    last_trained_at = Column(DateTime(timezone=True), nullable=True)
    involved_rounds = Column(JSON, nullable=True)  # List of round numbers [1, 2, 3]
    last_training_type = Column(String(20), nullable=True)  # LOCAL or FEDERATED
    
    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    hospital = relationship("Hospital", backref="datasets")
    
    def __repr__(self):
        return f"<Dataset {self.filename}>"
