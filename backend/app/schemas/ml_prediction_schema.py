"""
ML_REGRESSION Prediction Schemas
Single-point regression prediction (NOT time series forecast)
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class MLPredictionRequest(BaseModel):
    """
    Request for ML_REGRESSION single-point prediction
    
    Example:
    {
        "model_id": 1,
        "features": {
            "er_visits": 120,
            "staff_count": 45,
            "flu_cases": 38,
            "bed_occupancy_lag_1": 82.5
        }
    }
    """
    model_id: int = Field(..., description="ML_REGRESSION model ID")
    features: Dict[str, float] = Field(..., description="Input features as key-value pairs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "features": {
                    "er_visits": 120,
                    "staff_count": 45,
                    "flu_cases": 38
                }
            }
        }


class MLPredictionResponse(BaseModel):
    """
    Response for ML_REGRESSION single-point prediction
    
    Returns single numeric prediction (NOT a sequence)
    """
    model_architecture: str = Field(default="ML_REGRESSION", description="Always ML_REGRESSION")
    model_id: int
    training_type: str = Field(..., description="LOCAL or FEDERATED")
    target_column: str = Field(..., description="Target variable predicted")
    prediction: float = Field(..., description="Single predicted value")
    input_features: Dict[str, float] = Field(..., description="Features used for prediction")
    feature_count: int = Field(..., description="Number of features used")
    timestamp: str = Field(..., description="Prediction generation timestamp")
    ai_summary: Optional[str] = Field(default=None, description="AI-generated prediction summary")
    model_accuracy: Optional[Dict[str, float]] = Field(default=None, description="Model performance metrics")
    confidence_interval: Optional[Dict[str, float]] = Field(default=None, description="Prediction confidence interval")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_architecture": "ML_REGRESSION",
                "model_id": 1,
                "training_type": "LOCAL",
                "target_column": "bed_occupancy",
                "prediction": 86.3,
                "input_features": {
                    "er_visits": 120,
                    "staff_count": 45,
                    "flu_cases": 38
                },
                "feature_count": 3,
                "timestamp": "2026-02-27T10:30:00"
            }
        }


class MLPredictionSaveRequest(BaseModel):
    """Request to save ML prediction result"""
    model_id: int
    features: Dict[str, float]
    prediction: float
    dataset_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "features": {"er_visits": 120, "staff_count": 45},
                "prediction": 86.3,
                "dataset_id": 5
            }
        }


class MLPredictionSaveResponse(BaseModel):
    """Response for saved ML prediction"""
    prediction_record_id: int
    message: str = "ML prediction saved successfully"
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_record_id": 42,
                "message": "ML prediction saved successfully",
                "timestamp": "2026-02-27T10:30:00"
            }
        }


class MLPredictionHistoryItem(BaseModel):
    id: int
    model_id: int
    model_type: Optional[str] = None
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = None
    round_number: Optional[int] = None
    target_column: Optional[str] = None
    prediction_value: float
    input_snapshot: Dict[str, float]
    created_at: datetime

    class Config:
        from_attributes = True


class MLPredictionHistoryResponse(BaseModel):
    """List of saved ML predictions"""
    predictions: list[MLPredictionHistoryItem]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "predictions": [
                    {
                        "id": 42,
                        "model_id": 1,
                        "target_column": "bed_occupancy",
                        "prediction_value": 86.3,
                        "input_snapshot": {"er_visits": 120, "staff_count": 45},
                        "created_at": "2026-02-27T10:30:00"
                    }
                ],
                "total_count": 1
            }
        }


class MLModelValidationRequest(BaseModel):
    """Validate if features match model training schema"""
    model_id: int
    features: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "features": {"er_visits": 120, "staff_count": 45}
            }
        }


class MLModelValidationResponse(BaseModel):
    """Validation result for ML model features"""
    is_valid: bool
    model_id: int
    required_features: list[str]
    provided_features: list[str]
    missing_features: list[str]
    extra_features: list[str]
    warnings: list[str]
    can_proceed: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "model_id": 1,
                "required_features": ["er_visits", "staff_count", "flu_cases"],
                "provided_features": ["er_visits", "staff_count", "flu_cases"],
                "missing_features": [],
                "extra_features": [],
                "warnings": [],
                "can_proceed": True
            }
        }
