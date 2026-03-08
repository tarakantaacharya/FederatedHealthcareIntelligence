"""
Comprehensive metrics calculator for regression models
Computes all 10 evaluation metrics for model comparison
"""
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
from typing import Dict, Tuple


class MetricsCalculator:
    """Calculate comprehensive regression metrics"""
    
    @staticmethod
    def calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray, 
                             num_features: int = None) -> Dict[str, float]:
        """
        Calculate all 10 metrics for regression model
        
        Returns:
            Dictionary with MAE, MSE, RMSE, R², Adjusted R², MAPE, sMAPE, WAPE, MASE, RMSLE
        """
        y_true = np.asarray(y_true, dtype=np.float64)
        y_pred = np.asarray(y_pred, dtype=np.float64)
        n_samples = len(y_true)
        
        # 1. MAE (Mean Absolute Error)
        mae = float(mean_absolute_error(y_true, y_pred))
        
        # 2. MSE (Mean Squared Error)
        mse = float(mean_squared_error(y_true, y_pred))
        
        # 3. RMSE (Root Mean Squared Error)
        rmse = float(np.sqrt(mse))
        
        # 4. R² (Coefficient of Determination)
        r2 = float(r2_score(y_true, y_pred))
        
        # 5. Adjusted R²
        if num_features and n_samples > num_features + 1:
            adjusted_r2 = 1 - (1 - r2) * (n_samples - 1) / (n_samples - num_features - 1)
            adjusted_r2 = float(max(-1, min(1, adjusted_r2)))
        else:
            adjusted_r2 = r2
        
        # 6. MAPE (Mean Absolute Percentage Error) - avoid division by zero
        eps = 1e-10
        mape_values = np.abs((y_true - y_pred) / (np.abs(y_true) + eps))
        mape = float(np.mean(mape_values[np.abs(y_true) > eps]) * 100) if np.any(np.abs(y_true) > eps) else 0.0
        
        # 7. sMAPE (Symmetric Mean Absolute Percentage Error)
        smape_denom = (np.abs(y_true) + np.abs(y_pred)) + eps
        smape_values = 2 * np.abs(y_true - y_pred) / smape_denom
        smape = float(np.mean(smape_values) * 100)
        
        # 8. WAPE (Weighted Absolute Percentage Error)
        wape_denom = np.sum(np.abs(y_true)) + eps
        wape = float(np.sum(np.abs(y_true - y_pred)) / wape_denom * 100) if wape_denom > eps else 0.0
        
        # 9. MASE (Mean Absolute Scaled Error) - requires seasonal naive forecast
        # Here we use lag-1 naive forecast as baseline
        if n_samples > 1:
            mae_naive = np.mean(np.abs(np.diff(y_true)))
            mase = float(mae / (mae_naive + eps)) if mae_naive > eps else 0.0
        else:
            mase = 0.0
        
        # 10. RMSLE (Root Mean Squared Logarithmic Error)
        # Requires positive values
        y_true_safe = np.maximum(y_true, 0)
        y_pred_safe = np.maximum(y_pred, 0)
        rmsle = float(np.sqrt(np.mean((np.log1p(y_true_safe) - np.log1p(y_pred_safe)) ** 2)))
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'adjusted_r2': adjusted_r2,
            'mape': mape,
            'smape': smape,
            'wape': wape,
            'mase': mase,
            'rmsle': rmsle
        }
    
    @staticmethod
    def select_best_model(model_metrics: Dict[str, Dict]) -> Tuple[str, Dict]:
        """
        Select best model based on combined comparison
        
        Priority: R² (higher) > RMSE (lower) > MAE (lower)
        
        Args:
            model_metrics: {model_name: {metric_name: value, ...}, ...}
        
        Returns:
            (best_model_name, best_metrics)
        """
        best_model = None
        best_score = -float('inf')
        
        for model_name, metrics in model_metrics.items():
            # Combined score: weight R² highly, penalize RMSE and MAE
            r2_score = metrics.get('r2', -1)
            rmse = metrics.get('rmse', float('inf'))
            mae = metrics.get('mae', float('inf'))
            
            # Composite score (higher is better)
            score = (r2_score * 1.0) - (rmse * 0.1) - (mae * 0.05)
            
            if score > best_score:
                best_score = score
                best_model = model_name
        
        return best_model, model_metrics[best_model]
