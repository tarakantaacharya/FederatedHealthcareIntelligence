export interface RoundStatistics {
  total_rounds: number;
  completed_rounds: number;
  in_progress_rounds: number;
  latest_round_number: number;
  global_models_created: number;
}

export interface HospitalContribution {
  hospital_id: number;
  hospital_name: string;
  loss: number | null;
  accuracy: number | null;
  mape?: number | null;
  rmse?: number | null;
  r2?: number | null;
  uploaded_at: string;
}

export interface RoundDetail {
  round_number: number;
  status: string;
  target_column?: string;
  num_participating_hospitals: number;
  average_loss: number | null;
  average_accuracy?: number | null;
  average_mape?: number | null;
  average_rmse?: number | null;
  average_r2?: number | null;
  started_at: string;
  completed_at: string | null;
  global_model_id: number | null;
  hospital_contributions: HospitalContribution[];
  aggregation_strategy?: string; // 'fedavg' or 'pfl'
}

export interface CentralRoundHistoryItem {
  round_number: number;
  status: string;
  target_column: string;
  model_type: string;
  num_participating_hospitals: number;
  started_at: string | null;
  completed_at: string | null;
  duration_hours: number | null;
}

export interface CentralRoundContributionItem {
  hospital_id: number;
  hospital_code: string;
  hospital_name: string;
  contribution_percentage: number;
  local_loss: number | null;
  local_accuracy: number | null;
  model_types: string[];
}

export interface CentralRoundHistoryDetail {
  round_number: number;
  status: string;
  target_column: string;
  features_taken: string[];
  num_participating_hospitals: number;
  model_type: string;
  aggregation_strategy: string;
  started_at: string | null;
  completed_at: string | null;
  duration_hours: number | null;
  global_model: {
    model_id: number | null;
    approved: boolean;
    model_hash: string | null;
    approved_by: string | null;
    approved_at: string | null;
  };
  global_model_metrics: {
    average_loss: number | null;
    average_accuracy: number | null;
    average_mape: number | null;
    average_rmse: number | null;
    average_r2: number | null;
  };
  hospital_contribution_distribution: CentralRoundContributionItem[];
}

export interface HospitalRoundHistoryItem {
  round_number: number;
  status: string;
  target_column: string;
  model_type: string;
  started_at: string | null;
  completed_at: string | null;
  duration_hours: number | null;
  dataset_count: number;
  types: string[];
}

export interface HospitalRoundHistoryDetail {
  round_number: number;
  status: string;
  target_column: string;
  features_taken: string[];
  model_type: string;
  aggregation_strategy: string;
  started_at: string | null;
  completed_at: string | null;
  duration_hours: number | null;
  hospital_contribution: {
    contribution_percentage: number;
    local_loss: number | null;
    local_accuracy: number | null;
    types: string[];
  };
  global_model_metrics: {
    average_loss: number | null;
    average_accuracy: number | null;
    average_mape: number | null;
    average_rmse: number | null;
    average_r2: number | null;
  };
  datasets_involved: Array<{
    dataset_id: number;
    filename: string;
    num_rows: number | null;
    num_columns: number | null;
  }>;
  extra: {
    total_models_submitted_by_hospital: number;
    dataset_count: number;
  };
}
