"""
Validation Results Storage

Persists dataset validation results to JSON files for retrieval
across page reloads and sessions.

One JSON file per dataset for easy indexing.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationResultsStorage:
    """Manages persistent storage of validation results"""
    
    def __init__(self, storage_dir: str = "./storage/validation_results"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[STORAGE] Validation results directory: {self.storage_dir}")
    
    def save_result(self, dataset_id: int, validation_result: Dict[str, Any]) -> bool:
        """
        Save validation result to JSON file.
        
        Args:
            dataset_id: Dataset ID
            validation_result: Validation result dict
            
        Returns:
            True if saved successfully
        """
        try:
            result_file = self.storage_dir / f"dataset_{dataset_id}_validation.json"
            
            # Ensure result has timestamp
            if "timestamp" not in validation_result:
                validation_result["timestamp"] = datetime.utcnow().isoformat()
            
            with open(result_file, 'w') as f:
                json.dump(validation_result, f, indent=2, default=str)
            
            logger.info(f"[STORAGE] ✓ Saved validation result for dataset {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"[STORAGE] Failed to save validation result for {dataset_id}: {str(e)}")
            return False
    
    def get_result(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation result from JSON file.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Validation result dict or None if not found
        """
        try:
            result_file = self.storage_dir / f"dataset_{dataset_id}_validation.json"
            
            if not result_file.exists():
                logger.debug(f"[STORAGE] No validation result found for dataset {dataset_id}")
                return None
            
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            logger.debug(f"[STORAGE] ✓ Retrieved validation result for dataset {dataset_id}")
            return result
            
        except Exception as e:
            logger.error(f"[STORAGE] Failed to retrieve validation result for {dataset_id}: {str(e)}")
            return None
    
    def delete_result(self, dataset_id: int) -> bool:
        """Delete validation result"""
        try:
            result_file = self.storage_dir / f"dataset_{dataset_id}_validation.json"
            if result_file.exists():
                result_file.unlink()
                logger.info(f"[STORAGE] Deleted validation result for dataset {dataset_id}")
            return True
        except Exception as e:
            logger.error(f"[STORAGE] Failed to delete validation result for {dataset_id}: {str(e)}")
            return False


# Global singleton instance
validation_storage = ValidationResultsStorage()
