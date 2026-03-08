"""
Real Dataset Validation Service

Performs comprehensive data quality checks on uploaded datasets:
- Row/column counts
- Missing value detection and statistics
- Duplicate row detection
- Data type inference
- Time index monotonicity validation
- Target column validation
- Basic outlier detection

Results stored to enable persistence across page reloads.
No in-memory only tracking.
"""

import pandas as pd
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatasetValidationService:
    """Real validation service for dataset quality checks"""
    
    # Configuration
    MISSING_THRESHOLD = 0.20  # 20% missing values triggers warning
    TIME_INDEX_COLUMNS = ['timestamp', 'date', 'time', 'datetime', 'period']
    TARGET_COLUMNS = ['target', 'label', 'y', 'value', 'target_value']
    
    @staticmethod
    def validate_dataset(file_path: str, dataset_id: int) -> Dict[str, Any]:
        """
        Perform comprehensive validation on uploaded dataset.
        
        Args:
            file_path: Path to uploaded CSV file
            dataset_id: Database dataset ID
            
        Returns:
            Structured validation result with all metrics
        """
        try:
            logger.info(f"[VALIDATION] Starting validation for dataset {dataset_id}")
            
            # Read dataset
            if not Path(file_path).exists():
                logger.error(f"[VALIDATION] File not found: {file_path}")
                return {
                    "dataset_id": dataset_id,
                    "valid": False,
                    "error": "Dataset file not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            file_path = os.path.normpath(file_path)
            df = pd.read_csv(file_path)
            logger.info(f"[VALIDATION] Loaded dataset: {df.shape[0]} rows, {df.shape[1]} cols")
            
            # Compute validation metrics
            result = {
                "dataset_id": dataset_id,
                "timestamp": datetime.utcnow().isoformat(),
                "file_path": str(file_path),
                
                # Basic metrics
                "shape": {
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1])
                },
                
                # Column information
                "column_names": df.columns.tolist(),
                "column_types": DatasetValidationService._infer_column_types(df),
                
                # Missing value analysis
                "missing_analysis": DatasetValidationService._analyze_missing_values(df),
                
                # Duplicate detection
                "duplicates": {
                    "total_duplicates": int(df.duplicated().sum()),
                    "duplicate_percentage": float((df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0)
                },
                
                # Time index validation
                "time_index": DatasetValidationService._validate_time_index(df),
                
                # Target column validation
                "target": DatasetValidationService._validate_target_column(df),
                
                # Data type distribution
                "numeric_columns": int((df.dtypes == 'float64').sum() + (df.dtypes == 'int64').sum()),
                "categorical_columns": int((df.dtypes == 'object').sum()),
                
                # Outlier detection summary
                "outlier_summary": DatasetValidationService._detect_outliers_summary(df),
            }
            
            # Determine readiness for training
            result["ready_for_training"] = DatasetValidationService._assess_readiness(result)
            result["valid"] = True
            
            logger.info(f"""[VALIDATION] ✓ Validation complete for dataset {dataset_id}:
                - Rows: {result['shape']['rows']}
                - Cols: {result['shape']['columns']}
                - Missing %: {result['missing_analysis']['overall_missing_percentage']:.1f}%
                - Duplicates: {result['duplicates']['total_duplicates']}
                - Ready: {result['ready_for_training']}
            """)
            
            return result
            
        except Exception as e:
            logger.error(f"[VALIDATION] Error validating dataset {dataset_id}: {str(e)}")
            return {
                "dataset_id": dataset_id,
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """Infer data types for all columns"""
        types = {}
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                types[col] = 'numeric'
            elif df[col].dtype == 'object':
                types[col] = 'categorical'
            elif df[col].dtype == 'datetime64[ns]':
                types[col] = 'datetime'
            else:
                types[col] = str(df[col].dtype)
        return types
    
    @staticmethod
    def _analyze_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing values across dataset"""
        missing_per_col = df.isnull().sum().to_dict()
        missing_pct_per_col = (df.isnull().sum() / len(df) * 100).to_dict()
        
        total_missing = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        overall_missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0
        
        return {
            "total_missing_values": int(total_missing),
            "overall_missing_percentage": float(overall_missing_pct),
            "columns_with_missing": {
                col: {
                    "missing_count": int(missing_per_col[col]),
                    "missing_percentage": float(missing_pct_per_col[col])
                }
                for col in df.columns
                if missing_per_col[col] > 0
            }
        }
    
    @staticmethod
    def _validate_time_index(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate time index column if present"""
        result = {
            "found": False,
            "valid": False,
            "column": None,
            "monotonic": False,
            "warning": None
        }
        
        # Check for time index column
        for col in df.columns:
            col_lower = col.lower()
            if any(tc in col_lower for tc in DatasetValidationService.TIME_INDEX_COLUMNS):
                result["found"] = True
                result["column"] = col
                
                try:
                    # Try to convert to datetime
                    time_series = pd.to_datetime(df[col], errors='coerce')
                    
                    # Check if monotonic increasing
                    is_monotonic = time_series.is_monotonic_increasing or time_series.is_monotonic_decreasing
                    result["monotonic"] = bool(is_monotonic)
                    result["valid"] = is_monotonic
                    
                    if not is_monotonic:
                        result["warning"] = "Time index is not monotonic increasing or decreasing"
                    
                except Exception as e:
                    result["warning"] = f"Could not parse as datetime: {str(e)}"
                
                break
        
        if not result["found"]:
            result["warning"] = "No time index column detected"
        
        return result
    
    @staticmethod
    def _validate_target_column(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate target column if present"""
        result = {
            "found": False,
            "valid": False,
            "column": None,
            "warning": None
        }
        
        # Check for target column
        for col in df.columns:
            col_lower = col.lower()
            if any(tc in col_lower for tc in DatasetValidationService.TARGET_COLUMNS):
                result["found"] = True
                result["column"] = col
                
                # Check if target has non-null values
                if df[col].isnull().sum() > 0:
                    result["warning"] = f"Target column has {df[col].isnull().sum()} missing values"
                else:
                    result["valid"] = True
                
                break
        
        if not result["found"]:
            result["warning"] = "No target column detected"
        
        return result
    
    @staticmethod
    def _detect_outliers_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Simple outlier detection for numeric columns"""
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) == 0:
            return {
                "numeric_columns_checked": 0,
                "columns_with_outliers": []
            }
        
        outlier_cols = []
        for col in numeric_cols:
            try:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                
                outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
                if outlier_count > 0:
                    outlier_cols.append({
                        "column": col,
                        "outlier_count": int(outlier_count),
                        "outlier_percentage": float(outlier_count / len(df) * 100)
                    })
            except Exception as e:
                logger.debug(f"Could not check outliers for {col}: {str(e)}")
        
        return {
            "numeric_columns_checked": len(numeric_cols),
            "columns_with_outliers": outlier_cols
        }
    
    @staticmethod
    def _assess_readiness(validation_result: Dict[str, Any]) -> bool:
        """
        Determine if dataset is ready for training based on validation results.
        
        Ready only if:
        - No more than MISSING_THRESHOLD missing values
        - Time index valid (if present)
        - Target column valid (if present)
        - Not excessive duplicates (>50%)
        """
        if not validation_result.get("valid"):
            return False
        
        # Check missing value threshold
        missing_pct = validation_result.get("missing_analysis", {}).get("overall_missing_percentage", 100)
        if missing_pct > (DatasetValidationService.MISSING_THRESHOLD * 100):
            logger.info(f"[READINESS] Dataset not ready: missing % {missing_pct:.1f}% exceeds threshold")
            return False
        
        # Check time index if found
        time_index = validation_result.get("time_index", {})
        if time_index.get("found") and not time_index.get("valid"):
            logger.info(f"[READINESS] Dataset not ready: time index invalid")
            return False
        
        # Check target column if found
        target = validation_result.get("target", {})
        if target.get("found") and not target.get("valid"):
            logger.info(f"[READINESS] Dataset not ready: target column invalid")
            return False
        
        # Check duplicate percentage
        dup_pct = validation_result.get("duplicates", {}).get("duplicate_percentage", 0)
        if dup_pct > 50:
            logger.info(f"[READINESS] Dataset not ready: duplicate % {dup_pct:.1f}% too high")
            return False
        
        logger.info(f"[READINESS] ✓ Dataset ready for training")
        return True
