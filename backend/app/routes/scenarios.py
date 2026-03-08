"""
Scenario analysis routes (Phase 17)
What-if analysis and sensitivity testing
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.schemas.scenario_schema import (
    ScenarioRequest,
    SensitivityRequest,
    CapacityStressTestRequest
)
from app.services.prediction_service import PredictionService
from app.services.scenario_service import ScenarioService

router = APIRouter()


@router.post("/what-if")
async def create_what_if_scenario(
    request: ScenarioRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Create what-if scenario with parameter adjustments
    
    - **model_id**: Base model
    - **forecast_horizon**: Forecast horizon
    - **adjustments**: Dictionary of parameter adjustments
    
    **Example Scenarios:**
    - {"er_visits": 1.2} → 20% increase in ER visits
    - {"admissions": 0.8} → 20% decrease in admissions
    - {"er_visits": 1.3, "staff_count": 0.9} → Combined effect
    
    Returns adjusted forecast showing impact of changes.
    """
    # Generate base forecast
    hospital = current_user["db_object"]
    base_forecast = PredictionService.generate_forecast(
        hospital=hospital,
        model_id=request.model_id,
        forecast_horizon=request.forecast_horizon,
        db=db
    )
    
    # Create scenario
    scenario = ScenarioService.create_scenario(
        base_forecast,
        request.adjustments
    )
    
    return scenario


@router.post("/sensitivity")
async def sensitivity_analysis(
    request: SensitivityRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Perform sensitivity analysis on a parameter
    
    - **model_id**: Model to use
    - **parameter**: Parameter to vary
    - **range_factors**: Range of multipliers
    
    **Use Cases:**
    - How does 10-20% increase in ER visits affect bed demand?
    - Impact of reduced staff count on patient throughput
    - Effect of seasonal flu surge on ICU capacity
    
    Returns forecasts for each scenario with impact metrics.
    """
    # Generate base forecast
    hospital = current_user["db_object"]
    base_forecast = PredictionService.generate_forecast(
        hospital=hospital,
        model_id=request.model_id,
        forecast_horizon=request.forecast_horizon,
        db=db
    )
    
    # Perform sensitivity analysis
    sensitivity = ScenarioService.sensitivity_analysis(
        base_forecast,
        request.parameter,
        request.range_factors
    )
    
    return sensitivity


@router.post("/capacity-stress-test")
async def capacity_stress_test(
    request: CapacityStressTestRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
):
    """
    Test capacity under increasing demand scenarios
    
    - **model_id**: Model to use
    - **hospital_capacity**: Total bed capacity
    - **stress_factors**: Demand multipliers (e.g., [1.0, 1.2, 1.4])
    
    **Returns:**
    - Hours over capacity
    - Peak utilization percentage
    - Capacity breach indicators
    
    **Use Cases:**
    - Pandemic preparedness (1.5x-2x normal demand)
    - Seasonal surge planning (1.2x-1.3x demand)
    - Infrastructure expansion decisions
    """
    # Generate base forecast
    hospital = current_user["db_object"]
    base_forecast = PredictionService.generate_forecast(
        hospital=hospital,
        model_id=request.model_id,
        forecast_horizon=request.forecast_horizon,
        db=db
    )
    
    # Perform stress test
    stress_test = ScenarioService.capacity_stress_test(
        base_forecast,
        request.hospital_capacity,
        request.stress_factors
    )
    
    return stress_test
