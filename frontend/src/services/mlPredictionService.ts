/**
 * ML_REGRESSION Prediction Service
 * STRICTLY for single-point regression predictions
 * NO TFT logic - completely separate from time-series forecasting
 */
import api from './api';

/**
 * ML Prediction Request
 */
export interface MLPredictionRequest {
  model_id: number;
  features: Record<string, number>;
}

/**
 * ML Prediction Response
 */
export interface MLPredictionResponse {
  model_architecture: string;  // Always "ML_REGRESSION"
  model_id: number;
  training_type: string;  // LOCAL or FEDERATED
  target_column: string;
  prediction: number;  // Single predicted value
  input_features: Record<string, number>;
  feature_count: number;
  timestamp: string;
  
  // NEW: Rich metrics and analysis (Phase 6+)
  ai_summary?: string;  // Gemini-generated AI analysis
  model_accuracy?: {
    r2?: number;
    rmse?: number;
    mape?: number;
    mae?: number;
  };
  confidence_interval?: {
    lower: number;
    upper: number;
    confidence_level: number;
    margin_of_error: number;
  };
}

/**
 * ML Model Validation Request
 */
export interface MLModelValidationRequest {
  model_id: number;
  features: Record<string, number>;
}

/**
 * ML Model Validation Response
 */
export interface MLModelValidationResponse {
  is_valid: boolean;
  model_id: number;
  required_features: string[];
  provided_features: string[];
  missing_features: string[];
  extra_features: string[];
  warnings: string[];
  can_proceed: boolean;
}

/**
 * ML Prediction Save Request
 */
export interface MLPredictionSaveRequest {
  model_id: number;
  features: Record<string, number>;
  prediction: number;
  dataset_id?: number;
}

/**
 * ML Prediction Save Response
 */
export interface MLPredictionSaveResponse {
  prediction_record_id: number;
  message: string;
  timestamp: string;
}

/**
 * ML Prediction History Item
 */
export interface MLPredictionHistoryItem {
  id: number;
  model_id: number;
  target_column?: string;
  prediction_value: number;
  input_snapshot: Record<string, number>;
  created_at: string;
}

/**
 * ML Prediction History Response
 */
export interface MLPredictionHistoryResponse {
  predictions: MLPredictionHistoryItem[];
  total_count: number;
}

/**
 * ML model metadata response
 */
export interface MLModelMetadataResponse {
  model_architecture: string;
  training_type: string;
  target_column?: string | null;
  trained_feature_columns: string[];
}

class MLPredictionService {
  /**
   * Generate single-point ML prediction
   * POST /api/predictions/ml
   * 
   * COMPREHENSIVE LOGGING:
   * - Request features and model ID
   * - Response prediction value and metadata
   * - Timing information
   * - Feature count validation
   */
  async predict(request: MLPredictionRequest): Promise<MLPredictionResponse> {
    const startTime = performance.now();
    const featureCount = Object.keys(request.features).length;
    const featureNames = Object.keys(request.features).sort();
    
    console.log('%c[ML_PREDICT_SERVICE] Prediction Request', 'color: #2563eb; font-weight: bold;');
    console.log('  Model ID:', request.model_id);
    console.log('  Features Count:', featureCount);
    console.log('  Feature Names:', featureNames);
    console.log('  Feature Values:', request.features);
    
    try {
      const response = await api.post<MLPredictionResponse>('/api/predictions/ml', request);
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_PREDICT_SERVICE] Prediction Success', 'color: #16a34a; font-weight: bold;');
      console.log('  Status: 200');
      console.log('  Prediction Value:', response.data.prediction);
      console.log('  Target Column:', response.data.target_column);
      console.log('  Training Type:', response.data.training_type);
      console.log('  Model Architecture:', response.data.model_architecture);
      console.log('  Feature Count (Response):', response.data.feature_count);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      return response.data;
    } catch (error: any) {
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_PREDICT_SERVICE] Prediction Error', 'color: #dc2626; font-weight: bold;');
      console.log('  Status:', error.response?.status || 'Unknown');
      console.log('  Error Message:', error.response?.data?.detail || error.message);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      console.log('  Full Error Response:', error.response?.data);
      
