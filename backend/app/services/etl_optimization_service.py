"""
ETL Optimization Service (Phase 32)
Batch processing, parallel parsing, and caching for dataset operations
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib
import json
import os
from functools import lru_cache
import logging
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Memory cache for dataset metadata
_metadata_cache: Dict[str, Dict] = {}


class ETLOptimizationService:
    """Service for optimized ETL operations"""
    
    MAX_WORKERS = 4  # Parallel processing workers
    CHUNK_SIZE = 10000  # Rows per chunk for batch processing
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute SHA256 hash of file for cache invalidation"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_cached_column_stats(file_hash: str, file_path: str) -> Dict:
        """
        Get cached column statistics (uses LRU cache)
        
        Args:
            file_hash: File hash for cache key
            file_path: Path to dataset file
        
        Returns:
            Dictionary with column statistics
        """
        logger.info(f"Computing statistics for {file_path} (cache miss)")
        
        # Read in chunks for memory efficiency
        chunks = []
        for chunk in pd.read_csv(file_path, chunksize=ETLOptimizationService.CHUNK_SIZE):
            chunks.append(chunk)
        
        df = pd.concat(chunks, ignore_index=True)
        
        stats = {
            'num_rows': len(df),
            'num_columns': len(df.columns),
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_counts': df.isnull().sum().to_dict(),
            'numeric_stats': {}
        }
        
        # Compute stats for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            stats['numeric_stats'][col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median())
            }
        
        return stats
    
    @staticmethod
    def batch_process_datasets(
        file_paths: List[str],
        operation: str = 'validate'
    ) -> List[Dict]:
        """
        Batch process multiple datasets in parallel
        
        Args:
            file_paths: List of dataset file paths
            operation: Operation to perform ('validate', 'profile', 'normalize')
        
        Returns:
            List of results for each dataset
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=ETLOptimizationService.MAX_WORKERS) as executor:
            if operation == 'validate':
                futures = [executor.submit(ETLOptimizationService._validate_dataset, fp) for fp in file_paths]
            elif operation == 'profile':
                futures = [executor.submit(ETLOptimizationService._profile_dataset, fp) for fp in file_paths]
            elif operation == 'normalize':
                futures = [executor.submit(ETLOptimizationService._normalize_dataset, fp) for fp in file_paths]
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    results.append({'error': str(e)})
        
        return results
    
    @staticmethod
    def _validate_dataset(file_path: str) -> Dict:
        """Validate dataset structure and data quality"""
        try:
            df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows
            
            issues = []
            
            # Check for completely empty columns
            empty_cols = [col for col in df.columns if df[col].isnull().all()]
            if empty_cols:
                issues.append(f"Empty columns: {', '.join(empty_cols)}")
            
            # Check for high missing value percentage
            missing_pct = (df.isnull().sum() / len(df)) * 100
            high_missing = [col for col, pct in missing_pct.items() if pct > 50]
            if high_missing:
                issues.append(f"High missing values (>50%): {', '.join(high_missing)}")
            
            # Check for duplicate columns
            if len(df.columns) != len(set(df.columns)):
                issues.append("Duplicate column names detected")
            
            return {
                'file_path': file_path,
                'valid': len(issues) == 0,
                'issues': issues,
                'num_rows': len(df),
                'num_columns': len(df.columns)
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'valid': False,
                'issues': [f"Read error: {str(e)}"]
            }
    
    @staticmethod
    def _profile_dataset(file_path: str) -> Dict:
        """Profile dataset to extract metadata"""
        try:
            file_hash = ETLOptimizationService.compute_file_hash(file_path)
            stats = ETLOptimizationService.get_cached_column_stats(file_hash, file_path)
            
            return {
                'file_path': file_path,
                'success': True,
                'stats': stats
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _normalize_dataset(file_path: str) -> Dict:
        """Normalize dataset values"""
        try:
            df = pd.read_csv(file_path)
            
            # Normalize numeric columns to [0, 1]
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            normalized_ranges = {}
            for col in numeric_cols:
                min_val = df[col].min()
                max_val = df[col].max()
                
                if max_val > min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)
                    normalized_ranges[col] = {'min': float(min_val), 'max': float(max_val)}
            
            # Save normalized dataset
            normalized_path = file_path.replace('.csv', '_normalized.csv')
            df.to_csv(normalized_path, index=False)
            
            return {
                'file_path': file_path,
                'normalized_path': normalized_path,
                'success': True,
                'normalized_columns': list(normalized_ranges.keys()),
                'ranges': normalized_ranges
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def parallel_feature_extraction(
        datasets: List[Dict[str, any]],
        target_column: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract features from multiple datasets in parallel
        
        Args:
            datasets: List of dataset dictionaries with 'file_path' key
            target_column: Name of target column
        
        Returns:
            Tuple of (X features, y targets) as numpy arrays
        """
        def extract_from_file(dataset_info):
            file_path = dataset_info['file_path']
            df = pd.read_csv(file_path)
            
            if target_column not in df.columns:
                raise ValueError(f"Target column '{target_column}' not found in {file_path}")
            
            y = df[target_column].values
            X = df.drop(columns=[target_column]).select_dtypes(include=[np.number]).values
            
            return X, y
        
        with ProcessPoolExecutor(max_workers=ETLOptimizationService.MAX_WORKERS) as executor:
            results = list(executor.map(extract_from_file, datasets))
        
        # Concatenate all results
        X_all = np.vstack([X for X, y in results])
        y_all = np.hstack([y for X, y in results])
        
        return X_all, y_all
    
    @staticmethod
    def clear_cache():
        """Clear all ETL caches"""
        ETLOptimizationService.get_cached_column_stats.cache_clear()
        global _metadata_cache
        _metadata_cache = {}
        logger.info("ETL caches cleared")
