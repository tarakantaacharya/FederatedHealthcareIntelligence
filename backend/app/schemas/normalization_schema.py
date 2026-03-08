"""
Pydantic schemas for normalization operations
"""
from pydantic import BaseModel
from typing import List, Dict, Any


class NormalizeRequest(BaseModel):
    """Request to normalize dataset"""
    dataset_id: int


class ValidationResult(BaseModel):
    """Validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_fields: List[str]
    total_rows: int


class NormalizeResponse(BaseModel):
    """Normalization response"""
    status: str
    dataset_id: int
    original_path: str
    normalized_path: str
    original_rows: int
    normalized_rows: int
    original_columns: int
    normalized_columns: int
    validation: ValidationResult
    normalized_at: str


class NormalizedPreviewResponse(BaseModel):
    """Normalized data preview"""
    dataset_id: int
    num_rows: int
    columns: List[str]
    data: List[Dict[str, Any]]
