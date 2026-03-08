import api from './api';
import { 
  ModelDownloadResponse, 
  GlobalModel,
  AggregatedWeightsPreviewResponse
} from '../types/modelUpdates';

class ModelUpdateService {
  /**
   * Download global model for specific round
   */
  async downloadGlobalModel(roundNumber: number): Promise<ModelDownloadResponse> {
    const response = await api.post<ModelDownloadResponse>(`/api/model-updates/download/${roundNumber}`);
    return response.data;
  }

  /**
   * Get available global models
   */
  async getAvailableModels(): Promise<GlobalModel[]> {
    const response = await api.get<GlobalModel[]>('/api/model-updates/global');
    return response.data;
  }

  /**
   * Get approved/distributed aggregated global weights preview for hospital
   */
  async getAggregatedWeightsPreview(modelId: number): Promise<AggregatedWeightsPreviewResponse> {
    const response = await api.get<AggregatedWeightsPreviewResponse>(`/api/model-updates/global/${modelId}/weights-json`);
    return response.data;
  }

  /**
   * Get approved aggregated global weights preview for Central admin
   */
  async getCentralAggregatedWeightsPreview(modelId: number): Promise<AggregatedWeightsPreviewResponse> {
    const response = await api.get<AggregatedWeightsPreviewResponse>(`/api/model-updates/admin/global/${modelId}/weights-json`);
    return response.data;
  }

  /**
   * Format sync percentage
   */
  formatSyncPercentage(percentage: number): string {
    return percentage.toFixed(1) + '%';
  }
}

export default new ModelUpdateService();
