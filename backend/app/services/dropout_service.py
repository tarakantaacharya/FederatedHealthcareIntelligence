"""
Dropout detection and handling service (Phase 21)
Manages hospital participation tracking and dropout recovery
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from app.models.hospital import Hospital
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound
from enum import Enum


class HospitalStatus(str, Enum):
    """Hospital participation status"""
    ACTIVE = 'active'
    DROPPED = 'dropped'
    LATE = 'late'
    RECOVERED = 'recovered'


class DropoutService:
    """Service for handling hospital dropouts"""
    
    PARTICIPATION_TIMEOUT_MINUTES = 30  # Hospital must participate within 30 min
    MAX_DROPOUT_RATE = 0.3  # Allow max 30% dropout per round
    
    @staticmethod
    def track_hospital_participation(
        round_number: int,
        db: Session
    ) -> Dict:
        """
        Track which hospitals participated in a round
        
        Args:
            round_number: Round number to check
            db: Database session
        
        Returns:
            Participation tracking dictionary
        """
        # Get round
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not round_obj:
            return {'error': 'Round not found'}
        
        # Get all registered hospitals
        all_hospitals = db.query(Hospital).all()
        all_hospital_ids = {h.id for h in all_hospitals}
        
        # Get hospitals that submitted weights
        participated_weights = db.query(ModelWeights).filter(
            ModelWeights.round_number == round_number,
            ModelWeights.is_global == False
        ).all()
        
        participated_hospital_ids = {w.hospital_id for w in participated_weights}
        
        # Calculate dropouts
        dropped_hospital_ids = all_hospital_ids - participated_hospital_ids
        
        # Get dropout details
        dropped_hospitals = db.query(Hospital).filter(
            Hospital.id.in_(dropped_hospital_ids)
        ).all() if dropped_hospital_ids else []
        
        # Calculate rates
        total_hospitals = len(all_hospital_ids)
        participated_count = len(participated_hospital_ids)
        dropped_count = len(dropped_hospital_ids)
        dropout_rate = dropped_count / total_hospitals if total_hospitals > 0 else 0
        
        return {
            'round_number': round_number,
            'total_hospitals': total_hospitals,
            'participated': participated_count,
            'dropped': dropped_count,
            'dropout_rate': dropout_rate,
            'participated_hospital_ids': list(participated_hospital_ids),
            'dropped_hospital_ids': list(dropped_hospital_ids),
            'dropped_hospitals': [
                {
                    'id': h.id,
                    'hospital_id': h.hospital_id,
                    'hospital_name': h.hospital_name
                }
                for h in dropped_hospitals
            ]
        }
    
    @staticmethod
    def create_dropout_mask(
        expected_hospitals: List[int],
        actual_hospitals: List[int]
    ) -> Dict:
        """
        Create dropout mask for aggregation
        
        Args:
            expected_hospitals: List of expected hospital IDs
            actual_hospitals: List of actual participating hospital IDs
        
        Returns:
            Dropout mask dictionary
        """
        expected_set = set(expected_hospitals)
        actual_set = set(actual_hospitals)
        
        dropped = expected_set - actual_set
        recovered = actual_set - expected_set  # Hospitals that rejoined
        
        return {
            'expected': list(expected_set),
            'actual': list(actual_set),
            'dropped': list(dropped),
            'recovered': list(recovered),
            'mask': {
                hospital_id: hospital_id in actual_set
                for hospital_id in expected_set
            }
        }
    
    @staticmethod
    def check_round_viability(
        round_number: int,
        db: Session
    ) -> Dict:
        """
        Check if round has enough participants to continue
        
        Args:
            round_number: Round number
            db: Database session
        
        Returns:
            Viability assessment
        """
        participation = DropoutService.track_hospital_participation(round_number, db)
        
        min_required = 3  # Minimum hospitals for federated learning
        
        is_viable = (
            participation['participated'] >= min_required and
            participation['dropout_rate'] <= DropoutService.MAX_DROPOUT_RATE
        )
        
        return {
            'round_number': round_number,
            'is_viable': is_viable,
            'participated': participation['participated'],
            'min_required': min_required,
            'dropout_rate': participation['dropout_rate'],
            'max_allowed_dropout_rate': DropoutService.MAX_DROPOUT_RATE,
            'recommendation': 'proceed' if is_viable else 'delay_or_cancel'
        }
    
    @staticmethod
    def get_hospital_participation_history(
        hospital_id: int,
        num_rounds: int,
        db: Session
    ) -> Dict:
        """
        Get hospital's participation history
        
        Args:
            hospital_id: Hospital ID
            num_rounds: Number of recent rounds to check
            db: Database session
        
        Returns:
            Participation history
        """
        # Get recent rounds
        recent_rounds = db.query(TrainingRound).order_by(
            TrainingRound.round_number.desc()
        ).limit(num_rounds).all()
        
        if not recent_rounds:
            return {'error': 'No rounds found'}
        
        participation_data = []
        
        for round_obj in recent_rounds:
            # Check if hospital participated
            weight = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.round_number == round_obj.round_number,
                ModelWeights.is_global == False
            ).first()
            
            participation_data.append({
                'round_number': round_obj.round_number,
                'participated': weight is not None,
                'status': HospitalStatus.ACTIVE if weight else HospitalStatus.DROPPED,
                'round_status': round_obj.status
            })
        
        # Calculate statistics
        participated_count = sum(1 for p in participation_data if p['participated'])
        participation_rate = participated_count / len(participation_data) if participation_data else 0
        
        # Detect consecutive dropouts
        consecutive_dropouts = 0
        for p in participation_data:
            if not p['participated']:
                consecutive_dropouts += 1
            else:
                break
        
        return {
            'hospital_id': hospital_id,
            'num_rounds_checked': len(participation_data),
            'participated_count': participated_count,
            'participation_rate': participation_rate,
            'consecutive_dropouts': consecutive_dropouts,
            'history': participation_data,
            'alert': consecutive_dropouts >= 3  # Alert if 3+ consecutive dropouts
        }
    
    @staticmethod
    def calculate_dropout_penalty(
        hospital_id: int,
        db: Session
    ) -> float:
        """
        Calculate weight penalty for unreliable hospitals
        
        Hospitals with frequent dropouts get lower aggregation weights
        
        Args:
            hospital_id: Hospital ID
            db: Database session
        
        Returns:
            Penalty multiplier (0.5 to 1.0)
        """
        history = DropoutService.get_hospital_participation_history(
            hospital_id, 10, db
        )
        
        if 'error' in history:
            return 1.0  # No penalty if no history
        
        participation_rate = history['participation_rate']
        
        # Calculate penalty
        if participation_rate >= 0.9:
            penalty = 1.0  # No penalty
        elif participation_rate >= 0.7:
            penalty = 0.9  # 10% penalty
        elif participation_rate >= 0.5:
            penalty = 0.75  # 25% penalty
        else:
            penalty = 0.5  # 50% penalty
        
        return penalty
    
    @staticmethod
    def attempt_recovery(
        round_number: int,
        dropped_hospital_ids: List[int],
        db: Session
    ) -> Dict:
        """
        Attempt to recover dropped hospitals
        
        Send notifications and allow late submissions
        
        Args:
            round_number: Round number
            dropped_hospital_ids: List of dropped hospital IDs
            db: Database session
        
        Returns:
            Recovery attempt results
        """
        recovery_results = []
        
        for hospital_id in dropped_hospital_ids:
            hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            
            if not hospital:
                continue
            
            # Check if hospital has submitted late
            late_weight = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.round_number == round_number,
                ModelWeights.is_global == False
            ).first()
            
            status = HospitalStatus.RECOVERED if late_weight else HospitalStatus.DROPPED
            
            recovery_results.append({
                'hospital_id': hospital_id,
                'hospital_name': hospital.hospital_name,
                'status': status,
                'has_late_submission': late_weight is not None
            })
        
        recovered_count = sum(1 for r in recovery_results if r['status'] == HospitalStatus.RECOVERED)
        
        return {
            'round_number': round_number,
            'attempted_recovery': len(dropped_hospital_ids),
            'recovered': recovered_count,
            'still_dropped': len(dropped_hospital_ids) - recovered_count,
            'results': recovery_results
        }
