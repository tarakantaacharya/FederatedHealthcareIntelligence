"""
Round Schema Management API Routes

Endpoints:
- POST /api/rounds/{round_id}/schema (ADMIN) - Create/update round schema
- GET /api/rounds/{round_id}/schema (PUBLIC) - Fetch round schema
- POST /api/training/validate-dataset (HOSPITAL) - Pre-validate dataset before training

GOVERNANCE:
- Central server creates and locks schema
- Hospitals view read-only schema
- Validation prevents mismatched training
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional, List, Any
from pydantic import BaseModel

from app.database import get_db
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound
from app.models.training_round_schema import TrainingRoundSchema
from app.models.dataset import Dataset
from app.utils.auth import require_role
from app.services.round_schema_validation_service import RoundSchemaValidationService

router = APIRouter(prefix="/api", tags=["round-schema"])

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class RoundSchemaCreateRequest(BaseModel):
    """Central server creates schema contract for round"""
    model_architecture: str  # "ML_REGRESSION" or "TFT"
    target_column: str
    feature_schema: List[str]  # Ordered list of required features
    feature_types: Optional[Dict[str, str]] = None  # Feature name -> data type mapping
    sequence_required: Optional[bool] = False
    lookback: Optional[int] = None
    horizon: Optional[int] = None
    model_hyperparameters: Optional[Dict] = None
    validation_rules: Optional[Dict] = None  # min_samples, max_missing_rate

class RoundSchemaResponse(BaseModel):
    """Schema contract response"""
    id: int
    round_id: int
    model_architecture: str
    target_column: str
    feature_schema: List[str]
    feature_types: Optional[Dict[str, str]]
    sequence_required: bool
    lookback: Optional[int]
    horizon: Optional[int]
    model_hyperparameters: Optional[Dict]
    validation_rules: Optional[Dict]
    
    class Config:
        from_attributes = True

class DatasetValidationRequest(BaseModel):
    """Hospital pre-validates dataset before federated training"""
    dataset_id: int
    round_id: int

class DatasetValidationResponse(BaseModel):
    """Validation result with actionable feedback"""
    is_valid: bool
    dataset_id: int
    round_id: int
    schema: Dict
    missing_features: List[str]
    extra_features: List[str]
    missing_target: bool
    type_mismatches: Dict[str, tuple]  # feature -> (expected, actual)
    errors: List[str]
    warnings: List[str]

# ============================================================================
# ROUTES
# ============================================================================

@router.post("/rounds/{round_id}/schema")
def create_round_schema(
    round_id: int,
    request: RoundSchemaCreateRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))  # ADMIN ONLY
) -> RoundSchemaResponse:
    """
    CENTRAL SERVER ONLY - Create schema governance contract for round.
    
    This locks:
    - Target column (hospitals cannot change)
    - Feature schema (hospitals must provide exactly these)
    - Model architecture (ML_REGRESSION or TFT)
    - Hyperparameters (central controls model config)
    
    HTTP Exceptions:
    - 403: Not an admin
    - 404: Round not found
    - 400: Invalid parameters
    - 409: Schema already exists for round
    """
    print(f"\n{'='*80}")
    user_id = current_user.get('id') or current_user.get('hospital_id') or 'unknown'
    print(f"[ROUND_SCHEMA_CREATE] ADMIN {user_id} creating schema for round {round_id}")
    print(f"{'='*80}")
    
    # Verify round exists
    round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
    if not round_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {round_id} not found"
        )
    
    # Check if schema already exists
    existing_schema = db.query(TrainingRoundSchema).filter(
        TrainingRoundSchema.round_id == round_id
    ).first()
    if existing_schema:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schema already exists for round {round_id}. Delete the round to create a new one."
        )
    
    # Validate parameters
    if request.model_architecture not in ["ML_REGRESSION", "TFT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_architecture: {request.model_architecture}. Must be 'ML_REGRESSION' or 'TFT'"
        )
    
    if not request.target_column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_column is required"
        )
    
    if not request.feature_schema or len(request.feature_schema) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="feature_schema cannot be empty"
        )
    
    if request.target_column in request.feature_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_column cannot be in feature_schema"
        )
    
    if request.model_architecture == "TFT":
        if request.lookback is None or request.horizon is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TFT requires lookback and horizon parameters"
            )
        if request.lookback < 1 or request.horizon < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="lookback and horizon must be >= 1"
            )
    
    print(f"[ROUND_SCHEMA_CREATE] PASS Validation passed")
    print(f"  Architecture: {request.model_architecture}")
    print(f"  Target: {request.target_column}")
    print(f"  Features: {len(request.feature_schema)} required")
    print(f"  Feature list: {request.feature_schema}")
    
    # Create schema
    schema = TrainingRoundSchema(
        round_id=round_id,
        model_architecture=request.model_architecture,
        target_column=request.target_column,
        feature_schema=request.feature_schema,
        feature_types=request.feature_types,
        sequence_required=request.sequence_required or False,
        lookback=request.lookback,
        horizon=request.horizon,
        model_hyperparameters=request.model_hyperparameters,
        validation_rules=request.validation_rules
    )
    
    db.add(schema)
    db.commit()
    db.refresh(schema)
    
    print(f"[ROUND_SCHEMA_CREATE] PASS Schema created (id={schema.id})")
    print(f"{'='*80}\n")
    
    return RoundSchemaResponse.model_validate(schema)

@router.get("/rounds/{round_id}/schema")
def get_round_schema(
    round_id: int,
    db: Session = Depends(get_db)
) -> RoundSchemaResponse:
    """
    Fetch round schema (PUBLIC - hospitals need to see what's locked).
    
    Returns:
    - Full schema if exists
    - 404 if schema doesn't exist (no round schema governance for this round)
    """
    print(f"[ROUND_SCHEMA_GET] Fetching schema for round {round_id}")
    
    schema = db.query(TrainingRoundSchema).filter(
        TrainingRoundSchema.round_id == round_id
    ).first()
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schema defined for round {round_id}. Round may not require schema governance."
        )
    
    print(f"[ROUND_SCHEMA_GET] PASS Found schema: {schema.model_architecture}, target={schema.target_column}, features={len(schema.feature_schema)}")
    
    return RoundSchemaResponse.model_validate(schema)

@router.post("/training/validate-dataset", response_model=DatasetValidationResponse)
def validate_dataset_for_federated_training(
    request: DatasetValidationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("HOSPITAL"))
) -> DatasetValidationResponse:
    """
    HOSPITAL - Pre-validate dataset before federated training.
    
    Hospitals call this BEFORE training to:
    1. Check if their dataset matches round schema
    2. Get actionable feedback on mismatches
    3. Optionally perform field mapping
    
    Returns:
    - is_valid: True if dataset ready for training
    - missing_features: Columns needed but not in dataset
    - extra_features: Columns in dataset but not needed
    - type_mismatches: Type conflicts (if schema specifies types)
    - errors: Validation failures (BLOCKS training)
    - warnings: Non-blocking issues
    
    HTTP Exceptions:
    - 404: Dataset not found or round schema not found
    - 403: Access denied to dataset
    """
    print(f"\n{'='*80}")
    print(f"[DATASET_VALIDATE] HOSPITAL {current_user['hospital_id']} validating dataset {request.dataset_id} against round {request.round_id}")
    print(f"{'='*80}")
    
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.hospital_id == current_user['db_object'].id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Get round schema
    schema = db.query(TrainingRoundSchema).filter(
        TrainingRoundSchema.round_id == request.round_id
    ).first()
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {request.round_id} has no schema defined"
        )
    
    # Validate dataset against schema
    validation_result = RoundSchemaValidationService.validate_dataset_against_round(
        db=db,
        dataset_id=request.dataset_id,
        round_id=request.round_id
    )
    
    # Log validation result
    RoundSchemaValidationService.log_validation_result(validation_result, prefix="[DATASET_VALIDATE]")
    print(f"{'='*80}\n")
    
    # Build response
    return DatasetValidationResponse(
        is_valid=validation_result['is_valid'],
        dataset_id=validation_result['dataset_id'],
        round_id=validation_result['round_id'],
        schema=validation_result['schema'],
        missing_features=validation_result['missing_features'],
        extra_features=validation_result['extra_features'],
        missing_target=validation_result['missing_target'],
        type_mismatches=validation_result['type_mismatches'],
        errors=validation_result['errors'],
        warnings=validation_result['warnings']
    )

@router.get("/rounds/{round_id}/schema/summary")
def get_round_schema_summary(
    round_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get simplified schema summary for UI display (read-only card).
    
    Returns only essential info for hospital UI:
    - Model type
    - Target column
    - Feature count
    - Sequence required
    """
    schema = db.query(TrainingRoundSchema).filter(
        TrainingRoundSchema.round_id == round_id
    ).first()
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schema for round {round_id}"
        )
    
    return {
        "round_id": round_id,
        "model_architecture": schema.model_architecture,
        "target_column": schema.target_column,
        "required_feature_count": len(schema.feature_schema),
        "sequence_required": schema.sequence_required,
        "lookback": schema.lookback,
        "horizon": schema.horizon,
        "is_locked": True  # Always true - schemas are immutable once created
    }

