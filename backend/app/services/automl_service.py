"""
AutoML Service

Orchestrates AutoML training and manages results
"""
import os
import json
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.dataset import Dataset
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.ml.automl_pipeline import AutoMLPipeline
from app.config import get_settings


class AutoMLService:
    """Service for AutoML operations"""
    
    @staticmethod
    def run_automl_training(
        db: Session,
        hospital: Hospital,
        dataset_id: int,
        target_column: str,
        training_type: str = "LOCAL"
    ) -> dict:
        """
        Run AutoML pipeline on hospital dataset
        
        Args:
            db: Database session
            hospital: Hospital object
            dataset_id: Dataset ID
            target_column: Target column name
            training_type: LOCAL or FEDERATED
        
        Returns:
            Results dict with best model info and leaderboard
        """
        # Verify dataset ownership
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.hospital_id == hospital.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied"
            )
        
        # Validate target column exists
        try:
            df = pd.read_csv(dataset.file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load dataset: {str(e)}"
            )
        
        if target_column not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target_column}' not found in dataset"
            )
        
        # Initialize AutoML pipeline
        automl = AutoMLPipeline(
            random_state=42,
            cv_folds=3,
            n_iter_search=10
        )
        
        # Run AutoML
        try:
            results = automl.run(
                df=df,
                target_column=target_column,
                save_path=os.path.join(get_settings().MODEL_DIR, hospital.hospital_id)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AutoML training failed: {str(e)}"
            )
        
        # Extract best model info
        best_model_info = results['best_model']
        best_model_name = best_model_info['model_name']
        
        # Save best model to database
        model_path = os.path.join(
            get_settings().MODEL_DIR,
            hospital.hospital_id,
            f'best_automl_model_{best_model_name}.pkl'
        )
        
        # Prepare training schema with full AutoML results
        training_schema = {
            'automl_results': results,
            'training_type': training_type,
            'model_architecture': 'ML_REGRESSION',
            'dataset_type': dataset.dataset_type or 'TABULAR',
            'target_column': target_column,
            'best_model': best_model_name,
            'candidate_models': [m['model_name'] for m in results['leaderboard']],
            'all_model_metrics': {
                m['model_name']: {k: v for k, v in m.items() if k not in ['model_name', 'best_hyperparameters', 'training_time']}
                for m in results['leaderboard']
            },
            'best_hyperparameters': best_model_info['best_hyperparameters'],
            'feature_info': results['preprocessing'],
            'automl_timestamp': datetime.utcnow().isoformat()
        }
        
        # Check if model already exists
        existing_model = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital.id,
            ModelWeights.dataset_id == dataset_id,
            ModelWeights.model_architecture == 'ML_REGRESSION'
        ).first()
        
        best_metrics = best_model_info['metrics']
        
        if existing_model:
            # Update existing model
            existing_model.model_path = model_path
            existing_model.model_type = f'automl_{best_model_name}'
            existing_model.training_type = training_type
            existing_model.local_mae = best_metrics['mae']
            existing_model.local_mse = best_metrics['mse']
            existing_model.local_rmse = best_metrics['rmse']
            existing_model.local_r2 = best_metrics['r2']
            existing_model.local_adjusted_r2 = best_metrics['adjusted_r2']
            existing_model.local_mape = best_metrics['mape']
            existing_model.local_smape = best_metrics['smape']
            existing_model.local_wape = best_metrics['wape']
            existing_model.local_mase = best_metrics['mase']
            existing_model.local_rmsle = best_metrics['rmsle']
            existing_model.training_schema = training_schema
            db.flush()
        else:
            # Create new model record
            model_weights = ModelWeights(
                hospital_id=hospital.id,
                dataset_id=dataset_id,
                model_path=model_path,
                model_type=f'automl_{best_model_name}',
                training_type=training_type,
                model_architecture='ML_REGRESSION',
                local_mae=best_metrics['mae'],
                local_mse=best_metrics['mse'],
                local_rmse=best_metrics['rmse'],
                local_r2=best_metrics['r2'],
                local_adjusted_r2=best_metrics['adjusted_r2'],
                local_mape=best_metrics['mape'],
                local_smape=best_metrics['smape'],
                local_wape=best_metrics['wape'],
                local_mase=best_metrics['mase'],
                local_rmsle=best_metrics['rmsle'],
                training_schema=training_schema,
                is_global=False,
                is_uploaded=False,
                is_mask_uploaded=False
            )
            db.add(model_weights)
            db.flush()
        
        db.commit()
        
        # Return response with all 10 metrics
        return {
            'model_id': existing_model.id if existing_model else model_weights.id,
            'dataset_id': dataset_id,
            'training_type': training_type,
            'automl_enabled': True,
            'best_model': best_model_name,
            'candidate_models': [m['model_name'] for m in results['leaderboard']],
            'leaderboard': results['leaderboard'],
            'metrics': best_metrics,
            'mae': best_metrics['mae'],
            'mse': best_metrics['mse'],
            'rmse': best_metrics['rmse'],
            'r2': best_metrics['r2'],
            'adjusted_r2': best_metrics['adjusted_r2'],
            'mape': best_metrics['mape'],
            'smape': best_metrics['smape'],
            'wape': best_metrics['wape'],
            'mase': best_metrics['mase'],
            'rmsle': best_metrics['rmsle'],
            'best_hyperparameters': best_model_info['best_hyperparameters'],
            'status': 'AUTOML_COMPLETE',
            'summary': results['summary']
        }
    
    @staticmethod
    def get_leaderboard(
        db: Session,
        hospital_id: int,
        dataset_id: int
    ) -> dict:
        """
        Get AutoML leaderboard for dataset
        
        Args:
            db: Database session
            hospital_id: Hospital ID
            dataset_id: Dataset ID
        
        Returns:
            Leaderboard data
        """
        model = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital_id,
            ModelWeights.dataset_id == dataset_id,
            ModelWeights.model_architecture == 'ML_REGRESSION',
            ModelWeights.training_schema.contains('automl_results')
        ).first()
        
        if not model or not model.training_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No AutoML results found for this dataset"
            )
        
        automl_results = model.training_schema.get('automl_results', {})
        
        return {
            'dataset_id': dataset_id,
            'best_model': automl_results.get('best_model', {}),
            'leaderboard': automl_results.get('leaderboard', []),
            'summary': automl_results.get('summary', {}),
            'preprocessing': automl_results.get('preprocessing', {}),
            'timestamp': model.updated_at.isoformat() if model.updated_at else None
        }