      throw error;
    }
  }

  /**
   * Validate features against model training schema
   * POST /api/predictions/ml/validate
   * 
   * COMPREHENSIVE LOGGING:
   * - Validation request details
   * - Feature comparison (required vs provided)
   * - Any missing or extra features
   * - Validation result
   */
  async validateFeatures(request: MLModelValidationRequest): Promise<MLModelValidationResponse> {
    const startTime = performance.now();
    
    console.log('%c[ML_VALIDATE_SERVICE] Validation Request', 'color: #7c3aed; font-weight: bold;');
    console.log('  Model ID:', request.model_id);
    console.log('  Provided Features:', Object.keys(request.features).sort());
    console.log('  Feature Count:', Object.keys(request.features).length);
    
    try {
      const response = await api.post<MLModelValidationResponse>(
        '/api/predictions/ml/validate',
        request
      );
      const duration = performance.now() - startTime;
      const data = response.data;
      
      console.log('%c[ML_VALIDATE_SERVICE] Validation Result', 
        data.is_valid ? 'color: #16a34a; font-weight: bold;' : 'color: #ea580c; font-weight: bold;'
      );
      console.log('  Valid:', data.is_valid);
      console.log('  Required Features:', data.required_features.sort());
      console.log('  Provided Features:', data.provided_features.sort());
      
      if (data.missing_features.length > 0) {
        console.warn('  ⚠️ Missing Features:', data.missing_features);
      }
      
      if (data.extra_features.length > 0) {
        console.warn('  ⚠️ Extra Features:', data.extra_features);
      }
      
      if (data.warnings.length > 0) {
        console.warn('  Warnings:', data.warnings);
      }
      
      console.log('  Can Proceed:', data.can_proceed);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      return response.data;
    } catch (error: any) {
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_VALIDATE_SERVICE] Validation Error', 'color: #dc2626; font-weight: bold;');
      console.log('  Status:', error.response?.status || 'Unknown');
      console.log('  Error Message:', error.response?.data?.detail || error.message);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      throw error;
    }
  }

  /**
   * Save ML prediction result
   * POST /api/predictions/ml/save
   * 
   * COMPREHENSIVE LOGGING:
   * - Save request parameters
   * - Response status
   * - Database ID of saved record
   */
  async savePrediction(request: MLPredictionSaveRequest): Promise<MLPredictionSaveResponse> {
    const startTime = performance.now();
    
    console.log('%c[ML_SAVE_SERVICE] Save Request', 'color: #06b6d4; font-weight: bold;');
    console.log('  Model ID:', request.model_id);
    console.log('  Prediction Value:', request.prediction);
    console.log('  Features Count:', Object.keys(request.features).length);
    
    try {
      const response = await api.post<MLPredictionSaveResponse>(
        '/api/predictions/ml/save',
        request
      );
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_SAVE_SERVICE] Save Success', 'color: #16a34a; font-weight: bold;');
      console.log('  Record ID:', response.data.prediction_record_id);
      console.log('  Message:', response.data.message);
      console.log('  Timestamp:', response.data.timestamp);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      return response.data;
    } catch (error: any) {
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_SAVE_SERVICE] Save Error', 'color: #dc2626; font-weight: bold;');
      console.log('  Status:', error.response?.status || 'Unknown');
      console.log('  Error Message:', error.response?.data?.detail || error.message);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      throw error;
    }
  }

  /**
   * Get ML prediction history
   * GET /api/predictions/ml/history
   * 
   * COMPREHENSIVE LOGGING:
   * - Request parameters (limit)
   * - Number of records returned
   * - Pagination info
   */
  async getHistory(limit = 20): Promise<MLPredictionHistoryResponse> {
    const startTime = performance.now();
    
    console.log('%c[ML_HISTORY_SERVICE] History Request', 'color: #8b5cf6; font-weight: bold;');
    console.log('  Limit:', limit);
    
    try {
      const response = await api.get<MLPredictionHistoryResponse>(
        '/api/predictions/ml/history',
        { params: { limit } }
      );
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_HISTORY_SERVICE] History Loaded', 'color: #16a34a; font-weight: bold;');
      console.log('  Records Returned:', response.data.predictions.length);
      console.log('  Total Count:', response.data.total_count);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      return response.data;
    } catch (error: any) {
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_HISTORY_SERVICE] History Error', 'color: #dc2626; font-weight: bold;');
      console.log('  Status:', error.response?.status || 'Unknown');
      console.log('  Error Message:', error.response?.data?.detail || error.message);
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      throw error;
    }
  }

  /**
   * Get model metadata for ML prediction inputs
   * GET /api/models/{model_id}/metadata
   * 
   * CRITICAL: This is the "source of truth" for what features the model expects
   * Used to dynamically render feature input fields
   * 
   * COMPREHENSIVE LOGGING:
   * - Model ID requested
   * - Response: model architecture, training type, target column, all trained features
   * - Feature validation (target not in features list)
   * - Warning if features empty or target in features
   */
  async getModelMetadata(modelId: number): Promise<MLModelMetadataResponse> {
    const startTime = performance.now();
    
    console.log('%c[ML_METADATA_SERVICE] Metadata Request', 'color: #f59e0b; font-weight: bold;');
    console.log('  Model ID:', modelId);
    console.log('  Endpoint: GET /api/models/{modelId}/metadata');
    console.log('  Purpose: Source of truth for prediction schema');
    
    try {
      const response = await api.get<MLModelMetadataResponse>(
        `/api/models/${modelId}/metadata`
      );
      const duration = performance.now() - startTime;
      const data = response.data;
      
      console.log('%c[ML_METADATA_SERVICE] Metadata Received', 'color: #16a34a; font-weight: bold;');
      console.log('  Model Architecture:', data.model_architecture);
      console.log('  Training Type:', data.training_type);
      console.log('  Target Column:', data.target_column);
      console.log('  Trained Features Count:', data.trained_feature_columns?.length || 0);
      console.log('  Trained Features:', data.trained_feature_columns);
      
      // SANITY CHECK: Target column should NOT be in features list
      if (data.target_column && data.trained_feature_columns?.includes(data.target_column)) {
        console.error('%c[ML_METADATA_SERVICE] ⚠️ ARCHITECTURE BUG: TARGET IN FEATURES LIST', 'color: #dc2626; font-weight: bold;');
        console.error('  Target:', data.target_column);
        console.error('  Features:', data.trained_feature_columns);
      }
      
      // WARNING: Zero features
      if (!data.trained_feature_columns || data.trained_feature_columns.length === 0) {
        console.warn('%c[ML_METADATA_SERVICE] ⚠️ WARNING: NO FEATURES IN METADATA', 'color: #ea580c; font-weight: bold;');
        console.warn('  This will cause prediction to fail');
        console.warn('  Check: training_service.py, _resolve_feature_columns(), training_schema storage');
      }
      
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      console.log('  Ready for dynamic UI rendering: YES');
      
      return response.data;
    } catch (error: any) {
      const duration = performance.now() - startTime;
      
      console.log('%c[ML_METADATA_SERVICE] Metadata Error', 'color: #dc2626; font-weight: bold;');
      console.log('  Status:', error.response?.status || 'Unknown');
      console.log('  Status Code:', error.response?.status);
      console.log('  Error Message:', error.response?.data?.detail || error.message);
      
      // 404 means model doesn't exist or metadata endpoint not implemented
      if (error.response?.status === 404) {
        console.error('  ⚠️ 404 Not Found - Possible causes:');
        console.error('     1. Model does not exist (modelId=' + modelId + ')');
        console.error('     2. Metadata endpoint not implemented or route missing');
        console.error('     3. Model has no training_schema stored in database');
      }
      
      // 400 means model exists but missing metadata
      if (error.response?.status === 400) {
        console.error('  ⚠️ 400 Bad Request - Model metadata incomplete or invalid');
      }
      
      console.log('  Duration:', `${duration.toFixed(2)}ms`);
      
      throw error;
    }
  }

  /**
   * Format prediction value for display
   */
  formatPrediction(value: number, decimals = 1): string {
    return value.toFixed(decimals);
  }

  /**
   * Build feature form fields from model schema
   */
  buildFeatureFields(requiredFeatures: string[]): Array<{
    name: string;
    label: string;
    type: 'number';
    required: boolean;
  }> {
    return requiredFeatures.map(feature => ({
      name: feature,
      label: feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      type: 'number' as const,
      required: true
    }));
  }

  /**
   * Extract required features from model
   */
  getRequiredFeatures(model: any): string[] {
    // Check both field names for backwards compatibility
    if (model.training_schema?.feature_columns) {
      return model.training_schema.feature_columns;
    }
    if (model.training_schema?.required_columns) {
      return model.training_schema.required_columns;
    }
    return [];
  }
}

const mlPredictionService = new MLPredictionService();

export default mlPredictionService;
