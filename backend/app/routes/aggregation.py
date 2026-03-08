"""
Central aggregation routes (Phase 5)
FedAvg implementation for global model creation
Unified authentication: requires ADMIN role
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.aggregation_schema import (
    AggregationRequest,
    AggregationResponse,
    GlobalModelResponse,
    TrainingRoundResponse
)
from app.services.aggregation_orchestrator import AggregationOrchestrator
from app.services.round_service import RoundService
from app.models.training_rounds import RoundStatus
from app.models.training_rounds import TrainingRound

router = APIRouter()


@router.post("/fedavg", response_model=AggregationResponse)
async def federated_average(
    aggregation_request: AggregationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):

    return AggregationOrchestrator.perform_masked_fedavg(
        round_number=aggregation_request.round_number,
        db=db
    )


@router.post("/compute", response_model=AggregationResponse)
async def compute_aggregation(
    aggregation_request: AggregationRequest = None,
    round_number: int = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Compute FedAvg aggregation (alias for /fedavg with query param support)
    
    Supports both:
    - POST /api/aggregation/compute with JSON body: {"round_number": N}
    - POST /api/aggregation/compute?round_number=N with empty body
    """
    # Get round_number from JSON body or query parameter
    if aggregation_request and hasattr(aggregation_request, 'round_number'):
        rn = aggregation_request.round_number
    elif round_number:
        rn = round_number
    else:
        from fastapi import Query
        raise ValueError("round_number must be provided in body or query")
    
    return AggregationOrchestrator.perform_masked_fedavg(
        round_number=rn,
        db=db
    )


@router.get("/global/{round_number}", response_model=GlobalModelResponse)
async def get_global_model(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Get global model for specific federated round
    
    - **round_number**: Federated learning round number
    
    Returns global model metadata and path.
    
    **Requires ADMIN role**
    """
    global_model = AggregationOrchestrator.get_global_model(round_number, db)
    return global_model


@router.get("/global-model", response_model=GlobalModelResponse)
async def get_latest_global_model(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """
    Get the latest global model

    Returns the most recent global model metadata.
    
    **Requires ADMIN role**
    """
    global_model = AggregationOrchestrator.get_latest_global_model(db)
    return global_model


@router.get("/rounds", response_model=List[TrainingRoundResponse])
async def list_training_rounds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    from app.models.hospital import Hospital
    from app.models.round_allowed_hospital import RoundAllowedHospital

    rounds = db.query(TrainingRound).offset(skip).limit(limit).all()
    result = []

    for round_obj in rounds:

        hospital_ids = []
        hospital_names = []

        # Base query: ONLY eligible hospitals
        base_query = db.query(Hospital).filter(
            Hospital.is_active == True,
            Hospital.is_verified == True,
            Hospital.is_allowed_federated == True
        )

        # 🔹 MANUAL selection
        if round_obj.selection_criteria == "MANUAL":
            allowed = db.query(RoundAllowedHospital).join(
                Hospital, Hospital.id == RoundAllowedHospital.hospital_id
            ).filter(
                RoundAllowedHospital.round_id == round_obj.id,
                Hospital.is_active == True,
                Hospital.is_verified == True,
                Hospital.is_allowed_federated == True
            ).all()

            hospital_ids = [a.hospital_id for a in allowed]

        # 🔹 REGION selection
        elif round_obj.selection_criteria == "REGION" and round_obj.selection_value:
            hospitals = base_query.filter(
                Hospital.location == round_obj.selection_value
            ).all()
            hospital_ids = [h.id for h in hospitals]

        # 🔹 SIZE selection
        elif round_obj.selection_criteria == "SIZE" and round_obj.selection_value:
            hospitals = base_query.filter(
                Hospital.size == round_obj.selection_value
            ).all()
            hospital_ids = [h.id for h in hospitals]

        # 🔹 EXPERIENCE selection
        elif round_obj.selection_criteria == "EXPERIENCE" and round_obj.selection_value:
            hospitals = base_query.filter(
                Hospital.experience_level == round_obj.selection_value
            ).all()
            hospital_ids = [h.id for h in hospitals]

        # 🔹 ALL (default)
        else:
            hospitals = base_query.all()
            hospital_ids = [h.id for h in hospitals]

        # Fetch hospital names safely
        if hospital_ids:
            hospitals = db.query(Hospital).filter(
                Hospital.id.in_(hospital_ids)
            ).all()
            hospital_names = [h.hospital_name for h in hospitals]

        round_response = {
            "id": round_obj.id,
            "round_number": round_obj.round_number,
            "target_column": round_obj.target_column,
            "model_type": round_obj.model_type,
            "training_enabled": round_obj.training_enabled,
            "num_participating_hospitals": round_obj.num_participating_hospitals or 0,
            "average_loss": round_obj.average_loss,
            "average_accuracy": round_obj.average_accuracy,
            "average_mape": round_obj.average_mape,
            "average_rmse": round_obj.average_rmse,
            "average_r2": round_obj.average_r2,
            "started_at": round_obj.started_at,
            "completed_at": round_obj.completed_at,
            "status": round_obj.status.value if hasattr(round_obj.status, "value") else round_obj.status,
            "participation_policy": round_obj.participation_policy,
            "selection_criteria": round_obj.selection_criteria,
            "selection_value": round_obj.selection_value,
            "is_emergency": round_obj.is_emergency,
            "hospital_ids": hospital_ids,
            "hospital_names": hospital_names,
            "required_target_column": round_obj.required_target_column,
            "required_canonical_features": round_obj.required_canonical_features or [],
            "required_feature_count": round_obj.required_feature_count,
            "required_feature_order_hash": round_obj.required_feature_order_hash,
            "required_model_architecture": round_obj.required_model_architecture,
            "required_hyperparameters": round_obj.required_hyperparameters or {}
        }

        result.append(TrainingRoundResponse(**round_response))

    return result
