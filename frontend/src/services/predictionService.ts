import api from './api';
import {
  ForecastRequest,
  ForecastResponse,
  PredictionSaveRequest,
  PredictionSaveResponse,
  PredictionHistoryResponse
} from '../types/predictions';

class PredictionService {
  /**
   * Generate forecast
   */
  async generateForecast(request: ForecastRequest): Promise<ForecastResponse> {
    const response = await api.post<ForecastResponse>('/api/predictions/forecast', request);
    return response.data;
  }

  /**
   * Check for data drift
   */
  async checkDrift(request: any): Promise<any> {
    const response = await api.post('/api/drift-detection/check-drift', request);
    return response.data;
  }

  /**
   * Validate schema compatibility between model and dataset
   */
  async validateSchema(request: { model_id: number; dataset_id: number }): Promise<any> {
    const response = await api.post('/api/predictions/validate-schema', request);
    return response.data;
  }

  /**
   * Save prediction result
   */
  async savePrediction(request: PredictionSaveRequest): Promise<PredictionSaveResponse> {
    const response = await api.post<PredictionSaveResponse>('/api/predictions/save', request);
    return response.data;
  }

  /**
   * Fetch saved prediction history (Phase 16)
   */
  async getPredictionHistory(limit = 20): Promise<PredictionHistoryResponse> {
    const response = await api.get<PredictionHistoryResponse>('/api/predictions/history', {
      params: { limit }
    });
    return response.data;
  }

  /**
   * Phase 43: Get paginated prediction list for dashboard
   */
  async listPredictions(limit: number = 20, offset: number = 0): Promise<any> {
    const response = await api.get('/api/predictions/list', {
      params: { limit, offset }
    });
    return response.data;
  }

  /**
   * Phase 43: Get comprehensive prediction detail view
   */
  async getPredictionDetail(predictionId: number): Promise<any> {
    const response = await api.get(`/api/predictions/${predictionId}`);
    return response.data;
  }

  /**
   * Phase 43: Export prediction as PDF, JSON, or CSV
   */
  async exportPrediction(predictionId: number, format: 'pdf' | 'json' | 'csv'): Promise<any> {
    const response = await api.post('/api/predictions/export', {
      prediction_id: predictionId,
      format: format
    });
    return response.data;
  }

  /**
   * Format MAPE as percentage
   */
  formatMAPE(mape: number | null): string {
    if (mape === null) return '0.00%';
    return mape.toFixed(2) + '%';
  }

  /**
   * Return a CSS color class for MAPE quality.
   */
  getQualityColor(mape: number | null): string {
    if (mape === null || Number.isNaN(mape)) {
      return 'text-gray-500';
    }
    if (mape <= 10) {
      return 'text-green-600';
    }
    if (mape <= 20) {
      return 'text-yellow-600';
    }
    return 'text-red-600';
  }

  /**
   * Format prediction value
   */
  formatPrediction(value: number): string {
    return Math.round(value).toString();
  }

  /**
   * Phase 43: Clear all predictions for current hospital
   */
  async clearPredictions(): Promise<any> {
    const response = await api.delete('/api/predictions/clear');
    return response.data;
  }

  /**
   * Phase 43: Delete selected predictions by IDs
   */
  async deleteSelectedPredictions(predictionIds: number[]): Promise<any> {
    const response = await api.post('/api/predictions/delete-selected', {
      prediction_ids: predictionIds
    });
    return response.data;
  }
}

const predictionService = new PredictionService();

export default predictionService;
