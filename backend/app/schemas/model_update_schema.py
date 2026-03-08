"""
Pydantic schemas for model update operations
"""
from pydantic import BaseModel
from typing import Optional, Dict, List, Literal
from datetime import datetime


class ModelUpdateRequest(BaseModel):
    model_id: int
    version: str


class ModelUpdateResponse(BaseModel):
    id: int
    model_id: int
    version: str
    update_type: str


# Phase 6: Global model distribution schemas
class GlobalModelDownloadResponse(BaseModel):
    """Response for downloading global model"""
    status: str
    round_number: int
    global_model_id: int
    local_copy_id: int
    local_path: str
    accuracy: Optional[float]
    loss: Optional[float]
    message: str


class LocalUpdateResponse(BaseModel):
    """Response for applying global model to local"""
    status: str
    round_number: int
    hospital_id: int
    hospital_name: str
    updated_model_id: int
    message: str


# PFL: Hospital-side personalization
class ModelPersonalizationRequest(BaseModel):
    """Request for FL/PFL personalization on hospital side"""
    round_number: int
    mode: Literal["FL", "PFL"] = "FL"
    personalization_lr: Optional[float] = 0.5
    
    class Config:
        json_schema_extra = {
            "example": {
                "round_number": 1,
                "mode": "PFL",
                "personalization_lr": 0.5
            }
        }


class ModelPersonalizationResponse(BaseModel):
    """Response for FL/PFL personalization"""
    status: str
    round_number: int
    hospital_id: int
    mode: str
    personalization_lr: Optional[float]
    message: str


class GlobalModelListResponse(BaseModel):
    """Schema for listing global models"""
    id: int
    round_number: int
    model_type: str
    accuracy: Optional[float]
    loss: Optional[float]
    created_at: Optional[datetime]
    training_type: Optional[str] = "FEDERATED"  # LOCAL | FEDERATED
    model_architecture: Optional[str] = "TFT"  # TFT | ML_REGRESSION
    training_schema: Optional[dict] = None  # Training schema with feature_columns, etc.
    target_column: Optional[str] = None  # Target column name
    display_name: str = ""  # Display format: "Round X - ARCHITECTURE"
    suggested_next_round: Optional[int] = None  # For LOCAL models: suggests next round
    is_global: Optional[bool] = False  # True if aggregated global model
    hospital_id: Optional[int] = None  # NULL for global models, set for hospital-specific models
    dataset_id: Optional[int] = None  # Dataset linked to model (required for per-dataset local listing)
    
    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    """Hospital's synchronization status with global models"""
    hospital_id: int
    total_global_rounds: int
    synced_rounds: List[int]
    missing_rounds: List[int]
    sync_percentage: float
