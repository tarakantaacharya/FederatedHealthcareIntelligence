export interface TrainingRequest {
  dataset_id: number;
  target_column?: string;
  epochs?: number;
  batch_size?: number;
  local_epsilon_budget?: number;
  learning_rate?: number;
  training_type?: 'LOCAL' | 'FEDERATED';
  model_architecture?: 'ML_REGRESSION' | 'TFT';
  custom_features?: string;
}

export interface TrainingMetrics {
  train_loss?: number;
  accuracy?: number | null;
  mape?: number | null;
  rmse?: number | null;
  r2?: number | null;
  grad_norm_pre?: number;
  grad_norm_post?: number;
  epsilon_spent?: number;
  epsilon_budget?: number;
  noise_multiplier?: number;
  clip_norm?: number;
  epochs?: number;
  output_size?: number;
  horizons?: number[];
  dp_enabled?: boolean;
  epochs_trained?: number;
  model_type?: string;
  train_mse?: number;
  train_mae?: number;
  train_r2?: number;
  test_mse?: number;
  test_mae?: number;
  test_r2?: number;
  test_rmse?: number;
  num_features?: number;
  num_samples?: number;
  top_5_features?: Record<string, number>;
  target_column?: string;
  trained_at?: string;
}

export interface TrainingResponse {
  model_id: number;
  model_path: string;
  dataset_id: number;
  target_column: string;
  metrics: TrainingMetrics;
  status: string;
}

export interface TrainedModel {
  id: number;
  hospital_id: number;
  round_number: number;
  model_type: string;
  training_type?: string | null;
  model_architecture?: string | null;
  aggregation_strategy?: string | null;
  local_loss: number | null;
  local_accuracy: number | null;
  local_mape?: number | null;
  local_rmse?: number | null;
  local_r2?: number | null;
  is_global: boolean;
  created_at: string;
}

export interface TrainingStatusItem {
  model_id: number;
  dataset_id: number | null;
  dataset_name: string | null;
  round_number: number | null;
  training_type: string;
  model_architecture: string;
  loss: number | null;
  accuracy: number | null;
  status: string;
  timestamp: string | null;
}
