"""
Federated round routes (Phase 7)
Round lifecycle management
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.database import get_db
from app.utils.auth import require_role
from app.security.rbac import require_admin_role
from app.schemas.round_schema import (
    RoundCreateRequest,
    RoundCreateResponse,
    RoundDetailResponse,
    RoundStatisticsResponse,
    RoundAnalyticsResponse,
    RoundDeleteResponse
)
from app.services.round_service import RoundService
from app.services.canonical_field_service import CanonicalFieldService
from app.models.training_rounds import RoundStatus, TrainingRound as TrainingRoundModel
from app.schemas.aggregation_schema import TrainingRoundResponse
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType
from app.models.hospital import Hospital
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.models.privacy_budget import PrivacyBudget
from app.services.round_schema_validation_service import RoundSchemaValidationService

router = APIRouter()


@router.post("/create", response_model=RoundCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_round(
    request: RoundCreateRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Create a new federated learning round with policy configuration
    
    Initializes a new round with status 'OPEN'.
    Round number is automatically incremented.
    
    - **target_column**: Target column for this federated round (must be registered in canonical schema)
    - **is_emergency**: If true, all verified hospitals can participate (overrides policies)
    - **participation_mode**: ALL (all verified hospitals) or SELECTIVE (apply criteria)
    - **selection_criteria**: For SELECTIVE: REGION, SIZE, EXPERIENCE, MANUAL
    - **selection_value**: Value for REGION/SIZE/EXPERIENCE (e.g., "EAST", "LARGE", "NEW")
    - **manual_hospital_ids**: For MANUAL selection, list of hospital IDs to include
    """
    if not request.target_column or not request.target_column.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target column must be selected by admin."
        )
    
    # Validate target column exists in canonical schema
    is_valid, reason = CanonicalFieldService.is_valid_target(db, request.target_column)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )

    if request.model_type not in ["TFT", "ML_REGRESSION"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_type must be TFT or ML_REGRESSION"
        )

    if not request.required_canonical_features or len(request.required_canonical_features) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="required_canonical_features is mandatory for federated contract"
        )

    normalized_features: List[str] = []
    seen = set()
    for feature in request.required_canonical_features:
        feature_name = str(feature).strip()
        if not feature_name or feature_name in seen:
            continue
        field = CanonicalFieldService.get_field_by_name(db, feature_name)
        if not field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Canonical feature '{feature_name}' is not registered"
            )
        if feature_name == request.target_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="required_canonical_features must not include the target column"
            )
        normalized_features.append(feature_name)
        seen.add(feature_name)
    
    # Validate selection criteria if SELECTIVE
    if request.participation_mode == "SELECTIVE":
        valid_criteria = ["REGION", "SIZE", "EXPERIENCE", "MANUAL"]
        if request.selection_criteria not in valid_criteria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid selection_criteria. Must be one of: {', '.join(valid_criteria)}"
            )
        
        if request.selection_criteria == "MANUAL":
            if not request.manual_hospital_ids or len(request.manual_hospital_ids) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="For MANUAL selection, manual_hospital_ids must be provided and non-empty"
                )
    
    new_round = RoundService.create_new_round(
        db, 
        target_column=request.target_column,
        is_emergency=request.is_emergency,
        participation_mode=request.participation_mode,
        selection_criteria=request.selection_criteria,
        selection_value=request.selection_value,
        model_type=request.model_type,
        aggregation_strategy=request.aggregation_strategy,
        required_canonical_features=normalized_features,
        required_hyperparameters=request.required_hyperparameters,
        allocated_privacy_budget=request.allocated_privacy_budget,
        tft_hidden_size=request.tft_hidden_size,
        tft_attention_heads=request.tft_attention_heads,
        tft_dropout=request.tft_dropout,
        tft_regularization_factor=request.tft_regularization_factor
    )
    
    # If MANUAL selection, add hospitals to RoundAllowedHospital table
    if request.participation_mode == "SELECTIVE" and request.selection_criteria == "MANUAL" and request.manual_hospital_ids:
        from app.models.round_allowed_hospital import RoundAllowedHospital
        for hospital_id in request.manual_hospital_ids:
            allowed_hospital = RoundAllowedHospital(
                round_id=new_round.id,
                hospital_id=hospital_id
            )
            db.add(allowed_hospital)
        db.commit()
    
    # Notify verified hospitals of new round
    verified_hospitals = db.query(Hospital).filter(Hospital.is_verified == True).all()
    for hospital in verified_hospitals:
        NotificationService.create_notification(
            db=db,
            hospital_id=hospital.id,
            admin_id=None,
            title="New Federated Round Created",
            message=f"Round {new_round.round_number} created with target '{new_round.target_column}'.",
            notification_type=NotificationType.INFO,
            action_url="/dashboard",
            action_label="View Round"
        )
    
    return {
        'round_number': new_round.round_number,
        'status': new_round.status.value,
        'target_column': new_round.target_column,
        'training_enabled': new_round.training_enabled,
        'is_emergency': new_round.is_emergency,
        'participation_mode': "ALL" if new_round.is_emergency else ("SELECTIVE" if request.participation_mode == "SELECTIVE" else "ALL"),
        'selection_criteria': new_round.selection_criteria,
        'selection_value': new_round.selection_value,
        'started_at': new_round.started_at,
        'required_target_column': new_round.required_target_column,
        'required_canonical_features': new_round.required_canonical_features or [],
        'required_feature_count': new_round.required_feature_count,
        'required_feature_order_hash': new_round.required_feature_order_hash,
        'required_model_architecture': new_round.required_model_architecture,
        'required_hyperparameters': new_round.required_hyperparameters or {},
        'allocated_privacy_budget': new_round.allocated_privacy_budget,
        'aggregation_strategy': new_round.aggregation_strategy,
        'message': f'Round {new_round.round_number} created successfully with policy: {selection_policy_summary(new_round)}'
    }


