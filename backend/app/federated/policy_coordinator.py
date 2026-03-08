"""
Federated Privacy Policy Coordinator

Central server coordinates privacy policies across federated rounds.
Each round has a centrally-defined privacy policy that all hospitals must enforce.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json
from app.federated.privacy_policy import (
    FederatedPrivacyPolicy,
    generate_default_privacy_policy,
    generate_strict_privacy_policy
)


class FederatedPolicyCoordinator:
    """
    Central coordinator for federated privacy policies.
    
    Responsibilities:
    1. Generate privacy policy for each federated round
    2. Distribute policy to all participating hospitals
    3. Verify hospitals enforce policy
    4. Log policy compliance
    """
    
    @staticmethod
    def generate_round_policy(
        round_number: int,
        num_participating_hospitals: int
    ) -> FederatedPrivacyPolicy:
        """
        Generate central privacy policy for a federated round.
        
        Policy is deterministic based on round number.
        All hospitals receive identical policy for a given round.
        
        Args:
            round_number: Federated round number (1-indexed)
            num_participating_hospitals: Number of hospitals in this round
        
        Returns:
            FederatedPrivacyPolicy: Central policy enforced on all hospitals
        
        Note:
            - Policy cannot be overridden locally
            - Hospital violating policy will fail training
        """
        # Generate default policy (validated via federated testing)
        policy = generate_default_privacy_policy()
        
        print(f"[POLICY GENERATION] Round {round_number}")
        print(f"[POLICY GENERATION] Hospitals participating: {num_participating_hospitals}")
        print(f"[POLICY GENERATION] Policy: {policy.to_json()}")
        
        return policy
    
    @staticmethod
    def get_policy_for_hospital(
        policy: FederatedPrivacyPolicy,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Get policy details for hospital enforcement.
        
        Args:
            policy: FederatedPrivacyPolicy
            hospital_id: Hospital identifier
        
        Returns:
            Dictionary with policy parameters for hospital
        """
        policy_dict = policy.to_dict()
        policy_dict["hospital_id"] = hospital_id
        policy_dict["issued_at"] = datetime.utcnow().isoformat()
        
        return policy_dict
    
    @staticmethod
    def validate_hospital_compliance(
        hospital_id: str,
        local_epochs: int,
        batch_size: int,
        policy: FederatedPrivacyPolicy
    ) -> tuple[bool, str]:
        """
        Check if hospital parameters comply with central policy.
        
        Args:
            hospital_id: Hospital identifier
            local_epochs: Requested local epochs
            batch_size: Requested batch size
            policy: FederatedPrivacyPolicy to check against
        
        Returns:
            Tuple (compliant: bool, message: str)
        """
        if local_epochs > policy.max_local_epochs:
            return (
                False,
                f"Hospital {hospital_id}: epochs ({local_epochs}) exceeds policy "
                f"({policy.max_local_epochs})"
            )
        
        if batch_size > policy.max_batch_size:
            return (
                False,
                f"Hospital {hospital_id}: batch_size ({batch_size}) exceeds policy "
                f"({policy.max_batch_size})"
            )
        
        return (True, f"Hospital {hospital_id}: compliant with policy")
    
    @staticmethod
    def log_policy_enforcement(
        hospital_id: str,
        round_number: int,
        policy: FederatedPrivacyPolicy,
        local_epochs: int,
        batch_size: int,
        actual_epsilon: float,
        convergence_loss: float
    ) -> Dict[str, Any]:
        """
        Log policy enforcement for audit trail.
        
        Args:
            hospital_id: Hospital identifier
            round_number: Federated round number
            policy: FederatedPrivacyPolicy enforced
            local_epochs: Actual epochs used
            batch_size: Actual batch size used
            actual_epsilon: DP epsilon spent
            convergence_loss: Final training loss
        
        Returns:
            Audit log entry
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "hospital_id": hospital_id,
            "round_number": round_number,
            "policy": policy.to_dict(),
            "training": {
                "local_epochs": local_epochs,
                "batch_size": batch_size,
            },
            "privacy": {
                "epsilon_per_round": policy.epsilon_per_round,
                "epsilon_actual": actual_epsilon,
                "clip_norm": policy.clip_norm,
                "noise_multiplier": policy.noise_multiplier,
                "dp_mode": policy.dp_mode,
            },
            "metrics": {
                "convergence_loss": convergence_loss,
            }
        }
        
        print(f"[DP POLICY AUDIT LOG]")
        print(f"Hospital: {hospital_id}")
        print(f"Round: {round_number}")
        print(f"epsilon_spent: {actual_epsilon}")
        print(f"convergence_loss: {convergence_loss}")
        print(f"batch_size: {batch_size}")
        
        return log_entry
    
    @staticmethod
    def generate_round_policy_file(
        policy: FederatedPrivacyPolicy,
        round_number: int,
        output_dir: str = "./storage/models/central/policies"
    ) -> str:
        """
        Save policy to file for distribution to hospitals.
        
        Args:
            policy: FederatedPrivacyPolicy to save
            round_number: Federated round number
            output_dir: Directory to save policy file
        
        Returns:
            Path to saved policy file
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"policy_round_{round_number}.json")
        with open(filepath, "w") as f:
            f.write(policy.to_json())
        
        print(f"[POLICY FILE] Saved to {filepath}")
        return filepath
    
    @staticmethod
    def load_round_policy(
        round_number: int,
        policy_dir: str = "./storage/models/central/policies"
    ) -> FederatedPrivacyPolicy:
        """
        Load policy for a specific round.
        
        Args:
            round_number: Federated round number
            policy_dir: Directory containing policy files
        
        Returns:
            FederatedPrivacyPolicy loaded from file
        """
        import os
        
        filepath = os.path.join(policy_dir, f"policy_round_{round_number}.json")
        
        if not os.path.exists(filepath):
            print(f"[POLICY] File not found: {filepath}, generating new policy")
            return generate_default_privacy_policy()
        
        with open(filepath, "r") as f:
            policy_dict = json.load(f)
        
        return FederatedPrivacyPolicy.from_dict(policy_dict)
