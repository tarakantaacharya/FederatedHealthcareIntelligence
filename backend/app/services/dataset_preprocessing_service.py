"""
Dataset Preprocessing Service

Handles data cleaning, column editing, and data type management for datasets.
- Detects and fixes data quality issues
- Allows column renaming and type conversion
- Creates versioned copies when dataset is already trained
- Preserves original data when necessary
"""

import pandas as pd
import numpy as np
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.dataset import Dataset
from app.config import get_settings

settings = get_settings()


class DatasetPreprocessingService:
    """Service for dataset preprocessing operations"""
    
    @staticmethod
    def detect_column_types(file_path: str) -> Dict[str, Any]:
        """
        Detect data types for all columns in dataset.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dict with column names and their detected types
        """
        try:
            file_path = os.path.normpath(file_path)
            df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows for efficiency
            
            column_types = {}
            for col in df.columns:
                # Infer type based on dtype and content
                dtype_str = str(df[col].dtype)
                
                if dtype_str in ['int64', 'int32', 'int16', 'int8']:
                    col_type = 'integer'
                elif dtype_str in ['float64', 'float32', 'float16']:
                    col_type = 'float'
                elif dtype_str == 'bool':
                    col_type = 'boolean'
                elif dtype_str == 'datetime64[ns]':
                    col_type = 'datetime'
                elif dtype_str == 'object':
                    # Try to infer more specific type
                    sample = df[col].dropna()
                    if len(sample) == 0:
                        col_type = 'string'
                    elif sample.apply(lambda x: isinstance(x, str)).all():
                        # Check if it's a date string
                        try:
                            pd.to_datetime(sample.iloc[:10])
                            col_type = 'datetime'
                        except:
                            col_type = 'string'
                    else:
                        col_type = 'mixed'
                else:
                    col_type = 'unknown'
                
                # Get statistics
                non_null_count = int(df[col].count())
                null_count = int(df[col].isnull().sum())
                unique_count = int(df[col].nunique())
                
                column_types[col] = {
                    'type': col_type,
                    'pandas_dtype': dtype_str,
                    'non_null_count': non_null_count,
                    'null_count': null_count,
                    'unique_count': unique_count
                }
            
            return {
                'columns': column_types,
                'total_rows': len(df),
                'detected_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to detect column types: {str(e)}"
            )
    
    @staticmethod
    def get_data_quality_report(file_path: str) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dict with quality metrics
        """
        try:
            file_path = os.path.normpath(file_path)
            df = pd.read_csv(file_path)
            
            report = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': {},
                'duplicates': {
                    'count': int(df.duplicated().sum()),
                    'percentage': float(df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
                },
                'columns': {}
            }
            
            # Analyze each column
            for col in df.columns:
                col_data = {
                    'missing_count': int(df[col].isnull().sum()),
                    'missing_percentage': float(df[col].isnull().sum() / len(df) * 100) if len(df) > 0 else 0,
                    'unique_count': int(df[col].nunique()),
                    'dtype': str(df[col].dtype)
                }
                
                # Add statistics for numeric columns
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_data.update({
                        'min': float(df[col].min()) if not df[col].isnull().all() else None,
                        'max': float(df[col].max()) if not df[col].isnull().all() else None,
                        'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                        'std': float(df[col].std()) if not df[col].isnull().all() else None
                    })
                
                report['columns'][col] = col_data
                
                if col_data['missing_count'] > 0:
                    report['missing_values'][col] = col_data['missing_count']
            
            report['has_issues'] = (
                len(report['missing_values']) > 0 or 
                report['duplicates']['count'] > 0
            )
            
            return report
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate quality report: {str(e)}"
            )
    
    @staticmethod
    def clean_dataset(
        db: Session,
        dataset: Dataset,
        operations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply cleaning operations to dataset.
        
        Args:
            db: Database session
            dataset: Dataset object
            operations: Dict with cleaning operations
                {
                    'remove_duplicates': bool,
                    'handle_missing': {'strategy': 'drop'|'fill', 'fill_value': any},
                    'remove_columns': List[str],
                    'rename_columns': Dict[str, str],
                    'convert_types': Dict[str, str]
                }
                
        Returns:
            Dict with cleaning results
        """
        try:
            # Check if dataset is already trained
            is_trained = dataset.times_trained > 0
            
            # Load dataset
            file_path = os.path.normpath(dataset.file_path)
            df = pd.read_csv(file_path)
            original_shape = df.shape
            
            results = {
                'original_shape': original_shape,
                'operations_applied': [],
                'created_backup': False
            }
            
            # If trained, create backup first
            if is_trained:
                backup_path = DatasetPreprocessingService._create_backup(
                    db, dataset, df
                )
                results['created_backup'] = True
                results['backup_path'] = backup_path
            
            # Apply operations
            if operations.get('remove_duplicates', False):
                before = len(df)
                df = df.drop_duplicates()
                removed = before - len(df)
                if removed > 0:
                    results['operations_applied'].append(
                        f"Removed {removed} duplicate rows"
                    )
            
            if 'handle_missing' in operations:
                strategy = operations['handle_missing'].get('strategy', 'drop')
                if strategy == 'drop':
                    before = len(df)
                    df = df.dropna()
                    removed = before - len(df)
                    if removed > 0:
                        results['operations_applied'].append(
                            f"Dropped {removed} rows with missing values"
                        )
                elif strategy == 'fill':
                    fill_value = operations['handle_missing'].get('fill_value', 0)
                    df = df.fillna(fill_value)
                    results['operations_applied'].append(
                        f"Filled missing values with {fill_value}"
                    )
            
            if 'remove_columns' in operations and operations['remove_columns']:
                cols_to_remove = [c for c in operations['remove_columns'] if c in df.columns]
                if cols_to_remove:
                    df = df.drop(columns=cols_to_remove)
                    results['operations_applied'].append(
                        f"Removed columns: {', '.join(cols_to_remove)}"
                    )
            
            if 'rename_columns' in operations and operations['rename_columns']:
                rename_map = {k: v for k, v in operations['rename_columns'].items() if k in df.columns}
                if rename_map:
                    df = df.rename(columns=rename_map)
                    results['operations_applied'].append(
                        f"Renamed {len(rename_map)} columns"
                    )
            
            if 'convert_types' in operations and operations['convert_types']:
                for col, target_type in operations['convert_types'].items():
                    if col in df.columns:
                        try:
                            if target_type == 'integer':
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                            elif target_type == 'float':
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            elif target_type == 'string':
                                df[col] = df[col].astype(str)
                            elif target_type == 'datetime':
                                df[col] = pd.to_datetime(df[col], errors='coerce')
                            results['operations_applied'].append(
                                f"Converted {col} to {target_type}"
                            )
                        except Exception as e:
                            results['operations_applied'].append(
                                f"Failed to convert {col}: {str(e)}"
                            )
            
            # Save cleaned dataset
            df.to_csv(file_path, index=False)
            
            # Update database record
            dataset.num_rows = len(df)
            dataset.num_columns = len(df.columns)
            dataset.column_names = json.dumps(df.columns.tolist())
            db.commit()
            
            results['new_shape'] = (len(df), len(df.columns))
            results['success'] = True
            
            return results
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clean dataset: {str(e)}"
            )
    
    @staticmethod
    def _create_backup(
        db: Session,
        dataset: Dataset,
        df: pd.DataFrame
    ) -> str:
        """
        Create a backup copy of dataset before modifying.
        
        Args:
            db: Database session
            dataset: Original dataset
            df: DataFrame to backup
            
        Returns:
            Path to backup file
        """
        # Create backup directory
        backup_dir = os.path.join(settings.UPLOAD_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{Path(dataset.filename).stem}_backup_{timestamp}.csv"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Save backup
        df.to_csv(backup_path, index=False)
        
        # Create backup dataset record
        backup_dataset = Dataset(
            hospital_id=dataset.hospital_id,
            filename=backup_filename,
            file_path=backup_path,
            file_size_bytes=os.path.getsize(backup_path),
            num_rows=len(df),
            num_columns=len(df.columns),
            column_names=dataset.column_names,
            is_normalized=dataset.is_normalized,
            normalized_path=dataset.normalized_path,
            times_trained=dataset.times_trained,
            times_federated=dataset.times_federated,
            last_trained_at=dataset.last_trained_at,
            involved_rounds=dataset.involved_rounds,
            last_training_type=dataset.last_training_type
        )
        
        db.add(backup_dataset)
        db.commit()
        
        return backup_path
    
    @staticmethod
    def get_preview_data(file_path: str, rows: int = 10) -> Dict[str, Any]:
        """
        Get preview of dataset for UI display.
        
        Args:
            file_path: Path to CSV file
            rows: Number of rows to preview
            
        Returns:
            Dict with preview data
        """
        try:
            file_path = os.path.normpath(file_path)
            df = pd.read_csv(file_path, nrows=rows)
            
            # Convert to JSON-serializable format
            preview = {
                'columns': df.columns.tolist(),
                'data': df.replace({np.nan: None}).to_dict('records'),
                'total_rows': rows,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return preview
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate preview: {str(e)}"
            )
