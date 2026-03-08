"""
ML_REGRESSION Prediction Routes
STRICTLY for single-point regression predictions
NO TFT logic - completely separate from time-series forecasting
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.utils.auth import require_role
from app.schemas.ml_prediction_schema import (
    MLPredictionRequest,
    MLPredictionResponse,
    MLPredictionSaveRequest,
    MLPredictionSaveResponse,
    MLPredictionHistoryResponse,
    MLModelValidationRequest,
    MLModelValidationResponse
)
from app.services.ml_prediction_service import MLPredictionService


router = APIRouter()


@router.post("/ml", response_model=MLPredictionResponse, status_code=status.HTTP_200_OK)
async def predict_ml(
    request: MLPredictionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate single-point prediction using ML_REGRESSION model
    
    **ARCHITECTURE: ML_REGRESSION ONLY**
    - Uses sklearn Random Forest
    - Returns single predicted value (NOT a sequence)
    - No time component
    - No horizon
    - Deterministic mapping from features to prediction
    
    **Request Body:**
    ```json
    {
      "model_id": 1,
      "features": {
        "er_visits": 120,
        "staff_count": 45,
        "flu_cases": 38
      }
    }
    ```
    
    **Response:**
    ```json
    {
      "model_architecture": "ML_REGRESSION",
      "model_id": 1,
      "training_type": "LOCAL",
      "target_column": "bed_occupancy",
      "prediction": 86.3,
      "input_features": {...},
      "feature_count": 3,
      "timestamp": "2026-02-27T10:30:00"
    }
    ```
    
    **Use Cases:**
    - Predict bed occupancy from current hospital metrics
    - Estimate resource needs from operational data
    - Single-point forecasts without time dependency
    
    **Validation:**
    - Model MUST be ML_REGRESSION architecture
    - Features MUST match training schema
    - All required features MUST be provided
    
    **Errors:**
    - 400: Model is TFT (use /api/predictions/tft instead)
    - 400: Missing required features
    - 404: Model not found
    - 403: Access denied to model
    """
    hospital = current_user["db_object"]
    
    prediction_result = MLPredictionService.predict(
        hospital=hospital,
        model_id=request.model_id,
        features=request.features,
        db=db
    )
    
    return prediction_result


@router.post("/ml/validate", response_model=MLModelValidationResponse)
async def validate_ml_features(
    request: MLModelValidationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Validate if provided features match ML model training schema
    
    **Use Before Prediction:**
    - Check if all required features are provided
    - Identify missing or extra features
    - Confirm model compatibility
    
    **Request:**
    ```json
    {
      "model_id": 1,
      "features": {
        "er_visits": 120,
        "staff_count": 45
      }
    }
    ```
    
    **Response:**
    ```json
    {
      "is_valid": false,
      "model_id": 1,
      "required_features": ["er_visits", "staff_count", "flu_cases"],
      "provided_features": ["er_visits", "staff_count"],
      "missing_features": ["flu_cases"],
      "extra_features": [],
      "warnings": ["Missing required features: ['flu_cases']"],
      "can_proceed": false
    }
    ```
    """
    validation_result = MLPredictionService.validate_features(
        model_id=request.model_id,
        features=request.features,
        db=db
    )
    
    return validation_result


@router.post("/ml/save", response_model=MLPredictionSaveResponse)
async def save_ml_prediction(
    request: MLPredictionSaveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Save ML prediction result for audit/history
    
    **Request:**
    ```json
    {
      "model_id": 1,
      "features": {"er_visits": 120, "staff_count": 45},
      "prediction": 86.3,
      "dataset_id": 5
    }
    ```
    
    **Response:**
    ```json
    {
      "prediction_record_id": 42,
      "message": "ML prediction saved successfully",
      "timestamp": "2026-02-27T10:30:00"
    }
    ```
    """
    hospital = current_user["db_object"]
    
    save_result = MLPredictionService.save_prediction(
        hospital=hospital,
        model_id=request.model_id,
        features=request.features,
        prediction=request.prediction,
        dataset_id=request.dataset_id,
        db=db
    )
    
    return save_result


@router.get("/ml/history", response_model=MLPredictionHistoryResponse)
async def get_ml_prediction_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    List saved ML prediction history for current hospital
    
    **Query Parameters:**
    - `limit`: Maximum number of records to return (default: 20)
    
    **Response:**
    ```json
    {
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
    ```
    """
    hospital = current_user["db_object"]
    
    history = MLPredictionService.list_predictions(
        hospital=hospital,
        db=db,
        limit=limit
    )
    
    return history
