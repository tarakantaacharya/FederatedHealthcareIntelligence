"""
Pydantic schemas for Differential Privacy
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class DPConfig(BaseModel):
    """DP configuration"""
    epsilon: float = Field(default=1.0, description="Privacy budget per round")
    delta: float = Field(default=1e-5, description="Privacy parameter")
    decay_rate: float = Field(default=0.95, description="Epsilon decay rate")
    min_epsilon: float = Field(default=0.1, description="Minimum epsilon")
    clip_norm: float = Field(default=1.0, description="Gradient clipping norm")
    noise_multiplier: float = Field(default=1.0, description="Noise scale multiplier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "epsilon": 1.0,
                "delta": 1e-5,
                "decay_rate": 0.95,
                "min_epsilon": 0.1,
                "clip_norm": 1.0,
                "noise_multiplier": 1.0
            }
        }


class PrivacyMetadata(BaseModel):
    """Privacy metadata for a round"""
    round_number: int
    epsilon: float
    delta: float
    clip_norm: float
    noise_multiplier: float
    total_epsilon_spent: float
    timestamp: str


class PrivacyBudgetStatus(BaseModel):
    """Privacy budget status"""
    total_epsilon_spent: float
    delta: float
    initial_epsilon: float
    current_min_epsilon: float
    num_rounds: int
    privacy_guarantee: str


class AggregationWithDPRequest(BaseModel):
    """Request for DP-enabled aggregation"""
    round_number: int
    enable_dp: bool = Field(default=True, description="Enable differential privacy")
    dp_config: Optional[DPConfig] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "round_number": 1,
                "enable_dp": True,
                "dp_config": {
                    "epsilon": 1.0,
                    "delta": 1e-5
                }
            }
        }


class AggregationWithDPResponse(BaseModel):
    """Response from DP-enabled aggregation"""
    status: str
    round_number: int
    global_model_id: int
    num_hospitals: int
    avg_loss: float
    avg_accuracy: float
    global_weights_path: str
    privacy_applied: bool
    privacy_metadata: Optional[Dict]
    message: str
