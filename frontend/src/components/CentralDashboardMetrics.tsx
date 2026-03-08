import React, { useEffect, useState } from 'react';
import dashboardService from '../services/dashboardService';

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

const CentralDashboardMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<CentralMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await dashboardService.getCentralMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
        console.error('Error fetching central metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-4 text-center">Loading central metrics...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!metrics) return <div className="p-4 text-center">No data available</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Hospital Network */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">HOSPITAL NETWORK</h3>
        <div className="space-y-3">
          <div>
            <p className="text-2xl font-bold text-blue-600">{metrics.hospitals.total}</p>
            <p className="text-xs text-gray-500">Total Hospitals</p>
          </div>
          <div>
            <p className="text-xl font-bold text-green-600">{metrics.hospitals.active}</p>
            <p className="text-xs text-gray-500">Active Now</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
            <div
              className="h-2 rounded-full bg-green-500"
              style={{ width: `${metrics.hospitals.participation_rate}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-600">{metrics.hospitals.participation_rate.toFixed(1)}% participation</p>
        </div>
      </div>

      {/* Federated Learning */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">FEDERATED LEARNING</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-2xl font-bold text-purple-600">{metrics.federated_learning.current_round}</p>
              <p className="text-xs text-gray-500">Current Round</p>
            </div>
            <div className={`px-2 py-1 rounded text-xs font-semibold ${
              metrics.federated_learning.is_round_active
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            }`}>
              {metrics.federated_learning.is_round_active ? 'ACTIVE' : 'CLOSED'}
            </div>
          </div>
          <div className="pt-2 border-t">
            <p className="text-lg font-bold text-indigo-600">{metrics.federated_learning.current_round_participants}</p>
            <p className="text-xs text-gray-500">Participants</p>
          </div>
        </div>
      </div>

      {/* Global Models */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">GLOBAL MODELS</h3>
        <div className="space-y-3">
          <div>
            <p className="text-3xl font-bold text-orange-600">{metrics.federated_learning.global_models_created}</p>
            <p className="text-xs text-gray-500">Models Created</p>
          </div>
          <div className="bg-orange-50 p-2 rounded text-xs text-gray-600">
            Aggregated from {metrics.hospitals.total} hospitals
          </div>
        </div>
      </div>

      {/* Privacy Accounting */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">PRIVACY ACCOUNTING</h3>
        <div className="space-y-3">
          <div>
            <p className="text-2xl font-bold text-red-600">{metrics.privacy_accounting.total_epsilon_spent.toFixed(2)}</p>
            <p className="text-xs text-gray-500">Total ε Spent</p>
          </div>
          <div>
            <p className="text-lg font-bold text-red-500">{metrics.privacy_accounting.average_epsilon_per_hospital.toFixed(3)}</p>
            <p className="text-xs text-gray-500">Avg ε/Hospital</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CentralDashboardMetrics;
