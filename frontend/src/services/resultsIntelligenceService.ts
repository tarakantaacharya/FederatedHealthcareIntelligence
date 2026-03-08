import api from './api';
import type {
  LocalModelMetrics,
  ApprovedGlobalModel,
  RoundGovernanceSummary,
  HorizonAnalytics,
  DriftAnalysis,
  PredictionMetricsCategory,
} from '../types/governance';

class ResultsIntelligenceService {
  async getHospitalOverview(): Promise<any> {
    const response = await api.get('/api/results-intelligence/hospital/overview');
    return response.data;
  }

  async getCentralOverview(): Promise<any> {
    const response = await api.get('/api/results-intelligence/central/overview');
    return response.data;
  }

  async getCentralHospitalDetail(hospitalId: number): Promise<any> {
    const response = await api.get(`/api/results-intelligence/central/hospitals/${hospitalId}`);
    return response.data;
  }

  async getCentralHospitalRoundDetail(hospitalId: number, roundNumber: number): Promise<any> {
    const response = await api.get(
      `/api/results-intelligence/central/hospitals/${hospitalId}/rounds/${roundNumber}`
    );
    return response.data;
  }

  // ============================================================================
  // NEW GOVERNANCE-ALIGNED METHODS (Phase 42+)
  // ============================================================================

  async getLocalModelMetrics(roundNumber?: number): Promise<LocalModelMetrics> {
    const params = roundNumber ? { round_number: roundNumber } : {};
    const response = await api.get(
      '/api/results-intelligence/hospital/local-model-metrics',
      { params }
    );
    return response.data;
  }

  async getApprovedGlobalModel(roundNumber?: number): Promise<ApprovedGlobalModel> {
    const params = roundNumber ? { round_number: roundNumber } : {};
    const response = await api.get(
      '/api/results-intelligence/hospital/global-model',
      { params }
    );
    return response.data;
  }

  async getHorizonAnalytics(horizonKey: string): Promise<HorizonAnalytics> {
    const response = await api.get(
      `/api/results-intelligence/hospital/horizon-analytics/${horizonKey}`
    );
    return response.data;
  }

  async getDriftAnalysis(baselineRound: number = 1): Promise<DriftAnalysis> {
    const response = await api.get(
      '/api/results-intelligence/hospital/drift-analysis',
      { params: { baseline_round: baselineRound } }
    );
    return response.data;
  }

  async getRoundGovernanceSummary(roundNumber: number): Promise<RoundGovernanceSummary> {
    const response = await api.get(
      `/api/results-intelligence/central/round/${roundNumber}/governance`
    );
    return response.data;
  }

  async getCentralGlobalModel(roundNumber?: number): Promise<ApprovedGlobalModel> {
    const params = roundNumber ? { round_number: roundNumber } : {};
    const response = await api.get(
      '/api/results-intelligence/central/global-model',
      { params }
    );
    return response.data;
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Categorize prediction values into Risk and Confidence buckets
   * This is done client-side for UI responsiveness
   */
  categorizePredictionMetrics(
    predictionValue: number | null,
    confidence: number | null
  ): PredictionMetricsCategory {
    // Risk categorization
    let riskCategory: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN' = 'UNKNOWN';
    let riskMin = 0,
      riskMax = 1;

    if (predictionValue !== null) {
      if (predictionValue < 0.3) {
        riskCategory = 'LOW';
        riskMin = 0;
        riskMax = 0.3;
      } else if (predictionValue < 0.7) {
        riskCategory = 'MEDIUM';
        riskMin = 0.3;
        riskMax = 0.7;
      } else {
        riskCategory = 'HIGH';
        riskMin = 0.7;
        riskMax = 1;
      }
    }

    // Confidence categorization
    let confCategory: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | 'UNKNOWN' = 'UNKNOWN';
    let confMin = 0,
      confMax = 1;

    if (confidence !== null) {
      if (confidence < 0.5) {
        confCategory = 'LOW';
        confMin = 0;
        confMax = 0.5;
      } else if (confidence < 0.75) {
        confCategory = 'MODERATE';
        confMin = 0.5;
        confMax = 0.75;
      } else if (confidence < 0.9) {
        confCategory = 'HIGH';
        confMin = 0.75;
        confMax = 0.9;
      } else {
        confCategory = 'VERY_HIGH';
        confMin = 0.9;
        confMax = 1;
      }
    }

    return {
      risk: {
        value: predictionValue,
        category: riskCategory,
        threshold_min: riskMin,
        threshold_max: riskMax,
      },
      confidence: {
        value: confidence,
        category: confCategory,
        threshold_min: confMin,
        threshold_max: confMax,
      },
    };
  }
}

export default new ResultsIntelligenceService();
