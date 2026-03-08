"""
Data Pipeline Tracker - Lightweight, Non-Intrusive Pipeline Status Monitoring

Provides read-only visibility into dataset processing stages without
modifying training logic, privacy governance, or federated orchestration.

Stages:
1. Upload - File successfully received
2. Validation - Schema and data type validation
3. Cleaning - Missing value handling, outlier detection
4. Feature Engineering - Temporal feature creation, lag features
5. Schema Harmonization - Cross-hospital schema alignment
6. Ready for Training - Passed all checks, ready for ML/TFT

No DB schema changes required - uses in-memory tracking with optional
persistence. Does NOT modify Dataset model.
"""

from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline processing stages"""
    UPLOAD = "upload"
    VALIDATION = "validation"
    CLEANING = "cleaning"
    FEATURE_ENGINEERING = "feature_engineering"
    HARMONIZATION = "harmonization"
    READY = "ready_for_training"


class StageStatus(str, Enum):
    """Status of individual stage"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class StageMetadata:
    """Metadata for a pipeline stage"""
    status: StageStatus
    timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict] = None  # rows, columns, missing_values, quality_score


@dataclass
class DataPipelineStatus:
    """Complete pipeline status for a dataset"""
    dataset_id: int
    hospital_id: int
    
    # Stage tracking
    upload: StageMetadata
    validation: StageMetadata
    cleaning: StageMetadata
    feature_engineering: StageMetadata
    harmonization: StageMetadata
    ready_for_training: StageMetadata
    
    # Aggregates
    overall_progress: int  # 0-100%
    is_ready: bool
    last_updated: datetime
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "dataset_id": self.dataset_id,
            "hospital_id": self.hospital_id,
            "stages": {
                "upload": {
                    "status": self.upload.status.value,
                    "timestamp": self.upload.timestamp.isoformat() if self.upload.timestamp else None,
                    "error": self.upload.error_message,
                    "metrics": self.upload.metrics
                },
                "validation": {
                    "status": self.validation.status.value,
                    "timestamp": self.validation.timestamp.isoformat() if self.validation.timestamp else None,
                    "error": self.validation.error_message,
                    "metrics": self.validation.metrics
                },
                "cleaning": {
                    "status": self.cleaning.status.value,
                    "timestamp": self.cleaning.timestamp.isoformat() if self.cleaning.timestamp else None,
                    "error": self.cleaning.error_message,
                    "metrics": self.cleaning.metrics
                },
                "feature_engineering": {
                    "status": self.feature_engineering.status.value,
                    "timestamp": self.feature_engineering.timestamp.isoformat() if self.feature_engineering.timestamp else None,
                    "error": self.feature_engineering.error_message,
                    "metrics": self.feature_engineering.metrics
                },
                "harmonization": {
                    "status": self.harmonization.status.value,
                    "timestamp": self.harmonization.timestamp.isoformat() if self.harmonization.timestamp else None,
                    "error": self.harmonization.error_message,
                    "metrics": self.harmonization.metrics
                },
                "ready_for_training": {
                    "status": self.ready_for_training.status.value,
                    "timestamp": self.ready_for_training.timestamp.isoformat() if self.ready_for_training.timestamp else None,
                    "error": self.ready_for_training.error_message,
                    "metrics": self.ready_for_training.metrics
                }
            },
            "overall_progress": self.overall_progress,
            "is_ready": self.is_ready,
            "last_updated": self.last_updated.isoformat()
        }


