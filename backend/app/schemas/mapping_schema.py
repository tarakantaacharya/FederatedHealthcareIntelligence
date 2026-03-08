"""
Pydantic schemas for mapping operations
"""
from pydantic import BaseModel
from typing import Dict, List


class Mapping(BaseModel):
    original_column: str
    canonical_field: str
    confidence: float


class AutoMapResponse(BaseModel):
    dataset_id: int
    mappings: List[Mapping]
    unmapped_columns: List[str]
    total_columns: int
    mapped_count: int
    unmapped_count: int
    mapping_success_rate: float


class ManualMappingRequest(BaseModel):
    dataset_id: int
    mappings: Dict[str, str]
