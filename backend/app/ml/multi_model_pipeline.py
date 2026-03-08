"""
Multi-Model ML Pipeline
=======================
ARCHITECTURAL UPGRADE: Replace single RandomForest with multi-model ensemble

This service trains multiple regression models and selects the best OR builds ensemble.

SUPPORTED MODELS:
- Linear Regression
- Random Forest Regressor
- Gradient Boosting Regressor
- Ridge Regression
- Lasso Regression
- XGBoost Regressor (if available)

EVALUATION METRICS:
- R² (R-squared / Coefficient of Determination)
- MAPE (Mean Absolute Percentage Error)
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)

SELECTION STRATEGY:
- Option A: Best single model based on R²
- Option B: Ensemble average of top 3 models
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_percentage_error, mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
import pickle
import json


class MultiModelMLPipeline:
    """
    Multi-model regression pipeline with automatic selection.
    
    ARCHITECTURAL ROLE:
    - Trains multiple ML models in parallel
    - Evaluates each model with comprehensive metrics
    - Selects best model OR builds ensemble
    - Stores all candidate models + metrics for transparency
    
    BOTH LOCAL AND FEDERATED:
    - Local: Hospital trains all models, selects best
    - Federated: All hospitals train same models, share best weights
    """
    
    def __init__(
        self,
        selection_strategy: str = "best",  # "best" or "ensemble"
        ensemble_top_n: int = 3,
        random_state: int = 42
    ):
        """
        Initialize multi-model pipeline.
        
        Args:
            selection_strategy: "best" (select best model) or "ensemble" (average top N)
            ensemble_top_n: Number of top models to ensemble (if strategy="ensemble")
            random_state: Random seed for reproducibility
        """
        self.selection_strategy = selection_strategy
        self.ensemble_top_n = ensemble_top_n
        self.random_state = random_state
        
        # Candidate models
        self.models = {
            "linear": LinearRegression(),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                n_jobs=-1
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=random_state
            ),
            "ridge": Ridge(alpha=1.0, random_state=random_state),
            "lasso": Lasso(alpha=1.0, random_state=random_state),
        }
        
        
        # Storage for trained models and metrics
        self.trained_models = {}
        self.model_metrics = {}
        self.best_model_name = None
        self.ensemble_models = []
        self.feature_names = []
        self.target_name = None
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        test_size: float = 0.2
    ) -> Dict:
        """
        Train all candidate models.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Optional validation features (if None, will split from train)
            y_val: Optional validation target
            test_size: Validation split size (if X_val not provided)
        
        Returns:
            Dict with training results:
            {
                "candidate_models": [...],
                "best_model": "...",
                "ensemble_models": [...],
                "metrics": {...},
                "selection_strategy": "best" | "ensemble"
            }
        """
        # Store feature names
        self.feature_names = list(X_train.columns)
        self.target_name = y_train.name
        
        # Split validation set if not provided
        if X_val is None or y_val is None:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train,
                test_size=test_size,
                random_state=self.random_state
            )
        
        print(f"\n{'='*80}")
        print(f"[MULTI_MODEL_ML] TRAINING PIPELINE")
        print(f"Candidate Models: {len(self.models)}")
        print(f"Model Names: {list(self.models.keys())}")
        print(f"Training Samples: {len(X_train)}, Validation Samples: {len(X_val)}")
        print(f"Features: {len(self.feature_names)}")
        print(f"Selection Strategy: {self.selection_strategy}")
        print(f"{'='*80}\n")
        
        # Train each model
        for model_name, model in self.models.items():
            print(f"Training {model_name}...")
            
            try:
                # Train
                model.fit(X_train, y_train)
                
                # Predict on validation
                y_pred = model.predict(X_val)
                
                # Calculate metrics
                metrics = self._calculate_metrics(y_val, y_pred, model_name)
                
                # Store
                self.trained_models[model_name] = model
                self.model_metrics[model_name] = metrics
                
                print(f"  [OK] {model_name}: R2={metrics['r2']:.4f}, "
                      f"RMSE={metrics['rmse']:.4f}, MAPE={metrics['mape']:.4f}")
            
            except Exception as e:
                print(f"  [FAIL] {model_name} failed: {str(e)}")
                continue
        
        # Select best model or ensemble
        if self.selection_strategy == "best":
            self._select_best_model()
        elif self.selection_strategy == "ensemble":
            self._build_ensemble()
        else:
            raise ValueError(f"Unknown selection strategy: {self.selection_strategy}")
        
        # Build result
        result = {
            "candidate_models": list(self.trained_models.keys()),
            "best_model": self.best_model_name,
            "ensemble_models": self.ensemble_models,
            "metrics": self.model_metrics,
            "selection_strategy": self.selection_strategy,
            "feature_names": self.feature_names,
            "target_name": self.target_name,
        }
        
        print(f"\n{'='*80}")
        print(f"[MULTI_MODEL_ML] TRAINING COMPLETE")
        if self.selection_strategy == "best":
            print(f"Best Model: {self.best_model_name}")
            print(f"R²: {self.model_metrics[self.best_model_name]['r2']:.4f}")
        else:
            print(f"Ensemble: {self.ensemble_models}")
        print(f"{'='*80}\n")
        
        return result
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, model_name: str) -> Dict:
        """Calculate comprehensive regression metrics (all 10 metrics)."""
        from app.ml.metrics_calculator import MetricsCalculator
        
        # Use MetricsCalculator for all 10 metrics
        metrics = MetricsCalculator.calculate_all_metrics(y_true, y_pred, len(self.feature_names))
        
        return metrics
    
    def _select_best_model(self):
        """Select best model based on R²."""
        if not self.model_metrics:
            raise ValueError("No models trained yet")
        
        # Sort by R² (descending)
        sorted_models = sorted(
            self.model_metrics.items(),
            key=lambda x: x[1]["r2"],
            reverse=True
        )
        
        self.best_model_name = sorted_models[0][0]
        print(f"\n[SELECTION] Best model: {self.best_model_name}")
    
    def _build_ensemble(self):
        """Build ensemble from top N models."""
        if not self.model_metrics:
            raise ValueError("No models trained yet")
        
        # Sort by R² (descending)
        sorted_models = sorted(
            self.model_metrics.items(),
            key=lambda x: x[1]["r2"],
            reverse=True
        )
        
        # Take top N
        self.ensemble_models = [
            model_name for model_name, _ in sorted_models[:self.ensemble_top_n]
        ]
        
        print(f"\n[ENSEMBLE] Top {self.ensemble_top_n} models: {self.ensemble_models}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using selected strategy.
        
        Args:
            X: Features for prediction
        
        Returns:
            Predictions array
        """
        if self.selection_strategy == "best":
            if self.best_model_name is None:
                raise ValueError("No best model selected. Call train() first.")
            
            model = self.trained_models[self.best_model_name]
            return model.predict(X)
        
        elif self.selection_strategy == "ensemble":
            if not self.ensemble_models:
                raise ValueError("No ensemble built. Call train() first.")
            
            # Average predictions from ensemble models
            predictions = []
            for model_name in self.ensemble_models:
                model = self.trained_models[model_name]
                pred = model.predict(X)
                predictions.append(pred)
            
            # Average
            ensemble_pred = np.mean(predictions, axis=0)
            return ensemble_pred
        
        else:
            raise ValueError(f"Unknown selection strategy: {self.selection_strategy}")
    
    def get_model_weights(self) -> Dict:
        """
        Get model weights for federated aggregation.
        
        For federated learning, only the selected model's weights are shared.
        
        Returns:
            Dict with serializable weights
        """
        if self.selection_strategy == "best":
            if self.best_model_name is None:
                raise ValueError("No best model selected")
            
            model = self.trained_models[self.best_model_name]
            return self._extract_weights(model, self.best_model_name)
        
        elif self.selection_strategy == "ensemble":
            # For ensemble, share all ensemble model weights
            weights = {}
            for model_name in self.ensemble_models:
                model = self.trained_models[model_name]
                weights[model_name] = self._extract_weights(model, model_name)
            
            return weights
        
        else:
            raise ValueError(f"Unknown selection strategy: {self.selection_strategy}")
    
    def _extract_weights(self, model, model_name: str) -> Dict:
        """Extract weights from sklearn model."""
        weights = {"model_type": model_name}
        
        if hasattr(model, "coef_"):
            weights["coef"] = model.coef_.tolist()
        
        if hasattr(model, "intercept_"):
            weights["intercept"] = float(model.intercept_) if np.isscalar(model.intercept_) else model.intercept_.tolist()
        
        if hasattr(model, "feature_importances_"):
            weights["feature_importances"] = model.feature_importances_.tolist()
        
        # For tree-based models, store params instead of full tree structure
        if model_name in ["random_forest", "gradient_boosting", "xgboost"]:
            weights["n_estimators"] = getattr(model, "n_estimators", None)
            weights["max_depth"] = getattr(model, "max_depth", None)
        
        return weights
    
    def save_models(self, directory: str) -> Dict[str, str]:
        """
        Save all trained models to directory.
        
        Args:
            directory: Directory to save models
        
        Returns:
            Dict mapping model names to file paths
        """
        import os
        os.makedirs(directory, exist_ok=True)
        
        saved_paths = {}
        
        for model_name, model in self.trained_models.items():
            file_path = os.path.join(directory, f"{model_name}.pkl")
            
            with open(file_path, 'wb') as f:
                pickle.dump(model, f)
            
            saved_paths[model_name] = file_path
        
        # Save metadata
        metadata_path = os.path.join(directory, "pipeline_metadata.json")
        metadata = {
            "selection_strategy": self.selection_strategy,
            "best_model": self.best_model_name,
            "ensemble_models": self.ensemble_models,
            "metrics": self.model_metrics,
            "feature_names": self.feature_names,
            "target_name": self.target_name,
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        saved_paths["metadata"] = metadata_path
        
        return saved_paths
    
    def load_models(self, directory: str):
        """
        Load all trained models from directory.
        
        Args:
            directory: Directory with saved models
        """
        import os
        
        # Load metadata
        metadata_path = os.path.join(directory, "pipeline_metadata.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.selection_strategy = metadata["selection_strategy"]
        self.best_model_name = metadata["best_model"]
        self.ensemble_models = metadata["ensemble_models"]
        self.model_metrics = metadata["metrics"]
        self.feature_names = metadata["feature_names"]
        self.target_name = metadata["target_name"]
        
        # Load models
        self.trained_models = {}
        
        for model_name in metadata["metrics"].keys():
            file_path = os.path.join(directory, f"{model_name}.pkl")
            
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    model = pickle.load(f)
                
                self.trained_models[model_name] = model
