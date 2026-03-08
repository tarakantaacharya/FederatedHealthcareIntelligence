"""
Scenario analysis service (Phase 17)
What-if analysis and sensitivity testing
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from app.ml.baseline_model import BaselineForecaster


class ScenarioService:
    """Service for scenario analysis and what-if simulations"""
    
    @staticmethod
    def create_scenario(
        base_forecast: Dict,
        adjustments: Dict[str, float]
    ) -> Dict:
        """
        Create what-if scenario with adjusted parameters
        
        Args:
            base_forecast: Base forecast dictionary
            adjustments: Parameter adjustments (e.g., {"er_visits": 1.2} for 20% increase)
        
        Returns:
            Adjusted forecast scenario
        """
        scenario_forecasts = []
        
        for point in base_forecast['forecasts']:
            adjusted_point = point.copy()
            
            # Apply multiplicative adjustments
            for param, factor in adjustments.items():
                if param in ['er_visits', 'admissions', 'staff_count']:
                    # These affect bed_occupancy
                    adjusted_point['prediction'] *= factor
                    adjusted_point['lower_bound'] *= factor
                    adjusted_point['upper_bound'] *= factor
            
            scenario_forecasts.append(adjusted_point)
        
        return {
            'scenario_name': f"What-if: {adjustments}",
            'base_model_id': base_forecast['model_id'],
            'adjustments': adjustments,
            'forecasts': scenario_forecasts,
            'generated_at': base_forecast['generated_at']
        }
    
    @staticmethod
    def sensitivity_analysis(
        base_forecast: Dict,
        parameter: str,
        range_factors: List[float] = [0.8, 0.9, 1.0, 1.1, 1.2]
    ) -> Dict:
        """
        Perform sensitivity analysis on a parameter
        
        Args:
            base_forecast: Base forecast
            parameter: Parameter to vary
            range_factors: Multiplier range (e.g., [0.8, 1.2] for ±20%)
        
        Returns:
            Sensitivity analysis results
        """
        scenarios = []
        
        for factor in range_factors:
            scenario = ScenarioService.create_scenario(
                base_forecast,
                {parameter: factor}
            )
            
            # Calculate impact metrics
            avg_prediction = np.mean([p['prediction'] for p in scenario['forecasts']])
            base_avg = np.mean([p['prediction'] for p in base_forecast['forecasts']])
            
            impact_percentage = ((avg_prediction - base_avg) / base_avg) * 100
            
            scenarios.append({
                'factor': factor,
                'adjustment_percentage': (factor - 1.0) * 100,
                'avg_prediction': float(avg_prediction),
                'impact_percentage': float(impact_percentage),
                'forecasts': scenario['forecasts'][:10]  # First 10 points for preview
            })
        
        return {
            'parameter': parameter,
            'base_average': float(base_avg),
            'scenarios': scenarios
        }
    
    @staticmethod
    def capacity_stress_test(
        base_forecast: Dict,
        hospital_capacity: int,
        stress_factors: List[float] = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    ) -> Dict:
        """
        Test capacity under increasing demand scenarios
        
        Args:
            base_forecast: Base forecast
            hospital_capacity: Total bed capacity
            stress_factors: Demand multipliers
        
        Returns:
            Capacity stress test results
        """
        results = []
        
        for factor in stress_factors:
            # Create stressed scenario
            scenario = ScenarioService.create_scenario(
                base_forecast,
                {'demand': factor}
            )
            
            # Calculate capacity metrics
            predictions = [p['prediction'] for p in scenario['forecasts']]
            
            hours_over_capacity = sum(1 for p in predictions if p > hospital_capacity)
            max_demand = max(predictions)
            avg_utilization = (np.mean(predictions) / hospital_capacity) * 100
            peak_utilization = (max_demand / hospital_capacity) * 100
            
            results.append({
                'stress_factor': factor,
                'demand_increase_percent': (factor - 1.0) * 100,
                'hours_over_capacity': hours_over_capacity,
                'max_demand': float(max_demand),
                'avg_utilization_percent': float(avg_utilization),
                'peak_utilization_percent': float(peak_utilization),
                'capacity_breached': max_demand > hospital_capacity
            })
        
        return {
            'hospital_capacity': hospital_capacity,
            'forecast_horizon': len(base_forecast['forecasts']),
            'stress_tests': results
        }
