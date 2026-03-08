"""
Local training routes (Phase 3)
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.training_schema import (
    TrainingRequest,
    TrainingResponse,
    ModelListResponse,
    ModelDetailResponse
)
from app.services.training_orchestrator import TrainingOrchestrator

router = APIRouter()


@router.post("/start", status_code=status.HTTP_201_CREATED, response_model=TrainingResponse)
async def start_local_training(
    training_request: TrainingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    import sys
    import os
    print("="*70)
    print("=== ROUTE ENTERED ===")
    print(f"PID: {os.getpid()}")
    print(f"Python: {sys.executable}")
    print(f"[ROUTE] Training Type: {training_request.training_type}")
    print(f"[ROUTE] Model Architecture: {training_request.model_architecture}")
    print("="*70)
    sys.stdout.flush()
    
    """
    Start model training on hospital dataset
    
    Phase B: Supports LOCAL and FEDERATED training modes
    
    - **dataset_id**: Dataset to train on (must be owned by hospital)
    - **target_column**: Target column (optional for FEDERATED, auto-detected from round)
    - **epochs**: Training epochs (unused for ML_REGRESSION)
    - **training_type**: LOCAL (independent) or FEDERATED (collaborative)
    - **model_architecture**: ML_REGRESSION (sklearn) or TFT (transformer)
    
    LOCAL mode:
    - No round required
    - No eligibility check
    - No weight/mask upload
    - Saves model locally only
    
    FEDERATED mode:
    - Requires active round
    - Eligibility check enforced
    - Target column from current round
    - Enables weight/mask upload for aggregation
    """
    from app.services.round_service import RoundService
    from app.federated.policy_coordinator import FederatedPolicyCoordinator
    from app.federated.privacy_policy import generate_default_privacy_policy
    from app.models import TrainingRound
    
    print("[ROUTE] REQUEST VALIDATED")
    print(f"[ROUTE] training_request.dataset_id = {training_request.dataset_id}")
    print(f"[ROUTE] training_request.epochs = {training_request.epochs}")
    sys.stdout.flush()
    
    print(f"[ROUTE] DEPENDENCY PASSED: current_user role={current_user.get('role')}")
    sys.stdout.flush()
    
    hospital = current_user["db_object"]
    print(f"[ROUTE] hospital = {hospital.hospital_id}")
    sys.stdout.flush()

    # Phase B: Conditional logic for LOCAL vs FEDERATED
    target_column = training_request.target_column
    current_round = None
    privacy_policy = None  # For FEDERATED mode, load central policy
    
    if training_request.training_type == "FEDERATED":
        # FEDERATED mode: Enforce round and eligibility
        from app.services.participation_service import ParticipationService
        
        print("[ROUTE] FEDERATED MODE: Checking round and eligibility")
        sys.stdout.flush()
        
        current_round = RoundService.require_training_round(db)
        target_column = current_round.target_column  # Override with round's target
        print(f"[ROUTE] ROUND CHECK PASSED: target_column={target_column}")
        sys.stdout.flush()
        
        # Check eligibility for this round
        is_eligible, reason = ParticipationService.can_participate(
            hospital.id, current_round.id, db
        )
        
        if not is_eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "ineligible", "reason": reason}
            )
        
        print("[ROUTE] ELIGIBILITY CHECK PASSED")
        sys.stdout.flush()
        
        # ===== PHASE 42: LOAD CENTRAL PRIVACY POLICY =====
        print("[ROUTE] FEDERATED MODE: Loading central privacy policy")
        coordinator = FederatedPolicyCoordinator()
        
        # Get policy for current round (or default if not found)
        privacy_policy = coordinator.generate_round_policy(
            round_number=current_round.round_number,
            num_participating_hospitals=db.query(TrainingRound).filter(
                TrainingRound.id == current_round.id
            ).count()
        )
        print(f"[ROUTE] Policy loaded: epsilon={privacy_policy.epsilon_per_round}, "
              f"clip_norm={privacy_policy.clip_norm}, "
              f"noise_multiplier={privacy_policy.noise_multiplier}")
        sys.stdout.flush()
    else:
        # LOCAL mode: No round or eligibility check required, but POLICY IS MANDATORY
        print("[ROUTE] LOCAL MODE: Skipping round and eligibility checks")
        print("[ROUTE] LOCAL MODE: POLICY ENFORCEMENT ACTIVE (mandatory for all training)")
        sys.stdout.flush()
        
        if not target_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target_column is required for LOCAL training mode"
            )
        
        # ===== PHASE 42: LOAD PRIVACY POLICY FOR LOCAL TRAINING =====
        print("[ROUTE] LOCAL MODE: Loading privacy policy (enforced for all training modes)")
        coordinator = FederatedPolicyCoordinator()
        privacy_policy = coordinator.generate_round_policy(
            round_number=1,  # Default round for local training
            num_participating_hospitals=1
        )
        print(f"[ROUTE] Policy loaded: epsilon={privacy_policy.epsilon_per_round}, "
              f"clip_norm={privacy_policy.clip_norm}, "
              f"noise_multiplier={privacy_policy.noise_multiplier}")
        sys.stdout.flush()
    
    print("[ROUTE] CALLING TrainingOrchestrator.start_local_training")
    sys.stdout.flush()
    result = TrainingOrchestrator.start_local_training(
        db=db,
        hospital=hospital,
        dataset_id=training_request.dataset_id,
        target_column=target_column,
        epochs=training_request.epochs,
        training_request=training_request,
        privacy_policy=privacy_policy,
        batch_size=getattr(training_request, 'batch_size', 32)
    )
    
    print("[ROUTE] TrainingOrchestrator RETURNED")
    sys.stdout.flush()
    return result


@router.get("/models", response_model=List[ModelListResponse])
async def list_trained_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    List all trained models for current hospital
    
    - **skip**: Pagination offset
    - **limit**: Max results
    
    Returns list of local models trained by this hospital.
    """
    hospital = current_user["db_object"]
    models = TrainingOrchestrator.list_trained_models(
        db=db,
        hospital_id=hospital.id,
        skip=skip,
        limit=limit
    )
    
    return models


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model_details(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get detailed information about a specific model
    
    - **model_id**: Model database ID
    
    Requires ownership verification.
    """
    hospital = current_user["db_object"]
    model = TrainingOrchestrator.get_model_details(db, model_id, hospital.id)
    return model


@router.get("/status")
async def get_training_status(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get structured training status records (Phase B).
    
    Hospitals see only their records.
    Admins see all records.
    """
    from app.services.training_service import TrainingService
    
    hospital_id = None
    if current_user.get("role") == "HOSPITAL":
        hospital_id = current_user["db_object"].id
    
    return TrainingService.get_training_status(db, hospital_id=hospital_id)


@router.get("/status/{model_id}")
async def get_model_training_status(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get complete training status for specific model
    
    Returns all metrics, metadata, candidate models, and feature importance
    
    Requires: Model ownership or admin role
    """
    from app.models.model_weights import ModelWeights
    
    hospital = current_user["db_object"]
    
    # Ownership verification
    model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if current_user.get("role") == "HOSPITAL" and model.hospital_id != hospital.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build complete status response
    status_data = {
        "model_id": model.id,
        "dataset_id": model.dataset_id,
        "model_type": model.model_type,
        "training_type": str(model.training_type),
        "model_architecture": model.model_architecture,
        "model_path": model.model_path,
        "status": "TRAINING_COMPLETE",
        
        # All 10 metrics (from database columns)
        "metrics": {
            "mae": model.local_mae or 0.0,
            "mse": model.local_mse or 0.0,
            "rmse": model.local_rmse or 0.0,
            "r2": model.local_r2 or 0.0,
            "adjusted_r2": model.local_adjusted_r2 or 0.0,
            "mape": model.local_mape or 0.0,
            "smape": model.local_smape or 0.0,
            "wape": model.local_wape or 0.0,
            "mase": model.local_mase or 0.0,
            "rmsle": model.local_rmsle or 0.0,
        },
        
        # Metadata from training_schema
        "best_model": model.training_schema.get("best_model") if model.training_schema else None,
        "candidate_models": model.training_schema.get("candidate_models") if model.training_schema else [],
        "all_model_metrics": model.training_schema.get("all_model_metrics") if model.training_schema else {},
        "feature_importance": model.training_schema.get("feature_importance") if model.training_schema else {},
        
        "num_features": model.training_schema.get("total_feature_count") if model.training_schema else 0,
        "num_samples": model.training_schema.get("num_samples") if model.training_schema else 0,
        "training_timestamp": model.created_at.isoformat() if model.created_at else None,
    }
    
    return status_data

@router.post("/automl/start", status_code=status.HTTP_201_CREATED)
async def start_automl_training(
    training_request: TrainingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Start AutoML pipeline (automatic hyperparameter tuning with all 5 models)
    
    AutoML pipeline:
    1. Preprocesses data (handles missing values, encoding, scaling)
    2. Trains all 5 candidate models with hyperparameter tuning
    3. Computes 10 evaluation metrics for each model
    4. Automatically selects best model
    5. Returns leaderboard with all results
    
    Requires:
    - dataset_id: Dataset to train on
    - target_column: Target column name (required for LOCAL training)
    - training_type: LOCAL or FEDERATED
    """
    from app.services.automl_service import AutoMLService
    
    hospital = current_user["db_object"]
    
    result = AutoMLService.run_automl_training(
        db=db,
        hospital=hospital,
        dataset_id=training_request.dataset_id,
        target_column=training_request.target_column,
        training_type=getattr(training_request, 'training_type', 'LOCAL')
    )
    
    return result


@router.get("/automl/leaderboard/{dataset_id}")
async def get_automl_leaderboard(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get AutoML leaderboard for a dataset
    
    Returns:
    - All models trained with their metrics
    - Best model information
    - Leaderboard sorted by performance
    """
    from app.services.automl_service import AutoMLService
    
    hospital = current_user["db_object"]
    
    leaderboard = AutoMLService.get_leaderboard(
        db=db,
        hospital_id=hospital.id,
        dataset_id=dataset_id
    )
    
    return leaderboard