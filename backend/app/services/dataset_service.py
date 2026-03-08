"""
Dataset service
Business logic for dataset upload and management
"""
import pandas as pd
import os
import json
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.models.dataset import Dataset
from app.models.hospital import Hospital
from app.models.model_weights import ModelWeights
from app.utils.storage import save_uploaded_file, delete_file


class DatasetService:
    """Dataset management service"""
    
    @staticmethod
    async def upload_dataset(
        db: Session,
        file: UploadFile,
        hospital: Hospital
    ) -> Dataset:
        """
        Upload and process CSV dataset
        
        Args:
            db: Database session
            file: Uploaded CSV file
            hospital: Hospital object
        
        Returns:
            Created Dataset object
        
        Raises:
            HTTPException: If file is invalid
        """
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )
        
        # Save file to storage
        file_metadata = await save_uploaded_file(file, hospital.hospital_id)
        
        # Read CSV to extract metadata - normalize path for Windows/Unix compatibility
        try:
            file_path = os.path.normpath(file_metadata["file_path"])
            df = pd.read_csv(file_path)
            # Enforce float32 for numeric columns to satisfy TFT preprocessing
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                df[numeric_cols] = df[numeric_cols].astype("float32")
                df.to_csv(file_path, index=False)
            num_rows = len(df)
            num_columns = len(df.columns)
            column_names = df.columns.tolist()
        except Exception as e:
            # Delete uploaded file if parsing fails
            delete_file(file_metadata["file_path"])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse CSV: {str(e)}"
            )
        
        # Detect dataset type based on columns
        normalized_columns = [str(col).strip().lower() for col in column_names]
        dataset_type = "TIME_SERIES" if "timestamp" in normalized_columns else "TABULAR"
        
        # Create database record
        dataset = Dataset(
            hospital_id=hospital.id,
            filename=file_metadata["filename"],
            file_path=file_metadata["file_path"],
            file_size_bytes=file_metadata["file_size_bytes"],
            num_rows=num_rows,
            num_columns=num_columns,
            column_names=json.dumps(column_names),  # Store as JSON string
            is_normalized=False,
            dataset_type=dataset_type  # Set based on column detection
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Track pipeline status (non-intrusive monitoring)
        from app.services.data_pipeline_tracker import pipeline_tracker
        pipeline_tracker.initialize_pipeline(dataset.id, hospital.id)
        pipeline_tracker.mark_upload_complete(
            dataset.id,
            metrics={
                "rows": num_rows,
                "columns": num_columns,
                "file_size_kb": file_metadata["file_size_bytes"] / 1024
            }
        )
        
        return dataset
    
    @staticmethod
    def get_hospital_datasets(
        db: Session,
        hospital_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Dataset]:
        """Get all datasets for a hospital"""
        return db.query(Dataset).filter(
            Dataset.hospital_id == hospital_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_dataset_by_id(
        db: Session,
        dataset_id: int,
        hospital_id: int
    ) -> Dataset:
        """
        Get specific dataset (ownership verified)
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            hospital_id: Hospital ID (for ownership check)
        
        Returns:
            Dataset object
        
        Raises:
            HTTPException: If dataset not found or not owned by hospital
        """
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.hospital_id == hospital_id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied"
            )
        
        return dataset
    
    @staticmethod
    def delete_dataset(
        db: Session,
        dataset_id: int,
        hospital_id: int
    ) -> bool:
        """
        Delete dataset and associated files
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            hospital_id: Hospital ID (for ownership check)
        
        Returns:
            True if deleted
        
        Raises:
            HTTPException: If dataset not found or has dependencies
        """
        import logging
        import traceback
        from sqlalchemy.exc import IntegrityError
        from app.models.model_weights import ModelWeights
        
        logger = logging.getLogger(__name__)
        
        logger.info(f"[DELETE_SERVICE] Starting delete for dataset {dataset_id}, hospital {hospital_id}")
        
        try:
            # Step 1: Get dataset (with ownership check)
            logger.info(f"[DELETE_SERVICE] Step 1: Getting dataset by ID")
            dataset = DatasetService.get_dataset_by_id(db, dataset_id, hospital_id)
            logger.info(f"[DELETE_SERVICE] Found dataset: {dataset.filename} (ID={dataset.id})")
            
            # Step 2: Check for existing model weights
            logger.info(f"[DELETE_SERVICE] Step 2: Checking for model weight references")
            existing_models = db.query(ModelWeights).filter(
                ModelWeights.dataset_id == dataset.id
            ).count()
            
            if existing_models > 0:
                logger.warning(f"[DELETE_SERVICE] Dataset has {existing_models} model weight references")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete dataset: {existing_models} model weights reference this dataset."
                )
            
            logger.info(f"[DELETE_SERVICE] No model weight references found")
            
            # Step 3: Delete file from storage
            logger.info(f"[DELETE_SERVICE] Step 3: Deleting file from disk")
            try:
                delete_file(dataset.file_path)
                logger.info(f"[DELETE_SERVICE] Deleted file: {dataset.file_path}")
            except Exception as e:
                logger.warning(f"[DELETE_SERVICE] Could not delete file {dataset.file_path}: {e}")
            
            # Step 4: Delete normalized file if exists
            if dataset.normalized_path:
                logger.info(f"[DELETE_SERVICE] Step 4: Deleting normalized file")
                try:
                    delete_file(dataset.normalized_path)
                    logger.info(f"[DELETE_SERVICE] Deleted normalized file: {dataset.normalized_path}")
                except Exception as e:
                    logger.warning(f"[DELETE_SERVICE] Could not delete normalized file {dataset.normalized_path}: {e}")
            
            # Step 5: Delete database record with integrity protection
            logger.info(f"[DELETE_SERVICE] Step 5: Deleting from database")
            try:
                db.delete(dataset)
                db.commit()
                logger.info(f"[DELETE_SERVICE] ✅ Successfully deleted dataset {dataset_id}")
                return True
            except IntegrityError as ie:
                db.rollback()
                logger.error(f"[DELETE_SERVICE] IntegrityError during delete: {str(ie)}")
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete dataset due to existing references."
                )
            
        except HTTPException as http_ex:
            # Don't rollback for HTTPException - just re-raise
            logger.error(f"[DELETE_SERVICE] ❌ HTTPException: {http_ex.status_code} - {http_ex.detail}")
            raise
            
        except Exception as e:
            logger.error(f"[DELETE_SERVICE] ❌ Unexpected error deleting dataset {dataset_id}")
            logger.error(f"[DELETE_SERVICE] Exception type: {type(e).__name__}")
            logger.error(f"[DELETE_SERVICE] Exception message: {str(e)}")
            logger.error(f"[DELETE_SERVICE] Traceback: {traceback.format_exc()}")
            db.rollback()
            raise

    @staticmethod
    def get_dataset_models(
        db: Session,
        dataset_id: int,
        hospital_id: int
    ) -> list[dict]:
        """Get all trained models for a dataset owned by the current hospital."""
        # Enforce ownership before listing model artifacts.
        DatasetService.get_dataset_by_id(db, dataset_id, hospital_id)

        rows = db.query(ModelWeights).filter(
            ModelWeights.dataset_id == dataset_id,
            ModelWeights.hospital_id == hospital_id
        ).order_by(ModelWeights.created_at.desc()).all()

        result = []
        for row in rows:
            raw_arch = (row.model_architecture or "").upper()
            if raw_arch == "TFT":
                architecture = "TFT"
            else:
                architecture = "ML"

            model_name = f"Round {row.round_number} - {architecture}"

            result.append({
                "id": row.id,
                "model_name": model_name,
                "type": str(row.training_type.value if hasattr(row.training_type, "value") else row.training_type),
                "architecture": architecture,
                "timestamp": row.created_at,
            })

        return result
