"""
Pydantic schemas for weight transfer operations
"""
from pydantic import BaseModel, Field
from typing import Dict, Any


class WeightUploadRequest(BaseModel):
    """Request to upload weights to central server"""
    model_id: int = Field(..., description="Local model ID to upload")
    round_number: int = Field(default=1, description="Federated learning round number")
    actual_hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Actual hyperparameters used during training")

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "round_number": 1,
                "actual_hyperparameters": {
                    "epochs": 5,
                    "batch_size": 32,
                    "learning_rate": 0.001
                }
            }
        }


class WeightUploadResponse(BaseModel):
    """
    Response after weight upload
    
    PHASE 41 GOVERNANCE:
    - Returns structured response with governance validation
    - Includes round_id for traceability
    - Includes checkpoint_hash for integrity
    """
    status: str
    round_id: int | None = None
    model_id: int
    weight_id: int | None = None
    hospital_id: int
    round_number: int
    weights_path: str
    checkpoint_hash: str | None = None
    mask_hash: str | None = None
    message: str
    mask_upload_required: bool = True
    mask_hash: str | None = None
    mask_payload: str | None = None


class MaskUploadRequest(BaseModel):
    """
    Request to upload MPC mask to server
    
    PHASE 41 GOVERNANCE:
    - model_id required to enforce mask prerequisites
    - mask_payload and mask_hash must match generation
    """
    model_id: int = Field(..., description="Trained model ID this mask belongs to")
    round_number: int = Field(..., description="Federated learning round number")
    mask_payload: str = Field(..., description="Serialized mask JSON")
    mask_hash: str | None = Field(default=None, description="Optional precomputed mask hash")


class MaskUploadResponse(BaseModel):
    """
    Response after mask upload
    
    PHASE 41 GOVERNANCE:
    - Returns structured response with governance validation
    - Includes round_id and model_id for traceability
    """
    status: str
    round_id: int | None = None
    model_id: int | None = None
    hospital_id: int
    round_number: int
    mask_path: str
    mask_hash: str


class MaskGenerationRequest(BaseModel):
    """Request to generate MPC mask"""
    model_id: int = Field(..., description="Trained model ID")
    dataset_id: int = Field(..., description="Dataset ID used for training")
    round_number: int = Field(default=1, description="Federated learning round number")


class MaskGenerationResponse(BaseModel):
    """Response with generated mask payload"""
    status: str
    model_id: int
    mask_payload: str
    mask_hash: str


class WeightExtractionResponse(BaseModel):
    """Response with extracted weights"""
    model_id: int
    hospital_id: int
    hospital_name: str
    round_number: int
    weights: Dict[str, Any]
    metadata: Dict[str, Any]
