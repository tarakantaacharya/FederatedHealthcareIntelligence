import api from './api';
import { AggregationRequest, AggregationResponse, TrainingRound } from '../types/aggregation';

class AggregationService {
    /**
   * Get participation matrix (governance eligibility check)
   */
  async getParticipationMatrix(roundNumber: number): Promise<any> {
    const response = await api.get(
      `/api/aggregation/participation/${roundNumber}`
    );
    return response.data;
  }
  /**
   * Perform FedAvg aggregation
   */
  async performAggregation(request: AggregationRequest): Promise<AggregationResponse> {
    const response = await api.post<AggregationResponse>('/api/aggregation/fedavg', request);
    return response.data;
  }

  /**
   * Get global model for round
   */
  async getGlobalModel(roundNumber: number): Promise<any> {
    const response = await api.get(`/api/aggregation/global/${roundNumber}`);
    return response.data;
  }

  /**
   * Get latest global model (admin)
   */
  async getLatestGlobalModel(): Promise<any> {
    const response = await api.get('/api/aggregation/global-model');
    return response.data;
  }

  /**
   * List all training rounds
   */
  async getTrainingRounds(skip: number = 0, limit: number = 100): Promise<TrainingRound[]> {
    const response = await api.get<TrainingRound[]>('/api/aggregation/rounds', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Format accuracy as percentage
   */
  formatAccuracy(accuracy: number): string {
    return (accuracy * 100).toFixed(2) + '%';
  }

  /**
   * Format loss with 2 decimals
   */
  formatLoss(loss: number): string {
    return loss.toFixed(2);
  }

  /**
   * Clear all federated rounds (Admin-only, development use)
   */
  async clearAllRounds(): Promise<any> {
    const response = await api.post('/api/rounds/clear', {});
    return response.data;
  }

  /**
   * Create a new federated round
   */
  async createRound(targetColumn: string): Promise<any> {
    const response = await api.post('/api/rounds/create', {
      target_column: targetColumn
    });
    return response.data;
  }

  /**
   * Start a federated round
   */
  async startRound(roundNumber: number): Promise<any> {
    const response = await api.post(`/api/rounds/${roundNumber}/start`);
    return response.data;
  }
}

export default new AggregationService();
