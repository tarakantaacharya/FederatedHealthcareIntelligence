"""
Pydantic schemas for model metadata retrieval
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ModelMetadataResponse(BaseModel):
    """Metadata required for prediction input rendering and model info"""
    model_architecture: str
    training_type: str
    target_column: Optional[str] = None
    trained_feature_columns: List[str]
    feature_count: Optional[int] = None
    # Multi-model training metadata (for LOCAL ML_REGRESSION)
    candidate_models: Optional[List[str]] = None
    best_model: Optional[str] = None
    all_model_metrics: Optional[Dict[str, Any]] = None
    test_r2: Optional[float] = None
    test_rmse: Optional[float] = None
    test_mae: Optional[float] = None
    test_mape: Optional[float] = None

    class Config:
        from_attributes = True
