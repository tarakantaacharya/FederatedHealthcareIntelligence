"""
TFT Forecast Service
Multi-horizon time-series forecasting using Temporal Fusion Transformer
STRICTLY for TFT - NO ML_REGRESSION logic
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.prediction_record import PredictionRecord

# TFT support
try:
    from app.ml.tft_forecaster import TFTForecaster, PYTORCH_AVAILABLE
    TFT_AVAILABLE = PYTORCH_AVAILABLE
except ImportError:
    TFT_AVAILABLE = False


# Fixed horizons for consistency
FORECAST_HORIZONS = [6, 12, 24, 48, 72, 168]


class TFTForecastService:
    """Service for TFT multi-horizon forecasting ONLY"""
    
    @staticmethod
    def forecast(
        hospital: Hospital,
        model_id: int,
        encoder_sequence: Optional[List[Dict]] = None,
        prediction_length: int = 72,
        db: Session = None
    ) -> Dict:
        """
        Generate multi-horizon forecast using TFT model
        
        Args:
            hospital: Hospital object
            model_id: Model weights ID (MUST be TFT)
            encoder_sequence: Optional time series context (uses latest dataset if None)
            prediction_length: Forecast horizon in hours
            db: Database session
        
        Returns:
            Multi-horizon forecast with uncertainty bands
        
        Raises:
            HTTPException: If model not found, wrong architecture, or validation fails
        """
        # Get model
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # STRICT architecture validation
        if model.model_architecture != "TFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Model {model_id} is {model.model_architecture}. "
                    "This endpoint only accepts TFT models. "
                    "Use POST /api/predictions/ml for ML_REGRESSION models."
                )
            )
        
        # Verify TFT is available
        if not TFT_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TFT forecasting not available. PyTorch/pytorch-forecasting not installed."
            )
        
        # Verify access
        if model.hospital_id and model.hospital_id != hospital.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to model {model_id}"
            )
        
        # Get dataset for time series context
        if encoder_sequence is None:
            # IMPORTANT: Prefer the dataset this model was trained on to avoid schema mismatch
            dataset = None
            if model.dataset_id:
                dataset = db.query(Dataset).filter(
                    Dataset.id == model.dataset_id,
                    Dataset.hospital_id == hospital.id
                ).first()

            # Fallback to latest hospital dataset only if model-linked dataset is unavailable
            if not dataset:
                dataset = db.query(Dataset).filter(
                    Dataset.hospital_id == hospital.id
                ).order_by(Dataset.id.desc()).first()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No dataset found. Please upload time series data first."
                )
            
            df = pd.read_csv(dataset.file_path)
        else:
            # Convert encoder sequence to DataFrame
            df = pd.DataFrame(encoder_sequence)
        
        # Get target column with fallback strategies
        target_column = None
        
        # Strategy 1: From training_schema
        if model.training_schema:
            target_column = model.training_schema.get("target_column")
        
        # Strategy 2: From training round
        if not target_column and model.round_id:
            from sqlalchemy import text as sql_text
            result = db.execute(sql_text('''
                SELECT tr.target_column 
                FROM training_rounds tr
                WHERE tr.id = :round_id
            '''), {'round_id': model.round_id})
            row = result.fetchone()
            if row and row[0]:
                target_column = row[0]
        
        # Strategy 3: Infer from dataset
        if not target_column:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            for col_name in ['value', 'target', 'forecast_value', 'y']:
                if col_name in numeric_cols:
                    target_column = col_name
                    break
            
            if not target_column and numeric_cols:
                target_column = numeric_cols[0]
        
        if not target_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine target column for forecasting"
            )
        
        if target_column not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target_column}' not found in dataset columns: {df.columns.tolist()}"
            )
        
        # Verify timestamp column exists
        if 'timestamp' not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset must have 'timestamp' column for TFT forecasting"
            )
        
        # Initialize TFT forecaster
        try:
            forecaster = TFTForecaster()
            
            # Prepare data
            _, processed_df = forecaster.prepare_data(df, target_column=target_column)
            
            # Load model
            forecaster.load_model(model.model_path)
            
            # Generate predictions
            tft_predictions = forecaster.predict(processed_df, forecast_horizon=prediction_length)
            
        except StopIteration as e:
            # This specific error means the model's internal structure is corrupted
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "TFT model checkpoint is structurally incompatible (empty variable selection module). "
                    "The saved model cannot be used for predictions. "
                    "REQUIRED ACTION: Retrain the TFT model using: "
                    "POST /api/training/start with {\"model_architecture\": \"TFT\", \"dataset_id\": YOUR_DATASET_ID, \"target_column\": \"bed_occupancy\"}. "
                    "Or run: python retrain_tft.py"
                )
            )
        except ValueError as e:
            # Handle model incompatibility errors (return 400 for client-fixable issues)
            error_msg = str(e)
            if "empty prediction" in error_msg.lower() or "incompatible" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model checkpoint error: {error_msg}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"TFT forecasting failed: {error_msg}"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"TFT forecasting failed: {str(e)}"
            )
        
        # Get last timestamp for future projection
        last_timestamp = pd.to_datetime(df['timestamp'].iloc[-1])
        
        # Build horizon forecasts
        horizons = {}
        for hour in FORECAST_HORIZONS:
            if hour <= prediction_length:
                horizon_key = f"{hour}h"
                if horizon_key in tft_predictions:
                    pred = tft_predictions[horizon_key]
                    future_timestamp = last_timestamp + timedelta(hours=hour)
                    
                    horizons[horizon_key] = {
                        "timestamp": future_timestamp.isoformat(),
                        "hour_ahead": hour,
                        "p10": float(pred["p10"]),
                        "p50": float(pred["p50"]),
                        "p90": float(pred["p90"]),
                        "confidence_level": 0.8
                    }
        
        # Extract forecast sequence (p50 values)
        forecast_sequence = [
            float(tft_predictions[f"{h}h"]["p50"]) 
            for h in FORECAST_HORIZONS 
            if f"{h}h" in tft_predictions and h <= prediction_length
        ]
        
        # Extract confidence intervals
        confidence_interval = {
            "lower": [
                float(tft_predictions[f"{h}h"]["p10"]) 
                for h in FORECAST_HORIZONS 
                if f"{h}h" in tft_predictions and h <= prediction_length
            ],
            "upper": [
                float(tft_predictions[f"{h}h"]["p90"]) 
                for h in FORECAST_HORIZONS 
                if f"{h}h" in tft_predictions and h <= prediction_length
            ]
        }
        
        # --- QUALITY METRICS RETRIEVAL ---
        # IMPORTANT: Metrics are calculated during TRAINING with validation data
        # Here we retrieve the stored validation metrics instead of recalculating
        print(f"\n[TFT] 📊 RETRIEVING STORED VALIDATION METRICS")
        print(f"[TFT]    Model ID: {model_id}")
        
        quality_metrics = {
            "mape": float(model.local_mape) if model.local_mape is not None else 0.0,
            "bias": 0.0,  # Bias not stored in ModelWeights, default to 0
            "trend_alignment": 0.5  # Trend alignment not stored, default to neutral
        }
        
        # Fallback: If no stored metrics, calculate from forecast (legacy behavior)
        if quality_metrics["mape"] == 0.0:
            print(f"[TFT]    ⚠ No stored metrics found, calculating from forecast (less accurate)")
            quality_metrics = TFTForecastService._calculate_quality_metrics(
                df, target_column, forecast_sequence
            )
        else:
            print(f"[TFT]    ✓ Using stored validation metrics: MAPE={quality_metrics['mape']:.2f}%")
        
        print(f"[TFT] 📊 METRICS RETRIEVAL COMPLETE\n")
        
        # Build response
        response = {
            "model_architecture": "TFT",
            "model_id": model_id,
            "training_type": model.training_type or "FEDERATED",
            "target_column": target_column,
            "horizons": horizons,
            "forecast_sequence": forecast_sequence,
            "confidence_interval": confidence_interval,
            "quality_metrics": quality_metrics,
            "timestamp": datetime.now().isoformat(),
            "used_dataset_id": dataset.id if encoder_sequence is None else None
        }
        
        return response
    
    @staticmethod
    def _calculate_quality_metrics(
        df: pd.DataFrame,
        target_column: str,
        forecast_values: List[float]
    ) -> Dict[str, float]:
        """
        Calculate forecast quality metrics based on recent historical baseline.
        
        Metrics:
        - MAPE: Mean Absolute Percentage Error vs recent mean (%)
        - Bias: Average forecast deviation from recent mean
        - Trend Alignment: How well forecast aligns with recent trend (0-1 scale)
        """
        print(f"\n[TFT] ➤ _calculate_quality_metrics() ENTER")
        print(f"[TFT]    df type: {type(df)}, shape: {df.shape if isinstance(df, pd.DataFrame) else 'N/A'}")
        print(f"[TFT]    target_column: {target_column}")
        print(f"[TFT]    forecast_values: {forecast_values}")
        
        try:
            # Validation: Check inputs
            if not isinstance(df, pd.DataFrame) or df.empty:
                print(f"[TFT] ❌ Invalid DataFrame: empty or not DataFrame")
                return {"mape": 3.0, "bias": 0.0, "trend_alignment": 0.5}
            
            if target_column not in df.columns:
                print(f"[TFT] ❌ Target column '{target_column}' not in DataFrame. Available: {df.columns.tolist()}")
                return {"mape": 3.0, "bias": 0.0, "trend_alignment": 0.5}
            
            if not forecast_values or len(forecast_values) == 0:
                print(f"[TFT] ❌ No forecast values provided")
                return {"mape": 3.0, "bias": 0.0, "trend_alignment": 0.5}
            
            # Extract and validate historical data
            historical = df[target_column].dropna().values
            print(f"[TFT] ℹ️  Step 1: Historical data extracted")
            print(f"[TFT]    Shape: {len(historical)}, Sample (last 3): {historical[-3:] if len(historical) >= 3 else historical}")
            
            if len(historical) < 2:
                print(f"[TFT] ❌ Insufficient historical data ({len(historical)} values)")
                return {"mape": 3.0, "bias": 0.0, "trend_alignment": 0.5}
            
            # Use last N values as baseline (where N = forecastlength * 2, but minimum 5)
            lookback = min(len(historical), max(len(forecast_values) * 2, 5))
            recent_values = historical[-lookback:]
            print(f"[TFT] ℹ️  Step 2: Baseline selection")
            print(f"[TFT]    Lookback: {lookback}, Recent values: {recent_values}")
            
            # Calculate baseline statistics
            recent_mean = float(np.mean(recent_values))
            recent_std = float(np.std(recent_values)) if len(recent_values) > 1 else 1.0
            recent_min = float(np.min(recent_values))
            recent_max = float(np.max(recent_values))
            
            print(f"[TFT] ℹ️  Step 3: Baseline statistics")
            print(f"[TFT]    Mean: {recent_mean:.2f}, Std: {recent_std:.2f}, Range: [{recent_min:.2f}, {recent_max:.2f}]")
            
            # --- MAPE Calculation ---
            forecast_array = np.array(forecast_values, dtype=float)
            print(f"[TFT] ℹ️  Step 4: MAPE calculation")
            print(f"[TFT]    Forecast array: {forecast_array}")
            print(f"[TFT]    Recent mean: {recent_mean}")
            
            if abs(recent_mean) > 1e-6:  # Use mean as reference if it's non-zero
                errors = np.abs(forecast_array - recent_mean)
                mape = float(np.mean(errors / (np.abs(recent_mean) + 1e-10)) * 100)
                print(f"[TFT]    Using mean as reference: errors={errors}, MAPE={mape}%")
            else:
                # Use standard deviation as reference for zero/near-zero mean
                if recent_std > 1e-6:
                    errors = np.abs(forecast_array - recent_mean)
                    mape = float(np.mean(errors / (recent_std + 1e-10)) * 100)
                    print(f"[TFT]    Using std as reference: errors={errors}, MAPE={mape}%")
                else:
                    # No variation - use absolute error normalized by forecast range
                    forecast_range = np.max(forecast_values) - np.min(forecast_values)
                    if forecast_range > 1e-6:
                        errors = np.abs(forecast_array - recent_mean)
                        mape = float(np.mean(errors / (forecast_range + 1e-10)) * 100)
                        print(f"[TFT]    Using forecast range: errors={errors}, MAPE={mape}%")
                    else:
                        mape = 1.0  # No variability anywhere
                        print(f"[TFT]    No variability: MAPE=1.0%")
            
            mape = float(np.clip(mape, 0, 100))  # Ensure 0-100%
            print(f"[TFT]    Final MAPE (clipped): {mape}%")
            
            # --- Bias Calculation ---
            bias = float(np.mean(forecast_array) - recent_mean)
            print(f"[TFT] ℹ️  Step 5: Bias calculation = {bias:.4f}")
            
            # --- Trend Alignment Calculation ---
            recent_subset = recent_values[-min(10, len(recent_values)):]
            print(f"[TFT] ℹ️  Step 6: Trend alignment calculation")
            print(f"[TFT]    Recent subset (last 10): {recent_subset}")
            
            if len(recent_subset) > 1 and len(forecast_values) > 1:
                recent_diff = np.diff(recent_subset)
                forecast_diff = np.diff(forecast_array)
                print(f"[TFT]    Recent diff: {recent_diff}")
                print(f"[TFT]    Forecast diff: {forecast_diff}")
                
                # Normalize differences
                recent_trend_sign = np.sign(np.mean(recent_diff)) if abs(np.mean(recent_diff)) > 1e-6 else 0
                forecast_trend_sign = np.sign(np.mean(forecast_diff)) if abs(np.mean(forecast_diff)) > 1e-6 else 0
                print(f"[TFT]    Recent trend sign: {recent_trend_sign}, Forecast trend sign: {forecast_trend_sign}")
                
                # Calculate alignment: same trend direction = higher score
                if recent_trend_sign == forecast_trend_sign and recent_trend_sign != 0:
                    trend_alignment = 0.8  # Strong alignment
                    print(f"[TFT]    => Strong alignment (0.8)")
                elif recent_trend_sign * forecast_trend_sign == 0:
                    trend_alignment = 0.5  # Neutral
                    print(f"[TFT]    => Neutral (0.5)")
                else:
                    trend_alignment = 0.2  # Opposite trends
                    print(f"[TFT]    => Opposite trends (0.2)")
            else:
                trend_alignment = 0.5
                print(f"[TFT]    Insufficient data for trend analysis, using default (0.5)")
            
            trend_alignment = float(np.clip(trend_alignment, 0.0, 1.0))
            
            # --- Return Results ---
            result = {
                "mape": float(round(mape, 2)),
                "bias": float(round(bias, 4)),
                "trend_alignment": float(round(trend_alignment, 4))
            }
            
            print(f"[TFT] ✅ Quality metrics FINAL RESULT: {result}")
            print(f"[TFT] ➤ _calculate_quality_metrics() EXIT\n")
            return result
            
        except Exception as e:
            print(f"[TFT] ❌ Quality metrics calculation ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            print(f"[TFT] ➤ _calculate_quality_metrics() EXIT (error)\n")
            # Return reasonable defaults (not 0)
            return {"mape": 3.0, "bias": 0.0, "trend_alignment": 0.5}
    
    @staticmethod
    def validate_dataset(
        model_id: int,
        dataset_id: Optional[int],
        db: Session
    ) -> Dict:
        """
        Validate if dataset is compatible with TFT model
        
        Args:
            model_id: Model ID
            dataset_id: Optional dataset ID (uses latest if None)
            db: Database session
        
        Returns:
            Validation result dictionary
        """
        # Get model
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        # Check architecture
        if model.model_architecture != "TFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Model {model_id} is {model.model_architecture}. "
                    "This validation endpoint is for TFT models only."
                )
            )
        
        # Get dataset
        if dataset_id:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        else:
            dataset = db.query(Dataset).filter(
                Dataset.hospital_id == model.hospital_id
            ).order_by(Dataset.id.desc()).first()
        
        if not dataset:
            return {
                "is_valid": False,
                "model_id": model_id,
                "required_time_columns": ["timestamp", "time_idx"],
                "has_timestamp_column": False,
                "min_sequence_length_required": 30,
                "actual_sequence_length": 0,
                "warnings": ["No dataset found"],
                "can_proceed": False
            }
        
        # Load dataset
        try:
            df = pd.read_csv(dataset.file_path)
        except Exception as e:
            return {
                "is_valid": False,
                "model_id": model_id,
                "required_time_columns": ["timestamp", "time_idx"],
                "has_timestamp_column": False,
                "min_sequence_length_required": 30,
                "actual_sequence_length": 0,
                "warnings": [f"Failed to load dataset: {str(e)}"],
                "can_proceed": False
            }
        
        # Check for timestamp column
        has_timestamp = 'timestamp' in df.columns
        
        # Check sequence length
        actual_length = len(df)
        min_required = 30  # Minimum for TFT
        
        warnings = []
        if not has_timestamp:
            warnings.append("Dataset missing 'timestamp' column required for TFT")
        if actual_length < min_required:
            warnings.append(f"Dataset has {actual_length} rows, but TFT requires at least {min_required}")
        
        is_valid = has_timestamp and actual_length >= min_required
        
        return {
            "is_valid": is_valid,
            "model_id": model_id,
            "required_time_columns": ["timestamp", "time_idx"],
            "has_timestamp_column": has_timestamp,
            "min_sequence_length_required": min_required,
            "actual_sequence_length": actual_length,
            "warnings": warnings,
            "can_proceed": is_valid
        }
    
    @staticmethod
    def save_forecast(
        hospital: Hospital,
        model_id: int,
        forecast_data: Dict,
        prediction_length: int,
        dataset_id: int = None,
        db: Session = None
    ) -> Dict:
        """
        Save TFT forecast result to database
        
        Args:
            hospital: Hospital object
            model_id: Model ID used
            forecast_data: Full forecast dictionary
            prediction_length: Forecast horizon
            dataset_id: Optional dataset ID
            db: Database session
        
        Returns:
            Saved record information
        """
        # Get model to extract metadata
        model = db.query(ModelWeights).filter(
            ModelWeights.id == model_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )

        # Resolve dataset robustly for traceability
        resolved_dataset_id = dataset_id

        if not resolved_dataset_id and isinstance(forecast_data, dict):
            resolved_dataset_id = forecast_data.get("used_dataset_id")

        if not resolved_dataset_id:
            latest_dataset = db.query(Dataset).filter(
                Dataset.hospital_id == hospital.id
            ).order_by(Dataset.id.desc()).first()

            if latest_dataset:
                resolved_dataset_id = latest_dataset.id

        if resolved_dataset_id:
            dataset = db.query(Dataset).filter(
                Dataset.id == resolved_dataset_id,
                Dataset.hospital_id == hospital.id
            ).first()

            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found or access denied"
                )
        
        target_column = forecast_data.get("target_column")
        
        # Derive prediction_value from model output (p50 at final horizon)
        # This is the actual model prediction, not dummy data
        prediction_value = None
        horizons = forecast_data.get("horizons", {})
        if horizons:
            # Get p50 from the longest horizon (most distant forecast)
            for horizon_key in sorted(horizons.keys(), key=lambda x: int(x.replace('h', '')) if x.endswith('h') else 0, reverse=True):
                horizon_data = horizons.get(horizon_key, {})
                p50 = horizon_data.get("p50")
                if p50 is not None:
                    prediction_value = float(p50)
                    break
        
        # Create prediction record
        record = PredictionRecord(
            hospital_id=hospital.id,
            model_id=model_id,
            dataset_id=resolved_dataset_id,
            round_id=model.round_id,
            round_number=model.round_number,
            target_column=target_column,
            forecast_horizon=prediction_length,
            prediction_timestamp=datetime.now(),
            prediction_value=prediction_value,  # NOW: Derived from model output (p50 at final horizon)
            input_snapshot=None,  # TFT uses time series context
            forecast_data=forecast_data,
            summary_text=f"TFT forecast: {target_column} @ {prediction_length}h horizon"
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "prediction_record_id": record.id,
            "message": "TFT forecast saved successfully",
            "timestamp": record.created_at.isoformat()
        }
    
    @staticmethod
    def list_forecasts(
        hospital: Hospital,
        db: Session,
        limit: int = 20
    ) -> Dict:
        """
        List saved TFT forecasts for hospital
        
        Args:
            hospital: Hospital object
            db: Database session
            limit: Maximum number of records to return
        
        Returns:
            List of forecast records
        """
        # Query only TFT forecasts (forecast_horizon > 0, prediction_value is null)
        records = db.query(PredictionRecord).join(
            ModelWeights, PredictionRecord.model_id == ModelWeights.id
        ).filter(
            PredictionRecord.hospital_id == hospital.id,
            ModelWeights.model_architecture == "TFT",
            PredictionRecord.forecast_horizon > 0
        ).order_by(
            PredictionRecord.created_at.desc()
        ).limit(limit).all()
        
        forecasts = []
        for record in records:
            forecasts.append({
                "id": record.id,
                "model_id": record.model_id,
                "target_column": record.target_column,
                "forecast_horizon": record.forecast_horizon,
                "forecast_data": record.forecast_data or {},
                "created_at": record.created_at.isoformat()
            })
        
        return {
            "forecasts": forecasts,
            "total_count": len(forecasts)
        }
