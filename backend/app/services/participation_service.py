"""
Participation Service (Phase A-Pro)
Evaluates hospital eligibility for training rounds based on governance policies.
Enforces server-side participation rules.
"""

from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.hospitals_profile import HospitalProfile
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.models.model_weights import ModelWeights


class ParticipationService:
    """Server-side enforcement of hospital eligibility for round participation."""
    
    @staticmethod
    def can_participate(
        hospital_id: int, 
        training_round_id: int, 
        db: Session
    ) -> Tuple[bool, str]:
        """
        Evaluates if hospital can participate in round.
        Returns (is_eligible, reason_string)
        
        Handles all 4 participation policies + emergency override.
        Enforces single-round constraint.
        """
        
        # Load entities
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            return False, "Hospital not found"
        
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == training_round_id).first()
        if not round_obj:
            return False, "Training round not found"

        # CHECK 0: Round must be active for participation
        if round_obj.status == RoundStatus.CLOSED:
            return False, "This round is closed and no longer accepts participation."

        if round_obj.status == RoundStatus.AGGREGATING:
            return False, "This round is aggregating and no longer accepts new participation."

        if not round_obj.training_enabled:
            return False, "Training is currently disabled for this round by central admin."
        
        # CHECK 1: Hospital must be VERIFIED
        if hospital.verification_status != "VERIFIED":
            return False, "Your hospital is not yet verified. Please wait for admin approval."
        
        # CHECK 2: Hospital must be allowed_federated (central admin control)
        if not hospital.is_allowed_federated:
            return False, "Federated participation has been disabled for your hospital by central admin."
        
        # CHECK 3: Hospital cannot participate in multiple active rounds
        is_active, active_round_id = ParticipationService.is_hospital_in_active_round(
            hospital_id, db
        )
        if is_active and active_round_id != training_round_id:
            return False, f"You are already participating in round {active_round_id}. One round per hospital at a time."
        
        # CHECK 4: Emergency override - bypass all policies
        if round_obj.is_emergency:
            return True, "PASS Emergency round — all verified hospitals included"
        
        # CHECK 5: Apply participation policy
        if round_obj.participation_policy == "ALL":
            return True, "PASS Eligible for this round"
        
        elif round_obj.participation_policy == "SELECTED":
            # SELECTED mode - check selection_criteria
            if round_obj.selection_criteria == "MANUAL":
                # Manual selection - check RoundAllowedHospital table
                allowed = db.query(RoundAllowedHospital).filter(
                    RoundAllowedHospital.round_id == training_round_id,
                    RoundAllowedHospital.hospital_id == hospital_id
                ).first()
                if allowed:
                    return True, "PASS Eligible for this round (manual selection)"
                return False, "This round is restricted to selected hospitals. You are not included."
            
            elif round_obj.selection_criteria == "REGION":
                # Region-based selection
                profile = db.query(HospitalProfile).filter(
                    HospitalProfile.hospital_id == hospital_id
                ).first()
                
                if not profile or not profile.region:
                    return False, "Your hospital region is not configured. Contact admin."
                
                if profile.region == round_obj.selection_value:
                    return True, f"PASS Your region ({profile.region}) is included in this round"
                return False, f"This round accepts hospitals from {round_obj.selection_value} region only. Your hospital is in {profile.region}."
            
            elif round_obj.selection_criteria == "SIZE":
                # Hospital size-based selection (SMALL, LARGE)
                profile = db.query(HospitalProfile).filter(
                    HospitalProfile.hospital_id == hospital_id
                ).first()
                
                if not profile or not profile.size_category:
                    return False, "Your hospital size category is not configured. Contact admin."
                
                if profile.size_category == round_obj.selection_value:
                    return True, f"PASS Your hospital size ({profile.size_category}) is eligible for this round"
                return False, f"This round requires {round_obj.selection_value}-sized hospitals. Your hospital is {profile.size_category}."
            
            elif round_obj.selection_criteria == "EXPERIENCE":
                # Experience level selection (NEW, EXPERIENCED)
                profile = db.query(HospitalProfile).filter(
                    HospitalProfile.hospital_id == hospital_id
                ).first()
                
                if not profile or not profile.experience_level:
                    return False, "Your hospital experience level is not configured. Contact admin."
                
                if profile.experience_level == round_obj.selection_value:
                    return True, f"PASS Your experience level ({profile.experience_level}) matches this round requirement"
                return False, f"This round requires {round_obj.selection_value} hospitals. Your hospital is {profile.experience_level}."
        
        return False, "Unable to determine eligibility"
    
    @staticmethod
    def get_eligible_hospitals(
        training_round_id: int, 
        db: Session
    ) -> List[Hospital]:
        """
        Returns list of hospitals eligible for a training round.
        Admin-only: used for central planning.
        """
        
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == training_round_id).first()
        if not round_obj:
            return []
        
        # Base query: verified + allowed_federated
        base_query = db.query(Hospital).filter(
            Hospital.verification_status == "VERIFIED",
            Hospital.is_allowed_federated == True
        )
        
        if round_obj.is_emergency:
            return base_query.all()
        
        if round_obj.participation_policy == "ALL":
            return base_query.all()
        
        elif round_obj.participation_policy == "SELECTED":
            return base_query.join(
                RoundAllowedHospital,
                RoundAllowedHospital.hospital_id == Hospital.id
            ).filter(
                RoundAllowedHospital.round_id == training_round_id
            ).all()
        
        elif round_obj.participation_policy == "REGION_BASED":
            import json
            allowed_regions = []
            if round_obj.policy_metadata:
                try:
                    metadata = json.loads(round_obj.policy_metadata) if isinstance(round_obj.policy_metadata, str) else round_obj.policy_metadata
                    allowed_regions = metadata.get("allowed_regions", [])
                except:
                    pass
            
            if not allowed_regions:
                return base_query.all()
            
            # Filter by region in hospitals_profile
            return base_query.join(
                HospitalProfile,
                HospitalProfile.hospital_id == Hospital.id
            ).filter(
                HospitalProfile.region.in_(allowed_regions)
            ).all()
        
        elif round_obj.participation_policy == "CAPACITY_BASED":
            import json
            threshold = 0
            if round_obj.policy_metadata:
                try:
                    metadata = json.loads(round_obj.policy_metadata) if isinstance(round_obj.policy_metadata, str) else round_obj.policy_metadata
                    threshold = metadata.get("bed_capacity_threshold", 0)
                except:
                    pass
            
            return base_query.join(
                HospitalProfile,
                HospitalProfile.hospital_id == Hospital.id
            ).filter(
                HospitalProfile.bed_capacity >= threshold
            ).all()
        
        return []
    
    @staticmethod
    def is_hospital_in_active_round(hospital_id: int, db: Session) -> Tuple[bool, int]:
        """
        Check if hospital is already participating in an active (non-completed) round.
        Enforces: "One hospital per round at a time"
        
        Returns (is_active, round_id) or (False, 0)
        """
        
        active_weight = db.query(ModelWeights).join(
            TrainingRound,
            TrainingRound.id == ModelWeights.round_number
        ).filter(
            ModelWeights.hospital_id == hospital_id,
            TrainingRound.status.in_(["OPEN", "TRAINING", "AGGREGATING"])
        ).order_by(ModelWeights.round_number.desc()).first()
        
        if active_weight and active_weight.round_number:
            return True, active_weight.round_number
        
        return False, 0

