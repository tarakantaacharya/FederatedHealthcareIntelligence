"""
Dropout handling routes (Phase 21)
Hospital participation tracking and recovery
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.services.dropout_service import DropoutService

router = APIRouter()


@router.get("/participation/{round_number}")
async def get_round_participation(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get participation tracking for a round
    
    - **round_number**: Round number
    
    Returns which hospitals participated and which dropped out.
    """
    participation = DropoutService.track_hospital_participation(round_number, db)
    return participation


@router.get("/viability/{round_number}")
async def check_round_viability(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check if round has enough participants
    
    - **round_number**: Round number
    
    Returns viability assessment and recommendations.
    """
    viability = DropoutService.check_round_viability(round_number, db)
    return viability


@router.get("/history/{hospital_id}")
async def get_participation_history(
    hospital_id: int,
    num_rounds: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get hospital's participation history
    
    - **hospital_id**: Hospital ID
    - **num_rounds**: Number of recent rounds to check
    
    Returns participation rate and consecutive dropout detection.
    """
    history = DropoutService.get_hospital_participation_history(
        hospital_id, num_rounds, db
    )
    return history


@router.post("/recover/{round_number}")
async def attempt_dropout_recovery(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Attempt to recover dropped hospitals
    
    - **round_number**: Round number
    
    Checks for late submissions and attempts recovery.
    """
    # Get dropped hospitals
    participation = DropoutService.track_hospital_participation(round_number, db)
    
    if participation.get('error'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=participation['error']
        )
    
    if participation['dropped'] == 0:
        return {
            'message': 'No dropped hospitals in this round',
            'round_number': round_number
        }
    
    # Attempt recovery
    recovery = DropoutService.attempt_recovery(
        round_number,
        participation['dropped_hospital_ids'],
        db
    )
    
    return recovery


@router.get("/penalty/{hospital_id}")
async def get_dropout_penalty(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get dropout penalty for hospital
    
    - **hospital_id**: Hospital ID
    
    Returns penalty multiplier based on participation history.
    Lower values indicate less reliable participation.
    """
    penalty = DropoutService.calculate_dropout_penalty(hospital_id, db)
    
    return {
        'hospital_id': hospital_id,
        'penalty_multiplier': penalty,
        'impact': f"{(1 - penalty) * 100:.0f}% weight reduction" if penalty < 1.0 else "No penalty"
    }
