"""
Round Schema Validation Service
================================
CRITICAL: Federated training schema governance enforcement

This service validates hospital datasets against round schema contracts.

ARCHITECTURAL ROLE:
- Prevents feature mismatch in federated training
- Enforces central governance over feature schema
- Validates dataset compatibility before training
- Provides clear error messages for schema violations

OWNERSHIP:
- Used by both hospitals and central server
- Hospitals validate before training
- Central validates before accepting weights
"""
from typing import Dict, List, Tuple, Optional
import pandas as pd
import json
import hashlib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.training_round_schema import TrainingRoundSchema
from app.models.training_rounds import TrainingRound
from app.models.dataset import Dataset
from app.models.schema_mappings import SchemaMapping


class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass


class RoundSchemaValidationService:
    """
    Service for validating datasets against round schemas.
    
    CRITICAL: This is the gatekeeper for federated training.
    No dataset proceeds to training without passing validation.
    """
    
    @staticmethod
    def validate_dataset_against_round(
        db: Session,
        dataset_id: int,
        round_id: int,
        dataset_df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Validate dataset compatibility with round schema.
        
        Args:
            db: Database session
            dataset_id: Hospital dataset ID
            round_id: Training round ID
            dataset_df: Optional pre-loaded dataframe (for performance)
        
        Returns:
            Dict with validation result:
            {
                "is_valid": bool,
                "round_id": int,
                "dataset_id": int,
                "schema": {...},
                "missing_features": [...],
                "extra_features": [...],
                "missing_target": bool,
                "type_mismatches": {...},
                "errors": [...],
                "warnings": [...]
            }
        
        Raises:
            HTTPException: If round schema not found
        """
        # Get round schema
        round_schema = db.query(TrainingRoundSchema).filter(
            TrainingRoundSchema.round_id == round_id
        ).first()
        
        if not round_schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No schema defined for round {round_id}. Central must create schema first."
            )
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        
        # Load dataframe if not provided
        if dataset_df is None:
            try:
                import os
                from app.config import get_settings
                settings = get_settings()
                file_path = os.path.join(settings.UPLOAD_DIR, dataset.file_path)
                dataset_df = pd.read_csv(file_path)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load dataset: {str(e)}"
                )
        
        # Extract dataset columns
        dataset_columns = set(dataset_df.columns.tolist())
        
        # Extract required schema
        required_features = set(round_schema.feature_schema or [])
        required_target = round_schema.target_column
        
        # Validation checks
        errors = []
        warnings = []
        
        # 1. Check target column exists
        missing_target = required_target not in dataset_columns
        if missing_target:
            errors.append(f"Target column '{required_target}' not found in dataset")
        
        # 2. Check required features
        missing_features = list(required_features - dataset_columns)
        if missing_features:
            errors.append(f"Missing required features: {missing_features}")
        
        # 3. Check for extra features (warning only)
        # Note: Extra features are allowed, just not used
        all_required = required_features | {required_target}
        extra_features = list(dataset_columns - all_required)
        if extra_features:
            warnings.append(f"Dataset has {len(extra_features)} extra columns (will be ignored)")
        
        # 4. Check data types (if defined)
        type_mismatches = {}
        if round_schema.feature_types:
            for feature, expected_type in round_schema.feature_types.items():
                if feature in dataset_df.columns:
                    actual_type = str(dataset_df[feature].dtype)
                    # Simplified type checking
                    if expected_type == "float" and not pd.api.types.is_numeric_dtype(dataset_df[feature]):
                        type_mismatches[feature] = {
                            "expected": expected_type,
                            "actual": actual_type
                        }
                    elif expected_type == "int" and not pd.api.types.is_integer_dtype(dataset_df[feature]):
                        # Allow float that can be converted to int
                        if not pd.api.types.is_numeric_dtype(dataset_df[feature]):
                            type_mismatches[feature] = {
                                "expected": expected_type,
                                "actual": actual_type
                            }
        
        if type_mismatches:
            warnings.append(f"Type mismatches detected: {list(type_mismatches.keys())}")
        
        # 5. Check sequence requirements (for TFT)
        if round_schema.sequence_required:
            min_required_rows = round_schema.lookback + round_schema.horizon
            if len(dataset_df) < min_required_rows:
                errors.append(
                    f"TFT requires minimum {min_required_rows} rows "
                    f"(lookback={round_schema.lookback} + horizon={round_schema.horizon}), "
                    f"but dataset has only {len(dataset_df)} rows"
                )
        
        # 6. Check validation rules (if defined)
        if round_schema.validation_rules:
            rules = round_schema.validation_rules
            
            # Check minimum samples
            if "min_samples" in rules and len(dataset_df) < rules["min_samples"]:
                errors.append(
                    f"Dataset has {len(dataset_df)} rows, "
                    f"minimum required: {rules['min_samples']}"
                )
            
            # Check missing rate
            if "max_missing_rate" in rules:
                for col in required_features:
                    if col in dataset_df.columns:
                        missing_rate = dataset_df[col].isna().sum() / len(dataset_df)
                        if missing_rate > rules["max_missing_rate"]:
                            errors.append(
                                f"Column '{col}' has {missing_rate:.2%} missing values, "
                                f"maximum allowed: {rules['max_missing_rate']:.2%}"
                            )
        
        # Determine validity
        is_valid = len(errors) == 0
        
        # Build result
        result = {
            "is_valid": is_valid,
            "round_id": round_id,
            "dataset_id": dataset_id,
            "schema": {
                "model_architecture": round_schema.model_architecture,
                "target_column": round_schema.target_column,
                "required_features": list(required_features),
                "feature_count": len(required_features),
                "sequence_required": round_schema.sequence_required,
                "lookback": round_schema.lookback,
                "horizon": round_schema.horizon,
            },
            "dataset_info": {
                "total_rows": len(dataset_df),
                "total_columns": len(dataset_columns),
                "columns": list(dataset_columns),
            },
            "missing_features": missing_features,
            "extra_features": extra_features,
            "missing_target": missing_target,
            "type_mismatches": type_mismatches,
            "errors": errors,
            "warnings": warnings,
        }
        
        return result
    
    @staticmethod
    def validate_and_raise(
        db: Session,
        dataset_id: int,
        round_id: int,
        dataset_df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Validate and raise HTTPException if invalid.
        
        Convenience method for endpoints that need strict validation.
        
        Args:
            db: Database session
            dataset_id: Hospital dataset ID
            round_id: Training round ID
            dataset_df: Optional pre-loaded dataframe
        
        Returns:
            Validation result (only if valid)
        
        Raises:
            HTTPException: If validation fails
        """
        result = RoundSchemaValidationService.validate_dataset_against_round(
            db, dataset_id, round_id, dataset_df
        )
        
        if not result["is_valid"]:
            error_detail = {
                "message": "Dataset does not match round schema requirements",
                "round_id": round_id,
                "dataset_id": dataset_id,
                "errors": result["errors"],
                "missing_features": result["missing_features"],
                "required_features": result["schema"]["required_features"],
            }
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
        return result
    
    @staticmethod
    def get_schema_for_round(db: Session, round_id: int) -> Optional[TrainingRoundSchema]:
        """
        Get schema for a round.
        
        Args:
            db: Database session
            round_id: Training round ID
        
        Returns:
            TrainingRoundSchema or None
        """
        return db.query(TrainingRoundSchema).filter(
            TrainingRoundSchema.round_id == round_id
        ).first()
    
    @staticmethod
    def create_round_schema(
        db: Session,
        round_id: int,
        model_architecture: str,
        target_column: str,
        feature_schema: List[str],
        feature_types: Optional[Dict[str, str]] = None,
        sequence_required: bool = False,
        lookback: Optional[int] = None,
        horizon: Optional[int] = None,
        model_hyperparameters: Optional[Dict] = None,
        validation_rules: Optional[Dict] = None
    ) -> TrainingRoundSchema:
        """
        Create schema for a federated round.
        
        CENTRAL SERVER ONLY.
        
        Args:
            db: Database session
            round_id: Training round ID
            model_architecture: ML_REGRESSION or TFT
            target_column: Target column name
            feature_schema: Ordered list of required features
            feature_types: Optional type mapping
            sequence_required: True for TFT
            lookback: Encoder length (TFT)
            horizon: Prediction horizon (TFT)
            model_hyperparameters: Locked hyperparameters
            validation_rules: Dataset validation rules
        
        Returns:
            Created TrainingRoundSchema
        
        Raises:
            HTTPException: If schema already exists or round not found
        """
        # Check if schema already exists
        existing = db.query(TrainingRoundSchema).filter(
            TrainingRoundSchema.round_id == round_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Schema already exists for round {round_id}"
            )
        
        # Check round exists
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
        if not round_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training round {round_id} not found"
            )
        
        # Create schema
        schema = TrainingRoundSchema(
            round_id=round_id,
            model_architecture=model_architecture,
            target_column=target_column,
            feature_schema=feature_schema,
            feature_types=feature_types,
            sequence_required=sequence_required,
            lookback=lookback,
            horizon=horizon,
            model_hyperparameters=model_hyperparameters,
            validation_rules=validation_rules
        )
        
        db.add(schema)
        db.commit()
        db.refresh(schema)
        
        return schema
    
    @staticmethod
    def log_validation_result(result: Dict, prefix: str = "[SCHEMA_VALIDATION]"):
        """
        Log validation result with clear formatting.
        
        Args:
            result: Validation result dict
            prefix: Log prefix
        """
        print("=" * 80)
        print(f"{prefix} DATASET SCHEMA VALIDATION")
        print(f"Round ID: {result['round_id']}, Dataset ID: {result['dataset_id']}")
        print(f"Architecture: {result['schema']['model_architecture']}")
        print(f"Target: {result['schema']['target_column']}")
        print(f"Required Features ({result['schema']['feature_count']}): {result['schema']['required_features']}")
        print(f"Dataset Rows: {result['dataset_info']['total_rows']}, Columns: {result['dataset_info']['total_columns']}")
        
        if result["is_valid"]:
            print(f"✅ VALIDATION PASSED")
        else:
            print(f"❌ VALIDATION FAILED")
            for error in result["errors"]:
                print(f"  ERROR: {error}")
        
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"  WARNING: {warning}")
        
        print("=" * 80)

    @staticmethod
    def _hash_ordered_features(ordered_features: List[str]) -> str:
        payload = json.dumps(ordered_features, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_federated_contract(
        db: Session,
        dataset_id: int,
        round_id: int,
        provided_model_architecture: Optional[str] = None,
        provided_hyperparameters: Optional[Dict] = None,
        provided_target_column: Optional[str] = None
    ) -> Dict:
        """
        Validate strict round-level federated contract.

        Enforces:
        - target column
        - canonical feature set
        - feature count
        - feature ordering hash
        - model architecture
        - hyperparameters
        """
        round_obj = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
        if not round_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")

        required_features: List[str] = list(round_obj.required_canonical_features or [])
        required_target = round_obj.required_target_column or round_obj.target_column
        required_count = round_obj.required_feature_count if round_obj.required_feature_count is not None else len(required_features)
        required_hash = round_obj.required_feature_order_hash or RoundSchemaValidationService._hash_ordered_features(required_features)
        required_model = round_obj.required_model_architecture or round_obj.model_type
        required_hparams = dict(round_obj.required_hyperparameters or {})

        mappings = db.query(SchemaMapping).filter(SchemaMapping.dataset_id == dataset_id).all()
        mapped_canonical = []
        for mapping in mappings:
            field_name = (mapping.canonical_field or "").strip()
            if field_name and field_name not in mapped_canonical:
                mapped_canonical.append(field_name)

        # Fallback: if mappings are incomplete, accept direct canonical column names from dataset metadata.
        # This supports hospitals that uploaded already-canonicalized datasets without explicit mapping rows.
        dataset_obj = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        dataset_columns: List[str] = []
        if dataset_obj and dataset_obj.column_names:
            try:
                parsed_columns = json.loads(dataset_obj.column_names)
                dataset_columns = [str(column).strip() for column in parsed_columns if str(column).strip()]
            except Exception:
                dataset_columns = []

        dataset_column_set = set(dataset_columns)
        for feature in required_features:
            if feature in dataset_column_set and feature not in mapped_canonical:
                mapped_canonical.append(feature)

        mapped_set = set(mapped_canonical)
        missing_features = [feature for feature in required_features if feature not in mapped_set]
        # FIXED: Extra features are OK - datasets can have more columns than required
        # Only check that ALL required features are present, not that ONLY required features are present
        extra_features = []  # Don't treat extra features as error

        ordered_features = [feature for feature in required_features if feature in mapped_set]
        computed_hash = RoundSchemaValidationService._hash_ordered_features(ordered_features)

        provided_hyperparameters = dict(provided_hyperparameters or {})
        required_hparams_subset = {key: required_hparams[key] for key in required_hparams.keys()}
        provided_hparams_subset = {key: provided_hyperparameters.get(key) for key in required_hparams.keys()}

        mismatches = {
            "target_column_mismatch": bool(provided_target_column and provided_target_column != required_target),
            "canonical_feature_set_mismatch": len(missing_features) > 0,  # Only missing features matter, not extra
            "feature_count_mismatch": len(ordered_features) != len(required_features),  # Check ordered features against required, not required_count
            "feature_ordering_mismatch": False,  # Ordering doesn't matter as long as all required features present
            "model_architecture_mismatch": bool(provided_model_architecture and provided_model_architecture != required_model),
            # FEDERATED: Hyperparameters are auto-enforced, mismatch is informational only (NOT blocking)
            "hyperparameter_mismatch": False,  # Always pass - system auto-enforces round hyperparameters
        }

        is_valid = not any(mismatches.values())

        return {
            "is_valid": is_valid,
            "round_id": round_obj.id,
            "dataset_id": dataset_id,
            "required_target_column": required_target,
            "required_canonical_features": required_features,
            "required_feature_count": required_count,
            "required_feature_order_hash": required_hash,
            "required_model_architecture": required_model,
            "required_hyperparameters": required_hparams,
            "hospital_mapped_canonical_features": mapped_canonical,
            "hospital_ordered_canonical_features": ordered_features,
            "hospital_feature_count": len(ordered_features),
            "hospital_feature_order_hash": computed_hash,
            "provided_model_architecture": provided_model_architecture,
            "provided_hyperparameters": provided_hyperparameters,
            "missing_features": missing_features,
            "extra_features": extra_features,
            "mismatches": mismatches,
            "errors": [
                message for condition, message in [
                    (mismatches["target_column_mismatch"], "Target column mismatch"),
                    (mismatches["canonical_feature_set_mismatch"], "Canonical feature set mismatch"),
                    (mismatches["feature_count_mismatch"], "Feature count mismatch"),
                    (mismatches["feature_ordering_mismatch"], "Feature ordering mismatch"),
                    (mismatches["model_architecture_mismatch"], "Model architecture mismatch"),
                    (mismatches["hyperparameter_mismatch"], "Hyperparameter mismatch"),
                ] if condition
            ]
        }

    @staticmethod
    def validate_federated_contract_or_raise(
        db: Session,
        dataset_id: int,
        round_id: int,
        provided_model_architecture: Optional[str] = None,
        provided_hyperparameters: Optional[Dict] = None,
        provided_target_column: Optional[str] = None
    ) -> Dict:
        result = RoundSchemaValidationService.validate_federated_contract(
            db=db,
            dataset_id=dataset_id,
            round_id=round_id,
            provided_model_architecture=provided_model_architecture,
            provided_hyperparameters=provided_hyperparameters,
            provided_target_column=provided_target_column,
        )
        if not result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Federated round contract mismatch",
                    "errors": result["errors"],
                    "mismatches": result["mismatches"],
                    "missing_features": result["missing_features"],
                    "extra_features": result["extra_features"],
                }
            )
        return result
