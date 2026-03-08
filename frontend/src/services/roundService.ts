import api from './api';
import {
  RoundStatistics,
  RoundDetail,
  CentralRoundHistoryItem,
  CentralRoundHistoryDetail,
  HospitalRoundHistoryItem,
  HospitalRoundHistoryDetail,
} from '../types/rounds';
import { TrainingRound } from '../types/aggregation';
import { AxiosResponse } from 'axios';

class RoundService {
  /**
   * Create new federated round
   */
  async createRound(): Promise<any> {
    const response = await api.post('/api/rounds/create');
    return response.data;
  }

  /**
   * Get current active round
   */
  async getCurrentRound(): Promise<TrainingRound> {
    const response = await api.get<TrainingRound>('/api/rounds/current');
    return response.data;
  }

  /**
   * Get active round (Phase 41)
   */
  async getActiveRound(): Promise<AxiosResponse<any>> {
    return api.get('/api/rounds/active');
  }

  async validateContract(
    roundId: number,
    datasetId: number,
    modelArchitecture: 'TFT' | 'ML_REGRESSION',
    hyperparameters: { epochs?: number; batch_size?: number; learning_rate?: number }
  ): Promise<AxiosResponse<any>> {
    return api.get(`/api/rounds/${roundId}/contract/validate`, {
      params: {
        dataset_id: datasetId,
        model_architecture: modelArchitecture,
        epochs: hyperparameters.epochs,
        batch_size: hyperparameters.batch_size,
        learning_rate: hyperparameters.learning_rate,
      }
    });
  }

  /**
   * Get round details
   */
  async getRoundDetails(roundNumber: number): Promise<RoundDetail> {
    const response = await api.get<RoundDetail>(`/api/rounds/${roundNumber}`);
    return response.data;
  }

  /**
   * Get round statistics
   */
  async getStatistics(): Promise<RoundStatistics> {
    const response = await api.get<RoundStatistics>('/api/rounds/statistics/overview');
    return response.data;
  }

  /**
   * Get participation matrix for specific round (Phase 41)
   */
  async getParticipationMatrix(roundId: number): Promise<AxiosResponse<any>> {
    return api.get(`/api/rounds/${roundId}/participation`);
  }

  /**
   * Get participation matrix for active round (Phase 41)
   */
  async getActiveParticipationMatrix(): Promise<AxiosResponse<any>> {
    return api.get('/api/rounds/active/participation');
  }

  /**
   * Get aggregation status (Phase 41)
   */
  async getAggregationStatus(roundId?: number): Promise<AxiosResponse<any>> {
    const endpoint = roundId 
      ? `/api/aggregation/status?round_id=${roundId}`
      : '/api/aggregation/status';
    return api.get(endpoint);
  }

  /**
   * Start aggregation for round (Phase 41)
   */
  async startAggregation(roundId?: number): Promise<AxiosResponse<any>> {
    const endpoint = roundId
      ? `/api/aggregation/compute?round_id=${roundId}`
      : '/api/aggregation/compute';
    return api.post(endpoint, {});
  }

  /**
   * Start a round
   */
  async startRound(roundNumber: number): Promise<TrainingRound> {
    const response = await api.post<TrainingRound>(`/api/rounds/${roundNumber}/start`);
    return response.data;
  }

  /**
   * Check hospital eligibility for round
   */
  async checkRoundEligibility(roundId: number): Promise<{ is_eligible: boolean; reason: string }> {
    const response = await api.get<{ is_eligible: boolean; reason: string }>(
      `/api/rounds/${roundId}/eligibility`
    );
    return response.data;
  }

  /**
   * Update round status (Phase 41)
   */
  async updateRoundStatus(
    roundId: number,
    status: 'planning' | 'in_progress' | 'completed'
  ): Promise<AxiosResponse<any>> {
    return api.patch(`/api/rounds/${roundId}/status`, { status });
  }

  async getCentralRoundHistory(): Promise<CentralRoundHistoryItem[]> {
    const response = await api.get<CentralRoundHistoryItem[]>('/api/rounds/history/central');
    return response.data;
  }

  async getCentralRoundHistoryDetail(roundNumber: number): Promise<CentralRoundHistoryDetail> {
    const response = await api.get<CentralRoundHistoryDetail>(`/api/rounds/history/central/${roundNumber}`);
    return response.data;
  }

  async getHospitalRoundHistory(): Promise<HospitalRoundHistoryItem[]> {
    const response = await api.get<HospitalRoundHistoryItem[]>('/api/rounds/history/hospital');
    return response.data;
  }

  async getHospitalRoundHistoryDetail(roundNumber: number): Promise<HospitalRoundHistoryDetail> {
    const response = await api.get<HospitalRoundHistoryDetail>(`/api/rounds/history/hospital/${roundNumber}`);
    return response.data;
  }
}

export default new RoundService();
