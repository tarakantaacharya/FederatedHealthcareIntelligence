"""
Model leaderboard tracking and selection

Tracks training results and selects best model
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ModelResult:
    """Result for a single trained model"""
    model_name: str
    best_hyperparameters: Dict[str, Any]
    mae: float
    mse: float
    rmse: float
    r2: float
    adjusted_r2: float
    mape: float
    smape: float
    wape: float
    mase: float
    rmsle: float
    training_time: float  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ModelLeaderboard:
    """
    Tracks and manages model training results
    """
    
    def __init__(self):
        """Initialize leaderboard"""
        self.results: List[ModelResult] = []
        self.best_model: Optional[ModelResult] = None
        self.best_score: float = -float('inf')
        
    def add_result(self, result: ModelResult) -> None:
        """
        Add model result to leaderboard
        
        Args:
            result: ModelResult object
        """
        self.results.append(result)
        
        # Update best model using composite score
        score = self._compute_score(result)
        if score > self.best_score:
            self.best_score = score
            self.best_model = result
    
    @staticmethod
    def _compute_score(result: ModelResult) -> float:
        """
        Compute composite score for model
        
        Priority: R² (higher) > RMSE (lower) > MAE (lower)
        
        Args:
            result: ModelResult
        
        Returns:
            Composite score
        """
        # Composite score: maximize R², minimize RMSE and MAE
        score = (result.r2 * 1.0) - (result.rmse * 0.1) - (result.mae * 0.05)
        return score
    
    def get_leaderboard(self) -> pd.DataFrame:
        """
        Get leaderboard as sorted DataFrame
        
        Returns:
            DataFrame with all model results sorted by score
        """
        if not self.results:
            return pd.DataFrame()
        
        data = [r.to_dict() for r in self.results]
        df = pd.DataFrame(data)
        
        # Add composite score column
        df['composite_score'] = df.apply(
            lambda row: self._compute_score(
                ModelResult(**row.to_dict())
            ),
            axis=1
        )
        
        # Sort by score (descending)
        df = df.sort_values('composite_score', ascending=False).reset_index(drop=True)
        
        return df
    
    def get_best_model(self) -> Optional[ModelResult]:
        """
        Get best model
        
        Returns:
            Best ModelResult or None
        """
        return self.best_model
    
    def get_best_model_info(self) -> Dict[str, Any]:
        """
        Get best model information
        
        Returns:
            Dict with best model details
        """
        if not self.best_model:
            return {}
        
        return {
            'model_name': self.best_model.model_name,
            'best_hyperparameters': self.best_model.best_hyperparameters,
            'metrics': {
                'mae': self.best_model.mae,
                'mse': self.best_model.mse,
                'rmse': self.best_model.rmse,
                'r2': self.best_model.r2,
                'adjusted_r2': self.best_model.adjusted_r2,
                'mape': self.best_model.mape,
                'smape': self.best_model.smape,
                'wape': self.best_model.wape,
                'mase': self.best_model.mase,
                'rmsle': self.best_model.rmsle
            },
            'training_time': self.best_model.training_time
        }
    
    def get_leaderboard_dict(self) -> List[Dict[str, Any]]:
        """
        Get leaderboard as list of dicts
        
        Returns:
            List of model results
        """
        df = self.get_leaderboard()
        if df.empty:
            return []
        
        # Convert to list of dicts, excluding composite_score
        return df.drop(columns=['composite_score'], errors='ignore').to_dict('records')
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get leaderboard summary
        
        Returns:
            Summary statistics
        """
        if not self.results:
            return {'total_models': 0}
        
        df = self.get_leaderboard()
        
        return {
            'total_models': len(self.results),
            'best_model': self.best_model.model_name if self.best_model else None,
            'best_r2': self.best_model.r2 if self.best_model else None,
            'best_rmse': self.best_model.rmse if self.best_model else None,
            'best_mae': self.best_model.mae if self.best_model else None,
            'average_r2': df['r2'].mean() if 'r2' in df else None,
            'average_rmse': df['rmse'].mean() if 'rmse' in df else None,
            'average_training_time': df['training_time'].mean() if 'training_time' in df else None
        }
