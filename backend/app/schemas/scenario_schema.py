"""
Pydantic schemas for scenario analysis
"""
from pydantic import BaseModel, Field
from typing import Dict, List


class ScenarioRequest(BaseModel):
    """Request to create scenario"""
    model_id: int
    forecast_horizon: int = Field(default=24, ge=1, le=168)
    adjustments: Dict[str, float] = Field(..., description="Parameter adjustments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "forecast_horizon": 24,
                "adjustments": {
                    "er_visits": 1.2,
                    "admissions": 1.1
                }
            }
        }


class SensitivityRequest(BaseModel):
    """Request for sensitivity analysis"""
    model_id: int
    forecast_horizon: int = Field(default=24, ge=1, le=168)
    parameter: str = Field(..., description="Parameter to analyze")
    range_factors: List[float] = Field(default=[0.8, 0.9, 1.0, 1.1, 1.2])
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "forecast_horizon": 24,
                "parameter": "er_visits",
                "range_factors": [0.8, 0.9, 1.0, 1.1, 1.2]
            }
        }


class CapacityStressTestRequest(BaseModel):
    """Request for capacity stress test"""
    model_id: int
    forecast_horizon: int = Field(default=24, ge=1, le=168)
    hospital_capacity: int = Field(..., gt=0)
    stress_factors: List[float] = Field(default=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "forecast_horizon": 24,
                "hospital_capacity": 500,
                "stress_factors": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
            }
        }
