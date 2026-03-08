"""
Training rounds model (Phase 7 foundation)
Tracks federated learning rounds
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RoundStatus(str, enum.Enum):
    """Training round status"""
    OPEN = 'OPEN'
    TRAINING = 'TRAINING'
    AGGREGATING = 'AGGREGATING'
    CLOSED = 'CLOSED'
    COMPLETED = 'COMPLETED'


class TrainingRound(Base):
    __tablename__ = "training_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False, unique=True, index=True)
    global_model_id = Column(Integer, ForeignKey("model_weights.id"), nullable=True)
    target_column = Column(String(255), nullable=False)
    
    # Metrics
    num_participating_hospitals = Column(Integer, default=0)
    average_loss = Column(Float)
    average_mape = Column(Float, nullable=True)  # Mean Absolute Percentage Error
    average_rmse = Column(Float, nullable=True)  # Root Mean Squared Error
    average_r2 = Column(Float, nullable=True)    # R-squared / Coefficient of determination
    average_accuracy = Column(Float, nullable=True)  # Average accuracy across hospitals
    
    # Timestamps (🔴 3️⃣ FIX: started_at should be set when round transitions to TRAINING, not at creation)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(SQLEnum(RoundStatus), default=RoundStatus.OPEN)
    training_enabled = Column(Boolean, default=True, nullable=False)  # Central control
    
    # Phase A-Pro: Participation governance
    participation_policy = Column(String(20), default='ALL', nullable=False)  # ALL, SELECTED, REGION_BASED, CAPACITY_BASED
    is_emergency = Column(Boolean, default=False, nullable=False)  # Override policies
    
    # Selection criteria for SELECTIVE mode and policy-based filtering
    selection_criteria = Column(String(50), nullable=True)  # REGION, SIZE, EXPERIENCE, MANUAL
    selection_value = Column(String(100), nullable=True)  # e.g., "EAST", "LARGE", "NEW"
    
    # Model architecture control (Phase B+)
    model_type = Column(String(20), default='TFT', nullable=False)  # TFT, ML_REGRESSION
    
    # Aggregation strategy (PFL support)
    aggregation_strategy = Column(String(20), default='fedavg', nullable=False)  # fedavg (default), pfl

    # Federated Schema Contract (immutable for round)
    required_target_column = Column(String(255), nullable=True)
    required_canonical_features = Column(JSON, nullable=True)  # Ordered canonical feature list
    required_feature_count = Column(Integer, nullable=True)
    required_feature_order_hash = Column(String(64), nullable=True)  # SHA256 hash
    required_model_architecture = Column(String(20), nullable=True)
    required_hyperparameters = Column(JSON, nullable=True)
    
    # TFT-Specific Hyperparameters (Phase 42 - Federated Contract Enforcement)
    tft_hidden_size = Column(Integer, nullable=True)  # Hidden dimension for TFT architecture
    tft_attention_heads = Column(Integer, nullable=True)  # Number of attention heads
    tft_dropout = Column(Float, nullable=True)  # Dropout rate (0.0-1.0)
    tft_regularization_factor = Column(Float, nullable=True)  # L2 regularization
    
    # Privacy Budget Allocation (per hospital for this round)
    allocated_privacy_budget = Column(Float, nullable=True)  # Epsilon budget allocated by admin for this round
    
    # Relationships
    global_model = relationship("ModelWeights", foreign_keys=[global_model_id])
    allowed_hospitals = relationship("RoundAllowedHospital", cascade="all, delete-orphan")
    round_schema = relationship("TrainingRoundSchema", back_populates="training_round", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrainingRound {self.round_number} - {self.status}>"
