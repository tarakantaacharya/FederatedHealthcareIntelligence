"""
Prediction routes (Phase 16 + Phase 43 Traceability)
Multi-horizon forecasting with uncertainty + Prediction drill-down system
"""
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.models.hospital import Hospital
from app.schemas.prediction_schema import (
    ForecastRequest,
    ForecastResponse,
    ModelComparisonRequest,
    ModelComparisonResponse,
    SchemaValidationRequest,
    SchemaValidationResponse,
    PredictionSaveRequest,
    PredictionSaveResponse,
    PredictionHistoryResponse,
    PredictionListResponse,
    PredictionDetailResponse,
    PredictionExportRequest
)
from app.services.prediction_service import PredictionService
from app.services.schema_service import SchemaService

router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate multi-step ahead forecast
    
    - **model_id**: Model to use (local or global)
    - **forecast_horizon**: Number of hours to forecast (1-168)
    
    **Returns:**
    - Point predictions for each time step
    - 95% confidence intervals (lower_bound, upper_bound)
    - Forecast quality metrics (MAPE, bias, trend alignment)
    
    **Example Use Cases:**
    - Forecast bed occupancy for next 24 hours
    - Predict ER visits for next week
    - Anticipate ICU demand for next 48 hours
    """
    try:
        hospital = current_user["db_object"]
        forecast = PredictionService.generate_forecast(
            hospital=hospital,
            model_id=request.model_id,
            forecast_horizon=request.forecast_horizon,
            db=db
        )
        
        return forecast
    except Exception as e:
        import traceback
        print(f"[ROUTE ERROR] Prediction failed: {str(e)}")
        print(traceback.format_exc())
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/compare-models", response_model=ModelComparisonResponse)
async def compare_model_forecasts(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Compare forecasts from multiple models
    
    - **model_ids**: List of model IDs to compare
    - **forecast_horizon**: Forecast horizon
    
    **Use Cases:**
    - Compare local vs global model
    - Evaluate different model versions
    - Ensemble predictions from multiple models
    
    Returns forecasts from all models for side-by-side comparison.
    """
    hospital = current_user["db_object"]
    comparison = PredictionService.compare_models(
        hospital=hospital,
        model_ids=request.model_ids,
        forecast_horizon=request.forecast_horizon,
        db=db
    )
    
    return comparison


