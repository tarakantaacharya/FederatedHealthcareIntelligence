"""
Pydantic schemas for Dataset entity
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DatasetUploadResponse(BaseModel):
    """Response after successful dataset upload"""
    id: int
    hospital_id: int
    filename: str
    file_path: str
    file_size_bytes: int
    num_rows: Optional[int]
    num_columns: Optional[int]
    dataset_type: str
    column_names: Optional[List[str]]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Individual dataset in list response"""
    id: int
    hospital_id: int
    filename: str
    file_size_bytes: int
    num_rows: Optional[int]
    num_columns: Optional[int]
    dataset_type: str
    is_normalized: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DatasetDetailResponse(BaseModel):
    """Detailed dataset information"""
    id: int
    hospital_id: int
    filename: str
    file_path: str
    file_size_bytes: int
    num_rows: Optional[int]
    num_columns: Optional[int]
    dataset_type: str
    column_names: Optional[List[str]]
    is_normalized: bool
    normalized_path: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DatasetModelSummaryResponse(BaseModel):
    """Trained model summary for a dataset"""
    id: int
    model_name: str
    type: str
    architecture: str
    timestamp: datetime

    class Config:
        from_attributes = True
