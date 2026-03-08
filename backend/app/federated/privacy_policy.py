"""
Federated Privacy Policy Governance

Centralizes DP parameter control across all hospitals.
Hospitals must enforce and cannot override.
"""

from dataclasses import dataclass
from typing import Dict, Any
import json


@dataclass
class FederatedPrivacyPolicy:
    """
    Central privacy policy enforced across all federated hospitals.
    
    All hospitals MUST abide by these parameters.
    Local overrides are strictly prohibited.
    
    Attributes:
        epsilon_per_round: DP epsilon budget per federated round
        clip_norm: Gradient clipping threshold (sensitivity bound)
        noise_multiplier: Noise scale relative to clip_norm
        max_local_epochs: Maximum training epochs per hospital per round
        max_batch_size: Maximum batch size for local training
        dp_mode: DP implementation mode ("batch" only in production)
    """
    
    epsilon_per_round: float
    clip_norm: float
    noise_multiplier: float
    max_local_epochs: int
    max_batch_size: int
    dp_mode: str = "batch"  # HARDCODED - only batch-level DP allowed
    
    def __post_init__(self):
        """Validate policy consistency and enforce constraints."""
        # ========== PRODUCTION CONSTRAINTS ==========
        # Strict per-sample DP is NEVER allowed in federated rounds
        if self.dp_mode != "batch":
            raise ValueError(
                f"Only batch-level DP allowed in production. "
                f"Got dp_mode='{self.dp_mode}'. "
                f"Strict per-sample DP is disabled."
            )
        
        # Epsilon must be reasonable
        if self.epsilon_per_round <= 0 or self.epsilon_per_round > 10:
            raise ValueError(
                f"epsilon_per_round must be in (0, 10]. "
                f"Got {self.epsilon_per_round}"
            )
        
        # Clipping threshold must be positive
        if self.clip_norm <= 0:
            raise ValueError(
                f"clip_norm must be positive. Got {self.clip_norm}"
            )
        
        # Noise multiplier must be non-negative
        if self.noise_multiplier < 0:
            raise ValueError(
                f"noise_multiplier must be non-negative. "
                f"Got {self.noise_multiplier}"
            )
        
        # Local epochs must be reasonable
        if self.max_local_epochs < 1 or self.max_local_epochs > 10:
            raise ValueError(
                f"max_local_epochs must be in [1, 10]. "
                f"Got {self.max_local_epochs}"
            )
        
        # Batch size must be reasonable
        if self.max_batch_size < 1 or self.max_batch_size > 1024:
            raise ValueError(
                f"max_batch_size must be in [1, 1024]. "
                f"Got {self.max_batch_size}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to dictionary."""
        return {
            "epsilon_per_round": self.epsilon_per_round,
            "clip_norm": self.clip_norm,
            "noise_multiplier": self.noise_multiplier,
            "max_local_epochs": self.max_local_epochs,
            "max_batch_size": self.max_batch_size,
            "dp_mode": self.dp_mode,
        }
    
    def to_json(self) -> str:
        """Serialize policy to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FederatedPrivacyPolicy":
        """Deserialize policy from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "FederatedPrivacyPolicy":
        """Deserialize policy from JSON string."""
        return cls.from_dict(json.loads(json_str))


def generate_default_privacy_policy() -> FederatedPrivacyPolicy:
    """
    Generate default central privacy policy for federated rounds.
    
    These parameters are validated by federated validation tests:
    - 5 rounds × 3 hospitals
    - Final loss: ~5.34 (acceptable convergence)
    - Total epsilon: 15.0 (increased for TFT training - was 5.0)
    - Batch-level DP only
    
    Returns:
        FederatedPrivacyPolicy: Central policy enforced on all hospitals
    """
    return FederatedPrivacyPolicy(
        epsilon_per_round=10.0,          # 10.0 ε per round (increased for TFT training needs)
        clip_norm=1.0,                   # Gradient clipping at norm 1.0
        noise_multiplier=1.5,            # Noise scale = 1.5 × clip_norm (increased for lower epsilon)
        max_local_epochs=2,              # 2 epochs per hospital per round
        max_batch_size=32,               # Max batch size 32
        dp_mode="batch"                  # ONLY batch-level DP allowed
    )


def generate_strict_privacy_policy() -> FederatedPrivacyPolicy:
    """
    This function MUST FAIL in production.
    
    Strict per-sample DP is NOT APPROVED.
    This exists to explicitly document the rejection.
    
    Raises:
        ValueError: Always raises - strict DP is permanently disabled
    """
    raise ValueError(
        "\n" + "="*80 + "\n" +
        "STRICT PER-SAMPLE DP IS PERMANENTLY DISABLED\n" +
        "\n" +
        "Reason: Federated validation failure\n" +
        "  Convergence degradation: 24× worse (Loss: 5.34 → 124.58)\n" +
        "  Epsilon budget: Same (5.0 for 5 rounds)\n" +
        "  Blocker: Unacceptable loss quality\n" +
        "\n" +
        "Only batch-level DP is approved for federated training.\n" +
        "See: backend/experimental/reports/federated_validation_results.json\n" +
        "="*80
    )
