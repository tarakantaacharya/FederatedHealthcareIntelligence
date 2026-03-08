"""
Pydantic schemas for federated aggregation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AggregationRequest(BaseModel):
    """Request to perform FedAvg aggregation"""
    round_number: int = Field(..., description="Federated learning round number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "round_number": 1
            }
        }


class AggregationResponse(BaseModel):
    """Response after aggregation"""
    status: str
    round_number: int
    global_model_id: int
    num_hospitals: int
    avg_loss: float
    avg_accuracy: Optional[float] = None
    avg_mape: Optional[float] = None
    avg_rmse: Optional[float] = None
    avg_r2: Optional[float] = None
    global_weights_path: str
    model_hash: str
    block_hash: Optional[str] = None
    chain_length: Optional[int] = None
    message: str


class GlobalModelResponse(BaseModel):
    """Global model information"""
    id: int
    round_number: int
    model_path: str
    model_type: str
    local_loss: Optional[float]
    local_accuracy: Optional[float]
    is_global: bool
    model_hash: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrainingRoundSchemaResponse(BaseModel):
    """Training round schema (governance contract) - READ-ONLY for hospitals"""
    id: int
    round_id: int
    model_architecture: str                      # ML_REGRESSION or TFT
    target_column: str                           # LOCKED target for this round
    feature_schema: List[str]                    # Ordered list of required columns
    feature_types: Optional[Dict[str, str]] = None  # Column → type mapping
    sequence_required: bool = False              # Whether data must be sequential (for TFT)
    lookback: Optional[int] = None               # Encoder length (for TFT)
    horizon: Optional[int] = None                # Prediction horizon (for TFT)
    model_hyperparameters: Optional[Dict[str, Any]] = None  # LOCKED hyperparameters
    validation_rules: Optional[Dict[str, Any]] = None       # Validation constraints
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TrainingRoundResponse(BaseModel):
    """Training round information"""
    id: int
    round_number: int
    target_column: Optional[str]
    model_type: Optional[str] = None
    training_enabled: bool = True
    num_participating_hospitals: int
    average_loss: Optional[float]
    average_accuracy: Optional[float]
    average_mape: Optional[float]
    average_rmse: Optional[float]
    average_r2: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    # NEW: Round governance fields
    participation_policy: Optional[str] = "ALL"  # ALL, SELECTIVE, REGION_BASED, CAPACITY_BASED
    selection_criteria: Optional[str] = None     # MANUAL, REGION, SIZE, EXPERIENCE
    selection_value: Optional[str] = None        # e.g., "EAST", "LARGE", "NEW"
    is_emergency: bool = False                   # Emergency override flag
    hospital_ids: List[int] = []                 # List of participating hospital IDs
    hospital_names: List[str] = []               # List of hospital names
    required_target_column: Optional[str] = None
    required_canonical_features: List[str] = []
    required_feature_count: Optional[int] = None
    required_feature_order_hash: Optional[str] = None
    required_model_architecture: Optional[str] = None
    required_hyperparameters: Dict[str, Any] = {}
    # NEW: Include round schema governance contract
    round_schema: Optional[TrainingRoundSchemaResponse] = None  # Schema governance (created by central)
    
    class Config:
        from_attributes = True