def selection_policy_summary(round_obj) -> str:
    """Generate human-readable policy summary"""
    if round_obj.is_emergency:
        return "EMERGENCY (all verified hospitals)"
    if round_obj.selection_criteria == "MANUAL":
        return f"Manual selection"
    if round_obj.selection_criteria:
        return f"{round_obj.selection_criteria}: {round_obj.selection_value}"
    return "All verified hospitals"


@router.get("/current", response_model=TrainingRoundResponse)
async def get_current_round(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get the current active federated round
    
    Returns in-progress round, or latest pending round, or creates new round.
    """
    current_round = RoundService.get_current_round(db)
    if not current_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active federated round"
        )
    return current_round


@router.get("/active")
async def get_active_round(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL"))
):
    current_round = RoundService.get_active_round(db)
    if not current_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active round"
        )

    is_eligible = True
    eligibility_reason = None

    if current_user.get("role") == "HOSPITAL":
        hospital = current_user.get("db_object")

        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to identify hospital"
            )

        if current_round.selection_criteria == "MANUAL":
            allowed = db.query(RoundAllowedHospital).filter(
                RoundAllowedHospital.round_id == current_round.id,
                RoundAllowedHospital.hospital_id == hospital.id
            ).first()

            if not allowed:
                is_eligible = False
                eligibility_reason = "Your hospital is not selected for this manual round"

    # NEW: Include round_schema in response
    round_schema_data = None
    if current_round.round_schema:
        round_schema_data = {
            "id": current_round.round_schema.id,
            "round_id": current_round.round_schema.round_id,
            "model_architecture": current_round.round_schema.model_architecture,
            "target_column": current_round.round_schema.target_column,
            "feature_schema": current_round.round_schema.feature_schema,
            "feature_types": current_round.round_schema.feature_types,
            "sequence_required": current_round.round_schema.sequence_required,
            "lookback": current_round.round_schema.lookback,
            "horizon": current_round.round_schema.horizon,
            "model_hyperparameters": current_round.round_schema.model_hyperparameters,
            "validation_rules": current_round.round_schema.validation_rules,
            "created_at": current_round.round_schema.created_at.isoformat() if current_round.round_schema.created_at else None,
            "updated_at": current_round.round_schema.updated_at.isoformat() if current_round.round_schema.updated_at else None,
        }

    return {
        "round_id": current_round.id,
        "round_number": current_round.round_number,
        "status": current_round.status.value,
        "target_column": current_round.target_column,
        "model_type": current_round.model_type,
        "required_target_column": current_round.required_target_column,
        "required_canonical_features": current_round.required_canonical_features or [],
        "required_feature_count": current_round.required_feature_count,
        "required_feature_order_hash": current_round.required_feature_order_hash,
        "required_model_architecture": current_round.required_model_architecture,
        "required_hyperparameters": current_round.required_hyperparameters or {},
        "participation_policy": current_round.participation_policy,
        "selection_criteria": current_round.selection_criteria,
        "selection_value": current_round.selection_value,
        "is_eligible": is_eligible,
        "eligibility_reason": eligibility_reason,
        "round_schema": round_schema_data  # NEW: Schema governance contract
    }


@router.get("/{round_id}/contract")
async def get_round_contract(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL"))
):
    round_obj = db.query(TrainingRoundModel).filter(TrainingRoundModel.id == round_id).first()
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")

    return {
        "round_id": round_obj.id,
        "round_number": round_obj.round_number,
        "required_target_column": round_obj.required_target_column,
        "required_canonical_features": round_obj.required_canonical_features or [],
        "required_feature_count": round_obj.required_feature_count,
        "required_feature_order_hash": round_obj.required_feature_order_hash,
        "required_model_architecture": round_obj.required_model_architecture,
        "required_hyperparameters": round_obj.required_hyperparameters or {},
    }


@router.get("/{round_id}/contract/validate")
async def validate_round_contract(
    round_id: int,
    dataset_id: int,
    model_architecture: str,
    epochs: int | None = None,
    batch_size: int | None = None,
    learning_rate: float | None = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    hyperparameters = {
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
    }
    hyperparameters = {k: v for k, v in hyperparameters.items() if v is not None}

    result = RoundSchemaValidationService.validate_federated_contract(
        db=db,
        dataset_id=dataset_id,
        round_id=round_id,
        provided_model_architecture=model_architecture,
        provided_hyperparameters=hyperparameters
    )
    return result


@router.get("/history/central")
async def get_central_round_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """Central-side list of completed federated rounds (read-only)."""
    return RoundService.get_central_round_history_list(db)


@router.get("/history/central/{round_number}")
async def get_central_round_history_detail(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """Central-side detailed history for one round (read-only)."""
    return RoundService.get_central_round_history_detail(db, round_number)


@router.get("/history/hospital")
async def get_hospital_round_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Hospital-side list of completed rounds where this hospital participated (read-only)."""
    hospital = current_user["db_object"]
    return RoundService.get_hospital_round_history_list(db, hospital.id)


@router.get("/history/hospital/{round_number}")
async def get_hospital_round_history_detail(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """Hospital-side detailed history for one participated round (read-only)."""
    hospital = current_user["db_object"]
    return RoundService.get_hospital_round_history_detail(db, round_number, hospital.id)

@router.get("/{round_number}", response_model=RoundDetailResponse)
async def get_round_details(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN", "HOSPITAL"))
):
    """
    Get detailed information about a specific round
    
    - **round_number**: Federated round number
    
    Includes list of participating hospitals and their contributions.
    
    **Requires ADMIN or HOSPITAL role** (admins for aggregation, hospitals for round monitoring)
    """
    details = RoundService.get_round_details(round_number, db)
    return details


@router.get("/{round_id}/eligibility")
async def check_round_eligibility(
    round_id: int,
    db: Session = Depends(get_db),
    current_hospital: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check if the current hospital is eligible for the specified round
    
    Returns eligibility status and human-readable reason for the hospital's dashboard.
    
    **Response:**
    - `is_eligible` (bool): Whether the hospital can participate
    - `reason` (str): Human-readable explanation
    
    Reasons may include:
    - "PASS Eligible for this round"
    - "Your hospital is not verified"
    - "Region mismatch"
    - "Already participating in another round"
    - etc.
    """
    from app.services.participation_service import ParticipationService
    
    hospital = current_hospital.get("db_object")
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to identify hospital"
        )
    
    # Check eligibility
    is_eligible, reason = ParticipationService.can_participate(hospital.id, round_id, db)
    
    return {
        "is_eligible": is_eligible,
        "reason": reason
    }


@router.get("/{round_number}/privacy-budget")
async def get_round_privacy_budget(
    round_number: int,
    db: Session = Depends(get_db),
    current_hospital: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get privacy budget status for hospital in specific round
    
    Returns:
    - allocated_budget: Total epsilon budget allocated by admin for this round (per hospital)
    - consumed_budget: Amount already spent by this hospital in this round
    - remaining_budget: Available epsilon for training
    """
    hospital = current_hospital.get("db_object")
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital not found"
        )
    
    # Get round info
    round_obj = db.query(TrainingRoundModel).filter(
        TrainingRoundModel.round_number == round_number
    ).first()
    
    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {round_number} not found"
        )
    
    allocated_budget = round_obj.allocated_privacy_budget or 0.0
    
    # Check if hospital has consumed any budget in this round
    privacy_record = db.query(PrivacyBudget).filter(
        PrivacyBudget.hospital_id == hospital.id,
        PrivacyBudget.round_number == round_number
    ).first()
    
    consumed_budget = privacy_record.epsilon_spent if privacy_record else 0.0
    remaining_budget = allocated_budget - consumed_budget
    
    return {
        "round_number": round_number,
        "allocated_budget": allocated_budget,
        "consumed_budget": consumed_budget,
        "remaining_budget": max(0.0, remaining_budget),
        "has_budget_allocated": allocated_budget > 0
    }


@router.delete("/{round_number}", response_model=RoundDeleteResponse)
async def delete_round(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Delete a round and all related records from central server
    """
    result = RoundService.delete_round(round_number, db)
    return result


@router.get("/statistics/overview", response_model=RoundStatisticsResponse)
async def get_round_statistics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get overall federated learning statistics
    
    Provides summary of all rounds, completion status, and global models.
    """
    stats = RoundService.get_round_statistics(db)
    return stats


@router.get("/{round_id}/statistics", response_model=RoundAnalyticsResponse)
async def get_round_level_statistics(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Get round-level analytics (admin only)
    
    Returns:
    - Number of contributing hospitals
    - Average loss and accuracy
    - Standard deviation (loss, accuracy)
    - Contributing regions
    """
    return RoundService.get_round_level_statistics(db, round_id)


@router.post("/{round_number}/start", response_model=TrainingRoundResponse)
async def start_round(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Mark a round as training
    
    - **round_number**: Round to start
    
    Changes round status from 'OPEN' to 'TRAINING'.
    """
    training_round = RoundService.start_round(round_number, db)
    return training_round


@router.post("/{round_number}/disable-training", response_model=TrainingRoundResponse)
async def disable_training(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Disable local training for a round (Central Server Control)
    
    Sets round status to CLOSED.
    """
    training_round = RoundService.set_round_status(round_number, db, RoundStatus.CLOSED)
    return training_round


@router.post("/{round_number}/enable-training", response_model=TrainingRoundResponse)
async def enable_training(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Enable local training for a round (Central Server Control)
    
    Sets round status to TRAINING.
    Enforces mutual exclusion: only ONE round can be TRAINING at a time.
    """
    # Check if another round is already TRAINING
    from app.models.training_rounds import TrainingRound
    existing_training = db.query(TrainingRound).filter(
        TrainingRound.status == RoundStatus.TRAINING
    ).first()
    
    if existing_training and existing_training.round_number != round_number:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot enable training for Round {round_number}. Round {existing_training.round_number} is already in TRAINING status. Disable it first."
        )
    
    training_round = RoundService.set_round_status(round_number, db, RoundStatus.TRAINING)
    
    # Notify verified hospitals that training is enabled
    verified_hospitals = db.query(Hospital).filter(Hospital.is_verified == True).all()
    for hospital in verified_hospitals:
        NotificationService.create_notification(
            db=db,
            hospital_id=hospital.id,
            admin_id=None,
            title="Training Enabled",
            message=f"Training is now enabled for Round {round_number}.",
            notification_type=NotificationType.SUCCESS,
            action_url="/training",
            action_label="Start Training"
        )
    return training_round


@router.post("/{round_number}/restart", response_model=TrainingRoundResponse)
async def restart_round(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Restart a closed training round
    
    Reset a CLOSED round back to OPEN status for re-execution.
    Only works if the round is in CLOSED status.
    """
    from app.models.training_rounds import TrainingRound
    
    # Get the round
    training_round = db.query(TrainingRound).filter(
        TrainingRound.round_number == round_number
    ).first()
    
    if not training_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {round_number} not found"
        )
    
    # Only allow restart if round is CLOSED
    if training_round.status != RoundStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only restart CLOSED rounds. Round {round_number} is currently {training_round.status}."
        )
    
    # Reset to OPEN
    training_round = RoundService.set_round_status(round_number, db, RoundStatus.OPEN)
    return training_round


@router.post("/clear")
async def clear_all_rounds(
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Clear all federated rounds and related data (Admin-only)

    This will:
    - Delete federated rounds
    - Delete federated model weights
    - Delete governance records
    - Preserve LOCAL hospital models
    """
    from app.models.training_rounds import TrainingRound
    from app.models.model_weights import ModelWeights
    from app.models.model_governance import ModelGovernance

    try:
        # Count before deletion
        round_count = db.query(TrainingRound).count()
        federated_weight_count = db.query(ModelWeights).filter(
            ModelWeights.training_type == "FEDERATED"
        ).count()
        governance_count = db.query(ModelGovernance).count()

        # Delete governance records
        db.query(ModelGovernance).delete()

        # Delete ONLY federated model weights
        db.query(ModelWeights).filter(
            ModelWeights.training_type == "FEDERATED"
        ).delete()

        # Delete rounds
        db.query(TrainingRound).delete()

        db.commit()

        return {
            "status": "success",
            "message": "Federated rounds cleared (LOCAL models preserved)",
            "deleted": {
                "rounds": round_count,
                "federated_weights": federated_weight_count,
                "governance_records": governance_count
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear rounds: {str(e)}"
        )


@router.get("/allowed-targets")
async def get_allowed_targets(
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Get list of allowed target columns approved by central governance
    
    Admin must select from this list when creating rounds.
    """
    allowed_targets = CanonicalFieldService.get_all_valid_targets(db)
    return {
        "allowed_targets": allowed_targets
    }

# Phase A-Pro: Round Participation Policies
# ────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional
from app.services.round_policy_service import RoundPolicyService


class AllowedHospitalRequest(BaseModel):
    hospital_id: int


class RegionPolicyRequest(BaseModel):
    allowed_regions: List[str]


class CapacityPolicyRequest(BaseModel):
    bed_capacity_threshold: int


@router.post("/{round_id}/allowed-hospitals")
def add_allowed_hospital(
    round_id: int,
    request: AllowedHospitalRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("ADMIN"))
):
    """Add hospital to SELECTED round allowlist."""
    
    success = RoundPolicyService.add_allowed_hospital(round_id, request.hospital_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital already in allowlist or does not exist"
        )
    
    return {"status": "added", "round_id": round_id, "hospital_id": request.hospital_id}


@router.delete("/{round_id}/allowed-hospitals/{hospital_id}")
def remove_allowed_hospital(
    round_id: int,
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("ADMIN"))
):
    """Remove hospital from SELECTED round allowlist."""
    
    success = RoundPolicyService.remove_allowed_hospital(round_id, hospital_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not in allowlist"
        )
    
    return {"status": "removed", "round_id": round_id, "hospital_id": hospital_id}


@router.get("/{round_id}/allowed-hospitals")
def get_allowed_hospitals(
    round_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("ADMIN"))
):
    """Get hospitals allowed for this round (SELECTED policy only)."""
    
    hospitals = RoundPolicyService.get_allowed_hospitals(round_id, db)
    return {"hospitals": hospitals}


@router.post("/{round_id}/policy/region-based")
def set_region_policy(
    round_id: int,
    request: RegionPolicyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("ADMIN"))
):
    """Set REGION_BASED participation policy for round."""
    
    success = RoundPolicyService.set_region_policy(round_id, request.allowed_regions, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    return {"status": "updated", "policy": "REGION_BASED", "allowed_regions": request.allowed_regions}


@router.post("/{round_id}/policy/capacity-based")
def set_capacity_policy(
    round_id: int,
    request: CapacityPolicyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_role("ADMIN"))
):
    """Set CAPACITY_BASED participation policy for round."""
    
    success = RoundPolicyService.set_capacity_policy(round_id, request.bed_capacity_threshold, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round not found"
        )
    
    return {"status": "updated", "policy": "CAPACITY_BASED", "threshold": request.bed_capacity_threshold}
