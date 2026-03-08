export interface NormalizeRequest {
  dataset_id: number;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  validated_fields: string[];
  total_rows: number;
}

export interface NormalizeResponse {
  status: string;
  dataset_id: number;
  original_path: string;
  normalized_path: string;
  original_rows: number;
  normalized_rows: number;
  original_columns: number;
  normalized_columns: number;
  validation: ValidationResult;
  normalized_at: string;
  detected_categories?: string[];
  category_validations?: Record<string, any>;
}

export interface NormalizedPreview {
  dataset_id: number;
  num_rows: number;
  columns: string[];
  data: Record<string, any>[];
}
