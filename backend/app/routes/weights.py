"""
Weight transfer routes (Phase 4)
Upload local weights to central server
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.weight_schema import (
    WeightUploadRequest,
    WeightUploadResponse,
    WeightExtractionResponse,
    MaskUploadRequest,
    MaskUploadResponse,
    MaskGenerationRequest,
    MaskGenerationResponse
)
from app.services.weight_service import WeightService

router = APIRouter()


@router.post("/upload", response_model=WeightUploadResponse)
async def upload_weights(
    upload_request: WeightUploadRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Upload local model weights to central server
    
    - **model_id**: Local trained model ID
    - **round_number**: Federated learning round number (default: 1)
    
    Extracts weights from local model and uploads to central aggregation server.
    Weights are stored in JSON format for FedAvg aggregation (Phase 5).
    """
    hospital = current_user["db_object"]
    if not hospital.is_allowed_federated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital is not allowed to participate in federated rounds."
        )
    result = WeightService.upload_weights_to_central(
        model_id=upload_request.model_id,
        db=db,
        hospital=hospital,
        round_number=upload_request.round_number,
        actual_hyperparameters=upload_request.actual_hyperparameters
    )
    
    return result


@router.post("/masks/generate", response_model=MaskGenerationResponse)
async def generate_mask(
    generate_request: MaskGenerationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Generate MPC mask for a trained model
    
    - **model_id**: Trained model ID
    - **round_number**: Federated learning round number (default: 1)
    
    Generates random mask based on model weight shapes and returns serialized JSON.
    Frontend must call this before mask upload.
    """
    hospital = current_user["db_object"]
    if not hospital.is_allowed_federated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital is not allowed to participate in federated rounds."
        )
    mask_info = WeightService.generate_mask(
        model_id=generate_request.model_id,
        dataset_id=generate_request.dataset_id,
        db=db,
        hospital=hospital,
        round_number=generate_request.round_number
    )
    
    return {
        'status': 'mask_generated',
        'model_id': generate_request.model_id,
        'mask_payload': mask_info['mask_payload'],
        'mask_hash': mask_info['mask_hash']
    }


@router.post("/masks/upload", response_model=MaskUploadResponse)
async def upload_mask(
    upload_request: MaskUploadRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Upload MPC mask for a specific round
    
    PHASE 41 GOVERNANCE:
    - Verifies weights were uploaded first (is_uploaded == TRUE)
    - Enforces UNIQUE (model_id) for masks
    - Returns structured response with governance confirmation

    - **round_number**: Federated learning round number
    - **mask_payload**: Serialized mask JSON
    - **mask_hash**: Mask checksum from generation
    """
    hospital = current_user["db_object"]
    if not hospital.is_allowed_federated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital is not allowed to participate in federated rounds."
        )
    
    # PHASE 41: Get model_id from upload request
    # Update: Check if model_id is in upload_request, if not infer from context
    model_id = getattr(upload_request, 'model_id', None)
    if not model_id:
        raise ValueError("model_id required in mask upload request")
    
    mask_info = WeightService.save_mask_upload(
        round_number=upload_request.round_number,
        hospital_id=hospital.id,
        mask_payload=upload_request.mask_payload,
        mask_hash=upload_request.mask_hash,
        db=db,
        model_id=model_id
    )

    return {
        'status': 'success',
        'round_id': mask_info['round_id'],
        'model_id': mask_info['model_id'],
        'hospital_id': hospital.id,
        'round_number': upload_request.round_number,
        'mask_path': mask_info['mask_path'],
        'mask_hash': mask_info['mask_hash']
    }


@router.get("/extract/{model_id}", response_model=WeightExtractionResponse)
async def extract_weights(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Extract weights from trained model (for inspection)
    
    - **model_id**: Local model ID
    
    Returns serialized model weights without uploading.
    Useful for debugging and verification.
    """
    hospital = current_user["db_object"]
    if not hospital.is_allowed_federated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital is not allowed to participate in federated rounds."
        )
    weights_data = WeightService.extract_weights(model_id, db, hospital)
    return weights_data


@router.get("/central/round/{round_number}/hospital/{hospital_id}")
async def get_central_uploaded_weights_for_hospital(
    round_number: int,
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Admin-only: view uploaded central weight JSON for one hospital in a round.

    Returns the exact stored JSON payload used for aggregation input.
    """
    return WeightService.get_uploaded_weights_for_hospital(
        round_number=round_number,
        hospital_id=hospital_id,
        db=db,
    )
