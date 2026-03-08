export interface ForecastRequest {
  model_id: number;
  dataset_id?: number;
  forecast_horizon: number;
}

export interface ForecastPoint {
  timestamp: string;
  hour_ahead: number;
  prediction: number;
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
}

export interface QualityMetrics {
  mape: number | null;
  bias: number | null;
  trend_alignment: number | null;
  validation_samples: number;
}

export interface TFTQuantilePoint {
  timestamp: string;
  hour_ahead: number;
  p10: number;
  p50: number;
  p90: number;
  confidence_level: number;
}

export interface ForecastResponse {
  model_id: number;
  model_type: string;
  target_variable: string;
  forecast_horizon: number;
  generated_at: string;

  // Baseline format
  horizon_forecasts?: Record<string, ForecastPoint>;

  // TFT format
  horizons?: Record<string, TFTQuantilePoint>;

  forecasts?: ForecastPoint[];
  quality_metrics: QualityMetrics;
}

export interface SchemaValidationSnapshot {
  schema_match: boolean | null;
  missing_columns: string[];
  extra_columns: string[];
  warnings: string[];
  can_auto_align: boolean;
  model_schema: {
    required_columns: string[];
    excluded_columns: string[];
    target_column: string | null;
    num_features: number;
  } | null;
  dataset_schema: {
    columns: string[];
    num_columns: number;
  } | null;
}

export interface PredictionSaveRequest {
  model_id: number;
  dataset_id?: number;
  forecast_horizon: number;
  forecast_data: ForecastResponse;
}

export interface PredictionSaveResponse {
  id: number;
  message: string;
  created_at: string;
  round_number: number | null;
  target_column: string | null;
  prediction_timestamp?: string | null;
  prediction_value?: number | null;
  summary_text?: string | null;
}

export interface MLForecastData {
  type: "ML_REGRESSION";
  prediction: number;
}

export type UnifiedForecastData =
  | MLForecastData
  | ForecastResponse;

export interface PredictionHistoryItem {
  id: number;
  model_id: number;
  model_type: string | null;
  dataset_id: number | null;
  dataset_name: string | null;
  round_id: number | null;
  round_number: number | null;
  target_column: string | null;
  forecast_horizon: number;
  created_at: string;
  prediction_timestamp?: string | null;
  prediction_value?: number | null;
  input_snapshot?: Record<string, any> | null;
  summary_text?: string | null;
  forecast_data: UnifiedForecastData;
  schema_validation: SchemaValidationSnapshot | null;
}

export interface PredictionHistoryResponse {
  items: PredictionHistoryItem[];
}
