export interface Mapping {
  original_column: string;
  canonical_field: string;
  confidence: number;
}

export interface AutoMapResponse {
  dataset_id: number;
  total_columns: number;
  mapped_count: number;
  unmapped_count: number;
  mapping_success_rate: number;
  mappings: Mapping[];
  unmapped_columns: string[];
}

export interface ManualMappingRequest {
  dataset_id: number;
  mappings: Record<string, string>;
}

export interface DatasetMappingResponse {
  dataset_id: number;
  mappings: Mapping[];
}