@router.get("/latest-forecast")
async def get_latest_forecast(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get latest forecast (default 24 hour horizon)
    
    - **model_id**: Model ID
    
    Quick endpoint for dashboard display.
    """
    hospital = current_user["db_object"]
    forecast = PredictionService.generate_forecast(
        hospital=hospital,
        model_id=model_id,
        forecast_horizon=24,
        db=db
    )
    
    return forecast


@router.post("/validate-schema", response_model=SchemaValidationResponse)
async def validate_dataset_schema(
    request: SchemaValidationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Validate if dataset schema matches model training schema.
    
    **Use Before Prediction:**
    - Check if dataset is compatible with model
    - Identify missing or extra columns
    - Get auto-alignment warnings
    
    **Returns:**
    - schema_match: True if exact match, False if differences exist
    - missing_columns: Columns required by model but not in dataset
    - extra_columns: Columns in dataset but not used by model
    - warnings: List of alignment warnings
    - can_auto_align: Whether automatic feature alignment is possible
    - model_schema: Training schema metadata
    - dataset_schema: Current dataset schema
    
    **Example Response:**
    ```json
    {
        "schema_match": false,
        "missing_columns": [],
        "extra_columns": ["staff_to_bed_ratio"],
        "warnings": ["Dataset has 1 extra columns - will drop during inference"],
        "can_auto_align": true,
        "model_schema": { "required_columns": [...], "num_features": 8 },
        "dataset_schema": { "columns": [...], "num_columns": 11 }
    }
    ```
    """
    validation_result = SchemaService.validate_schema(
        model_id=request.model_id,
        dataset_id=request.dataset_id,
        db=db
    )
    
    return validation_result


@router.post("/save", response_model=PredictionSaveResponse)
async def save_prediction(
    request: PredictionSaveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Save a prediction result for later review and schema checks."""
    hospital = current_user["db_object"]
    result = PredictionService.save_prediction(
        hospital=hospital,
        model_id=request.model_id,
        dataset_id=request.dataset_id,
        forecast_horizon=request.forecast_horizon,
        forecast_data=request.forecast_data,
        db=db
    )
    return result


@router.get("/history", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """List saved prediction history for the current hospital."""
    hospital = current_user["db_object"]
    return PredictionService.list_saved_predictions(
        hospital=hospital,
        db=db,
        limit=limit
    )


# Phase 43: Prediction Traceability & Drill-Down System

@router.get("/list", response_model=Dict[str, Any])
async def list_predictions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get paginated list of saved predictions for hospital dashboard.
    
    **Columns:**
    - Prediction ID
    - Dataset Name
    - Model Type (LOCAL / FEDERATED)
    - Training Round
    - Timestamp
    - Action (View Details)
    
    **Returns:**
    - items: List of prediction records
    - total: Total count of predictions
    - limit: Page size
    - offset: Pagination offset
    """
    hospital = current_user["db_object"]
    return PredictionService.list_saved_predictions(
        hospital=hospital,
        db=db,
        limit=limit,
        offset=offset
    )


@router.get("/{prediction_id}", response_model=Dict[str, Any])
async def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get comprehensive prediction detail view.
    
    **Sections:**
    1. **Prediction Summary**
       - Prediction ID, Hospital, Dataset, Training Round
       - Model Type, Target Variable, Predicted Value
       - Timestamp, Model Version
    
    2. **Performance Metrics**
       - R², RMSE, MAPE, Model Accuracy
       - Feature Importance (dict)
       - Confidence Interval (bounds)
    
    3. **Governance Metadata**
       - Model Type (LOCAL/FEDERATED)
       - DP Epsilon (if privacy-enabled)
       - Aggregation Participants (for federated)
       - Blockchain Audit Hash
       - Contribution Weight
    
    4. **Dataset Snapshot**
       - Dataset info, schema, record count
       - Target distribution
    
    5. **Forecast Data**
       - Full forecast with horizons
       - Schema validation results
       - Input snapshot
    """
    hospital = current_user["db_object"]
    return PredictionService.get_prediction_detail(
        prediction_id=prediction_id,
        hospital=hospital,
        db=db
    )


@router.post("/export")
async def export_prediction(
    request: PredictionExportRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Export prediction as PDF, JSON, or CSV report.
    
    **Formats:**
    - **pdf**: Professional report with metrics, charts, governance info
    - **json**: Full machine-readable prediction data
    - **csv**: Flattened forecast data for spreadsheet analysis
    
    **Use Cases:**
    - Archive prediction for audit trail
    - Share reports with stakeholders
    - Integrate with external analysis tools
    """
    hospital = current_user["db_object"]
    
    # Verify access to prediction
    from app.models.prediction_record import PredictionRecord
    prediction = db.query(PredictionRecord).filter(
        PredictionRecord.id == request.prediction_id,
        PredictionRecord.hospital_id == hospital.id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found or access denied"
        )

    # Format-specific export logic
    if request.format == "json":
        detail = PredictionService.get_prediction_detail(
            prediction_id=request.prediction_id,
            hospital=hospital,
            db=db
        )
        return {
            "file_content": detail,
            "filename": f"prediction_{request.prediction_id}.json",
            "format": "json"
        }

    elif request.format == "csv":
        # Extract forecast data as CSV
        forecast_data = prediction.forecast_data or {}
        forecasts = forecast_data.get("forecasts", [])

        csv_content = "timestamp,hour_ahead,prediction,lower_bound,upper_bound,confidence\n"
        for forecast in forecasts:
            csv_content += f"{forecast.get('timestamp', '')},{forecast.get('hour_ahead', '')},{forecast.get('prediction', '')},{forecast.get('lower_bound', '')},{forecast.get('upper_bound', '')},{forecast.get('confidence_level', '')}\n"

        return {
            "file_content": csv_content,
            "filename": f"prediction_{request.prediction_id}.csv",
            "format": "csv"
        }

    elif request.format == "pdf":
        # Generate comprehensive PDF report with AI summaries and charts
        try:
            from app.services.report_service import ReportGenerationService

            # Convert ORM object to dict for report service
            prediction_dict = {
                "id": prediction.id,
                "target_column": prediction.target_column,
                "model_type": prediction.model_type,
                "model_version": prediction.model_version,
                "forecast_horizon": prediction.forecast_horizon,
                "prediction_timestamp": prediction.prediction_timestamp,
                "prediction_value": prediction.prediction_value,
                "round_number": prediction.round_number,
                "forecast_data": prediction.forecast_data,
                "model_accuracy_snapshot": prediction.model_accuracy_snapshot,
                "feature_importance": prediction.feature_importance,
                "confidence_interval": prediction.confidence_interval,
                "aggregation_participants": prediction.aggregation_participants,
                "dp_epsilon_used": prediction.dp_epsilon_used,
                "prediction_hash": prediction.prediction_hash,
                "summary_text": prediction.summary_text,
                "created_at": prediction.created_at
            }
            
            hospital_dict = {
                "hospital_name": hospital.hospital_name,
                "hospital_id": hospital.hospital_id,
                "location": hospital.location
            }
            
            # Generate PDF
            pdf_bytes = ReportGenerationService.generate_prediction_report(
                prediction_record=prediction_dict,
                hospital_info=hospital_dict
            )
            
            # Return base64 encoded PDF
            import base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return {
                "file_content": pdf_base64,
                "filename": f"prediction_report_{request.prediction_id}.pdf",
                "format": "pdf",
                "message": "PDF report generated successfully"
            }
        except Exception as e:
            print(f"[EXPORT] PDF generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": f"PDF export failed: {str(e)}",
            "filename": f"prediction_{request.prediction_id}.pdf",
            "format": "pdf"
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported export format"
    )


@router.delete("/clear")
async def clear_all_predictions(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Clear all saved predictions for the current hospital
    
    **Returns:**
    - Count of deleted predictions
    
    **Permissions:**
    - HOSPITAL role required
    """
    hospital_id = current_user.get("id")
    hospital = db.query(Hospital).filter(Hospital.hospital_id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hospital not found"
        )
    
    deleted_count = PredictionService.clear_all_predictions(
        hospital_id=hospital.id,
        db=db
    )
    
    return {
        "message": f"Cleared {deleted_count} predictions",
        "deleted_count": deleted_count
    }


@router.post("/delete-selected")
async def delete_selected_predictions(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Delete selected predictions by IDs
    
    **Request:**
    - prediction_ids: List of prediction IDs to delete
    
    **Returns:**
    - Count of deleted predictions
    
    **Permissions:**
    - HOSPITAL role required
    - User can only delete their own predictions
    """
    hospital_id = current_user.get("id")
    hospital = db.query(Hospital).filter(Hospital.hospital_id == hospital_id).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hospital not found"
        )
    
    prediction_ids = request.get("prediction_ids", [])
    
    if not prediction_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No prediction IDs provided"
        )
    
    deleted_count = PredictionService.delete_selected_predictions(
        hospital_id=hospital.id,
        prediction_ids=prediction_ids,
        db=db
    )
    
    return {
        "message": f"Deleted {deleted_count} predictions",
        "deleted_count": deleted_count
    }

