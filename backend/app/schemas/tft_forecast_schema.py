"""
TFT Forecast Schemas
Multi-horizon time-series forecasting (NOT single-point regression)
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class EncoderTimestep(BaseModel):
    timestamp: datetime
    values: Dict[str, float]

class TFTForecastRequest(BaseModel):
    """
    Request for TFT multi-horizon forecast
    
    Example:
    {
        "model_id": 20,
        "encoder_sequence": [...last N timesteps...],
        "prediction_length": 72
    }
    """
    model_id: int = Field(..., description="TFT model ID")
    encoder_sequence: Optional[List[EncoderTimestep]] = Field(
        default=None, 
        description="Optional: Time series context (if not provided, uses latest dataset)"
    )
    prediction_length: int = Field(default=72, ge=6, le=168, description="Forecast horizon in hours")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 20,
                "encoder_sequence": None,
                "prediction_length": 72
            }
        }

class ConfidenceInterval(BaseModel):
    lower: List[float]
    upper: List[float]

class HorizonForecast(BaseModel):
    """Forecast for a specific horizon"""
    timestamp: datetime
    hour_ahead: int
    p10: float = Field(..., description="10th percentile (lower confidence bound)")
    p50: float = Field(..., description="50th percentile (median prediction)")
    p90: float = Field(..., description="90th percentile (upper confidence bound)")
    confidence_level: float = Field(default=0.8, description="Confidence interval coverage")


class TFTForecastResponse(BaseModel):
    """
    Response for TFT multi-horizon forecast
    
    Returns multi-step time series forecast with uncertainty bands
    """
    model_architecture: str = Field(default="TFT", description="Always TFT")
    model_id: int
    training_type: str = Field(..., description="LOCAL or FEDERATED")
    target_column: str = Field(..., description="Target variable forecasted")
    used_dataset_id: Optional[int] = Field(default=None, description="Dataset ID used for forecast context")
    
    # Multi-horizon outputs (6h, 12h, 24h, 48h, 72h, 168h)
    horizons: Dict[str, HorizonForecast] = Field(..., description="Forecasts at different horizons (keyed by horizon like '6h', '24h')")
    
    # Full forecast array (for plotting)
    forecast_sequence: List[float] = Field(..., description="Complete forecast sequence")
    
    # Uncertainty quantification
    confidence_interval: ConfidenceInterval = Field(
        ..., 
        description="Lower and upper bounds for confidence intervals"
    )
    
    # Quality metrics
    quality_metrics: Dict[str, float] = Field(
        ..., 
        description="Forecast quality indicators (MAPE, bias, etc.)"
    )
    
    timestamp: str = Field(..., description="Forecast generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_architecture": "TFT",
                "model_id": 20,
                "training_type": "FEDERATED",
                "target_column": "icu_ventilator_usage",
                "used_dataset_id": 5,
                "horizons": {
                    "6h": {
                        "timestamp": "2026-02-27T16:00:00",
                        "hour_ahead": 6,
                        "p10": 12.3,
                        "p50": 15.7,
                        "p90": 19.4,
                        "confidence_level": 0.8
                    },
                    "24h": {
                        "timestamp": "2026-02-28T10:00:00",
                        "hour_ahead": 24,
                        "p10": 14.1,
                        "p50": 18.2,
                        "p90": 22.8,
                        "confidence_level": 0.8
                    },
                    "72h": {
                        "timestamp": "2026-03-02T10:00:00",
                        "hour_ahead": 72,
                        "p10": 16.5,
                        "p50": 21.3,
                        "p90": 26.7,
                        "confidence_level": 0.8
                    },
                    "168h": {
                        "timestamp": "2026-03-06T10:00:00",
                        "hour_ahead": 168,
                        "p10": 18.9,
                        "p50": 24.1,
                        "p90": 29.6,
                        "confidence_level": 0.8
                    }
                },
                "forecast_sequence": [15.7, 16.2, 17.1, 18.2, 19.5, 21.3],
                "confidence_interval": {
                    "lower": [12.3, 13.0, 13.9, 14.1, 15.2, 16.5],
                    "upper": [19.4, 20.1, 21.3, 22.8, 24.5, 26.7]
                },
                "quality_metrics": {
                    "mape": 5.2,
                    "bias": 0.3,
                    "trend_alignment": 0.92
                },
                "timestamp": "2026-02-27T10:00:00"
            }
        }


class TFTForecastSaveRequest(BaseModel):
    """Request to save TFT forecast result"""
    model_id: int
    forecast_data: Dict
    prediction_length: int
    dataset_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 20,
                "forecast_data": {
                    "horizons": {"6h": {...}, "24h": {...}, "72h": {...}},
                    "forecast_sequence": [15.7, 16.2, 17.1],
                    "confidence_interval": {"lower": [...], "upper": [...]}
                },
                "prediction_length": 72,
                "dataset_id": 5
            }
        }


class TFTForecastSaveResponse(BaseModel):
    """Response for saved TFT forecast"""
    prediction_record_id: int
    message: str = "TFT forecast saved successfully"
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_record_id": 43,
                "message": "TFT forecast saved successfully",
                "timestamp": "2026-02-27T10:30:00"
            }
        }


class TFTForecastHistoryItem(BaseModel):
    """Individual TFT forecast history entry"""
    id: int
    model_id: int
    target_column: Optional[str]
    forecast_horizon: int
    forecast_data: Dict
    created_at: str
    
    class Config:
        from_attributes = True


class TFTForecastHistoryResponse(BaseModel):
    """List of saved TFT forecasts"""
    forecasts: list[TFTForecastHistoryItem]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "forecasts": [
                    {
                        "id": 43,
                        "model_id": 20,
                        "target_column": "icu_ventilator_usage",
                        "forecast_horizon": 72,
                        "forecast_data": {
                            "horizons": {"6h": {...}, "24h": {...}},
                            "forecast_sequence": [15.7, 16.2]
                        },
                        "created_at": "2026-02-27T10:30:00"
                    }
                ],
                "total_count": 1
            }
        }


class TFTModelValidationRequest(BaseModel):
    """Validate if dataset is compatible with TFT model"""
    model_id: int
    dataset_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 20,
                "dataset_id": 5
            }
        }


class TFTModelValidationResponse(BaseModel):
    """Validation result for TFT model"""
    is_valid: bool
    model_id: int
    required_time_columns: list[str]
    has_timestamp_column: bool
    min_sequence_length_required: int
    actual_sequence_length: Optional[int]
    warnings: list[str]
    can_proceed: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "model_id": 20,
                "required_time_columns": ["timestamp", "time_idx"],
                "has_timestamp_column": True,
                "min_sequence_length_required": 30,
                "actual_sequence_length": 240,
                "warnings": [],
                "can_proceed": True
            }
        }
