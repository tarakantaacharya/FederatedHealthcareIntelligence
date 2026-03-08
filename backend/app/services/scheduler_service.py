"""
Distributed scheduler service (Phase 22)
Manages federated learning round scheduling
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.hospital import Hospital
from enum import Enum


class SchedulePolicy(str, Enum):
    """Scheduling policies"""
    FIXED_INTERVAL = 'fixed_interval'  # Every N hours
    AVAILABILITY_BASED = 'availability_based'  # When enough hospitals online
    MANUAL = 'manual'  # Manual trigger only


class HospitalAvailability(str, Enum):
    """Hospital availability status"""
    ONLINE = 'online'
    OFFLINE = 'offline'
    BUSY = 'busy'
    MAINTENANCE = 'maintenance'


class SchedulerService:
    """Service for scheduling federated rounds"""
    
    DEFAULT_ROUND_INTERVAL_HOURS = 24
    MIN_ONLINE_HOSPITALS = 3
    ROUND_DEADLINE_HOURS = 6  # Hospitals have 6 hours to submit
    
    @staticmethod
    def schedule_next_round(
        policy: SchedulePolicy,
        interval_hours: Optional[int] = None,
        db: Session = None
    ) -> Dict:
        """
        Schedule the next federated round
        
        Args:
            policy: Scheduling policy
            interval_hours: Hours until next round (for FIXED_INTERVAL)
            db: Database session
        
        Returns:
            Schedule information
        """
        # Get latest round
        latest_round = db.query(TrainingRound).order_by(
            TrainingRound.round_number.desc()
        ).first()
        
        next_round_number = (latest_round.round_number + 1) if latest_round else 1
        
        if policy == SchedulePolicy.FIXED_INTERVAL:
            interval = interval_hours or SchedulerService.DEFAULT_ROUND_INTERVAL_HOURS
            
            if latest_round and latest_round.completed_at:
                scheduled_start = latest_round.completed_at + timedelta(hours=interval)
            else:
                scheduled_start = datetime.now() + timedelta(hours=interval)
            
            scheduled_deadline = scheduled_start + timedelta(
                hours=SchedulerService.ROUND_DEADLINE_HOURS
            )
            
        elif policy == SchedulePolicy.AVAILABILITY_BASED:
            # Check hospital availability
            availability = SchedulerService.check_hospital_availability(db)
            
            if availability['online_count'] >= SchedulerService.MIN_ONLINE_HOSPITALS:
                scheduled_start = datetime.now()
            else:
                # Wait 1 hour and check again
                scheduled_start = datetime.now() + timedelta(hours=1)
            
            scheduled_deadline = scheduled_start + timedelta(
                hours=SchedulerService.ROUND_DEADLINE_HOURS
            )
            
        else:  # MANUAL
            scheduled_start = None
            scheduled_deadline = None
        
        return {
            'next_round_number': next_round_number,
            'policy': policy,
            'scheduled_start': scheduled_start.isoformat() if scheduled_start else None,
            'scheduled_deadline': scheduled_deadline.isoformat() if scheduled_deadline else None,
            'interval_hours': interval_hours,
            'status': 'scheduled' if scheduled_start else 'awaiting_manual_trigger'
        }
    
    @staticmethod
    def check_hospital_availability(db: Session) -> Dict:
        """
        Check which hospitals are currently available
        
        Args:
            db: Database session
        
        Returns:
            Availability summary
        """
        all_hospitals = db.query(Hospital).all()
        
        # In production, this would check actual heartbeats/health endpoints
        # For now, we'll use last activity timestamp
        
        online_threshold = datetime.now() - timedelta(minutes=30)
        
        availability = []
        online_count = 0
        
        for hospital in all_hospitals:
            # Check if hospital has recent activity
            # This would typically check last_heartbeat or last_active timestamp
            # For now, assume all are online (in production, add heartbeat mechanism)
            
            status = HospitalAvailability.ONLINE  # Simplified
            
            if status == HospitalAvailability.ONLINE:
                online_count += 1
            
            availability.append({
                'hospital_id': hospital.id,
                'hospital_name': hospital.hospital_name,
                'status': status
            })
        
        return {
            'total_hospitals': len(all_hospitals),
            'online_count': online_count,
            'offline_count': len(all_hospitals) - online_count,
            'availability': availability,
            'ready_for_round': online_count >= SchedulerService.MIN_ONLINE_HOSPITALS
        }
    
    @staticmethod
    def create_scheduled_round(
        schedule_info: Dict,
        db: Session
    ) -> TrainingRound:
        """
        Create a scheduled round in the database
        
        Args:
            schedule_info: Schedule information from schedule_next_round
            db: Database session
        
        Returns:
            Created TrainingRound object
        """
        round_obj = TrainingRound(
            round_number=schedule_info['next_round_number'],
            status=RoundStatus.PENDING
        )
        
        db.add(round_obj)
        db.commit()
        db.refresh(round_obj)
        
        return round_obj
    
    @staticmethod
    def get_round_schedule(
        num_rounds: int,
        db: Session
    ) -> List[Dict]:
        """
        Get schedule for upcoming rounds
        
        Args:
            num_rounds: Number of upcoming rounds to schedule
            db: Database session
        
        Returns:
            List of scheduled rounds
        """
        schedule = []
        
        # Get latest round
        latest_round = db.query(TrainingRound).order_by(
            TrainingRound.round_number.desc()
        ).first()
        
        start_round = (latest_round.round_number + 1) if latest_round else 1
        
        # Calculate schedule based on fixed interval
        current_time = datetime.now()
        
        for i in range(num_rounds):
            round_number = start_round + i
            scheduled_start = current_time + timedelta(
                hours=i * SchedulerService.DEFAULT_ROUND_INTERVAL_HOURS
            )
            scheduled_deadline = scheduled_start + timedelta(
                hours=SchedulerService.ROUND_DEADLINE_HOURS
            )
            
            schedule.append({
                'round_number': round_number,
                'scheduled_start': scheduled_start.isoformat(),
                'scheduled_deadline': scheduled_deadline.isoformat(),
                'hours_until_start': (scheduled_start - current_time).total_seconds() / 3600
            })
        
        return schedule
    
    @staticmethod
    def check_round_deadline(
        round_number: int,
        db: Session
    ) -> Dict:
        """
        Check if round deadline has passed
        
        Args:
            round_number: Round number
            db: Database session
        
        Returns:
            Deadline status
        """
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not round_obj:
            return {'error': 'Round not found'}
        
        # Calculate deadline (started_at + deadline hours)
        if round_obj.started_at:
            deadline = round_obj.started_at + timedelta(
                hours=SchedulerService.ROUND_DEADLINE_HOURS
            )
            
            now = datetime.now()
            is_past_deadline = now > deadline
            time_remaining = (deadline - now).total_seconds() / 3600 if not is_past_deadline else 0
            
            return {
                'round_number': round_number,
                'started_at': round_obj.started_at.isoformat(),
                'deadline': deadline.isoformat(),
                'is_past_deadline': is_past_deadline,
                'hours_remaining': time_remaining,
                'status': 'OVERDUE' if is_past_deadline else 'ACTIVE'
            }
        else:
            return {
                'round_number': round_number,
                'status': 'NOT_STARTED',
                'message': 'Round has not started yet'
            }
