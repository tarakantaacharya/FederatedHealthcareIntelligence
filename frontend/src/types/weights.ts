export interface WeightUploadRequest {
  model_id: number;
  round_number: number;
}

export interface WeightUploadResponse {
  status: string;
  model_id: number;
  hospital_id: number;
  round_number: number;
  weights_path: string;
  message: string;
  mask_upload_required?: boolean;
  mask_hash?: string | null;
  mask_payload?: string | null;
}

export interface MaskGenerationRequest {
  model_id: number;
  dataset_id: number;
  round_number: number;
}

export interface MaskGenerationResponse {
  status: string;
  model_id: number;
  mask_payload: string;
  mask_hash: string;
}

export interface MaskUploadRequest {
  model_id: number;
  round_number: number;
  mask_payload: string;
  mask_hash?: string | null;
}

export interface MaskUploadResponse {
  status: string;
  hospital_id: number;
  round_number: number;
  mask_path: string;
  mask_hash: string;
}
