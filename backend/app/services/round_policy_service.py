"""
Round Policy Service (Phase A-Pro)
Manages round participation policies (add/remove allowed hospitals for SELECTED policy).
"""

from sqlalchemy.orm import Session
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound
from typing import List, Optional


class RoundPolicyService:
    """Manages round participation policy configurations."""
    
    @staticmethod
    def add_allowed_hospital(round_id: int, hospital_id: int, db: Session) -> bool:
        """Add hospital to SELECTED round allowlist."""
        
        # Verify hospital exists
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            return False
        
        # Verify round exists
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
        if not round_obj:
            return False
        
        # Check if already in allowlist
        existing = db.query(RoundAllowedHospital).filter(
            RoundAllowedHospital.round_id == round_id,
            RoundAllowedHospital.hospital_id == hospital_id
        ).first()
        
        if existing:
            return False
        
        # Add to allowlist
        allowed = RoundAllowedHospital(round_id=round_id, hospital_id=hospital_id)
        db.add(allowed)
        db.commit()
        db.refresh(allowed)
        return True
    
    @staticmethod
    def remove_allowed_hospital(round_id: int, hospital_id: int, db: Session) -> bool:
        """Remove hospital from SELECTED round allowlist."""
        
        result = db.query(RoundAllowedHospital).filter(
            RoundAllowedHospital.round_id == round_id,
            RoundAllowedHospital.hospital_id == hospital_id
        ).delete()
        
        db.commit()
        return result > 0
    
    @staticmethod
    def get_allowed_hospitals(round_id: int, db: Session) -> List[dict]:
        """Get list of hospitals allowed for SELECTED round."""
        
        allowed = db.query(RoundAllowedHospital, Hospital).join(
            Hospital,
            Hospital.id == RoundAllowedHospital.hospital_id
        ).filter(
            RoundAllowedHospital.round_id == round_id
        ).all()
        
        return [
            {
                "hospital_id": h.id,
                "hospital_name": h.hospital_name,
                "region": getattr(h.hospitals_profile, "region", None) if hasattr(h, "hospitals_profile") else None
            }
            for _, h in allowed
        ]
    
    @staticmethod
    def set_region_policy(
        round_id: int, 
        allowed_regions: List[str], 
        db: Session
    ) -> bool:
        """Set REGION_BASED participation policy."""
        
        import json
        
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
        if not round_obj:
            return False
        
        metadata = {"allowed_regions": allowed_regions}
        round_obj.policy_metadata = json.dumps(metadata)
        db.commit()
        return True
    
    @staticmethod
    def set_capacity_policy(
        round_id: int, 
        bed_capacity_threshold: int, 
        db: Session
    ) -> bool:
        """Set CAPACITY_BASED participation policy."""
        
        import json
        
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
        if not round_obj:
            return False
        
        metadata = {"bed_capacity_threshold": bed_capacity_threshold}
        round_obj.policy_metadata = json.dumps(metadata)
        db.commit()
        return True
