"""
Baseline sklearn model for hospital resource forecasting
Simple regression model as foundation before TFT (Phase 15)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import json
from typing import Dict, Tuple
from datetime import datetime


class BaselineForecaster:
    """
    Baseline forecasting model using Random Forest
    Predicts future hospital resource demand
    """
    
    def __init__(self, target_column: str = 'bed_occupancy'):
        """
        Initialize baseline model
        
        Args:
            target_column: Column name to predict
        """
        self.target_column = target_column
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering for time series data
        
        Args:
            df: Raw dataframe with timestamp column
        
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Parse timestamp if exists
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day'] = df['timestamp'].dt.day
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['year'] = df['timestamp'].dt.year
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Create lag features for target variable
        if self.target_column in df.columns:
            for lag in [1, 2, 3, 7]:  # Previous 1, 2, 3, 7 time periods
                df[f'{self.target_column}_lag_{lag}'] = df[self.target_column].shift(lag)
        
        # Drop NaN rows created by lag features
        df = df.dropna()
        
        return df
    
    def train(
        self, 
        df: pd.DataFrame, 
        test_size: float = 0.2
    ) -> Dict:
        """
        Train the baseline model
        
        Args:
            df: Training dataframe
            test_size: Fraction of data for testing
        
        Returns:
            Dictionary with training metrics
        """
        # Feature engineering
        df = self.prepare_features(df)
        
        # Check if target column exists
        if self.target_column not in df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in dataset")
        
        # Select feature columns (exclude target and timestamp)
        exclude_cols = [self.target_column, 'timestamp']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        # Prepare X and y
        X = df[self.feature_columns]
        y = df[self.target_column]
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False  # Time series: no shuffle
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        metrics = {
            'train_mse': float(mean_squared_error(y_train, y_pred_train)),
            'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
            'train_r2': float(r2_score(y_train, y_pred_train)),
            'test_mse': float(mean_squared_error(y_test, y_pred_test)),
            'test_mae': float(mean_absolute_error(y_test, y_pred_test)),
            'test_r2': float(r2_score(y_test, y_pred_test)),
            'num_features': len(self.feature_columns),
            'num_samples': len(df),
            'target_column': self.target_column,
            'trained_at': datetime.now().isoformat()
        }
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            df: DataFrame with same features as training data
        
        Returns:
            Array of predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Feature engineering
        df = self.prepare_features(df)
        
        # Ensure all feature columns exist
        X = df[self.feature_columns]
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def get_model_weights(self) -> Dict:
        """
        Extract model weights for federated learning
        
        Returns:
            Dictionary containing serialized model components
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before extracting weights")
        
        # For Random Forest, we extract tree structures
        # In real federated learning, you'd use more sophisticated weight extraction
        weights = {
            'model_params': {
                'n_estimators': self.model.n_estimators,
                'max_depth': self.model.max_depth,
                'feature_importances': self.model.feature_importances_.tolist(),
            },
            'scaler_mean': self.scaler.mean_.tolist(),
            'scaler_scale': self.scaler.scale_.tolist(),
            'feature_columns': self.feature_columns,
            'target_column': self.target_column
        }
        
        return weights
    
    def save_model(self, filepath: str) -> None:
        """
        Save complete model to disk
        
        Args:
            filepath: Path to save model file
        """
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
    
    @staticmethod
    def load_model(filepath: str) -> 'BaselineForecaster':
        """
        Load model from disk
        
        Args:
            filepath: Path to model file
        
        Returns:
            Loaded BaselineForecaster instance
        """
        model_data = joblib.load(filepath)
        
        forecaster = BaselineForecaster(target_column=model_data['target_column'])
        forecaster.model = model_data['model']
        forecaster.scaler = model_data['scaler']
        forecaster.feature_columns = model_data['feature_columns']
        forecaster.is_trained = model_data['is_trained']
        
        return forecaster
