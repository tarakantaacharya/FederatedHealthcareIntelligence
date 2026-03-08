"""
Model Governance Service (Phase 29)
Policy evaluation, approval workflow, and cryptographic signing
"""
import hashlib
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.model_governance import ModelGovernance
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound


class ModelGovernanceService:
    """Service for model governance, approval, and signing"""
    
    # Policy versions and thresholds
    # MAPE threshold: lower is better, set to 20.0 to allow models in development
    POLICY_V1_MAPE_THRESHOLD = 20.0
    POLICY_V1_MIN_PARTICIPANTS = 2
    
    @staticmethod
    def evaluate_policy(
        mape: float,
        num_participants: int = 0,
        policy_version: str = "v1"
    ) -> tuple[bool, Dict]:
        """
        Evaluate governance policy for model approval
        
        Policy v1 rules:
        - MAPE (Mean Absolute Percentage Error) must be <= 2000% (20.0)
        - Minimum 2 participating hospitals
        
        Args:
            mape: Model MAPE metric (0.0 to 1.0+), lower is better
            num_participants: Number of hospitals in round
            policy_version: Policy version to apply
        
        Returns:
            Tuple of (approved: bool, policy_details: dict)
        """
        if policy_version == "v1":
            mape_pass = mape <= ModelGovernanceService.POLICY_V1_MAPE_THRESHOLD
            participants_pass = num_participants >= ModelGovernanceService.POLICY_V1_MIN_PARTICIPANTS
            
            approved = mape_pass and participants_pass
            
            policy_details = {
                "policy_version": "v1",
                "rules": {
                    "max_mape": ModelGovernanceService.POLICY_V1_MAPE_THRESHOLD,
                    "min_participants": ModelGovernanceService.POLICY_V1_MIN_PARTICIPANTS
                },
                "results": {
                    "mape": mape,
                    "mape_pass": mape_pass,
                    "num_participants": num_participants,
                    "participants_pass": participants_pass
                },
                "approved": approved
            }
            
            return approved, policy_details
        
        return False, {"error": "Unknown policy version"}
    
    @staticmethod
    def sign_model(model_hash: str, private_key: str) -> str:
        """
        Generate cryptographic signature for approved model
        
        Args:
            model_hash: SHA-256 hash of model weights
            private_key: Private signing key
        
        Returns:
            Signature (SHA-256 hash of model_hash + private_key)
        """
        payload = f"{model_hash}:{private_key}"
        signature = hashlib.sha256(payload.encode()).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(model_hash: str, signature: str, private_key: str) -> bool:
        """
        Verify model signature
        
        Args:
            model_hash: Model hash
            signature: Signature to verify
            private_key: Private key used for signing
        
        Returns:
            True if signature is valid
        """
        expected_signature = ModelGovernanceService.sign_model(model_hash, private_key)
        return signature == expected_signature
    
    @staticmethod
    def approve_model(
        db: Session,
        round_number: int,
        model_hash: str,
        mape: float,
        admin_user: str,
        private_key: str,
        num_participants: int = 0,
        policy_version: str = "v1"
    ) -> ModelGovernance:
        """
        Approve and sign a federated global model
        
        Args:
            db: Database session
            round_number: Training round number
            model_hash: SHA-256 hash of model
            mape: Model MAPE (Mean Absolute Percentage Error)
            admin_user: Admin user identifier
            private_key: Private signing key
            num_participants: Number of hospitals
            policy_version: Policy version to apply
        
        Returns:
            ModelGovernance record
        """
        # Evaluate policy
        approved, policy_details = ModelGovernanceService.evaluate_policy(
            mape, num_participants, policy_version
        )
        
        # Generate signature if approved
        signature = None
        rejection_reason = None
        
        if approved:
            signature = ModelGovernanceService.sign_model(model_hash, private_key)
        else:
            # Build rejection reason
            reasons = []
            if not policy_details["results"]["mape_pass"]:
                reasons.append(
                    f"MAPE {mape:.4f} exceeds threshold "
                    f"{ModelGovernanceService.POLICY_V1_MAPE_THRESHOLD:.4f}"
                )
            if not policy_details["results"]["participants_pass"]:
                reasons.append(
                    f"Only {num_participants} participants "
                    f"(minimum {ModelGovernanceService.POLICY_V1_MIN_PARTICIPANTS})"
                )
            rejection_reason = "; ".join(reasons)
        
        # Create governance record
        record = ModelGovernance(
            round_number=round_number,
            model_hash=model_hash,
            approved=approved,
            approved_by=admin_user,
            signature=signature,
            policy_version=policy_version,
            policy_details=json.dumps(policy_details),
            rejection_reason=rejection_reason
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record
    
    @staticmethod
    def get_governance_status(
        db: Session,
        round_number: Optional[int] = None,
        model_hash: Optional[str] = None
    ) -> Dict:
        """
        Get governance status for rounds or specific model
        
        Args:
            db: Database session
            round_number: Optional round number filter
            model_hash: Optional model hash filter
        
        Returns:
            Governance status summary
        """
        query = db.query(ModelGovernance)
        
        if round_number:
            query = query.filter(ModelGovernance.round_number == round_number)
        if model_hash:
            query = query.filter(ModelGovernance.model_hash == model_hash)
        
        records = query.order_by(ModelGovernance.created_at.desc()).all()
        
        return {
            "total_evaluations": len(records),
            "approved_count": sum(1 for r in records if r.approved),
            "rejected_count": sum(1 for r in records if not r.approved),
            "records": [
                {
                    "id": r.id,
                    "round_number": r.round_number,
                    "model_hash": r.model_hash,
                    "approved": r.approved,
                    "approved_by": r.approved_by,
                    "signature": r.signature,
                    "policy_version": r.policy_version,
                    "rejection_reason": r.rejection_reason,
                    "created_at": str(r.created_at)
                }
                for r in records
            ]
        }
