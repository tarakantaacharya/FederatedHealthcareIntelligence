import api from './api';

interface HospitalMetrics {
  hospital_id: string;
  hospital_name: string;
  resources: {
    datasets: number;
    local_models: number;
    predictions: number;
  };
  current_round: {
    round_number: number | null;
    is_active: boolean;
    status: string;
  };
  privacy: {
    total_epsilon_spent: number;
    round_budget: number;
    rank: number;
  };
  timestamp: string;
}

interface CentralMetrics {
  hospitals: {
    total: number;
    active: number;
    participation_rate: number;
  };
  federated_learning: {
    current_round: number;
    is_round_active: boolean;
    current_round_participants: number;
    global_models_created: number;
  };
  privacy_accounting: {
    total_epsilon_spent: number;
    average_epsilon_per_hospital: number;
  };
  timestamp: string;
}

interface RecentActivity {
  recent_trainings: Array<{
    model_id: number;
    round: number;
    architecture: string;
    timestamp: string | null;
  }>;
  recent_predictions: Array<{
    prediction_id: number;
    model_id: number;
    target_value: number;
    timestamp: string | null;
  }>;
}

class DashboardService {
  async getHospitalMetrics(): Promise<HospitalMetrics> {
    const response = await api.get<HospitalMetrics>(`/api/dashboard/hospital/metrics`);
    return response.data;
  }

  async getCentralMetrics(): Promise<CentralMetrics> {
    const response = await api.get<CentralMetrics>(`/api/dashboard/central/metrics`);
    return response.data;
  }

  async getHospitalRecentActivity(limit: number = 10): Promise<RecentActivity> {
    const response = await api.get<RecentActivity>(`/api/dashboard/hospital/recent-activity`, {
      params: { limit }
    });
    return response.data;
  }
}

export default new DashboardService();
