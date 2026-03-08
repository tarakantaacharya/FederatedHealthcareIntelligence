"""
Privacy governance API endpoints

Provides read-only access to:
- Current privacy policy parameters
- Epsilon usage metrics
- DP mode status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app.utils.auth import require_role
from app.federated.privacy_policy import generate_default_privacy_policy
from app.federated.policy_coordinator import FederatedPolicyCoordinator

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/policy")
async def get_current_privacy_policy(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get current privacy policy parameters.
    
    Returns:
    - epsilon_per_round: DP epsilon budget per round
    - clip_norm: Gradient clipping threshold
    - noise_multiplier: Gaussian noise scale
    - max_local_epochs: Maximum local training epochs
    - max_batch_size: Maximum batch size
    - dp_mode: Always "batch" (strict DP permanently disabled)
    - strict_dp_enabled: Always false
    """
    policy = generate_default_privacy_policy()
    
    return {
        "epsilon_per_round": policy.epsilon_per_round,
        "clip_norm": policy.clip_norm,
        "noise_multiplier": policy.noise_multiplier,
        "max_local_epochs": policy.max_local_epochs,
        "max_batch_size": policy.max_batch_size,
        "dp_mode": policy.dp_mode,
        "strict_dp_enabled": False,  # HARDCODED - permanently disabled
        "timestamp": datetime.utcnow().isoformat(),
        "policy_status": "ENFORCED_BATCH_DP_ONLY"
    }


@router.get("/metrics")
async def get_epsilon_usage_metrics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get epsilon usage metrics for privacy tracking.
    
    Returns:
    - current_round_epsilon: Epsilon spent in current round
    - cumulative_epsilon: Total epsilon spent across all rounds
    - max_allowed_epsilon: Maximum privacy budget allowed
    - epsilon_remaining: Remaining privacy budget
    - round_number: Current federated round number
    - rounds_completed: Number of completed rounds
    """
    from app.models.training_rounds import TrainingRound, RoundStatus
    
    # Get current round
    current_round = db.query(TrainingRound).filter(
        TrainingRound.status == RoundStatus.TRAINING
    ).first()
    
    if not current_round:
        # Try to get most recent round
        current_round = db.query(TrainingRound).order_by(
            TrainingRound.round_number.desc()
        ).first()
    
    round_number = current_round.round_number if current_round else 0
    
    # Get policy
    policy = generate_default_privacy_policy()
    
    # Calculate epsilon usage
    current_round_epsilon = policy.epsilon_per_round
    cumulative_epsilon = round_number * policy.epsilon_per_round
    max_allowed_epsilon = 10.0  # Standard budget
    epsilon_remaining = max(0.0, max_allowed_epsilon - cumulative_epsilon)
    
    return {
        "current_round_epsilon": current_round_epsilon,
        "cumulative_epsilon": cumulative_epsilon,
        "max_allowed_epsilon": max_allowed_epsilon,
        "epsilon_remaining": epsilon_remaining,
        "epsilon_utilization_percent": (cumulative_epsilon / max_allowed_epsilon * 100) if max_allowed_epsilon > 0 else 0.0,
        "round_number": round_number,
        "rounds_completed": round_number - 1 if round_number > 0 else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "dp_mode": "batch",
        "strict_dp_available": False
    }


@router.get("/status")
async def get_privacy_status(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL", "ADMIN"))
):
    """
    Get overall privacy governance status.
    
    Returns:
    - governance_active: Always true
    - batch_dp_enforced: Always true
    - strict_dp_blocked: Always true
    - policy_enforcement_level: "MANDATORY"
    - compliance_status: "ENFORCED"
    """
    return {
        "governance_active": True,
        "batch_dp_enforced": True,
        "strict_dp_blocked": True,
        "policy_enforcement_level": "MANDATORY",
        "compliance_status": "ENFORCED",
        "local_training_policy_enforced": True,
        "federated_training_policy_enforced": True,
        "local_overrides_allowed": False,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Privacy governance layer active - batch-level DP only"
    }
