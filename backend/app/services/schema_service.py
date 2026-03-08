"""
Schema Validation and Feature Alignment Service
Handles dynamic schema matching for TFT inference
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.model_weights import ModelWeights
from app.models.dataset import Dataset
from app.models.training_rounds import TrainingRound


class SchemaService:
    """
    Service for validating and aligning dataset schemas with trained models.
    Handles variable column counts for TFT inference.
    """
    
    @staticmethod
    def validate_schema(
        model_id: int,
        dataset_id: int,
        db: Session
    ) -> Dict:
        """
        Validate if dataset schema matches model training schema.
        
        Args:
            model_id: Model weights ID
            dataset_id: Dataset ID to validate
            db: Database session
            
        Returns:
            {
                "schema_match": bool,
                "missing_columns": List[str],
                "extra_columns": List[str],
                "warnings": List[str],
                "can_auto_align": bool,
                "model_schema": Dict,
                "dataset_schema": Dict
            }
        """
        # Get model and training schema
        model = db.query(ModelWeights).filter(ModelWeights.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Load dataset columns
        try:
            df = pd.read_csv(dataset.file_path, nrows=1)
            dataset_columns = set(df.columns)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read dataset: {str(e)}"
            )
        
        model_schema = model.training_schema
        
        # FALLBACK: If model doesn't have training_schema, infer from dataset
        if not model_schema:
            print(f"[SCHEMA] Model {model_id} has no training_schema metadata - inferring from training round...")
            
            # Try to get target_column from training_round
            target_column = None
            training_round = model.training_round
            if not training_round and model.round_id:
                training_round = db.query(TrainingRound).filter(
                    TrainingRound.id == model.round_id
                ).first()
            if not training_round and model.round_number is not None:
                training_round = db.query(TrainingRound).filter(
                    TrainingRound.round_number == model.round_number
                ).first()
            if training_round:
                target_column = training_round.target_column
                print(f"[SCHEMA] Found target_column from training_round: {target_column}")
            
            # If no training_round or no target_column, try to infer
            if not target_column:
                print(f"[SCHEMA] No training_round found, inferring target from dataset...")
                for col_name in ['value', 'target', 'y', 'forecast_value', 'target_value']:
                    if col_name in dataset_columns:
                        target_column = col_name
                        print(f"[SCHEMA] Inferred target from common names: {target_column}")
                        break
            
            # Last resort: first numeric column
            if not target_column:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                target_column = numeric_cols[0] if numeric_cols else None
                if target_column:
                    print(f"[SCHEMA] Using first numeric column as target: {target_column}")
            
            # Inferred schema: all columns except excluded ones
            excluded_columns = {'time_idx', 'group_id', 'timestamp', 'index'}
            model_schema = {
                "required_columns": [c for c in dataset_columns if c not in excluded_columns],
                "excluded_columns": list(excluded_columns),
                "target_column": target_column,
                "num_features": len([c for c in dataset_columns if c not in excluded_columns])
            }
            print(f"[SCHEMA] Inferred schema: {len(model_schema['required_columns'])} features, target={target_column}")

            # Persist inferred schema for this model to stabilize UI results
            try:
                model.training_schema = model_schema
                db.add(model)
                db.commit()
                db.refresh(model)
                print(f"[SCHEMA] Saved inferred training_schema for model {model_id}")
            except Exception as e:
                db.rollback()
                print(f"[SCHEMA] Failed to persist inferred schema: {e}")
        
        # Extract model schema
        required_columns = set(model_schema.get("required_columns", []))
        excluded_columns = set(model_schema.get("excluded_columns", []))
        target_column = model_schema.get("target_column")
        
        # Compute differences
        missing_columns = list(required_columns - dataset_columns)
        extra_columns = list(dataset_columns - required_columns - excluded_columns)
        
        # Check if schemas match
        schema_match = len(missing_columns) == 0 and len(extra_columns) == 0
        
        # Determine if auto-alignment is possible
        can_auto_align = True  # Can always drop extra or add zero-filled columns
        
        # Generate warnings
        warnings = []
        if missing_columns:
            warnings.append(f"Dataset missing {len(missing_columns)} required columns - will add zero-filled placeholders")
        if extra_columns:
            warnings.append(f"Dataset has {len(extra_columns)} extra columns - will drop during inference")
        if not target_column or target_column not in dataset_columns:
            warnings.append(f"Target column '{target_column}' not found in dataset")
            can_auto_align = False
        else:
            warnings.append(f"PASS Dataset schema compatible! Target column: {target_column}")
        
        return {
            "schema_match": schema_match,
            "missing_columns": missing_columns,
            "extra_columns": extra_columns,
            "warnings": warnings,
            "can_auto_align": can_auto_align,
            "model_schema": {
                "required_columns": list(required_columns),
                "excluded_columns": list(excluded_columns),
                "target_column": target_column,
                "num_features": len(required_columns)
            },
            "dataset_schema": {
                "columns": list(dataset_columns),
                "num_columns": len(dataset_columns)
            }
        }
    
    @staticmethod
    def align_features(
        df: pd.DataFrame,
        model_schema: Dict,
        verbose: bool = False
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Automatically align dataset features to match model training schema.
        
        Args:
            df: Input dataframe
            model_schema: Model training schema dict
            verbose: Print alignment operations
            
        Returns:
            Tuple of (aligned_df, warnings)
        """
        warnings = []
        required_columns = model_schema.get("required_columns", [])
        excluded_columns = set(model_schema.get("excluded_columns", []))
        target_column = model_schema.get("target_column")
        
        df_aligned = df.copy()
        current_columns = set(df_aligned.columns)
        
        # 1. Drop extra columns (not in required_columns and not excluded)
        extra_columns = current_columns - set(required_columns) - excluded_columns
        if extra_columns:
            df_aligned = df_aligned.drop(columns=list(extra_columns))
            warnings.append(f"Dropped {len(extra_columns)} extra columns: {list(extra_columns)[:5]}")
            if verbose:
                print(f"[ALIGN] Dropped columns: {extra_columns}")
        
        # 2. Add missing columns with zero-fill
        missing_columns = set(required_columns) - current_columns
        if missing_columns:
            for col in missing_columns:
                df_aligned[col] = 0.0  # Zero-fill missing features
                warnings.append(f"Added zero-filled column: {col}")
            if verbose:
                print(f"[ALIGN] Added zero-filled columns: {missing_columns}")
        
        # 3. Reorder columns to match training order
        try:
            df_aligned = df_aligned[required_columns]
        except KeyError as e:
            warnings.append(f"Column ordering failed: {str(e)}")
        
        # 4. Ensure target column exists
        if target_column and target_column not in df_aligned.columns:
            # Try to find it in original df
            if target_column in df.columns:
                df_aligned[target_column] = df[target_column]
                warnings.append(f"Restored target column: {target_column}")
            else:
                warnings.append(f"WARNING: Target column '{target_column}' not found - prediction may fail")
        
        return df_aligned, warnings
    
    @staticmethod
    def extract_schema_from_dataframe(
        df: pd.DataFrame,
        target_column: str,
        excluded_columns: Optional[List[str]] = None
    ) -> Dict:
        """
        Extract training schema from a dataframe.
        
        Args:
            df: Training dataframe
            target_column: Target column name
            excluded_columns: Columns to exclude (time_idx, group_id, timestamp, etc.)
            
        Returns:
            Schema dict: {
                "required_columns": List[str],      # Main field (backend standard)
                "feature_columns": List[str],       # Alias for frontend compatibility
                "excluded_columns": List[str],
                "target_column": str,
                "num_features": int
            }
        """
        if excluded_columns is None:
            excluded_columns = ["time_idx", "group_id", "timestamp", target_column]
        
        all_columns = list(df.columns)
        excluded_set = set(excluded_columns)
        
        # Required columns = all columns except excluded
        required_columns = [col for col in all_columns if col not in excluded_set]
        
        return {
            "required_columns": required_columns,      # Backend standard name
            "feature_columns": required_columns,       # Frontend alias for compatibility
            "excluded_columns": list(excluded_set),
            "target_column": target_column,
            "num_features": len(required_columns)
        }

