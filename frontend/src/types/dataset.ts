export interface Dataset {
  id: number;
  hospital_id: number;
  filename: string;
  file_size_bytes: number;
  num_rows: number | null;
  num_columns: number | null;
  is_normalized: boolean;
  uploaded_at: string;
  dataset_type?: 'TABULAR' | 'TIME_SERIES';
}

export interface DatasetDetail {
  id: number;
  hospital_id: number;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  num_rows: number | null;
  num_columns: number | null;
  column_names: string[] | null;
  is_normalized: boolean;
  normalized_path: string | null;
  uploaded_at: string;
  dataset_type?: 'TABULAR' | 'TIME_SERIES';
}

export interface DatasetStatus {
  dataset_id: number;
  trained_local: boolean;
  trained_federated: boolean;
  rounds: number[];
  mask_uploaded: boolean;
  weights_uploaded: boolean;
  times_trained: number;
  times_federated: number;
  last_trained_at: string | null;
  last_training_type: string | null;
}

export interface DatasetModelSummary {
  id: number;
  model_name: string;
  type: 'LOCAL' | 'FEDERATED';
  architecture: 'TFT' | 'ML';
  timestamp: string;
}
