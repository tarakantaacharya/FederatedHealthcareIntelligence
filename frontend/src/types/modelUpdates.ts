export interface ModelDownloadRequest {
  round_number: number;
}

export interface ModelDownloadResponse {
  status: string;
  round_number: number;
  global_model_id: number;
  local_copy_id: number;
  local_path: string;
  accuracy: number | null;
  loss: number | null;
  message: string;
}

export interface ModelUpdateResponse {
  status: string;
  round_number: number;
  hospital_id: number;
  hospital_name: string;
  updated_model_id: number;
  message: string;
}

export interface SyncStatus {
  hospital_id: number;
  total_global_rounds: number;
  synced_rounds: number[];
  missing_rounds: number[];
  sync_percentage: number;
}

export interface GlobalModel {
  id: number;
  round_number: number;
  model_type: string;
  dataset_id?: number;
  loss: number | null;
  accuracy: number | null;
  created_at: string;
  training_type?: string;  // LOCAL | FEDERATED
  model_architecture?: string;  // TFT | ML_REGRESSION
  training_schema?: {
    feature_columns?: string[];      // Legacy/alternate name
    required_columns?: string[];     // Backend actual field name
    target_column?: string;
    excluded_columns?: string[];
    num_features?: number;
  } | null;
  target_column?: string | null;
  is_global?: boolean;     // ADD THIS
  hospital_id?: number | null; // ADD THIS
}

export interface AggregatedWeightsPreviewResponse {
  model_id: number;
  round_number: number;
  model_hash: string;
  approved: boolean;
  approved_by?: number | null;
  signature?: string | null;
  policy_version?: string | null;
  distributed_to_hospital: boolean;
  hospital_id: number;
  hospital_code: string;
  weights_json: any;
}
