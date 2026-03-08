"""
Model weights tracking (Phase 4)
Stores local and global model weights

GOVERNANCE INVARIANTS (Phase 41):
- UNIQUE (hospital_id, dataset_id, round_id): Exactly ONE model per round per hospital per dataset
- is_uploaded: Only TRUE after SHA256 validation passes
- is_mask_uploaded: Only TRUE after mask prerequisites verified
- round_id: Foreign key to TrainingRound - enforces round participation
- dataset_id: Non-nullable to enforce uniqueness (global models use sentinel value 0)
- training_type: Enum-enforced (LOCAL | FEDERATED)
- is_global: Non-nullable boolean for governance clarity
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Index, UniqueConstraint, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TrainingType(str, enum.Enum):
    """Training type enumeration for type safety"""
    LOCAL = "LOCAL"
    FEDERATED = "FEDERATED"


class ModelWeights(Base):
    __tablename__ = "model_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)  # NULL for global
    # 🔴 2️⃣ FIX: Non-nullable to prevent NULL bypassing unique constraint (global models use 0)
    dataset_id = Column(Integer, nullable=False, default=0)
    # 🔴 3️⃣ WARNING: round_number is denormalized - must stay in sync with training_round.round_number
    # Used extensively in queries (50+ references) - kept for performance but round_id is authority
    round_number = Column(Integer, nullable=False, default=0)
    # 🔴 4️⃣ FIX: round_id is THE authoritative foreign key (indexed for performance)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=True, index=True)
    
    # Model file
    model_path = Column(String(512), nullable=False)
    model_type = Column(String(50), default="sklearn_baseline")  # or "tft"
    # 🔴 5️⃣ FIX: Enum-enforced training type for governance type safety
    training_type = Column(SQLEnum(TrainingType), default=TrainingType.FEDERATED, nullable=False)
    model_architecture = Column(String(20), default="TFT")  # REGRESSION | TFT
    
    # Metrics
    local_loss = Column(Float)
    local_accuracy = Column(Float)
    local_mape = Column(Float, nullable=True)
    local_rmse = Column(Float, nullable=True)
    local_r2 = Column(Float, nullable=True)
    
    # All 10 metrics (from best model)
    local_mae = Column(Float, nullable=True)
    local_mse = Column(Float, nullable=True)
    local_adjusted_r2 = Column(Float, nullable=True)
    local_smape = Column(Float, nullable=True)
    local_wape = Column(Float, nullable=True)
    local_mase = Column(Float, nullable=True)
    local_rmsle = Column(Float, nullable=True)
    
    # Differential Privacy Metadata
    epsilon_spent = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    clip_norm = Column(Float, nullable=True)
    noise_multiplier = Column(Float, nullable=True)
    dp_mode = Column(String(20), nullable=True)
    policy_snapshot = Column(JSON, nullable=True)

    # Status (Phase 41 governance enforcement)
    # 🔴 6️⃣ FIX: Non-nullable boolean - never allow NULL in governance flags
    is_global = Column(Boolean, default=False, nullable=False)
    is_uploaded = Column(Boolean, default=False, nullable=False)  # Weights validated & uploaded
    is_mask_uploaded = Column(Boolean, default=False, nullable=False)  # Mask generated & uploaded
    
    # Phase 8: Model Hashing
    model_hash = Column(String(128), nullable=True)  # SHA256 hash
    hash_algorithm = Column(String(50), default="sha256")  # hash algorithm used
    weights_hash = Column(String(128), nullable=True)  # SHA256 of checkpoint file
    
    # Training Schema Metadata (for inference validation)
    training_schema = Column(JSON, nullable=True)  # {"required_columns": [], "excluded_columns": [], "target_column": ""}
    
    # Hyperparameter Compliance Tracking (Phase 42 - Federated Contract Enforcement)
    actual_hyperparameters = Column(JSON, nullable=True)  # Actual hyperparameters used during training
    hyperparameter_compliant = Column(Boolean, default=False, nullable=False)  # Whether complies with contract
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # GOVERNANCE CONSTRAINTS (Phase 41)
    __table_args__ = (
        # 🔴 4️⃣ FIX: Index on round_id for aggregation query performance
        Index('idx_round_id', 'round_id'),
        # Global models indexed by round
        Index('idx_round_global', 'round_number', 'is_global'),
        # INVARIANT: Exactly ONE model per (hospital_id, dataset_id, round_id, architecture)
        # This ensures each hospital can only submit one model per round per dataset
        UniqueConstraint(
            'hospital_id',
            'dataset_id',
            'round_id',
            'model_architecture',
            name='uq_hospital_dataset_round_arch'
        ),
        # Note: Global model uniqueness (one per round) enforced at application level
        # in aggregation service, since MySQL doesn't support filtered unique indexes
    )
    
    # Relationships
    hospital = relationship("Hospital", backref="model_weights")
    # dataset = relationship("Dataset", backref="model_weights")  # Commented: Causes mapper initialization error
    training_round = relationship("TrainingRound", backref="model_weights", foreign_keys=[round_id])
    
    def __repr__(self):
        if self.is_global:
            return f"<ModelWeights Global Round {self.round_number}>"
        return f"<ModelWeights Hospital {self.hospital_id} Dataset {self.dataset_id} Round {self.round_id}>"
