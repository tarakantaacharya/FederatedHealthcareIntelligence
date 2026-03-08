"""
Prediction record model (Phase 43 - Prediction Traceability)
Stores saved predictions for hospital audit/history with full metadata traceability

Phase B Extensions:
- model_type: LOCAL or FEDERATED (determines model lineage)
- model_version: Version identifier for model tracking
- prediction_hash: SHA256(dataset_id + round_id + hospital_id + timestamp) for audit integrity
- feature_importance: Optional dict of feature names to importance scores
- confidence_interval: Optional dict with lower/upper bounds
- model_accuracy_snapshot: Metrics from training round
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("model_weights.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=True)
    round_number = Column(Integer, nullable=True)
    target_column = Column(String(255), nullable=True)
    forecast_horizon = Column(Integer, nullable=False, default=72)
    
    # Phase 43: Model metadata for traceability
    model_type = Column(String(20), nullable=True)  # LOCAL or FEDERATED
    model_version = Column(String(100), nullable=True)  # Version identifier
    
    # Phase B: Prediction report fields
    prediction_timestamp = Column(DateTime(timezone=True), nullable=True)
    prediction_value = Column(Float, nullable=True)
    input_snapshot = Column(JSON, nullable=True)
    summary_text = Column(Text, nullable=True)

    forecast_data = Column(JSON, nullable=False)
    schema_validation = Column(JSON, nullable=True)
    
    # Phase 43: Advanced metrics & governance
    feature_importance = Column(JSON, nullable=True)  # {feature_name: score}
    confidence_interval = Column(JSON, nullable=True)  # {lower: x, upper: y}
    model_accuracy_snapshot = Column(JSON, nullable=True)  # {r2: x, rmse: y, mape: z}
    prediction_hash = Column(String(256), nullable=True)  # SHA256 for audit
    dp_epsilon_used = Column(Float, nullable=True)  # DP budget consumed
    aggregation_participants = Column(Integer, nullable=True)  # Hospital count for federated
    blockchain_hash = Column(String(256), nullable=True)  # Blockchain audit reference
    contribution_weight = Column(Float, nullable=True)  # This hospital's contribution %

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    hospital = relationship("Hospital", backref="prediction_records")
    model = relationship("ModelWeights", backref="prediction_records")
    dataset = relationship("Dataset", backref="prediction_records")
    training_round = relationship("TrainingRound", backref="prediction_records", foreign_keys=[round_id])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_hospital_created', 'hospital_id', 'created_at'),
        Index('idx_round_predictions', 'round_id', 'created_at'),
        Index('idx_dataset_predictions', 'dataset_id', 'created_at'),
        Index('idx_prediction_hash', 'prediction_hash'),
    )

    def __repr__(self):
        return f"<PredictionRecord {self.id} model={self.model_id} round={self.round_number} type={self.model_type}>"
