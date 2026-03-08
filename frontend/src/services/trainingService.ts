import api from './api';
import { TrainingRequest, TrainingResponse, TrainedModel, TrainingStatusItem } from '../types/training';

class TrainingService {
  /**
   * Start local model training
   */
  async startTraining(request: TrainingRequest): Promise<TrainingResponse> {
    const response = await api.post<TrainingResponse>('/api/training/start', request);
    return response.data;
  }

  /**
   * Get all trained models for current hospital
   */
  async getModels(skip: number = 0, limit: number = 100): Promise<TrainedModel[]> {
    const response = await api.get<TrainedModel[]>('/api/training/models', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Get model details by ID
   */
  async getModelById(modelId: number): Promise<TrainedModel> {
    const response = await api.get<TrainedModel>(`/api/training/models/${modelId}`);
    return response.data;
  }

  /**
   * Get training status records
   */
  async getTrainingStatus(): Promise<TrainingStatusItem[]> {
    const response = await api.get<TrainingStatusItem[]>('/api/training/status');
    return response.data;
  }

  /**
   * Get privacy budget status (epsilon/delta)
   */
  async getPrivacyBudget(): Promise<any> {
    const response = await api.get<any>('/api/privacy-budget/status');
    return response.data;
  }

  /**
   * Get current federated round info
   */
  async getCurrentRound(): Promise<any> {
    const response = await api.get<any>('/api/rounds/current');
    return response.data;
  }

  /**
   * Format R² score as percentage
   */
  formatR2(r2: number): string {
    return (r2 * 100).toFixed(2) + '%';
  }

  /**
   * Format MSE/MAE with 2 decimals
   */
  formatMetric(value: number): string {
    return value.toFixed(2);
  }

  /**
   * Format loss with 4 decimals
   */
  formatLoss(value: number): string {
    return value.toFixed(4);
  }
}

export default new TrainingService();
