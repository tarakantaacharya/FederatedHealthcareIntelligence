"""
Model Management Service
Handles clearing and cleanup of local and global models
"""
import os
from typing import Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.model_weights import ModelWeights
from app.models.model_registry import ModelRegistry
from app.models.hospital import Hospital
from app.models.blockchain import Blockchain
from app.models.model_governance import ModelGovernance


class ModelManagementService:
    """Service for managing model lifecycle and cleanup operations"""
    
    @staticmethod
    def clear_local_models(
        hospital_id: int,
        db: Session,
        delete_files: bool = True
    ) -> Dict[str, int]:
        """
        Clear all local models for a specific hospital.
        
        Args:
            hospital_id: Hospital database ID (not hospital_id string)
            db: Database session
            delete_files: Whether to delete physical model files from disk
            
        Returns:
            Dict with counts of deleted records
        """
        # Verify hospital exists
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital with ID {hospital_id} not found"
            )
        
        # Get all local models for this hospital
        local_models = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital_id,
            ModelWeights.is_global == False
        ).all()
        
        deleted_files = 0
        deleted_weights = 0
        deleted_registry = 0
        failed_deletions = []
        
        # Delete physical model files if requested
        if delete_files:
            for model in local_models:
                if model.model_path and os.path.exists(model.model_path):
                    try:
                        os.remove(model.model_path)
                        deleted_files += 1
                    except Exception as e:
                        failed_deletions.append({
                            "model_id": model.id,
                            "path": model.model_path,
                            "error": str(e)
                        })
        
        # Delete from ModelWeights
        deleted_weights = db.query(ModelWeights).filter(
            ModelWeights.hospital_id == hospital_id,
            ModelWeights.is_global == False
        ).delete(synchronize_session=False)
        
        # Delete from ModelRegistry
        deleted_registry = db.query(ModelRegistry).filter(
            ModelRegistry.hospital_id == hospital_id,
            ModelRegistry.is_global == False
        ).delete(synchronize_session=False)
        
        # Log to blockchain for audit trail
        try:
            blockchain_entry = Blockchain(
                round_number=0,  # Administrative action
                block_data={
                    "action": "clear_local_models",
                    "hospital_id": hospital_id,
                    "hospital_name": hospital.hospital_name,
                    "deleted_weights": deleted_weights,
                    "deleted_registry": deleted_registry,
                    "deleted_files": deleted_files,
                    "failed_deletions": len(failed_deletions)
                }
            )
            db.add(blockchain_entry)
        except Exception as e:
            # Log blockchain error but don't fail the operation
            print(f"Warning: Failed to log to blockchain: {e}")
        
        db.commit()
        
        return {
            "deleted_weights_records": deleted_weights,
            "deleted_registry_records": deleted_registry,
            "deleted_files": deleted_files,
            "failed_file_deletions": len(failed_deletions),
            "failed_deletion_details": failed_deletions if failed_deletions else []
        }
    
    @staticmethod
    def clear_global_models(
        db: Session,
        delete_files: bool = True,
        clear_governance: bool = False
    ) -> Dict[str, int]:
        """
        Clear all global models from the central server.
        ADMIN-ONLY operation.
        
        Args:
            db: Database session
            delete_files: Whether to delete physical model files from disk
            clear_governance: Whether to also clear governance records (use with caution)
            
        Returns:
            Dict with counts of deleted records
        """
        # Get all global models (is_global=True, hospital_id=NULL for central models only)
        global_models = db.query(ModelWeights).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).all()
        
        deleted_files = 0
        deleted_weights = 0
        deleted_registry = 0
        deleted_governance = 0
        failed_deletions = []
        
        # Delete physical model files if requested
        if delete_files:
            for model in global_models:
                if model.model_path and os.path.exists(model.model_path):
                    try:
                        os.remove(model.model_path)
                        deleted_files += 1
                    except Exception as e:
                        failed_deletions.append({
                            "model_id": model.id,
                            "path": model.model_path,
                            "error": str(e)
                        })
        
        # Delete from ModelWeights (central models only: is_global=True, hospital_id=NULL)
        deleted_weights = db.query(ModelWeights).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).delete(synchronize_session=False)
        
        # Delete from ModelRegistry (central models only: is_global=True, hospital_id=NULL)
        deleted_registry = db.query(ModelRegistry).filter(
            ModelRegistry.is_global == True,
            ModelRegistry.hospital_id == None
        ).delete(synchronize_session=False)
        
        # Optionally clear governance records (use with extreme caution)
        if clear_governance:
            deleted_governance = db.query(ModelGovernance).delete(synchronize_session=False)
        
        # Log to blockchain for audit trail
        try:
            blockchain_entry = Blockchain(
                round_number=0,  # Administrative action
                block_data={
                    "action": "clear_global_models",
                    "deleted_weights": deleted_weights,
                    "deleted_registry": deleted_registry,
                    "deleted_files": deleted_files,
                    "deleted_governance": deleted_governance,
                    "failed_deletions": len(failed_deletions)
                }
            )
            db.add(blockchain_entry)
        except Exception as e:
            # Log blockchain error but don't fail the operation
            print(f"Warning: Failed to log to blockchain: {e}")
        
        db.commit()
        
        return {
            "deleted_weights_records": deleted_weights,
            "deleted_registry_records": deleted_registry,
            "deleted_files": deleted_files,
            "deleted_governance_records": deleted_governance,
            "failed_file_deletions": len(failed_deletions),
            "failed_deletion_details": failed_deletions if failed_deletions else []
        }
    
    @staticmethod
    def get_model_summary(
        hospital_id: int = None,
        db: Session = None
    ) -> Dict:
        """
        Get summary of models for a hospital or globally.
        
        Args:
            hospital_id: Optional hospital ID (None for global summary)
            db: Database session
            
        Returns:
            Dict with model counts and statistics
        """
        if hospital_id:
            # Local models for specific hospital
            local_count = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.is_global == False
            ).count()
            
            local_models = db.query(ModelWeights).filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.is_global == False
            ).all()
            
            return {
                "hospital_id": hospital_id,
                "local_model_count": local_count,
                "models_by_type": {
                    "TFT": len([m for m in local_models if m.model_architecture == "TFT"]),
                    "ML_REGRESSION": len([m for m in local_models if m.model_architecture == "ML_REGRESSION"])
                },
                "models_by_training_type": {
                    "LOCAL": len([m for m in local_models if m.training_type == "LOCAL"]),
                    "FEDERATED": len([m for m in local_models if m.training_type == "FEDERATED"])
                }
            }
        else:
            # Global models summary (central only: is_global=True, hospital_id=NULL)
            global_count = db.query(ModelWeights).filter(
                ModelWeights.is_global == True,
                ModelWeights.hospital_id == None
            ).count()
            
            global_models = db.query(ModelWeights).filter(
                ModelWeights.is_global == True,
                ModelWeights.hospital_id == None
            ).all()
            
            return {
                "global_model_count": global_count,
                "models_by_type": {
                    "TFT": len([m for m in global_models if m.model_architecture == "TFT"]),
                    "ML_REGRESSION": len([m for m in global_models if m.model_architecture == "ML_REGRESSION"])
                },
                "models_by_round": {}  # Could add round-based breakdown
            }
