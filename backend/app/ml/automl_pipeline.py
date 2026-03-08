"""
AutoML Pipeline

Orchestrates automated model training with hyperparameter tuning
"""
import time
import numpy as np
import pandas as pd
import pickle
import os
from typing import Dict, Tuple, Any, Optional
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from app.ml.data_processor import DataProcessor
from app.ml.metrics_calculator import MetricsCalculator
from app.ml.hyperparameter_search import HyperparameterSpaces
from app.ml.model_leaderboard import ModelLeaderboard, ModelResult


class AutoMLPipeline:
    """
    Automated Machine Learning pipeline
    
    Orchestrates entire AutoML process:
    1. Data preprocessing
    2. Hyperparameter tuning
    3. Model training
    4. Evaluation
    5. Best model selection
    """
    
    def __init__(self, random_state: int = 42, cv_folds: int = 3, n_iter_search: int = 10):
        """
        Initialize AutoML pipeline
        
        Args:
            random_state: Random seed
            cv_folds: Cross-validation folds for GridSearchCV/RandomizedSearchCV
            n_iter_search: Number of iterations for RandomizedSearchCV
        """
        self.random_state = random_state
        self.cv_folds = cv_folds
        self.n_iter_search = n_iter_search
        
        self.data_processor = DataProcessor()
        self.leaderboard = ModelLeaderboard()
        self.trained_models = {}  # {model_name: best_estimator}
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
    
    # ==================== DATA PIPELINE ====================
    
    def ingest_dataset(self, file_path: str, target_column: str) -> None:
        """
        Ingest dataset from CSV
        
        Args:
            file_path: Path to CSV file
            target_column: Target column name
        """
        df = pd.read_csv(file_path)
        self.data_processor.validate_data(df, target_column)
        print(f"[AutoML] Ingested dataset with shape: {df.shape}")
    
    def preprocess_data(self, df: pd.DataFrame, target_column: str, test_size: float = 0.2) -> None:
        """
        Preprocess data and split into train/test
        
        Args:
            df: Input dataframe
            target_column: Target column name
            test_size: Test set fraction
        """
        print(f"\n[AutoML] DATA PREPROCESSING")
        print("="*80)
        
        # Fit preprocessor
        X, y = self.data_processor.fit_preprocess(df, target_column)
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state
        )
        
        # Print info
        feature_info = self.data_processor.get_feature_info()
        print(f"Numerical features: {feature_info['num_numerical']}")
        print(f"Categorical features: {feature_info['num_categorical']}")
        print(f"Training samples: {len(self.X_train)}")
        print(f"Test samples: {len(self.X_test)}")
        print(f"Target variance: {self.y_train.var():.4f}")
        print("="*80 + "\n")
    
    # ==================== MODEL TRAINING ====================
    
    def _create_models(self) -> Dict[str, Any]:
        """
        Create candidate models
        
        Returns:
            Dict of model_name: model_instance
        """
        return {
            'linear': LinearRegression(),
            'ridge': Ridge(),
            'lasso': Lasso(),
            'random_forest': RandomForestRegressor(random_state=self.random_state),
            'gradient_boosting': GradientBoostingRegressor(random_state=self.random_state),
        }
    
    def _tune_hyperparameters(self, model_name: str, model: Any, X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[Any, Dict[str, Any]]:
        """
        Tune hyperparameters for a model
        
        Args:
            model_name: Name of model
            model: Model instance
            X_train: Training features
            y_train: Training target
        
        Returns:
            Tuple of (best_estimator, best_params)
        """
        space = HyperparameterSpaces.get_space(model_name)
        
        print(f"  [{model_name}] Searching hyperparameters...")
        
        search = RandomizedSearchCV(
            model,
            space,
            n_iter=self.n_iter_search,
            cv=self.cv_folds,
            scoring='r2',
            random_state=self.random_state,
            n_jobs=-1,
            verbose=0
        )
        
        search.fit(X_train, y_train)
        
        print(f"  [{model_name}] Best R² score: {search.best_score_:.4f}")
        
        return search.best_estimator_, search.best_params_
    
    def train_all_models(self) -> None:
        """
        Train all candidate models with hyperparameter tuning
        """
        if self.X_train is None:
            raise RuntimeError("Must call preprocess_data() first")
        
        print(f"\n[AutoML] TRAINING & HYPERPARAMETER TUNING")
        print("="*80)
        print(f"Using RandomizedSearchCV with {self.n_iter_search} iterations and {self.cv_folds}-fold CV")
        print("="*80 + "\n")
        
        models = self._create_models()
        
        for model_name, model in models.items():
            print(f"Training {model_name}...")
            
            start_time = time.time()
            
            try:
                # Tune hyperparameters
                best_estimator, best_params = self._tune_hyperparameters(
                    model_name, model, self.X_train, self.y_train
                )
                
                # Make predictions on test set
                y_pred = best_estimator.predict(self.X_test)
                
                # Calculate metrics
                metrics = MetricsCalculator.calculate_all_metrics(
                    self.y_test.values,
                    y_pred,
                    num_features=self.X_train.shape[1]
                )
                
                elapsed = time.time() - start_time
                
                # Create result
                result = ModelResult(
                    model_name=model_name,
                    best_hyperparameters=best_params,
                    mae=metrics['mae'],
                    mse=metrics['mse'],
                    rmse=metrics['rmse'],
                    r2=metrics['r2'],
                    adjusted_r2=metrics['adjusted_r2'],
                    mape=metrics['mape'],
                    smape=metrics['smape'],
                    wape=metrics['wape'],
                    mase=metrics['mase'],
                    rmsle=metrics['rmsle'],
                    training_time=elapsed
                )
                
                # Store results
                self.leaderboard.add_result(result)
                self.trained_models[model_name] = best_estimator
                
                print(f"  [{model_name}] ✓ R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}, Time={elapsed:.2f}s\n")
                
            except Exception as e:
                print(f"  [{model_name}] ✗ Training failed: {str(e)}\n")
                continue
        
        print("="*80 + "\n")
    
    # ==================== EVALUATION ====================
    
    def get_leaderboard(self) -> pd.DataFrame:
        """
        Get leaderboard of all trained models
        
        Returns:
            DataFrame with model results sorted by score
        """
        return self.leaderboard.get_leaderboard()
    
    def get_best_model_info(self) -> Dict[str, Any]:
        """
        Get best model information
        
        Returns:
            Dict with model name, params, and metrics
        """
        return self.leaderboard.get_best_model_info()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get training summary
        
        Returns:
            Summary statistics
        """
        return self.leaderboard.get_summary()
    
    # ==================== MODEL SAVING ====================
    
    def save_best_model(self, save_path: str) -> str:
        """
        Save best trained model to disk
        
        Args:
            save_path: Directory to save model
        
        Returns:
            Full path to saved model
        """
        if not self.leaderboard.best_model:
            raise RuntimeError("No model trained yet")
        
        best_model_name = self.leaderboard.best_model.model_name
        best_estimator = self.trained_models[best_model_name]
        
        # Create directory if not exists
        os.makedirs(save_path, exist_ok=True)
        
        # Save model
        model_file = os.path.join(save_path, f'best_automl_model_{best_model_name}.pkl')
        
        with open(model_file, 'wb') as f:
            pickle.dump(best_estimator, f)
        
        print(f"[AutoML] Best model saved to: {model_file}")
        
        return model_file
    
    def save_all_models(self, save_path: str) -> Dict[str, str]:
        """
        Save all trained models
        
        Args:
            save_path: Directory to save models
        
        Returns:
            Dict of model_name: file_path
        """
        os.makedirs(save_path, exist_ok=True)
        
        saved_models = {}
        for model_name, estimator in self.trained_models.items():
            model_file = os.path.join(save_path, f'automl_{model_name}.pkl')
            
            with open(model_file, 'wb') as f:
                pickle.dump(estimator, f)
            
            saved_models[model_name] = model_file
        
        print(f"[AutoML] All models saved to: {save_path}")
        
        return saved_models
    
    # ==================== RESULTS EXPORT ====================
    
    def get_results_dict(self) -> Dict[str, Any]:
        """
        Get all AutoML results as dictionary
        
        Returns:
            Complete results dict
        """
        return {
            'best_model': self.leaderboard.get_best_model_info(),
            'leaderboard': self.leaderboard.get_leaderboard_dict(),
            'summary': self.leaderboard.get_summary(),
            'preprocessing': self.data_processor.get_feature_info()
        }
    
    # ==================== END-TO-END PIPELINE ====================
    
    def run(self, df: pd.DataFrame, target_column: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete AutoML pipeline
        
        Args:
            df: Input dataframe
            target_column: Target column name
            save_path: Optional path to save models
        
        Returns:
            Results dictionary
        """
        print("\n" + "="*80)
        print("AUTOML PIPELINE STARTED")
        print("="*80 + "\n")
        
        # Step 1: Preprocess
        self.preprocess_data(df, target_column)
        
        # Step 2: Train all models
        self.train_all_models()
        
        # Step 3: Save models if path provided
        if save_path:
            self.save_best_model(save_path)
        
        # Step 4: Get results
        results = self.get_results_dict()
        
        print("="*80)
        print("AUTOML PIPELINE COMPLETE")
        print("="*80)
        print(f"\nBest Model: {results['best_model']['model_name']}")
        print(f"Best R²: {results['best_model']['metrics']['r2']:.4f}")
        print(f"Best RMSE: {results['best_model']['metrics']['rmse']:.4f}")
        print(f"Best MAE: {results['best_model']['metrics']['mae']:.4f}\n")
        
        return results
