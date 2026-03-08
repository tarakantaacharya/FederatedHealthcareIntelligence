"""
Model metadata routes - Enhanced for complete prediction schema visibility
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.services.model_management_service import ModelManagementService
from app.schemas.model_metadata_schema import ModelMetadataResponse

router = APIRouter()


@router.get("/models/{model_id}/metadata", response_model=ModelMetadataResponse)
async def get_model_metadata(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get trained feature columns and target column for a model.

    This endpoint is used by the ML prediction UI to render inputs
    that match the exact trained feature order.
    
    CRITICAL: This endpoint is the source of truth for which features
    should be provided during prediction. Frontend MUST use these
    trained_feature_columns, NOT dataset columns.
    
    Returns:
    {
      "model_architecture": "ML_REGRESSION" or "TFT",
      "training_type": "LOCAL" or "FEDERATED",
      "target_column": "bed_occupancy",
      "trained_feature_columns": ["er_visits", "admissions", ...],
      "feature_count": 7,
      "notes": "All features EXCEPT target column are included"
    }
    """
    model = db.query(ModelWeights).options(
        joinedload(ModelWeights.training_round)
    ).filter(
        ModelWeights.id == model_id
    ).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )

    if current_user.get("role") == "HOSPITAL":
        hospital = current_user["db_object"]
        if model.hospital_id not in (None, hospital.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to model {model_id}"
            )

    training_schema = model.training_schema or {}
    trained_features = (
        training_schema.get("required_columns") or
        training_schema.get("feature_columns") or
        training_schema.get("trained_feature_columns") or
        []
    )

    target_column = training_schema.get("target_column")
    if not target_column and model.training_round:
        target_column = model.training_round.target_column

    # CRITICAL FIX: Ensure target column is NOT in the feature list
    if target_column:
        trained_features = [col for col in trained_features if col != target_column]

    # COMPREHENSIVE LOGGING
    print(f"\n{'='*80}")
    print(f"[MODEL_METADATA] REQUEST for model_id={model_id}")
    print(f"{'='*80}")
    print(f"[MODEL_METADATA] Model Architecture: {model.model_architecture or 'UNKNOWN'}")
    print(f"[MODEL_METADATA] Training Type: {model.training_type or 'UNKNOWN'}")
    print(f"[MODEL_METADATA] Target Column: {target_column}")
    print(f"[MODEL_METADATA] Feature Count: {len(trained_features)}")
    print(f"[MODEL_METADATA] Features ({len(trained_features)}): {trained_features}")
    
    if not trained_features:
        print(f"[MODEL_METADATA_WARNING] NO TRAINED FEATURES! Schema may be incomplete.")
    
    if target_column in trained_features:
        print(f"[MODEL_METADATA_ERROR] TARGET COLUMN IN FEATURES - BUG DETECTED!")
    
    print(f"{'='*80}\n")

    # Extract multi-model training metadata from training_schema
    candidate_models = training_schema.get("candidate_models")
    best_model = training_schema.get("best_model")
    all_model_metrics = training_schema.get("all_model_metrics")
    test_r2 = training_schema.get("test_r2")
    test_rmse = training_schema.get("test_rmse")
    test_mae = training_schema.get("test_mae")
    test_mape = training_schema.get("test_mape")

    response = ModelMetadataResponse(
        model_architecture=model.model_architecture or "UNKNOWN",
        training_type=model.training_type or "LOCAL",
        target_column=target_column,
        trained_feature_columns=trained_features,
        feature_count=len(trained_features),
        candidate_models=candidate_models,
        best_model=best_model,
        all_model_metrics=all_model_metrics,
        test_r2=test_r2,
        test_rmse=test_rmse,
        test_mae=test_mae,
        test_mape=test_mape
    )
    
    return response


@router.delete("/models/clear-local")
async def clear_local_models(
    delete_files: bool = Query(True, description="Delete physical model files from disk"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Clear all local models for current hospital."""
    # Get hospital from current_user
    hospital_id_str = current_user.get("id")
    hospital = db.query(Hospital).filter(Hospital.hospital_id == hospital_id_str).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital {hospital_id_str} not found"
        )
    
    result = ModelManagementService.clear_local_models(
        hospital_id=hospital.id,
        db=db,
        delete_files=delete_files
    )
    
    return {
        "success": True,
        "message": f"Local models cleared for hospital {hospital.hospital_name}",
        "hospital_id": hospital.hospital_id,
        "hospital_name": hospital.hospital_name,
        "details": result
    }


@router.get("/models/summary")
async def get_local_models_summary(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Get summary of local models for the current hospital."""
    # Get hospital from current_user
    hospital_id_str = current_user.get("id")
    hospital = db.query(Hospital).filter(Hospital.hospital_id == hospital_id_str).first()
    
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital {hospital_id_str} not found"
        )
    
    summary = ModelManagementService.get_model_summary(
        hospital_id=hospital.id,
        db=db
    )
    
    return {
        "hospital_id": hospital.hospital_id,
        "hospital_name": hospital.hospital_name,
        **summary
    }