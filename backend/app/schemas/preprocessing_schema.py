"""
Dataset Preprocessing Schemas

Pydantic schemas for preprocessing requests and responses
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class ColumnTypeInfo(BaseModel):
    """Column type information"""
    type: str
    pandas_dtype: str
    non_null_count: int
    null_count: int
    unique_count: int


class DataTypeDetectionResponse(BaseModel):
    """Response for data type detection"""
    columns: Dict[str, ColumnTypeInfo]
    total_rows: int
    detected_at: str


class ColumnQualityInfo(BaseModel):
    """Column quality information"""
    missing_count: int
    missing_percentage: float
    unique_count: int
    dtype: str
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None


class DataQualityResponse(BaseModel):
    """Response for data quality report"""
    total_rows: int
    total_columns: int
    missing_values: Dict[str, int]
    duplicates: Dict[str, Any]
    columns: Dict[str, ColumnQualityInfo]
    has_issues: bool


class MissingValueStrategy(BaseModel):
    """Strategy for handling missing values"""
    strategy: str = Field(..., description="'drop' or 'fill'")
    fill_value: Optional[Any] = Field(None, description="Value to use when strategy is 'fill'")


class DataCleaningRequest(BaseModel):
    """Request for data cleaning operations"""
    remove_duplicates: bool = False
    handle_missing: Optional[MissingValueStrategy] = None
    remove_columns: Optional[List[str]] = None
    rename_columns: Optional[Dict[str, str]] = None
    convert_types: Optional[Dict[str, str]] = None


class DataCleaningResponse(BaseModel):
    """Response for data cleaning operations"""
    success: bool
    original_shape: tuple
    new_shape: tuple
    operations_applied: List[str]
    created_backup: bool
    backup_path: Optional[str] = None


class DataPreviewResponse(BaseModel):
    """Response for dataset preview"""
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    dtypes: Dict[str, str]


class PreprocessingStatusResponse(BaseModel):
    """Response for preprocessing status"""
    dataset_id: int
    has_quality_issues: bool
    quality_report: Optional[DataQualityResponse] = None
    column_types: Optional[Dict[str, ColumnTypeInfo]] = None
    is_trained: bool
    backup_available: bool
