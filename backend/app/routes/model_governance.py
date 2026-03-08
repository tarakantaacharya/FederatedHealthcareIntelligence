"""
Model Governance Routes (Phase 29)
Admin-only approval and signing of federated models
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.services.model_governance_service import ModelGovernanceService
from app.services.model_management_service import ModelManagementService
from app.models.model_governance import ModelGovernance
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound
from app.security.rbac import require_admin_role
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ApprovalRequest(BaseModel):
    """Request model for model approval"""
    round_number: int
    model_hash: str
    mape: float
    num_participants: int = 0
    policy_version: str = "v1"
    
    # Suppress protected namespace warning for fields like "model_hash"
    model_config = {
        "protected_namespaces": ()
    }


class ApprovalResponse(BaseModel):
    """Response model for approval decision"""
    id: int
    round_number: int
    model_hash: str
    approved: bool
    approved_by: Optional[str]
    signature: Optional[str]
    policy_version: str
    rejection_reason: Optional[str]
    created_at: str
    
    # Suppress protected namespace warning for fields like "model_hash"
    model_config = {
        "protected_namespaces": ()
    }


@router.post("/approve", response_model=ApprovalResponse)
async def approve_global_model(
    approval_request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Approve and cryptographically sign a federated global model
    
    **Admin-only endpoint** (Phase 30: RBAC enforced)
    
    - **round_number**: Training round number
    - **model_hash**: SHA-256 hash of model weights
    - **mape**: Model MAPE (Mean Absolute Percentage Error, lower is better)
    - **num_participants**: Number of participating hospitals
    - **policy_version**: Policy version to apply (default: v1)
    
    Policy v1 requires:
    - MAPE <= 15% (0.15)
    - Minimum 2 participating hospitals
    
    Returns governance record with approval decision and signature (if approved).
    """
    # Get private key from settings (in production, use secure vault)
    PRIVATE_KEY = getattr(settings, "GOVERNANCE_PRIVATE_KEY", "central_private_key_v1")
    
    # Approve model
    governance_record = ModelGovernanceService.approve_model(
        db=db,
        round_number=approval_request.round_number,
        model_hash=approval_request.model_hash,
        mape=approval_request.mape,
        admin_user=getattr(current_admin, "admin_name", getattr(current_admin, "admin_id", "admin")),
        private_key=PRIVATE_KEY,
        num_participants=approval_request.num_participants,
        policy_version=approval_request.policy_version
    )
    
    return ApprovalResponse(
        id=governance_record.id,
        round_number=governance_record.round_number,
        model_hash=governance_record.model_hash,
        approved=governance_record.approved,
        approved_by=governance_record.approved_by,
        signature=governance_record.signature,
        policy_version=governance_record.policy_version,
        rejection_reason=governance_record.rejection_reason,
        created_at=str(governance_record.created_at)
    )


@router.get("/status")
async def get_governance_status(
    round_number: Optional[int] = Query(None),
    model_hash: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Get governance status for rounds or specific model
    
    - **round_number**: Optional filter by round
    - **model_hash**: Optional filter by model hash
    
    Returns summary of governance evaluations.
    """
    status_data = ModelGovernanceService.get_governance_status(
        db, round_number, model_hash
    )
    return status_data


@router.get("/pending")
async def get_pending_global_models(
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    List global models pending governance approval
    """
    approved_hashes = {
        row[0]
        for row in db.query(ModelGovernance.model_hash)
        .filter(ModelGovernance.approved == True)
        .all()
    }

    global_models = db.query(ModelWeights).filter(
        ModelWeights.is_global == True,
        ModelWeights.hospital_id == None,
        ModelWeights.model_hash.isnot(None)
    ).order_by(ModelWeights.round_number.desc()).all()

    pending = []
    for model in global_models:
        if model.model_hash in approved_hashes:
            continue

        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == model.round_number
        ).first()

        num_participants = training_round.num_participating_hospitals if training_round else 0
        
        # Fallback: if round doesn't have count, query actual participants from model_weights
        if num_participants == 0:
            actual_participants = db.query(ModelWeights).filter(
                ModelWeights.round_number == model.round_number,
                ModelWeights.training_type == "FEDERATED",
                ModelWeights.is_global == False,
                ModelWeights.is_uploaded == True,
                ModelWeights.is_mask_uploaded == True
            ).all()
            if actual_participants:
                num_participants = len(actual_participants)

        pending.append({
            "model_id": model.id,
            "round_number": model.round_number,
            "model_hash": model.model_hash,
            "model_type": model.model_type,
            "accuracy": model.local_accuracy,
            "loss": model.local_loss,
            "num_participants": num_participants,
            "created_at": str(model.created_at)
        })

    return {
        "pending": pending,
        "count": len(pending)
    }

