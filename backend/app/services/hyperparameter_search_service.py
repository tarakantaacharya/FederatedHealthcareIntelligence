"""
Hyperparameter Search Service (Phase 35)
Privacy-preserving federated hyperparameter tuning
"""
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class HyperparameterSearchService:
    """Service for federated hyperparameter optimization"""
    
    # Default search spaces for different models
    PARAM_GRIDS = {
        'random_forest': {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        },
        'xgboost': {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 10],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0]
        }
    }
    
    @staticmethod
    def local_hyperparameter_search(
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = 'random_forest',
        search_type: str = 'grid',
        cv_folds: int = 5,
        n_iter: int = 20
    ) -> Tuple[Dict, float]:
        """
        Perform local hyperparameter search
        
        Args:
            X_train: Training features
            y_train: Training targets
            model_type: Model type ('random_forest', 'xgboost')
            search_type: 'grid' or 'random'
            cv_folds: Number of cross-validation folds
            n_iter: Number of iterations for random search
        
        Returns:
            Tuple of (best_params, best_score)
        """
        logger.info(f"Starting {search_type} search for {model_type}")
        
        # Get base model and param grid
        if model_type == 'random_forest':
            base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
            param_grid = HyperparameterSearchService.PARAM_GRIDS['random_forest']
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Perform search
        if search_type == 'grid':
            search = GridSearchCV(
                base_model,
                param_grid,
                cv=cv_folds,
                scoring='neg_mean_squared_error',
                n_jobs=-1,
                verbose=1
            )
        else:  # random
            search = RandomizedSearchCV(
                base_model,
                param_grid,
                n_iter=n_iter,
                cv=cv_folds,
                scoring='neg_mean_squared_error',
                n_jobs=-1,
                random_state=42,
                verbose=1
            )
        
        search.fit(X_train, y_train)
        
        best_params = search.best_params_
        best_score = -search.best_score_  # Convert back from negative MSE
        
        logger.info(f"Best params: {best_params}, Best MSE: {best_score:.4f}")
        
        return best_params, best_score
    
    @staticmethod
    def add_differential_privacy_to_metrics(
        metrics: Dict[str, float],
        epsilon: float = 0.5,
        sensitivity: float = 1.0
    ) -> Dict[str, float]:
        """
        Add Laplace noise to metrics for privacy
        
        Args:
            metrics: Dictionary of metric values
            epsilon: Privacy budget
            sensitivity: Sensitivity of the metric
        
        Returns:
            Noisy metrics dictionary
        """
        scale = sensitivity / epsilon
        
        noisy_metrics = {}
        for key, value in metrics.items():
            noise = np.random.laplace(0, scale)
            noisy_metrics[key] = float(value + noise)
        
        logger.info(f"Applied DP noise (ε={epsilon}) to metrics")
        return noisy_metrics
    
    @staticmethod
    def aggregate_hyperparameter_votes(
        hospital_results: List[Dict[str, any]]
    ) -> Dict:
        """
        Aggregate hyperparameter preferences across hospitals
        
        Args:
            hospital_results: List of dicts with 'params' and 'score' from each hospital
        
        Returns:
            Consensus hyperparameters
        """
        if not hospital_results:
            return {}
        
        # For each hyperparameter, use majority vote or weighted average
        all_params = {}
        
        for result in hospital_results:
            params = result['params']
            score = result.get('score', 1.0)
            
            for param_name, param_value in params.items():
                if param_name not in all_params:
                    all_params[param_name] = []
                
                all_params[param_name].append((param_value, score))
        
        # Aggregate
        consensus_params = {}
        for param_name, values in all_params.items():
            # For numeric parameters, use weighted average
            # For categorical, use mode
            first_val = values[0][0]
            
            if isinstance(first_val, (int, float)):
                # Weighted average
                weights = np.array([score for _, score in values])
                weights = weights / weights.sum()
                vals = np.array([val for val, _ in values])
                consensus_params[param_name] = float(np.average(vals, weights=weights))
            else:
                # Mode (most common value)
                from collections import Counter
                val_counts = Counter([val for val, _ in values])
                consensus_params[param_name] = val_counts.most_common(1)[0][0]
        
        logger.info(f"Consensus hyperparameters: {consensus_params}")
        return consensus_params
