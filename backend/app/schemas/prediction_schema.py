"""
Pydantic schemas for predictions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ForecastRequest(BaseModel):
    """Request to generate forecast"""
    model_id: int = Field(..., description="Model ID to use for prediction")
    forecast_horizon: int = Field(default=24, ge=1, le=168, description="Hours to forecast (max 7 days)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "forecast_horizon": 24
            }
        }


class ForecastPoint(BaseModel):
    """Single forecast point"""
    timestamp: str
    hour_ahead: int
    prediction: float
    lower_bound: float
    upper_bound: float
    confidence_level: float


class QualityMetrics(BaseModel):
    """Forecast quality metrics"""
    mape: Optional[float]
    bias: Optional[float]
    trend_alignment: Optional[float]
    r2: Optional[float]
    mae: Optional[float]
    mse: Optional[float]
    rmse: Optional[float]
    validation_samples: int


class ForecastResponse(BaseModel):
    """Forecast response"""
    model_id: int
    model_type: str
    target_variable: str
    forecast_horizon: int
    generated_at: str
    horizon_forecasts: Dict[str, ForecastPoint]
    forecasts: List[ForecastPoint]
    quality_metrics: QualityMetrics
    ai_summary: Optional[str] = Field(None, description="AI-generated summary of the prediction")
    actual_values: Optional[List[float]] = Field(None, description="Actual values from validation set for comparison")
    predicted_values: Optional[List[float]] = Field(None, description="Predicted values matching actuals for validation")


class ModelComparisonRequest(BaseModel):
    """Request to compare multiple models"""
    model_ids: List[int] = Field(..., description="List of model IDs to compare")
    forecast_horizon: int = Field(default=24, ge=1, le=168)
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_ids": [1, 2, 3],
                "forecast_horizon": 24
            }
        }


class ModelComparison(BaseModel):
    """Individual model comparison"""
    model_id: int
    model_type: Optional[str]
    forecasts: Optional[List[ForecastPoint]]
    quality_metrics: Optional[QualityMetrics]
    error: Optional[str]


class ModelComparisonResponse(BaseModel):
    """Model comparison response"""
    num_models: int
    forecast_horizon: int
    comparisons: List[ModelComparison]
    generated_at: str


class SchemaValidationRequest(BaseModel):
    """Request to validate dataset schema against model"""
    model_id: int = Field(..., description="Model ID to validate against")
    dataset_id: int = Field(..., description="Dataset ID to validate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 3,
                "dataset_id": 8
            }
        }


class ModelSchemaInfo(BaseModel):
    """Model training schema information"""
    required_columns: List[str]
    excluded_columns: List[str]
    target_column: Optional[str]
    num_features: int


class DatasetSchemaInfo(BaseModel):
    """Dataset schema information"""
    columns: List[str]
    num_columns: int


class SchemaValidationResponse(BaseModel):
    """Schema validation response"""
    schema_match: Optional[bool]
    missing_columns: List[str]
    extra_columns: List[str]
    warnings: List[str]
    can_auto_align: bool
    model_schema: Optional[ModelSchemaInfo]
    dataset_schema: Optional[DatasetSchemaInfo]
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_match": False,
                "missing_columns": [],
                "extra_columns": ["staff_to_bed_ratio"],
                "warnings": ["Dataset has 1 extra columns - will drop during inference"],
                "can_auto_align": True,
                "model_schema": {
                    "required_columns": ["bed_occupancy", "er_visits", "admissions"],
                    "excluded_columns": ["time_idx", "group_id", "timestamp"],
                    "target_column": "icu_ventilator_usage",
                    "num_features": 8
                },
                "dataset_schema": {
                    "columns": ["timestamp", "bed_occupancy", "er_visits"],
                    "num_columns": 11
                }
            }
        }


class PredictionSaveRequest(BaseModel):
    """Request to save a prediction result"""
    model_id: int
    dataset_id: Optional[int] = None
    forecast_horizon: int
    forecast_data: Dict[str, Any]


class PredictionSaveResponse(BaseModel):
    """Response after saving prediction"""
    id: int
    message: str
    created_at: str
    round_number: Optional[int]
    target_column: Optional[str]


class PredictionHistoryItem(BaseModel):
    """Saved prediction history item"""
    id: int
    model_id: int
    model_type: Optional[str]
    dataset_id: Optional[int]
    dataset_name: Optional[str]
    round_id: Optional[int]
    round_number: Optional[int]
    target_column: Optional[str]
    forecast_horizon: int
    created_at: str
    forecast_data: Dict[str, Any]
    schema_validation: Optional[Dict[str, Any]]


class PredictionHistoryResponse(BaseModel):
    """Saved prediction history response"""
    items: List[PredictionHistoryItem]


# Phase 43: Prediction Traceability & Drill-Down System

class DatasetSnapshot(BaseModel):
    """Dataset information for prediction detail"""
    id: int
    filename: str
    num_rows: int
    num_columns: int
    uploaded_at: str
    times_trained: int
    last_training_type: Optional[str]


class TrainingRoundInfo(BaseModel):
    """Training round information for prediction"""
    id: int
    round_number: int
    target_column: str
    num_participating_hospitals: int
    status: str
    average_loss: Optional[float]
    average_mape: Optional[float]
    average_rmse: Optional[float]
    average_r2: Optional[float]
    started_at: str
    completed_at: Optional[str]


class GovernanceMetadata(BaseModel):
    """Privacy & governance metadata"""
    model_type: str  # "LOCAL" or "FEDERATED"
    dp_epsilon_used: Optional[float]
    aggregation_participants: Optional[int]
    blockchain_hash: Optional[str]
    contribution_weight: Optional[float]


class PerformanceMetrics(BaseModel):
    """Model performance snapshot"""
    r2: Optional[float]
    rmse: Optional[float]
    mape: Optional[float]
    model_accuracy: Optional[float]


class PredictionDetailResponse(BaseModel):
    """Comprehensive prediction detail view"""
    # Section 1: Prediction Summary
    id: int
    hospital_id: int
    hospital_name: str
    dataset: Optional[DatasetSnapshot]
    training_round: Optional[TrainingRoundInfo]
    model_type: str  # LOCAL or FEDERATED
    model_version: Optional[str]
    target_column: str
    prediction_value: Optional[float]
    prediction_timestamp: Optional[str]
    created_at: str
    
    # Section 2: Performance Metrics
    performance_metrics: Optional[PerformanceMetrics]
    feature_importance: Optional[Dict[str, float]]
    confidence_interval: Optional[Dict[str, float]]
    
    # Section 3: Governance Metadata
    governance: Optional[GovernanceMetadata]
    prediction_hash: Optional[str]
    forecast_horizon: int
    
    # Section 4: Forecast Data
    forecast_data: Dict[str, Any]
    schema_validation: Optional[Dict[str, Any]]
    input_snapshot: Optional[Dict[str, Any]]


class PredictionListItem(BaseModel):
    """Prediction list item for hospital predictions page"""
    id: int
    dataset_name: Optional[str]
    model_type: str
    round_number: Optional[int]
    target_column: Optional[str]
    prediction_timestamp: Optional[str]
    created_at: str
    forecast_horizon: int
    
    class Config:
        from_attributes = True


class PredictionListResponse(BaseModel):
    """Wrapper for predictions list"""
    items: List[PredictionListItem]
    total: int
    limit: int
    offset: int


class PredictionExportRequest(BaseModel):
    """Request to export prediction"""
    prediction_id: int
    format: str = Field(..., pattern="^(pdf|json|csv)$")


class PredictionReportData(BaseModel):
    """Report generation data"""
    prediction_id: int
    hospital_name: str
    dataset_name: Optional[str]
    target_column: Optional[str]
    predicted_value: Optional[float]
    confidence_interval: Optional[Dict[str, float]]
    feature_importance: Optional[Dict[str, float]]
    model_type: str
    generated_at: str
    domain: str = "forecasting"

