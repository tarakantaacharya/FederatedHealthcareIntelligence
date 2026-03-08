"""
Pydantic schemas for training operations (Phase B: Dual training modes)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Literal, List


class TrainingRequest(BaseModel):
    """Request to start local training
    
    Phase B: Supports both LOCAL and FEDERATED training modes
    - LOCAL: No round required, no weight upload, saves locally only
    - FEDERATED: Requires active round, eligibility check, enables weight/mask upload
    
    PHASE 42: Privacy Policy Governance
    - batch_size: Validated against central policy (FEDERATED mode)
    - epochs: Validated against central policy (FEDERATED mode)
    - DP parameters overridden by central policy
    
    CUSTOM FEATURES (LOCAL ONLY):
    - custom_features: Comma-separated list of feature names to use
    - If provided, overrides automatic feature detection
    - Only applicable to LOCAL training mode
    """
    dataset_id: int = Field(..., description="Dataset ID to train on")
    target_column: Optional[str] = Field(default=None, description="Column to predict (auto-detected for FEDERATED)")
    epochs: Optional[int] = Field(default=5, description="Training epochs (validated against policy for FEDERATED)")
    batch_size: Optional[int] = Field(default=32, description="Batch size (validated against policy for FEDERATED)")
    local_epsilon_budget: Optional[float] = Field(
        default=None,
        description="LOCAL mode only: hospital-defined epsilon budget override"
    )
    
    # Phase B: Training mode and architecture
    training_type: Literal["LOCAL", "FEDERATED"] = Field(
        default="FEDERATED", 
        description="Training mode: LOCAL (independent) or FEDERATED (collaborative)"
    )
    model_architecture: Literal["ML_REGRESSION", "TFT"] = Field(
        default="TFT", 
        description="Model architecture: ML_REGRESSION (sklearn baseline) or TFT (Temporal Fusion Transformer)"
    )
    
    # Custom features for LOCAL training only
    custom_features: Optional[str] = Field(
        default=None,
        description="LOCAL mode only: Comma-separated list of feature names (e.g., 'feature_1,feature_2,feature_3'). If provided, uses only these features instead of automatic detection."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 1,
                "target_column": "bed_occupancy",
                "epochs": 2,
                "batch_size": 32,
                "local_epsilon_budget": 10.0,
                "training_type": "LOCAL",
                "model_architecture": "ML_REGRESSION",
                "custom_features": "patients,staff_count,room_temp,equipment_usage"
            }
        }


class TrainingResponse(BaseModel):
    """Complete training response with all metrics"""
    model_id: int
    dataset_id: int
    dataset_name: Optional[str] = None
    target_column: str
    model_type: str
    training_type: str
    model_architecture: str
    model_path: str
    best_model: Optional[str] = None
    
    # All 10 metrics
    mae: float
    mse: float
    rmse: float
    r2: float
    adjusted_r2: float
    mape: float
    smape: float
    wape: float
    mase: float
    rmsle: float
    
    # Metadata
    num_features: int
    num_samples: int
    feature_importance: Optional[Dict] = None
    all_model_metrics: Optional[Dict] = None
    candidate_models: Optional[List[str]] = None
    ensemble_models: Optional[List[str]] = None
    selection_strategy: Optional[str] = None
    
    training_timestamp: str
    epsilon_spent: Optional[float] = None
    epsilon_budget: Optional[float] = None
    
    # Legacy compatibility fields
    train_loss: Optional[float] = None
    test_r2: Optional[float] = None
    test_mae: Optional[float] = None
    test_mse: Optional[float] = None
    test_rmse: Optional[float] = None
    test_mape: Optional[float] = None
    train_r2: Optional[float] = None
    train_mae: Optional[float] = None
    train_mse: Optional[float] = None
    accuracy: Optional[float] = None
    budget_message: Optional[str] = None
    grad_norm_pre: Optional[float] = None
    round_number: Optional[int] = None
    status: str = "TRAINING_COMPLETE"
    top_5_features: Optional[Dict] = None
    feature_count: Optional[int] = None
    num_trees: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "dataset_id": 1,
                "dataset_name": "Hospital Data",
                "target_column": "bed_occupancy",
                "model_type": "ML_REGRESSION",
                "training_type": "LOCAL",
                "model_architecture": "ML_REGRESSION",
                "model_path": "/models/local_model.pkl",
                "best_model": "random_forest",
                "mae": 5.2,
                "mse": 35.8,
                "rmse": 5.98,
                "r2": 0.89,
                "adjusted_r2": 0.87,
                "mape": 8.5,
                "smape": 7.2,
                "wape": 6.8,
                "mase": 1.2,
                "rmsle": 0.45,
                "num_features": 15,
                "num_samples": 500,
                "candidate_models": ["linear", "random_forest", "gradient_boosting", "ridge", "lasso"],
                "training_timestamp": "2026-03-04T15:30:00",
                "status": "TRAINING_COMPLETE"
            }
        }

class ModelListResponse(BaseModel):
    """Individual model in list"""
    id: int
    hospital_id: int
    round_number: int
    model_type: str
    training_type: Optional[str] = None
    model_architecture: Optional[str] = None
    local_loss: Optional[float]
    local_accuracy: Optional[float]
    local_mape: Optional[float] = None
    local_rmse: Optional[float] = None
    local_r2: Optional[float] = None
    is_global: bool
    created_at: datetime
    display_name: str = ""  # Simple format: "Round 0", "Round 1", etc.
    suggested_next_round: Optional[int] = None  # For LOCAL models: suggests next round
    
    class Config:
        from_attributes = True


class ModelDetailResponse(BaseModel):
    """Detailed model information"""
    id: int
    hospital_id: int
    round_number: int
    model_path: str
    model_type: str
    training_type: Optional[str] = None
    model_architecture: Optional[str] = None
    local_loss: Optional[float]
    local_accuracy: Optional[float]
    local_mape: Optional[float] = None
    local_rmse: Optional[float] = None
    local_r2: Optional[float] = None
    is_global: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelStatusResponse(BaseModel):
    """Complete model training status with all metrics"""
    model_id: int
    dataset_id: int
    dataset_name: Optional[str] = None
    model_type: str
    training_type: str
    model_architecture: str
    
    metrics: Dict = Field(
        description="All 10 regression metrics: mae, mse, rmse, r2, adjusted_r2, mape, smape, wape, mase, rmsle"
    )
    
    best_model: Optional[str] = None
    candidate_models: Optional[Dict] = None
    all_model_metrics: Optional[Dict] = None
    
    feature_importance: Optional[Dict] = None
    num_features: int
    num_samples: int
    
    training_time: Optional[str] = None
    training_timestamp: str
    model_path: str
    
    status: str = "TRAINING_COMPLETE"
    epsilon_spent: Optional[float] = None
    epsilon_budget: Optional[float] = None
