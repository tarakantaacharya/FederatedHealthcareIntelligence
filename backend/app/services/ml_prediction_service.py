"""
ML_REGRESSION Prediction Service
Single-point regression prediction using sklearn models
Supports both legacy single models and multi-model pipelines
STRICTLY for ML_REGRESSION - NO TFT logic
"""
import pandas as pd
import numpy as np
import pickle
import os
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import Dict
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.models.prediction_record import PredictionRecord
from app.models.dataset import Dataset
from app.ml.multi_model_pipeline import MultiModelMLPipeline
from app.config import get_settings

settings = get_settings()

class MLPredictionService:
    """Service for ML_REGRESSION single-point predictions ONLY"""

    @staticmethod
    def _build_effective_features(
        required_features: list[str],
        provided_features: Dict[str, float]
    ) -> tuple[Dict[str, float], list[str], list[str], list[str]]:
        """
        Build effective feature payload by auto-synthesizing temporal features.

        Rules:
        - If required feature is explicitly provided, use it.
        - If required feature is `<base>_lag_<n>` and `<base>` exists, reuse base value.
        - If required feature is `<base>_rollmean_<n>` and `<base>` exists, reuse base value.
        - Otherwise mark as missing.
        """
        effective_features: Dict[str, float] = {}
        auto_generated: list[str] = []

        for feature_name in required_features:
            if feature_name in provided_features:
                effective_features[feature_name] = float(provided_features[feature_name])
                continue

            synthesized_value = None

            if "_lag_" in feature_name:
                base_name = feature_name.rsplit("_lag_", 1)[0]
                if base_name in provided_features:
                    synthesized_value = float(provided_features[base_name])

            elif "_rollmean_" in feature_name:
                base_name = feature_name.rsplit("_rollmean_", 1)[0]
                if base_name in provided_features:
                    synthesized_value = float(provided_features[base_name])

            if synthesized_value is not None:
                effective_features[feature_name] = synthesized_value
                auto_generated.append(feature_name)

        required_set = set(required_features)
        effective_set = set(effective_features.keys())
        provided_set = set(provided_features.keys())

        missing_features = sorted(list(required_set - effective_set))
        extra_features = sorted(list(provided_set - required_set))

        return effective_features, missing_features, extra_features, auto_generated
    
    @staticmethod
    def predict(
        hospital: Hospital,
        model_id: int,
        features: Dict[str, float],
        db: Session
    ) -> Dict:
        """
        Generate single-point prediction using ML_REGRESSION model
        
        Args:
            hospital: Hospital object
            model_id: Model weights ID (MUST be ML_REGRESSION)
            features: Dictionary of feature names to values
            db: Database session
        
        Returns:
            Single prediction value with metadata
        
        Raises:
            HTTPException: If model not found, wrong architecture, or validation fails
        """
        # Get model (allow LOCAL, FEDERATED, and approved GLOBAL models)
        # Global models have hospital_id == None, local models have hospital_id == hospital.id
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id,
            (ModelWeights.hospital_id == hospital.id) | (ModelWeights.hospital_id == None)
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # STRICT architecture validation (CRITICAL: Prevent TFT/forecasting models from accepting single-point requests)
        if model.model_architecture != "ML_REGRESSION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Model {model_id} is {model.model_architecture}. "
                    "This endpoint only accepts ML_REGRESSION models. "
                    "Use POST /api/predictions/tft for TFT models."
                )
            )
        
        # Verify access
        if model.hospital_id and model.hospital_id != hospital.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to model {model_id}"
            )
        
        # Get training schema for feature validation (CRITICAL SECTION)
        if not model.training_schema:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model_id} missing training schema metadata"
            )
        
        # Extract required features (try both field names for backwards compatibility)
        required_features = (
            model.training_schema.get("feature_columns") or
            model.training_schema.get("required_columns") or
            []
        )
        target_column = model.training_schema.get("target_column")
        
        if not required_features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model_id} has no feature columns in training schema"
            )
        
        if not target_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model_id} has no target_column in training schema"
            )
        
        # VALIDATION: Ensure target column is NOT in the feature list (sanity check)
        if target_column in required_features:
            print(f"[ML_PREDICT_ERROR] TARGET COLUMN IN FEATURES! target={target_column}, features={required_features}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training schema error: target column '{target_column}' appears in feature list"
            )
        
        # FEATURE VALIDATION + AUTO-SYNTHESIS:
        # allow minimal/base feature input and derive temporal features internally.
        effective_features, missing_features, extra_features, auto_generated = MLPredictionService._build_effective_features(
            required_features=required_features,
            provided_features=features
        )
        provided_features = set(features.keys())

        # COMPREHENSIVE CONSOLE LOGGING
        print(f"\n{'='*80}")
        print(f"[ML_PREDICT] PREDICTION REQUEST VALIDATION")
        print(f"{'='*80}")
        
        # Check if this is a multi-model pipeline
        is_multi_model = (
            "candidate_models" in model.training_schema or
            "best_model" in model.training_schema
        )
        
        print(f"[ML_PREDICT] MODEL: id={model_id}, architecture={model.model_architecture}, training_type={model.training_type}")
        print(f"[ML_PREDICT] MODEL_TYPE: {'MULTI_MODEL_PIPELINE' if is_multi_model else 'LEGACY_SINGLE_MODEL'}")
        if is_multi_model:
            best_model = model.training_schema.get('best_model', 'unknown')
            candidate_models = model.training_schema.get('candidate_models', [])
            print(f"[ML_PREDICT] BEST_MODEL: {best_model}")
            print(f"[ML_PREDICT] CANDIDATES: {', '.join(candidate_models)}")
        print(f"[ML_PREDICT] TARGET: {target_column}")
        print(f"[ML_PREDICT] TRAINED FEATURES ({len(required_features)}): {sorted(required_features)}")
        print(f"[ML_PREDICT] PROVIDED FEATURES ({len(provided_features)}): {sorted(provided_features) if provided_features else 'NONE'}")
        
        if missing_features:
            print(f"[ML_PREDICT_ERROR] MISSING FEATURES: {sorted(missing_features)}")
        if extra_features:
            print(f"[ML_PREDICT_WARNING] EXTRA FEATURES: {sorted(extra_features)}")
        if auto_generated:
            print(f"[ML_PREDICT_INFO] AUTO-GENERATED FEATURES ({len(auto_generated)}): {sorted(auto_generated)}")
        
        if not missing_features and not extra_features:
            print(f"[ML_PREDICT_OK] Feature validation PASSED - exact match")
        
        print(f"{'='*80}\n")
        
        # REJECT if features don't match exactly
        if missing_features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Missing required features: {sorted(list(missing_features))}. "
                    f"Model was trained on: {sorted(required_features)}"
                )
            )
        
        # Load model based on type
        if not model.model_path or not os.path.exists(model.model_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model file not found at {model.model_path}"
            )
        
        # Detect federated JSON weight artifacts even if DB flags drift.
        # Some approved/distributed models are stored as a single JSON file with "weights".
        is_json_artifact = str(model.model_path).lower().endswith('.json')
        is_global_federated = (model.is_global and model.hospital_id is None)
        if is_json_artifact:
            try:
                import json
                with open(model.model_path, 'r') as f:
                    json_probe = json.load(f)
                if isinstance(json_probe, dict) and isinstance(json_probe.get("weights"), dict):
                    is_global_federated = True
            except Exception:
                # Non-weight JSON files should continue through normal branch checks.
                pass
        
        # Check if this is a multi-model pipeline (only for LOCAL models)
        is_multi_model = (
            not is_global_federated and
            model.training_schema and
            ("candidate_models" in model.training_schema or "best_model" in model.training_schema)
        )
        
        if is_global_federated:
            # Load global federated model (JSON with averaged weights)
            try:
                import json
                with open(model.model_path, 'r') as f:
                    weights_data = json.load(f)
                
                # Create sklearn LinearRegression model and set coefficients
                from sklearn.linear_model import LinearRegression
                sklearn_model = LinearRegression()
                
                # Set the coefficients from aggregated weights
                sklearn_model.coef_ = np.array(weights_data["weights"].get("coef", []))
                sklearn_model.intercept_ = weights_data["weights"].get("intercept", 0.0)
                
                print(f"[ML_PREDICT] Loaded global federated model from {model.model_path}")
                print(f"[ML_PREDICT] Round {weights_data.get('round_number')}, {weights_data.get('num_hospitals')} hospitals")
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load global federated model: {str(e)}"
                )
        elif is_multi_model:
            # Load multi-model pipeline
            try:
                # Model path can be a pipeline metadata file or a model directory.
                # For JSON artifacts, only use pipeline loader when pipeline metadata exists.
                if str(model.model_path).lower().endswith('pipeline_metadata.json') or str(model.model_path).lower().endswith('multi_model_metadata.json'):
                    model_dir = os.path.dirname(model.model_path)
                elif str(model.model_path).lower().endswith('.json'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Model {model_id} points to JSON weights artifact, not a pipeline directory: "
                            f"{model.model_path}"
                        )
                    )
                else:
                    model_dir = model.model_path
                
                pipeline = MultiModelMLPipeline()
                pipeline.load_models(model_dir)
                
                print(f"[ML_PREDICT] Loaded MultiModelMLPipeline from {model_dir}")
                print(f"[ML_PREDICT] Using {pipeline.selection_strategy} strategy with model: {pipeline.best_model_name}")
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load multi-model pipeline: {str(e)}"
                )
        else:
            # Load legacy single pickle model
            try:
                with open(model.model_path, 'rb') as f:
                    sklearn_model = pickle.load(f)
                print(f"[ML_PREDICT] Loaded legacy single model from {model.model_path}")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load model: {str(e)}"
                )
        
        # Prepare feature vector in trained order
        try:
            feature_vector = np.array([
                effective_features[col] for col in required_features
            ]).reshape(1, -1)
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Feature {str(e)} not found in input"
            )
        
        # Generate prediction using appropriate model
        try:
            if is_multi_model:
                # Use pipeline's predict method (automatically uses best model or ensemble)
                prediction_value = float(pipeline.predict(feature_vector)[0])
            else:
                # Use legacy single model
                prediction_value = float(sklearn_model.predict(feature_vector)[0])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prediction failed: {str(e)}"
            )
        
        # Build response
        model_type = "global_federated" if is_global_federated else ("multi_model" if is_multi_model else "single_model")
        
        response = {
            "model_architecture": "ML_REGRESSION",
            "model_id": model_id,
            "training_type": model.training_type or "FEDERATED",
            "model_type": model_type,
            "target_column": target_column,
            "prediction": prediction_value,
            "input_features": effective_features,
            "feature_count": len(required_features),
            "timestamp": datetime.now().isoformat(),
            
            # NEW: Add metrics for UI display
            "model_accuracy": {
                "r2": model.local_r2 if model.local_r2 is not None else 0.0,
                "rmse": model.local_rmse if model.local_rmse is not None else 0.0,
                "mape": model.local_mape if model.local_mape is not None else 0.0,
                "mae": model.local_mae if model.local_mae is not None else 0.0
            }
        }
        
        # Add confidence interval if RMSE available
        if model.local_rmse and model.local_rmse > 0:
            margin_of_error = 1.96 * model.local_rmse
            response["confidence_interval"] = {
                "lower": float(prediction_value - margin_of_error),
                "upper": float(prediction_value + margin_of_error),
                "confidence_level": 0.95,
                "margin_of_error": float(margin_of_error)
            }
        
        # Generate AI summary if Gemini available
        ai_summary = None
        try:
            from app.services.gemini_service import GeminiService
            if settings.ENABLE_AI_SUMMARIES:
                forecast_values = [prediction_value]
                metrics_dict = {
                    "r2": model.local_r2 or 0,
                    "rmse": model.local_rmse or 0,
                    "mape": model.local_mape or 0,
                    "mae": model.local_mae or 0
                }
                ai_summary = GeminiService.generate_prediction_summary(
                    {
                        "target_column": target_column or "target",
                        "forecast_horizon": 0,
                        "model_type": "ML_REGRESSION"
                    },
                    forecast_values,
                    metrics_dict,
                    {"hospital_name": hospital.hospital_name if hospital else "Unknown", "model_arch": "ML_REGRESSION"}
                )
                if ai_summary:
                    response["ai_summary"] = ai_summary
        except Exception:
            pass

        # Always provide a baseline explanation when AI provider is unavailable
        if not response.get("ai_summary"):
            r2 = response["model_accuracy"].get("r2", 0.0)
            rmse = response["model_accuracy"].get("rmse", 0.0)
            mape = response["model_accuracy"].get("mape", 0.0)
            response["ai_summary"] = (
                f"Predicted {target_column}: {prediction_value:.2f}. "
                f"Model quality snapshot - R2: {r2:.3f}, RMSE: {rmse:.3f}, MAPE: {mape:.2f}%. "
                "This summary is generated locally because AI summarization is unavailable."
            )
        
        # Add multi-model specific metadata if available
        if is_multi_model:
            response["best_model"] = model.training_schema.get("best_model")
            response["selection_strategy"] = model.training_schema.get("selection_strategy")
            response["candidate_models"] = model.training_schema.get("candidate_models", [])
        
        return response
    
    @staticmethod
    def validate_features(
        model_id: int,
        features: Dict[str, float],
        db: Session
    ) -> Dict:
        """
        Validate if provided features match model training schema
        
        Args:
            model_id: Model ID
            features: Dictionary of feature names to values
            db: Database session
        
        Returns:
            Validation result dictionary
        """
        # Get model (allow LOCAL, FEDERATED, and approved GLOBAL models)
        # No hospital filter needed for validation - any model ID is valid
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # Check architecture
        if model.model_architecture != "ML_REGRESSION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Model {model_id} is {model.model_architecture}. "
                    "This validation endpoint is for ML_REGRESSION models only."
                )
            )
        
        # Get training schema
        if not model.training_schema:
            return {
                "is_valid": False,
                "model_id": model_id,
                "required_features": [],
                "provided_features": list(features.keys()),
                "missing_features": [],
                "extra_features": list(features.keys()),
                "warnings": ["Model has no training schema metadata"],
                "can_proceed": False
            }
        
        # Check both field names for backwards compatibility
        required_features = (
            model.training_schema.get("feature_columns") or 
            model.training_schema.get("required_columns") or 
            []
        )
        provided_features = list(features.keys())
        
        effective_features, missing_features, extra_features, auto_generated = MLPredictionService._build_effective_features(
            required_features=required_features,
            provided_features=features
        )

        print(
            f"[ML_VALIDATE] model_id={model_id} "
            f"required={required_features} "
            f"provided={provided_features} "
            f"missing={missing_features} "
            f"extra={extra_features}"
        )
        
        warnings = []
        if extra_features:
            warnings.append(f"Extra features will be ignored: {extra_features}")
        if missing_features:
            warnings.append(f"Missing required features: {missing_features}")
        if auto_generated:
            warnings.append(
                f"Auto-generated temporal features from base inputs: {sorted(auto_generated)}"
            )
        
        is_valid = len(missing_features) == 0
        can_proceed = is_valid
        
        return {
            "is_valid": is_valid,
            "model_id": model_id,
            "required_features": required_features,
            "provided_features": provided_features,
            "missing_features": missing_features,
            "extra_features": extra_features,
            "warnings": warnings,
            "can_proceed": can_proceed
        }
    
    @staticmethod
    def save_prediction(
        hospital: Hospital,
        model_id: int,
        features: Dict[str, float],
        prediction: float,
        dataset_id: int = None,
        db: Session = None
    ) -> Dict:
        """
        Save ML prediction result to database
        
        Args:
            hospital: Hospital object
            model_id: Model ID used
            features: Input features
            prediction: Predicted value
            dataset_id: Optional dataset ID
            db: Database session
        
        Returns:
            Saved record information
        """
        # Get model to extract metadata (allow LOCAL, FEDERATED, and approved GLOBAL models)
        # Global models have hospital_id == None, local models have hospital_id == hospital.id
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id,
            (ModelWeights.hospital_id == hospital.id) | (ModelWeights.hospital_id == None)
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        target_column = None
        if model.training_schema:
            target_column = model.training_schema.get("target_column")
        
        # Build comprehensive forecast_data for ML predictions (parallel to TFT)
        forecast_data = {
            "prediction": prediction,
            "type": "ML_REGRESSION",
            "quality_metrics": {
                "r2": model.local_r2,
                "rmse": model.local_rmse,
                "mape": model.local_mape,
                "mae": model.local_mae
            },
            "regression_metrics": {
                "mse": model.local_mse,
                "adjusted_r2": model.local_adjusted_r2,
                "smape": model.local_smape,
                "wape": model.local_wape,
                "mase": model.local_mase,
                "rmsle": model.local_rmsle
            },
            "training_info": {
                "model_type": model.model_type,
                "model_architecture": model.model_architecture,
                "training_type": model.training_type.value if hasattr(model.training_type, 'value') else str(model.training_type),
                "loss": model.local_loss
            }
        }
        
        # Generate AI summary if Gemini is available
        ai_summary = ""
        try:
            from app.services.gemini_service import GeminiService
            if settings.ENABLE_AI_SUMMARIES:
                forecast_values = [prediction]  # Single point for ML
                metrics_dict = {
                    "r2": model.local_r2 or 0,
                    "rmse": model.local_rmse or 0,
                    "mape": model.local_mape or 0,
                    "mae": model.local_mae or 0
                }
                ai_summary = GeminiService.generate_prediction_summary(
                    {
                        "target_column": target_column or "target",
                        "forecast_horizon": 0,
                        "model_type": "ML_REGRESSION"
                    },
                    forecast_values,
                    metrics_dict,
                    {"hospital_name": hospital.hospital_name, "model_arch": model.model_architecture}
                )
                forecast_data["ai_summary"] = ai_summary
        except Exception as e:
            print(f"[Warning] Could not generate AI summary for ML prediction: {str(e)}")
        
        # Calculate confidence interval based on RMSE (±1.96*RMSE at 95% confidence)
        if model.local_rmse:
            margin_of_error = 1.96 * model.local_rmse
            forecast_data["confidence_interval"] = {
                "lower": prediction - margin_of_error,
                "upper": prediction + margin_of_error,
                "confidence_level": 0.95,
                "margin_of_error": margin_of_error
            }
        
        # Add model accuracy snapshot for UI display
        model_accuracy_snapshot = {
            "r2": model.local_r2,
            "rmse": model.local_rmse,
            "mape": model.local_mape,
            "mae": model.local_mae
        }
        
        # Add governance data
        governance_data = {
            "model_type": model.model_type,
            "training_type": model.training_type.value if hasattr(model.training_type, 'value') else str(model.training_type),
            "dp_epsilon_used": model.epsilon_spent,
            "contribution_weight": None  # ML predictions are local, no contribution weight
        }
        forecast_data["governance"] = governance_data
        
        # Resolve dataset_id automatically if not provided
        resolved_dataset_id = dataset_id or model.dataset_id

        # Persist chart-ready series so Prediction Detail can render non-empty graphics.
        # ML predictions are single-point, so we store one predicted value and best-available
        # reference actual value from dataset tail when possible.
        forecast_data["predicted_values"] = [float(prediction)]
        forecast_data["actual_values"] = []

        if resolved_dataset_id and target_column:
            dataset = db.query(Dataset).filter(Dataset.id == resolved_dataset_id).first()
            if dataset and dataset.file_path and os.path.exists(dataset.file_path):
                try:
                    df = pd.read_csv(dataset.file_path)
                    if target_column in df.columns:
                        tail_series = df[target_column].dropna()
                        if not tail_series.empty:
                            forecast_data["actual_values"] = [float(tail_series.iloc[-1])]
                except Exception as ex:
                    # Non-fatal: prediction should still be saved even if dataset preview fails.
                    print(f"[ML_SAVE] Could not extract actual_values: {str(ex)}")

        # Create prediction record
        record = PredictionRecord(
            hospital_id=hospital.id,
            model_id=model_id,
            dataset_id=resolved_dataset_id,
            round_id=model.round_id,
            round_number=model.round_number,
            target_column=target_column,
            forecast_horizon=0,  # ML = no horizon
            prediction_timestamp=datetime.now(),
            prediction_value=prediction,
            input_snapshot=features,
            forecast_data=forecast_data,
            model_accuracy_snapshot=model_accuracy_snapshot,
            summary_text=ai_summary or f"ML Regression: {target_column}={prediction:.2f} (R²={model.local_r2:.4f if model.local_r2 else 'N/A'})"
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "prediction_record_id": record.id,
            "message": "ML prediction saved successfully",
            "timestamp": record.created_at.isoformat()
        }
    
    @staticmethod
    def list_predictions(
        hospital: Hospital,
        db: Session,
        limit: int = 20
    ) -> Dict:
        """
        List saved ML predictions for hospital
        
        Args:
            hospital: Hospital object
            db: Database session
            limit: Maximum number of records to return
        
        Returns:
            List of prediction records
        """
        # Query only ML predictions (prediction_value is not null, forecast_horizon = 0)
        records = db.query(PredictionRecord).join(
            ModelWeights, PredictionRecord.model_id == ModelWeights.id
        ).filter(
            PredictionRecord.hospital_id == hospital.id,
            ModelWeights.model_architecture == "ML_REGRESSION",
            PredictionRecord.prediction_value.isnot(None)
        ).order_by(
            PredictionRecord.created_at.desc()
        ).limit(limit).all()
        
        predictions = []
        for record in records:
            # Extract model accuracy from snapshot
            model_accuracy = {}
            if record.model_accuracy_snapshot and isinstance(record.model_accuracy_snapshot, dict):
                model_accuracy = {
                    "r2": record.model_accuracy_snapshot.get("r2"),
                    "rmse": record.model_accuracy_snapshot.get("rmse"),
                    "mape": record.model_accuracy_snapshot.get("mape")
                }
            
            predictions.append({
                # Core prediction data
                "id": record.id,
                "model_id": record.model_id,
                "model_type": record.model.model_type if record.model else None,
                "model_architecture": record.model.model_architecture if record.model else None,
                "dataset_id": record.dataset_id,
                "dataset_name": record.dataset.filename if record.dataset else None,
                "round_number": record.round_number,
                "target_column": record.target_column,
                "prediction_value": record.prediction_value,
                "forecast_horizon": record.forecast_horizon,
                "input_snapshot": record.input_snapshot or {},
                
                # Rich metadata
                "feature_importance": record.feature_importance or {},
                "confidence_interval": record.confidence_interval or {},
                "model_accuracy": model_accuracy,
                
                # Governance & privacy
                "training_type": record.model_type,  # LOCAL or FEDERATED
                "model_version": record.model_version,
                "dp_epsilon_used": record.dp_epsilon_used,
                "aggregation_participants": record.aggregation_participants,
                "contribution_weight": record.contribution_weight,
                
                # Audit & traceability
                "prediction_hash": record.prediction_hash,
                "blockchain_hash": record.blockchain_hash,
                "summary_text": record.summary_text,
                "prediction_timestamp": record.prediction_timestamp.isoformat() if record.prediction_timestamp else None,
                "created_at": record.created_at.isoformat()
        })
        
        return {
            "predictions": predictions,
            "total_count": len(predictions)
        }
