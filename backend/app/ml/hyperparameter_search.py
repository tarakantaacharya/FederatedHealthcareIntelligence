"""
Hyperparameter search spaces for regression models

Defines search spaces for RandomizedSearchCV/Optuna tuning
"""
from typing import Dict, Any


class HyperparameterSpaces:
    """
    Predefined hyperparameter search spaces for each model
    """
    
    @staticmethod
    def linear_regression() -> Dict[str, Any]:
        """Linear Regression hyperparameters"""
        return {
            'fit_intercept': [True, False],
            'positive': [True, False]
        }
    
    @staticmethod
    def ridge_regression() -> Dict[str, Any]:
        """Ridge Regression hyperparameters"""
        return {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
            'fit_intercept': [True, False],
            'solver': ['auto', 'svd', 'cholesky', 'lsqr', 'saga']
        }
    
    @staticmethod
    def lasso_regression() -> Dict[str, Any]:
        """Lasso Regression hyperparameters"""
        return {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
            'fit_intercept': [True, False],
            'max_iter': [1000, 5000, 10000],
            'warm_start': [True, False]
        }
    
    @staticmethod
    def random_forest() -> Dict[str, Any]:
        """Random Forest Regressor hyperparameters"""
        return {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None],
            'bootstrap': [True, False],
            'criterion': ['squared_error', 'absolute_error', 'poisson']
        }
    
    @staticmethod
    def gradient_boosting() -> Dict[str, Any]:
        """Gradient Boosting Regressor hyperparameters"""
        return {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.001, 0.01, 0.05, 0.1],
            'max_depth': [3, 5, 7, 10],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'subsample': [0.6, 0.8, 1.0],
            'loss': ['squared_error', 'absolute_error', 'huber']
        }
    
    @staticmethod
    def get_all_spaces() -> Dict[str, Dict[str, Any]]:
        """Get all hyperparameter spaces"""
        return {
            'linear': HyperparameterSpaces.linear_regression(),
            'ridge': HyperparameterSpaces.ridge_regression(),
            'lasso': HyperparameterSpaces.lasso_regression(),
            'random_forest': HyperparameterSpaces.random_forest(),
            'gradient_boosting': HyperparameterSpaces.gradient_boosting(),
        }
    
    @staticmethod
    def get_space(model_name: str) -> Dict[str, Any]:
        """Get hyperparameter space for specific model"""
        spaces = HyperparameterSpaces.get_all_spaces()
        if model_name not in spaces:
            raise ValueError(f"Unknown model: {model_name}")
        return spaces[model_name]
