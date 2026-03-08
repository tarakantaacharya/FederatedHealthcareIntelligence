"""
Multi-model training pipeline
Trains 5 candidates (linear, random_forest, gradient_boosting, ridge, lasso)
Automatically selects best model based on comprehensive metrics
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from typing import Dict, Tuple
from datetime import datetime
from app.ml.metrics_calculator import MetricsCalculator


class MultiModelTrainer:
    """Train multiple candidate models and select best"""
    
    CANDIDATE_MODELS = {
        'linear': LinearRegression,
        'random_forest': RandomForestRegressor,
        'gradient_boosting': GradientBoostingRegressor,
        'ridge': Ridge,
        'lasso': Lasso,
    }
    
    def __init__(self, target_column: str = 'bed_occupancy'):
        self.target_column = target_column
        self.feature_columns = None
        self.scaler = StandardScaler()
        self.models = {}
        self.metrics = {}
        self.best_model_name = None
        self.best_model = None
        self.best_metrics = None
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature engineer dataset (lag features, time features)"""
        df = df.copy()
        
        # Parse timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day'] = df['timestamp'].dt.day
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['year'] = df['timestamp'].dt.year
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Lag features
        if self.target_column in df.columns:
            for lag in [1, 2, 3, 7]:
                df[f'{self.target_column}_lag_{lag}'] = df[self.target_column].shift(lag)
        
        df = df.dropna()
        return df
    
    def train_all_models(self, df: pd.DataFrame, test_size: float = 0.2) -> Dict:
        """
        Train all candidate models and compute metrics
        
        Returns:
            Dictionary with training results and metadata
        """
        # Prepare data
        df = self.prepare_data(df)
        
        if self.target_column not in df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found")
        
        # Select features
        exclude_cols = [self.target_column, 'timestamp']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        X = df[self.feature_columns].astype(np.float64)
        y = df[self.target_column].astype(np.float64)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train each model
        for model_name, model_class in self.CANDIDATE_MODELS.items():
            try:
                # Initialize model with reasonable hyperparameters
                if model_name == 'linear':
                    model = model_class()
                elif model_name == 'random_forest':
                    model = model_class(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
                elif model_name == 'gradient_boosting':
                    model = model_class(n_estimators=100, max_depth=5, random_state=42)
                elif model_name == 'ridge':
                    model = model_class(alpha=1.0)
                elif model_name == 'lasso':
                    model = model_class(alpha=0.1)
                
                # Train
                model.fit(X_train_scaled, y_train)
                
                # Predict
                y_pred_test = model.predict(X_test_scaled)
                
                # Compute all metrics
                metrics = MetricsCalculator.calculate_all_metrics(
                    y_test, y_pred_test, num_features=len(self.feature_columns)
                )
                
                self.models[model_name] = model
                self.metrics[model_name] = metrics
                
            except Exception as e:
                print(f"[WARNING] {model_name} training failed: {e}")
        
        # Select best model
        if self.metrics:
            self.best_model_name, self.best_metrics = MetricsCalculator.select_best_model(self.metrics)
            self.best_model = self.models[self.best_model_name]
        else:
            raise RuntimeError("No models trained successfully")
        
        return {
            'status': 'success',
            'best_model': self.best_model_name,
            'best_metrics': self.best_metrics,
            'all_model_metrics': self.metrics,
            'num_models_trained': len(self.models),
            'num_features': len(self.feature_columns),
            'num_samples': len(df),
            'training_timestamp': datetime.now().isoformat()
        }
    
    def save_model(self, path: str):
        """Save best model to disk"""
        joblib.dump(self.best_model, path)
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict using best model"""
        if self.best_model is None:
            raise ValueError("No model trained yet")
        
        df = self.prepare_data(df)
        X = df[self.feature_columns].astype(np.float64)
        X_scaled = self.scaler.transform(X)
        return self.best_model.predict(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from best model (if available)"""
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            return dict(zip(self.feature_columns, importances.tolist()))
        elif hasattr(self.best_model, 'coef_'):
            coefs = np.abs(self.best_model.coef_)
            return dict(zip(self.feature_columns, coefs.tolist()))
        else:
            return {}
