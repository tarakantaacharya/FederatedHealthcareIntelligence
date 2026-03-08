"""
Scheduler routes (Phase 22)
Federated round scheduling and hospital availability
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.security.rbac import require_admin_role
from app.services.scheduler_service import SchedulerService, SchedulePolicy

router = APIRouter()


@router.post("/schedule-next-round")
async def schedule_next_round(
    policy: SchedulePolicy = SchedulePolicy.FIXED_INTERVAL,
    interval_hours: int = 24,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin_role("ADMIN"))
):
    """
    Schedule the next federated round
    
    - **policy**: Scheduling policy (fixed_interval, availability_based, manual)
    - **interval_hours**: Hours until next round (for fixed_interval policy)
    
    **Phase 30: CENTRAL or ADMIN role required**
    
    Returns schedule information for next round.
    """
    schedule_info = SchedulerService.schedule_next_round(
        policy=policy,
        interval_hours=interval_hours,
        db=db
    )
    
    # Create round in database
    if schedule_info['scheduled_start']:
        round_obj = SchedulerService.create_scheduled_round(schedule_info, db)
        schedule_info['round_id'] = round_obj.id
    
    return schedule_info


@router.get("/hospital-availability")
async def check_hospital_availability(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check which hospitals are currently available
    
    Returns availability status for all hospitals.
    """
    availability = SchedulerService.check_hospital_availability(db)
    return availability


@router.get("/upcoming-schedule")
async def get_upcoming_schedule(
    num_rounds: int = 5,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Get schedule for upcoming rounds
    
    - **num_rounds**: Number of rounds to schedule (default: 5)
    
    Returns projected schedule based on current policy.
    """
    schedule = SchedulerService.get_round_schedule(num_rounds, db)
    return {
        'num_rounds': num_rounds,
        'schedule': schedule
    }


@router.get("/deadline-status/{round_number}")
async def check_round_deadline(
    round_number: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Check if round deadline has passed
    
    - **round_number**: Round number
    
    Returns deadline status and time remaining.
    """
    status = SchedulerService.check_round_deadline(round_number, db)
    return status