@router.get("/approved")
async def get_approved_global_models(
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    List approved global models
    """
    governance_records = db.query(ModelGovernance).filter(
        ModelGovernance.approved == True
    ).order_by(ModelGovernance.created_at.desc()).all()

    approved = []
    for record in governance_records:
        # Get the corresponding model weights
        model = db.query(ModelWeights).filter(
            ModelWeights.model_hash == record.model_hash,
            ModelWeights.round_number == record.round_number
        ).first()

        training_round = db.query(TrainingRound).filter(
            TrainingRound.round_number == record.round_number
        ).first()

        num_participants = training_round.num_participating_hospitals if training_round else 0
        
        # Fallback: if round doesn't have count, query actual participants from model_weights
        if num_participants == 0:
            actual_participants = db.query(ModelWeights).filter(
                ModelWeights.round_number == record.round_number,
                ModelWeights.training_type == "FEDERATED",
                ModelWeights.is_global == False,
                ModelWeights.is_uploaded == True,
                ModelWeights.is_mask_uploaded == True
            ).all()
            if actual_participants:
                num_participants = len(actual_participants)

        if model:
            approved.append({
                "model_id": model.id,
                "governance_id": record.id,
                "round_number": record.round_number,
                "model_hash": record.model_hash,
                "model_type": model.model_type,
                "accuracy": model.local_accuracy,
                "loss": model.local_loss,
                "mape": model.local_mape,
                "num_participants": training_round.num_participating_hospitals if training_round else 0,
                "approved_by": record.approved_by,
                "signature": record.signature,
                "approved_at": str(record.created_at)
            })

    return {
        "approved": approved,
        "count": len(approved)
    }

@router.get("/policy")
async def get_policy_info():
    """
    Get current governance policy details
    
    Returns policy version and rules.
    """
    return {
        "current_version": "v1",
        "policies": {
            "v1": {
                "description": "MAPE threshold and participation requirement",
                "rules": {
                    "min_accuracy": ModelGovernanceService.POLICY_V1_MAPE_THRESHOLD,
                    "min_participants": ModelGovernanceService.POLICY_V1_MIN_PARTICIPANTS
                }
            }
        }
    }


@router.delete("/clear-global")
async def clear_global_models(
    delete_files: bool = Query(True, description="Delete physical model files from disk"),
    clear_governance: bool = Query(False, description="Also clear governance records (use with extreme caution)"),
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(require_admin_role("ADMIN"))
):
    """
    Clear all global models from the central server.
    
    **ADMIN-ONLY ENDPOINT** - Use with caution!
    
    This endpoint:
    - Deletes all global model records from ModelWeights
    - Deletes all global model records from ModelRegistry
    - Optionally deletes physical model files from disk
    - Optionally clears governance approval records
    - Logs the action to blockchain for audit trail
    
    - **delete_files**: Whether to delete physical model files (default: true)
    - **clear_governance**: Whether to clear governance records (default: false)
    
    Returns counts of deleted records and files.
    """
    try:
        result = ModelManagementService.clear_global_models(
            db=db,
            delete_files=delete_files,
            clear_governance=clear_governance
        )
        
        return {
            "success": True,
            "message": "Global models cleared successfully",
            "admin_user": current_admin.get("admin_name") or current_admin.get("admin_id") or "admin",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear global models: {str(e)}"
        )


@router.get("/models/summary")
async def get_global_models_summary(
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(require_admin_role("ADMIN"))
):
    """
    Get summary of global models.
    
    **ADMIN-ONLY ENDPOINT**
    
    Returns statistics about global models across all rounds.
    """
    summary = ModelManagementService.get_model_summary(
        hospital_id=None,
        db=db
    )
    
    return summary
