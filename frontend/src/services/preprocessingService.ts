import api from './api';

export interface ColumnTypeInfo {
  type: string;
  pandas_dtype: string;
  non_null_count: number;
  null_count: number;
  unique_count: number;
}

export interface DataTypeDetectionResponse {
  columns: Record<string, ColumnTypeInfo>;
  total_rows: number;
  detected_at: string;
}

export interface ColumnQualityInfo {
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  dtype: string;
  min?: number;
  max?: number;
  mean?: number;
  std?: number;
}

export interface DataQualityResponse {
  total_rows: number;
  total_columns: number;
  missing_values: Record<string, number>;
  duplicates: {
    count: number;
    percentage: number;
  };
  columns: Record<string, ColumnQualityInfo>;
  has_issues: boolean;
}

export interface MissingValueStrategy {
  strategy: 'drop' | 'fill';
  fill_value?: any;
}

export interface DataCleaningRequest {
  remove_duplicates?: boolean;
  handle_missing?: MissingValueStrategy;
  remove_columns?: string[];
  rename_columns?: Record<string, string>;
  convert_types?: Record<string, string>;
}

export interface DataCleaningResponse {
  success: boolean;
  original_shape: [number, number];
  new_shape: [number, number];
  operations_applied: string[];
  created_backup: boolean;
  backup_path?: string;
}

export interface DataPreviewResponse {
  columns: string[];
  data: Record<string, any>[];
  total_rows: number;
  dtypes: Record<string, string>;
}

export interface PreprocessingStatusResponse {
  dataset_id: number;
  has_quality_issues: boolean;
  quality_report?: DataQualityResponse;
  column_types?: Record<string, ColumnTypeInfo>;
  is_trained: boolean;
  backup_available: boolean;
}

class PreprocessingService {
  /**
   * Detect data types for all columns
   */
  async detectColumnTypes(datasetId: number): Promise<DataTypeDetectionResponse> {
    const response = await api.get<DataTypeDetectionResponse>(
      `/api/preprocessing/${datasetId}/detect-types`
    );
    return response.data;
  }

  /**
   * Get data quality report
   */
  async getQualityReport(datasetId: number): Promise<DataQualityResponse> {
    const response = await api.get<DataQualityResponse>(
      `/api/preprocessing/${datasetId}/quality-report`
    );
    return response.data;
  }

  /**
   * Clean dataset with specified operations
   */
  async cleanDataset(
    datasetId: number,
    operations: DataCleaningRequest
  ): Promise<DataCleaningResponse> {
    const response = await api.post<DataCleaningResponse>(
      `/api/preprocessing/${datasetId}/clean`,
      operations
    );
    return response.data;
  }

  /**
   * Get dataset preview
   */
  async getPreview(datasetId: number, rows: number = 10): Promise<DataPreviewResponse> {
    const response = await api.get<DataPreviewResponse>(
      `/api/preprocessing/${datasetId}/preview`,
      { params: { rows } }
    );
    return response.data;
  }

  /**
   * Get comprehensive preprocessing status
   */
  async getPreprocessingStatus(datasetId: number): Promise<PreprocessingStatusResponse> {
    const response = await api.get<PreprocessingStatusResponse>(
      `/api/preprocessing/${datasetId}/preprocessing-status`
    );
    return response.data;
  }
}

export default new PreprocessingService();
