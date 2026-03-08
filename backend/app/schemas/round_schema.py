"""
Pydantic schemas for federated rounds
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class RoundCreateRequest(BaseModel):
    """Request to create new round"""
    target_column: Optional[str] = None
    is_emergency: bool = False
    participation_mode: str = "ALL"  # ALL, SELECTIVE
    selection_criteria: Optional[str] = None  # REGION, SIZE, EXPERIENCE, MANUAL
    selection_value: Optional[str] = None  # e.g., "EAST", "LARGE", "NEW"
    manual_hospital_ids: Optional[List[int]] = None  # For MANUAL selection
    model_type: str = "TFT"  # TFT, ML_REGRESSION
    aggregation_strategy: str = "fedavg"  # fedavg (default), pfl (personalized federated learning)
    required_canonical_features: List[str] = []
    required_hyperparameters: Dict[str, Any] = {}
    allocated_privacy_budget: Optional[float] = None  # Epsilon budget per hospital for this round
    # TFT-specific hyperparameters (Phase 42)
    tft_hidden_size: Optional[int] = None  # Hidden dimension for TFT
    tft_attention_heads: Optional[int] = None  # Number of attention heads
    tft_dropout: Optional[float] = None  # Dropout rate (0.0-1.0)
    tft_regularization_factor: Optional[float] = None  # L2 regularization


class RoundCreateResponse(BaseModel):
    """Response after creating new round"""
    round_number: int
    status: str
    target_column: Optional[str]
    training_enabled: bool = True
    is_emergency: bool = False
    participation_mode: str
    selection_criteria: Optional[str]
    selection_value: Optional[str]
    started_at: Optional[datetime]
    aggregation_strategy: str = "fedavg"
    required_target_column: Optional[str] = None
    required_canonical_features: List[str] = []
    required_feature_count: Optional[int] = None
    required_feature_order_hash: Optional[str] = None
    required_model_architecture: Optional[str] = None
    required_hyperparameters: Dict[str, Any] = {}
    allocated_privacy_budget: Optional[float] = None
    tft_hidden_size: Optional[int] = None
    tft_attention_heads: Optional[int] = None
    tft_dropout: Optional[float] = None
    tft_regularization_factor: Optional[float] = None
    message: str
    
    class Config:
        from_attributes = True


class HospitalContribution(BaseModel):
    """Hospital contribution to a round"""
    hospital_id: int
    hospital_name: str
    loss: Optional[float]
    accuracy: Optional[float]
    mape: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    uploaded_at: datetime


class RoundDetailResponse(BaseModel):
    """Detailed round information"""
    round_number: int
    status: str
    target_column: Optional[str]
    training_enabled: bool = True
    is_emergency: bool = False
    participation_mode: str = "ALL"
    selection_criteria: Optional[str]
    selection_value: Optional[str]
    num_participating_hospitals: int
    average_loss: Optional[float]
    average_accuracy: Optional[float] = None
    average_mape: Optional[float] = None
    average_rmse: Optional[float] = None
    average_r2: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime]
    global_model_id: Optional[int]
    required_target_column: Optional[str] = None
    required_canonical_features: List[str] = []
    required_feature_count: Optional[int] = None
    required_feature_order_hash: Optional[str] = None
    required_model_architecture: Optional[str] = None
    required_hyperparameters: Dict[str, Any] = {}
    allocated_privacy_budget: Optional[float] = None
    hospital_contributions: List[HospitalContribution]


class RoundStatisticsResponse(BaseModel):
    """Overall federated learning statistics"""
    total_rounds: int
    completed_rounds: int
    in_progress_rounds: int
    latest_round_number: int
    global_models_created: int


class RegionContribution(BaseModel):
    """Region contribution summary for a round"""
    region: str
    count: int


class RoundAnalyticsResponse(BaseModel):
    """Round-level analytics for admin dashboard"""
    round_id: int
    round_number: int
    num_hospitals: int
    avg_loss: Optional[float]
    avg_accuracy: Optional[float]
    std_loss: Optional[float]
    std_accuracy: Optional[float]
    contributing_regions: List[RegionContribution]


class RoundDeleteResponse(BaseModel):
    """Response after deleting a round and related data"""
    round_number: int
    deleted_training_round: bool
    deleted_model_weights: int
    deleted_model_masks: int
    deleted_privacy_budgets: int
    deleted_model_governance: int
    deleted_blockchain_rows: int
    deleted_model_files: int
    deleted_central_files: int
    message: str
