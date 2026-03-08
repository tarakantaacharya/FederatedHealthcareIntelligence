"""
Phase 5: API Response Validation  Utilities
Ensures all API responses have valid metric values (no NULL, NaN, or undefined)
"""
from typing import Dict, Any, Optional


def coalesce_metric(value: Optional[float], default: float = 0.0) -> float:
    """
    Coalesce a metric value to ensure it's never None/NaN.
    
    Args:
        value: The metric value (possibly None or NaN)
        default: Default value to use if value is invalid
        
    Returns:
        Valid float value (never None or NaN)
    """
    if value is None:
        return default
    
    # Convert to float
    try:
        float_val = float(value)
    except (TypeError, ValueError):
        return default
    
    # Check for NaN/inf
    if not isinstance(float_val, (int, float)) or float_val != float_val or float_val == float('inf') or float_val == float('-inf'):
        return default
    
    return float_val


def validate_metrics_dict(metrics: Dict[str, Any], metric_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    Validate and clean a metrics dictionary, ensuring all numeric values are valid.
    
    Args:
        metrics: Dictionary of metrics
        metric_keys: List of keys to validate (if None, validates all numeric values)
        
    Returns:
        Clean dictionary with all valid metrics
    """
    if not metrics:
        return {}
    
    clean_metrics = {}
    keys_to_check = metric_keys if metric_keys else list(metrics.keys())
    
    for key in keys_to_check:
        if key not in metrics:
            # Key doesn't exist, set default
            clean_metrics[key] = 0.0
            continue
        
        value = metrics[key]
        
        # Handle nested dicts recursively
        if isinstance(value, dict):
            clean_metrics[key] = validate_metrics_dict(value)
            continue
        
        # Handle lists
        if isinstance(value, list):
            clean_metrics[key] = [coalesce_metric(v) if isinstance(v, (int, float)) else v for v in value]
            continue
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            clean_metrics[key] = coalesce_metric(value)
        else:
            # Non-numeric, pass through
            clean_metrics[key] = value
    
    return clean_metrics


def validate_model_weights_response(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate ModelWeights response ensuring all metrics are populated.
    
    Args:
        model_data: ModelWeights dict from database query
        
    Returns:
        Clean model data with all metrics validated
    """
    metric_fields = [
        'local_loss', 'local_accuracy', 'local_mape', 'local_rmse', 'local_r2',
        'local_mae', 'local_mse', 'local_adjusted_r2', 'local_smape',
        'local_wape', 'local_mase', 'local_rmsle',
        'epsilon_spent', 'delta', 'clip_norm', 'noise_multiplier'
    ]
    
    for field in metric_fields:
        if field in model_data:
            model_data[field] = coalesce_metric(model_data.get(field))
    
    return model_data


def validate_training_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate training response ensuring all metrics are populated.
    
    Args:
        response: Training response dict
        
    Returns:
        Clean response with all metrics validated
    """
    metric_fields = [
        'mae', 'mse', 'rmse', 'r2', 'adjusted_r2', 'mape', 'smape',
        'wape', 'mase', 'rmsle', 'train_loss', 'epsilon_spent'
    ]
    
    # Validate top-level metrics
    for field in metric_fields:
        if field in response:
            response[field] = coalesce_metric(response.get(field))
    
    # Validate nested metrics dict
    if 'metrics' in response and isinstance(response['metrics'], dict):
        response['metrics'] = validate_metrics_dict(response['metrics'])
    
    # Validate all_model_metrics
    if 'all_model_metrics' in response and isinstance(response['all_model_metrics'], dict):
        for model_name, model_metrics in response['all_model_metrics'].items():
            if isinstance(model_metrics, dict):
                response['all_model_metrics'][model_name] = validate_metrics_dict(model_metrics)
    
    return response


def validate_round_statistics(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate round statistics response.
    
    Args:
        stats: Round statistics dict
        
    Returns:
        Clean stats with all metrics validated
    """
    metric_fields = [
        'avg_loss', 'avg_accuracy', 'avg_mape', 'avg_rmse', 'avg_r2',
        'avg_mae', 'avg_mse', 'avg_epsilon', 'duration_hours'
    ]
    
    for field in metric_fields:
        if field in stats:
            stats[field] = coalesce_metric(stats.get(field))
    
    # Validate hospital contributions
    if 'hospital_contributions' in stats and isinstance(stats['hospital_contributions'], list):
        for contrib in stats['hospital_contributions']:
            if isinstance(contrib, dict):
                for key in ['local_loss', 'local_accuracy', 'local_mape', 'local_rmse', 'local_r2',
                           'local_mae', 'local_mse', 'epsilon_spent']:
                    if key in contrib:
                        contrib[key] = coalesce_metric(contrib.get(key))
    
    return stats
