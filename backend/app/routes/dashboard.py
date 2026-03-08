"""
Dashboard Metrics Routes - Central and Hospital endpoints
Returns KPIs and metrics for dashboard rendering
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func

from app.database import get_db
from app.utils.auth import require_role
from app.models import (
    Hospital, TrainingRound, ModelWeights, Dataset, 
    PredictionRecord, PrivacyBudget
)

router = APIRouter()


@router.get("/hospital/metrics")
async def get_hospital_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict[str, Any]:
    """
    Hospital dashboard metrics
    
    Returns:
    - Active: datasets, local models, predictions
    - Current round: status, budget, eligibility
    - Recent activity: training, predictions
    """
    hospital = current_user["db_object"]
    
    # Count active resources
    datasets_count = db.query(Dataset).filter(Dataset.hospital_id == hospital.id).count()
    local_models_count = db.query(ModelWeights).filter(
        ModelWeights.hospital_id == hospital.id,
        ModelWeights.is_global == False
    ).count()
    predictions_count = db.query(PredictionRecord).filter(
        PredictionRecord.hospital_id == hospital.id
    ).count()
    
    # Get current round info
    current_round = db.query(TrainingRound).filter(
        TrainingRound.is_active == True
    ).first()
    
    round_metrics = {
        "round_number": current_round.round_number if current_round else None,
        "is_active": current_round.is_active if current_round else False,
        "status": current_round.status if current_round else "NONE"
    }
    
    # Privacy budget status
    total_spent = db.query(func.coalesce(func.sum(PrivacyBudget.epsilon), 0.0)).filter(
        PrivacyBudget.hospital_id == hospital.id
    ).scalar()
    
    return {
        "hospital_id": hospital.hospital_id,
        "hospital_name": hospital.hospital_name,
        "resources": {
            "datasets": datasets_count,
            "local_models": local_models_count,
            "predictions": predictions_count
        },
        "current_round": round_metrics,
        "privacy": {
            "total_epsilon_spent": float(total_spent),
            "round_budget": current_round.allocated_privacy_budget if current_round else 10.0,
            "rank": hospital.ranking  # From hospital profile
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/central/metrics")
async def get_central_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
) -> Dict[str, Any]:
    """
    Central admin dashboard metrics
    
    Returns:Federated learning KPIs:
    - Hospitals: count, active, regions
    - Current round: participants, aggregations, status
    - Global models: count, accuracy, deployment status
    - Privacy: total epsilon spent, remaining budget
    """
    
    # Hospital metrics
    total_hospitals = db.query(Hospital).count()
    active_hospitals = db.query(Hospital).filter(Hospital.is_active == True).count()
    
    # Round metrics
    current_round = db.query(TrainingRound).filter(
        TrainingRound.is_active == True
    ).first()
    
    round_participants = 0
    if current_round:
        round_participants = db.query(ModelWeights).filter(
            ModelWeights.round_number == current_round.round_number
        ).distinct(ModelWeights.hospital_id).count()
    
    # Global models
    global_models_count = db.query(ModelWeights).filter(
        ModelWeights.is_global == True
    ).count()
    
    # Privacy accounting
    total_epsilon_spent = db.query(func.coalesce(func.sum(PrivacyBudget.epsilon), 0.0)).scalar()
    
    return {
        "hospitals": {
            "total": total_hospitals,
            "active": active_hospitals,
            "participation_rate": (active_hospitals / total_hospitals * 100) if total_hospitals > 0 else 0
        },
        "federated_learning": {
            "current_round": current_round.round_number if current_round else 0,
            "is_round_active": current_round.is_active if current_round else False,
            "current_round_participants": round_participants,
            "global_models_created": global_models_count
        },
        "privacy_accounting": {
            "total_epsilon_spent": float(total_epsilon_spent),
            "average_epsilon_per_hospital": (
                float(total_epsilon_spent / total_hospitals) if total_hospitals > 0 else 0
            )
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/hospital/recent-activity")
async def get_hospital_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> Dict[str, Any]:
    """
    Recent activity for hospital dashboard
    
    Returns: recent trainings, predictions, model updates
    """
    hospital = current_user["db_object"]
    
    # Recent model weights (trainings)
    recent_trainings = db.query(ModelWeights).filter(
        ModelWeights.hospital_id == hospital.id
    ).order_by(ModelWeights.created_at.desc()).limit(limit).all()
    
    # Recent predictions
    recent_predictions = db.query(PredictionRecord).filter(
        PredictionRecord.hospital_id == hospital.id
    ).order_by(PredictionRecord.created_at.desc()).limit(limit).all()
    
    return {
        "recent_trainings": [
            {
                "model_id": m.id,
                "round": m.round_number,
                "architecture": m.model_architecture if hasattr(m, 'model_architecture') else 'UNKNOWN',
                "timestamp": m.created_at.isoformat() if m.created_at else None
            }
            for m in recent_trainings
        ],
        "recent_predictions": [
            {
                "prediction_id": p.id,
                "model_id": p.model_id,
                "target_value": p.predicted_value,
                "timestamp": p.created_at.isoformat() if p.created_at else None
            }
            for p in recent_predictions
        ]
    }
