"""
TFT Forecast Routes
STRICTLY for multi-horizon time-series forecasting
NO ML_REGRESSION logic - completely separate from single-point predictions
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.database import get_db
from app.utils.auth import require_role
from app.schemas.tft_forecast_schema import (
    TFTForecastRequest,
    TFTForecastResponse,
    TFTForecastSaveRequest,
    TFTForecastSaveResponse,
    TFTForecastHistoryResponse,
    TFTModelValidationRequest,
    TFTModelValidationResponse
)
from app.services.tft_forecast_service import TFTForecastService


router = APIRouter()


@router.post("/tft", response_model=TFTForecastResponse, status_code=status.HTTP_200_OK)
async def forecast_tft(
    request: TFTForecastRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate multi-horizon forecast using TFT model
    
    **ARCHITECTURE: TFT ONLY**
    - Uses Temporal Fusion Transformer (PyTorch)
    - Returns multi-step sequence forecast
    - Time-aware with timestamp context
    - Multiple horizons (6h, 12h, 24h, 48h, 72h, 168h)
    - Uncertainty quantification with confidence bands
    
    **Request Body:**
    ```json
    {
      "model_id": 20,
      "encoder_sequence": null,
      "prediction_length": 72
    }
    ```
    
    **Response:**
    ```json
    {
      "model_architecture": "TFT",
      "model_id": 20,
      "training_type": "FEDERATED",
      "target_column": "icu_ventilator_usage",
      "horizons": {
        "6h": {"timestamp": "...", "hour_ahead": 6, "p10": 12.3, "p50": 15.7, "p90": 19.4},
        "12h": {"timestamp": "...", "hour_ahead": 12, "p10": 13.2, "p50": 16.9, "p90": 20.5},
        "24h": {"timestamp": "...", "hour_ahead": 24, "p10": 14.1, "p50": 18.2, "p90": 22.8},
        "48h": {"timestamp": "...", "hour_ahead": 48, "p10": 15.3, "p50": 19.7, "p90": 24.0},
        "72h": {"timestamp": "...", "hour_ahead": 72, "p10": 16.5, "p50": 21.3, "p90": 26.7},
        "168h": {"timestamp": "...", "hour_ahead": 168, "p10": 18.9, "p50": 24.1, "p90": 29.6}
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
    ```
    
    **Use Cases:**
    - Multi-step ahead forecasting of ICU demand
    - Time series prediction with uncertainty
    - Trend forecasting with confidence bands
    - Long-range resource planning
    
    **Validation:**
    - Model MUST be TFT architecture
    - Dataset MUST have 'timestamp' column
    - Minimum sequence length required (30+ points)
    
    **Errors:**
    - 400: Model is ML_REGRESSION (use /api/predictions/ml instead)
    - 400: Missing timestamp column
    - 404: Model not found
    - 403: Access denied to model
    - 503: TFT not available (PyTorch not installed)
    """
    hospital = current_user["db_object"]
    
    forecast_result = TFTForecastService.forecast(
        hospital=hospital,
        model_id=request.model_id,
        encoder_sequence=request.encoder_sequence,
        prediction_length=request.prediction_length,
        db=db
    )
    
    return forecast_result


@router.post("/tft/validate", response_model=TFTModelValidationResponse)
async def validate_tft_dataset(
    request: TFTModelValidationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Validate if dataset is compatible with TFT model
    
    **Use Before Forecasting:**
    - Check if dataset has required time columns
    - Verify minimum sequence length
    - Confirm model compatibility
    
    **Request:**
    ```json
    {
      "model_id": 20,
      "dataset_id": 5
    }
    ```
    
    **Response:**
    ```json
    {
      "is_valid": true,
      "model_id": 20,
      "required_time_columns": ["timestamp", "time_idx"],
      "has_timestamp_column": true,
      "min_sequence_length_required": 30,
      "actual_sequence_length": 240,
      "warnings": [],
      "can_proceed": true
    }
    ```
    """
    validation_result = TFTForecastService.validate_dataset(
        model_id=request.model_id,
        dataset_id=request.dataset_id,
        db=db
    )
    
    return validation_result


@router.post("/tft/save", response_model=TFTForecastSaveResponse)
async def save_tft_forecast(
    request: TFTForecastSaveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Save TFT forecast result for audit/history
    
    **Request:**
    ```json
    {
      "model_id": 20,
      "forecast_data": {
        "horizons": {...},
        "forecast_sequence": [...],
        "confidence_interval": {...}
      },
      "prediction_length": 72,
      "dataset_id": 5
    }
    ```
    
    **Response:**
    ```json
    {
      "prediction_record_id": 43,
      "message": "TFT forecast saved successfully",
      "timestamp": "2026-02-27T10:30:00"
    }
    ```
    """
    hospital = current_user["db_object"]
    
    save_result = TFTForecastService.save_forecast(
        hospital=hospital,
        model_id=request.model_id,
        forecast_data=request.forecast_data,
        prediction_length=request.prediction_length,
        dataset_id=request.dataset_id,
        db=db
    )
    
    return save_result


@router.get("/tft/history", response_model=TFTForecastHistoryResponse)
async def get_tft_forecast_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    List saved TFT forecast history for current hospital
    
    **Query Parameters:**
    - `limit`: Maximum number of records to return (default: 20)
    
    **Response:**
    ```json
    {
      "forecasts": [
        {
          "id": 43,
          "model_id": 20,
          "target_column": "icu_ventilator_usage",
          "forecast_horizon": 72,
          "forecast_data": {
            "horizons": {...},
            "forecast_sequence": [...]
          },
          "created_at": "2026-02-27T10:30:00"
        }
      ],
      "total_count": 1
    }
    ```
    """
    hospital = current_user["db_object"]
    
    history = TFTForecastService.list_forecasts(
        hospital=hospital,
        db=db,
        limit=limit
    )
    
    return history
