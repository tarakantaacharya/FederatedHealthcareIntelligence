"""
Benchmarking routes for multi-hospital performance comparison (Phase 28)
Privacy-preserving aggregated metrics API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.services.benchmark_service import BenchmarkService
from app.security.rbac import require_admin_role, require_role

router = APIRouter()


@router.get("/round/{round_number}")
async def benchmark_by_round(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
) -> List[Dict]:
    """
    Get performance benchmarks for a specific training round
    
    - **round_number**: Training round number
    
    Returns aggregated performance metrics for all hospitals in the round.
    """
    if round_number < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Round number must be non-negative"
        )
    
    benchmarks = BenchmarkService.get_round_benchmarks(db, round_number)
    
    if not benchmarks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No benchmarks found for round {round_number}"
        )
    
    return benchmarks


@router.get("/leaderboard")
async def global_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
) -> List[Dict]:
    """
    Get global leaderboard of top-performing hospitals
    
    - **limit**: Maximum number of results (default: 10, max: 50)
    
    Returns ranked list of hospitals by average accuracy across all rounds.
    """
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 50"
        )
    
    leaderboard = BenchmarkService.get_leaderboard(db, limit)
    
    return leaderboard


@router.get("/hospital/progress")
async def hospital_progress(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> List[Dict]:
    """
    Get performance progression for the current hospital across rounds
    
    Returns historical performance metrics per round for authenticated hospital.
    """
    hospital = current_user["db_object"]
    progress = BenchmarkService.get_hospital_progress(db, hospital.id)
    
    return progress


@router.get("/round/{round_number}/statistics")
async def round_statistics(
    round_number: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
) -> Dict:
    """
    Get aggregated statistics for a specific round
    
    - **round_number**: Training round number
    
    Returns min, max, avg accuracy/loss and participant count.
    """
    if round_number < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Round number must be non-negative"
        )
    
    stats = BenchmarkService.get_round_statistics(db, round_number)
    
    if stats["num_participants"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for round {round_number}"
        )
    
    return stats
