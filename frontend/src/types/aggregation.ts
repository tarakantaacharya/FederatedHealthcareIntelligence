export interface AggregationRequest {
  round_number: number;
}

export interface AggregationResponse {
  status: string;
  round_number: number;
  global_model_id: number;
  num_hospitals: number;
  avg_loss: number;
  avg_accuracy: number | null;
  avg_mape?: number | null;
  avg_rmse?: number | null;
  avg_r2?: number | null;
  global_weights_path: string;
  model_hash?: string;
  blockchain_tx?: string | null;
  message: string;
}

export interface TrainingRoundSchema {
  id: number;
  round_id: number;
  model_architecture: string;         // ML_REGRESSION or TFT
  target_column: string;              // LOCKED target for this round
  feature_schema: string[];           // Ordered list of required columns
  feature_types?: Record<string, string>;  // Column → type mapping
  sequence_required?: boolean;        // Whether data must be sequential
  lookback?: number;                  // Encoder length (for TFT)
  horizon?: number;                   // Prediction horizon (for TFT)
  model_hyperparameters?: Record<string, any>;
  validation_rules?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TrainingRound {
  id: number;
  round_number: number;
  num_participating_hospitals: number;
  average_loss: number | null;
  average_accuracy?: number | null;
  average_mape?: number | null;
  average_rmse?: number | null;
  average_r2?: number | null;
  started_at: string | null;
  completed_at: string | null;
  status: string;
  target_column?: string;
  model_type?: string;
  training_enabled?: boolean;
  // NEW: Governance and participation fields
  participation_policy?: string;  // ALL, SELECTIVE, REGION_BASED, CAPACITY_BASED
  selection_criteria?: string;     // MANUAL, REGION, SIZE, EXPERIENCE
  selection_value?: string;        // e.g., "EAST", "LARGE", "NEW"
  is_emergency?: boolean;           // Emergency override flag
  hospital_ids?: number[];         // List of participating hospital IDs
  hospital_names?: string[];       // List of hospital names
  aggregation_strategy?: string;   // 'fedavg' or 'pfl'
  // NEW: Round schema (governance contract)
  round_schema?: TrainingRoundSchema | null;  // Schema contract created by central
}