class DataPipelineTracker:
    """
    In-memory pipeline status tracker for datasets.
    
    Tracks processing stages without modifying Dataset model or
    introducing DB migrations. Provides read-only observability.
    """
    
    def __init__(self):
        """Initialize tracker with empty state"""
        self._pipelines: Dict[int, DataPipelineStatus] = {}
    
    def initialize_pipeline(self, dataset_id: int, hospital_id: int) -> DataPipelineStatus:
        """
        Initialize a new pipeline for a dataset.
        Called when dataset is first uploaded.
        """
        now = datetime.utcnow()
        
        pipeline = DataPipelineStatus(
            dataset_id=dataset_id,
            hospital_id=hospital_id,
            upload=StageMetadata(status=StageStatus.PENDING),
            validation=StageMetadata(status=StageStatus.PENDING),
            cleaning=StageMetadata(status=StageStatus.PENDING),
            feature_engineering=StageMetadata(status=StageStatus.PENDING),
            harmonization=StageMetadata(status=StageStatus.PENDING),
            ready_for_training=StageMetadata(status=StageStatus.PENDING),
            overall_progress=0,
            is_ready=False,
            last_updated=now
        )
        
        self._pipelines[dataset_id] = pipeline
        logger.info(f"[PIPELINE] Initialized pipeline for dataset {dataset_id}")
        return pipeline
    
    def mark_upload_complete(
        self, 
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark upload stage complete with optional metrics"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            logger.warning(f"[PIPELINE] Dataset {dataset_id} not in tracker")
            return None
        
        pipeline.upload = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] Upload complete: {dataset_id}")
        return pipeline
    
    def mark_validation_start(self, dataset_id: int) -> Optional[DataPipelineStatus]:
        """Mark validation stage as processing"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.validation.status = StageStatus.PROCESSING
        pipeline.last_updated = datetime.utcnow()
        return pipeline
    
    def mark_validation_complete(
        self,
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark validation stage complete"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.validation = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] Validation complete: {dataset_id}")
        return pipeline
    
    def mark_validation_failed(
        self,
        dataset_id: int,
        error_message: str
    ) -> Optional[DataPipelineStatus]:
        """Mark validation as failed"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.validation = StageMetadata(
            status=StageStatus.FAILED,
            timestamp=datetime.utcnow(),
            error_message=error_message
        )
        pipeline.is_ready = False
        pipeline.last_updated = datetime.utcnow()
        
        logger.warning(f"[PIPELINE] Validation failed for {dataset_id}: {error_message}")
        return pipeline
    
    def mark_cleaning_complete(
        self,
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark cleaning stage complete"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.cleaning = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] Cleaning complete: {dataset_id}")
        return pipeline
    
    def mark_feature_engineering_complete(
        self,
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark feature engineering stage complete"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.feature_engineering = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] Feature engineering complete: {dataset_id}")
        return pipeline
    
    def mark_harmonization_complete(
        self,
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark schema harmonization stage complete"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.harmonization = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] Harmonization complete: {dataset_id}")
        return pipeline
    
    def mark_ready_for_training(
        self,
        dataset_id: int,
        metrics: Optional[Dict] = None
    ) -> Optional[DataPipelineStatus]:
        """Mark dataset as ready for training"""
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            return None
        
        pipeline.ready_for_training = StageMetadata(
            status=StageStatus.COMPLETE,
            timestamp=datetime.utcnow(),
            metrics=metrics or {}
        )
        pipeline.is_ready = True
        pipeline.last_updated = datetime.utcnow()
        self._update_progress(pipeline)
        
        logger.info(f"[PIPELINE] ✓ Dataset {dataset_id} is ready for training")
        return pipeline
    
    def get_pipeline_status(self, dataset_id: int) -> Optional[DataPipelineStatus]:
        """Retrieve pipeline status for a dataset"""
        return self._pipelines.get(dataset_id)
    
    def get_all_pipelines(
        self, 
        hospital_id: Optional[int] = None
    ) -> List[DataPipelineStatus]:
        """Retrieve all pipelines, optionally filtered by hospital"""
        if hospital_id is None:
            return list(self._pipelines.values())
        
        return [
            p for p in self._pipelines.values()
            if p.hospital_id == hospital_id
        ]
    
    def _update_progress(self, pipeline: DataPipelineStatus) -> None:
        """Update overall progress percentage based on completed stages"""
        stages = [
            pipeline.upload,
            pipeline.validation,
            pipeline.cleaning,
            pipeline.feature_engineering,
            pipeline.harmonization,
            pipeline.ready_for_training
        ]
        
        completed = sum(
            1 for s in stages
            if s.status == StageStatus.COMPLETE
        )
        
        pipeline.overall_progress = int((completed / len(stages)) * 100)
    
    def auto_progress_stages(self, dataset_id: int) -> Optional[DataPipelineStatus]:
        """
        Auto-progress pipeline through all stages.
        
        For demo/testing: simulates the data processing pipeline by marking
        each stage as complete sequentially. In production, these stages
        would be triggered by actual data processing services.
        """
        pipeline = self._pipelines.get(dataset_id)
        if not pipeline:
            logger.warning(f"[PIPELINE] Cannot auto-progress: dataset {dataset_id} not found")
            return None
        
        # If upload not complete, can't progress
        if pipeline.upload.status != StageStatus.COMPLETE:
            logger.warning(f"[PIPELINE] Cannot auto-progress: upload not complete for dataset {dataset_id}")
            return None
        
        # Mark each stage as complete in sequence
        self.mark_validation_complete(dataset_id, metrics={"passed": True})
        self.mark_cleaning_complete(dataset_id, metrics={"rows_cleaned": 0})
        self.mark_feature_engineering_complete(dataset_id, metrics={"features_created": 0})
        self.mark_harmonization_complete(dataset_id, metrics={"schema_matched": True})
        self.mark_ready_for_training(dataset_id, metrics={"quality_score": 0.95})
        
        logger.info(f"[PIPELINE] ✓ Auto-progressed dataset {dataset_id} through all stages")
        return pipeline


# Global singleton instance
pipeline_tracker = DataPipelineTracker()
