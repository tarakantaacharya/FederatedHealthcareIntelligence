"""
Model updates routes (Phase 6)
Distribution of global models to hospitals
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.utils.auth import require_role
from app.security.rbac import require_admin_role
from app.schemas.model_update_schema import (
    GlobalModelDownloadResponse,
    LocalUpdateResponse,
    GlobalModelListResponse,
    SyncStatusResponse,
    ModelPersonalizationRequest,
    ModelPersonalizationResponse
)
from app.services.model_update_service import ModelUpdateService

router = APIRouter()


@router.post("/download/{round_number}", response_model=GlobalModelDownloadResponse)
async def download_global_model(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Download global model weights for a specific round
    
    - **round_number**: Federated learning round number
    
    Downloads aggregated global model from central server to hospital's local storage.
    Creates a local copy of the global model for the hospital to use.
    """
    hospital = current_user["db_object"]
    result = ModelUpdateService.download_global_model(
        round_number=round_number,
        db=db,
        hospital=hospital
    )
    
    return result


@router.post("/apply/{round_number}", response_model=LocalUpdateResponse)
async def apply_global_model(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Update local model with global weights from a specific round
    
    - **round_number**: Federated learning round number
    
    Applies global model weights to the hospital's local model.
    This prepares the hospital for the next training round with the aggregated knowledge.
    """
    hospital = current_user["db_object"]
    result = ModelUpdateService.update_local_with_global(
        round_number=round_number,
        db=db,
        hospital=hospital
    )
    
    return result


@router.get("/global", response_model=List[GlobalModelListResponse])
async def list_global_models(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL"))
):
    """
    List all available models for prediction
    
    - HOSPITAL: Returns all LOCAL and FEDERATED models trained by this hospital
    - ADMIN: Returns all approved global federated models
    
    Hospitals can see which models are available for predictions (both local and global).
    """
    if current_user.get("role") == "HOSPITAL":
        hospital = current_user["db_object"]
        global_models = ModelUpdateService.get_all_available_models_for_hospital(db, hospital.id)
    else:
        global_models = ModelUpdateService.get_available_global_models(db)
    
    result = []
    for model in global_models:
        # Build response with all required fields
        response = GlobalModelListResponse(
            id=model.id,
            round_number=model.round_number,
            model_type=model.model_type,
            accuracy=model.local_accuracy,
            loss=model.local_loss,
            created_at=model.created_at,
            training_type=getattr(model, 'training_type', 'FEDERATED'),
            model_architecture=getattr(model, 'model_architecture', 'TFT'),
            training_schema=getattr(model, 'training_schema', None),
            target_column=model.training_round.target_column if hasattr(model, 'training_round') and model.training_round else None,
            dataset_id=getattr(model, 'dataset_id', None),

            # 🔥 ADD THESE TWO
            is_global=model.is_global,
            hospital_id=model.hospital_id
        )
        
        # Add display_name: "Round X - ARCHITECTURE"
        response.display_name = f"Round {model.round_number} - {model.model_architecture}"
        
        # Add suggested_next_round for LOCAL models
        if model.training_type == "LOCAL":
            response.suggested_next_round = model.round_number + 1
        
        result.append(response)
    
    return result


@router.get("/global/{model_id}/weights-json")
async def get_hospital_aggregated_weights_json(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Hospital read-only preview of approved/distributed aggregated global weights.

    - **model_id**: Any federated model visible to hospital (round is used to resolve
      the approved global aggregate artifact)
    """
    hospital = current_user["db_object"]
    return ModelUpdateService.get_hospital_aggregated_weights_preview(
        model_id=model_id,
        db=db,
        hospital=hospital
    )


@router.get("/admin/global/{model_id}/weights-json")
async def get_central_aggregated_weights_json(
    model_id: int,
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(require_admin_role("ADMIN"))
):
    """
    Central admin read-only preview of approved aggregated global weights.

    - **model_id**: Global model ID (must be governance-approved)
    - Admin can view all approved models without distribution restrictions
    """
    return ModelUpdateService.get_central_aggregated_weights_preview(
        model_id=model_id,
        db=db
    )


@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check hospital's synchronization status with global models
    
    Shows which rounds the hospital has synced and which are missing.
    Helps hospitals track their participation in federated learning.
    """
    hospital = current_user["db_object"]
    result = ModelUpdateService.get_hospital_sync_status(
        hospital_id=hospital.id,
        db=db
    )
    
    return result


@router.post("/personalize/{round_number}", response_model=ModelPersonalizationResponse)
async def personalize_model(
    round_number: int,
    request: ModelPersonalizationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Hospital-side FL/PFL personalization
    
    - **round_number**: Federated learning round
    - **mode**: "FL" (use global directly) or "PFL" (personalize locally)
    - **personalization_lr**: Learning rate for personalization (PFL only)
    
    FL: Wf = Wagg (low variance, high bias)
    PFL: Wf = W + lr*(W-Wagg) (high variance, low bias)
    """
    hospital = current_user["db_object"]
    result = ModelUpdateService.personalize_model(
        round_number=round_number,
        db=db,
        hospital=hospital,
        mode=request.mode,
        personalization_lr=request.personalization_lr or 0.5
    )
    
    return result
