import api from './api';

export interface AdminStats {
  totalHospitals: number;
  approvedHospitals: number;
  activeRounds: number;
  pendingApprovals: number;
  totalAggregations: number;
  averageGlobalLoss?: number | null;
  participationHeatmap?: Array<{ round_number: number; participants: number; status: string }>;
}

export interface Hospital {
  id: number;
  hospital_id: string;
  hospital_name: string;
  contact_email: string;
  location: string;
  is_active: boolean;
  is_verified: boolean;
  verification_status?: string;
  is_allowed_federated?: boolean;
  role: string;
  created_at: string;
}

export interface RoundPolicyRequest {
  target_column: string;
  is_emergency?: boolean;
  participation_mode?: 'ALL' | 'SELECTIVE';
  selection_criteria?: 'REGION' | 'SIZE' | 'EXPERIENCE' | 'MANUAL' | null;
  selection_value?: string | null;
  manual_hospital_ids?: number[] | null;
  model_type?: 'TFT' | 'ML_REGRESSION';
  required_canonical_features: string[];
  required_hyperparameters: Record<string, any>;
  allocated_privacy_budget?: number;
  tft_hidden_size?: number;
  tft_attention_heads?: number;
  tft_dropout?: number;
  tft_regularization_factor?: number;
}

export interface RoundAnalyticsResponse {
  round_id: number;
  round_number: number;
  num_hospitals: number;
  avg_loss: number | null;
  avg_accuracy: number | null;
  std_loss: number | null;
  std_accuracy: number | null;
  contributing_regions: Array<{ region: string; count: number }>;
}

export interface CanonicalField {
  id: number;
  field_name: string;
  description?: string;
  data_type?: string;
  category?: string;
  unit?: string;
  is_active: boolean;
}

class AdminService {
  /**
   * Get admin dashboard statistics
   */
  async getAdminStats(): Promise<AdminStats> {
    try {
      const response = await api.get('/api/admin/metrics');
      const data = response.data;
      return {
        totalHospitals: data.total_hospitals,
        approvedHospitals: data.approved_hospitals,
        activeRounds: data.active_rounds,
        pendingApprovals: data.pending_approvals,
        totalAggregations: data.total_aggregations,
        averageGlobalLoss: data.average_global_loss ?? null,
        participationHeatmap: data.participation_heatmap ?? []
      };
    } catch (error) {
      console.error('Failed to fetch admin stats:', error);
      // Return zeros on error
      return {
        totalHospitals: 0,
        approvedHospitals: 0,
        activeRounds: 0,
        pendingApprovals: 0,
        totalAggregations: 0,
        averageGlobalLoss: null,
        participationHeatmap: []
      };
    }
  }

  /**
   * Get all hospitals
   */
  async getAllHospitals(): Promise<Hospital[]> {
    const response = await api.get<Hospital[]>('/api/hospitals/admin/list');
    return response.data;
  }

  /**
   * Get hospital by ID
   */
  async getHospitalById(hospitalId: number): Promise<Hospital> {
    const response = await api.get<Hospital>(`/api/hospitals/${hospitalId}`);
    return response.data;
  }

  /**
   * Get hospital by ID (admin endpoint)
   */
  async getAdminHospitalById(hospitalId: number): Promise<Hospital> {
    const response = await api.get<Hospital>(`/api/hospitals/admin/${hospitalId}`);
    return response.data;
  }

  /**
   * Verify hospital
   */
  async verifyHospital(hospitalId: string): Promise<any> {
    const response = await api.post(`/api/hospitals/${hospitalId}/verify`);
    return response.data;
  }

  /**
   * Deactivate hospital
   */
  async deactivateHospital(hospitalId: string): Promise<any> {
    const response = await api.post(`/api/hospitals/${hospitalId}/deactivate`);
    return response.data;
  }

  /**
   * Activate hospital
   */
  async activateHospital(hospitalId: string): Promise<any> {
    const response = await api.post(`/api/hospitals/${hospitalId}/activate`);
    return response.data;
  }

  /**
   * Allow/deny hospital federated participation
   */
  async setFederatedAccess(hospitalId: string, allow: boolean): Promise<any> {
    const response = await api.post(`/api/hospitals/${hospitalId}/allow-federated`, null, {
      params: { allow }
    });
    return response.data;
  }

  /**
   * Create a new federated round with policy configuration
   */
  async createRound(policy: RoundPolicyRequest): Promise<any> {
    const payload: any = {
      target_column: policy.target_column,
      is_emergency: policy.is_emergency ?? false,
      participation_mode: policy.participation_mode ?? 'ALL',
      model_type: policy.model_type ?? 'TFT',
      required_canonical_features: policy.required_canonical_features ?? [],
      required_hyperparameters: policy.required_hyperparameters ?? {}
    };

    if (policy.allocated_privacy_budget !== undefined) {
      payload.allocated_privacy_budget = policy.allocated_privacy_budget;
    }

    if (policy.participation_mode === 'SELECTIVE') {
      payload.selection_criteria = policy.selection_criteria;
      payload.selection_value = policy.selection_value;
      if (policy.selection_criteria === 'MANUAL') {
        payload.manual_hospital_ids = policy.manual_hospital_ids || [];
      }
    }

    const response = await api.post('/api/rounds/create', payload);
    return response.data;
  }

  /**
   * Disable training for a round
   */
  async disableTraining(roundNumber: number): Promise<any> {
    const response = await api.post(`/api/rounds/${roundNumber}/disable-training`);
    return response.data;
  }

  /**
   * Enable training for a round
   */
  async enableTraining(roundNumber: number): Promise<any> {
    const response = await api.post(`/api/rounds/${roundNumber}/enable-training`);
    return response.data;
  }

  /**
   * Restart a closed round
   */
  async restartRound(roundNumber: number): Promise<any> {
    const response = await api.post(`/api/rounds/${roundNumber}/restart`);
    return response.data;
  }

  /**
   * Delete a round and related data
   */
  async deleteRound(roundNumber: number): Promise<any> {
    const response = await api.delete(`/api/rounds/${roundNumber}`);
    return response.data;
  }

  /**
   * Get canonical fields for target column selection
   */
  async getCanonicalFields(): Promise<CanonicalField[]> {
    try {
      const response = await api.get<{ total: number; fields: CanonicalField[] }>(
        '/api/canonical-fields'
      );
      return response.data.fields;
    } catch (error) {
      console.error('Failed to fetch canonical fields:', error);
      return [];
    }
  }

  /**
   * Get round-level analytics (admin)
   */
  async getRoundAnalytics(roundId: number): Promise<RoundAnalyticsResponse> {
    const response = await api.get<RoundAnalyticsResponse>(`/api/rounds/${roundId}/statistics`);
    return response.data;
  }
}

export default new AdminService();
