"""
Model hashing routes (Phase 19)
Hash generation and verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.model_weights import ModelWeights
from app.utils.auth import require_role
from app.services.model_hashing import ModelHashingService

router = APIRouter()


@router.get("/verify/{model_id}")
async def verify_model_hash(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Verify model hash integrity
    
    - **model_id**: Model to verify
    
    Computes current hash and compares with stored hash.
    Returns verification status.
    """
    # Get model
    model = db.query(ModelWeights).filter(
        ModelWeights.id == model_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify access
    hospital = current_user["db_object"]
    if model.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global model hashes are restricted to central administration."
        )
    if model.hospital_id and model.hospital_id != hospital.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if not model.model_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model has no stored hash"
        )
    
    # Verify hash
    is_valid = ModelHashingService.verify_model_hash(
        model.model_path,
        model.model_hash
    )
    
    # Get current hash
    current_hash = ModelHashingService.hash_model_file(model.model_path)
    
    return {
        'model_id': model_id,
        'stored_hash': model.model_hash,
        'current_hash': current_hash,
        'hash_algorithm': model.hash_algorithm,
        'is_valid': is_valid,
        'verification_status': 'VERIFIED' if is_valid else 'TAMPERED'
    }


@router.post("/rehash/{model_id}")
async def rehash_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Recompute and update model hash
    
    - **model_id**: Model to rehash
    
    Use after model updates to refresh stored hash.
    """
    # Get model
    model = db.query(ModelWeights).filter(
        ModelWeights.id == model_id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Verify ownership
    hospital = current_user["db_object"]
    if model.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Global model hashes are restricted to central administration."
        )
    if model.hospital_id != hospital.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only rehash your own models"
        )
    
    # Compute new hash
    new_hash = ModelHashingService.hash_model_file(model.model_path)
    
    # Update database
    old_hash = model.model_hash
    model.model_hash = new_hash
    model.hash_algorithm = 'sha256'
    db.commit()
    
    return {
        'status': 'rehashed',
        'model_id': model_id,
        'old_hash': old_hash,
        'new_hash': new_hash
    }


@router.get("/merkle-root/{round_number}")
async def get_round_merkle_root(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Get Merkle root of all models in a round
    
    - **round_number**: Federated round number
    
    Computes Merkle root from all hospital model hashes.
    Useful for batch verification.
    """
    # Get all models for this round
    models = db.query(ModelWeights).filter(
        ModelWeights.round_number == round_number,
        ModelWeights.is_global == False
    ).all()
    
    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No models found for round {round_number}"
        )
    
    # Collect hashes
    hashes = [m.model_hash for m in models if m.model_hash]
    
    if not hashes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hashed models in this round"
        )
    
    # Compute Merkle root
    merkle_root = ModelHashingService.generate_merkle_root(hashes)
    
    return {
        'round_number': round_number,
        'num_models': len(hashes),
        'merkle_root': merkle_root,
        'hospital_hashes': [
            {
                'hospital_id': m.hospital_id,
                'model_id': m.id,
                'hash': m.model_hash
            }
            for m in models if m.model_hash
        ]
    }
