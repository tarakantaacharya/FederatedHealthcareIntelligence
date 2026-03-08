import React, { useEffect, useState } from 'react';
import dashboardService from '../services/dashboardService';

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

const HospitalDashboardMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<HospitalMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await dashboardService.getHospitalMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
        console.error('Error fetching hospital metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-4 text-center">Loading metrics...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!metrics) return <div className="p-4 text-center">No data available</div>;

  // Calculate privacy budget status
  const budgetUsed = (metrics.privacy.total_epsilon_spent / metrics.privacy.round_budget) * 100;
  const budgetStatus = budgetUsed > 90 ? 'critical' : budgetUsed > 70 ? 'warning' : 'healthy';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Hospital Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-2">HOSPITAL</h3>
        <p className="text-2xl font-bold text-blue-600">{metrics.hospital_name}</p>
        <p className="text-xs text-gray-500 mt-2">ID: {metrics.hospital_id}</p>
        <p className="text-xs text-gray-500">Rank: #{metrics.privacy.rank}</p>
      </div>

      {/* Resources Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">RESOURCES</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Datasets:</span>
            <span className="font-bold text-lg">{metrics.resources.datasets}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Local Models:</span>
            <span className="font-bold text-lg">{metrics.resources.local_models}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Predictions:</span>
            <span className="font-bold text-lg">{metrics.resources.predictions}</span>
          </div>
        </div>
      </div>

      {/* Current Round */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">CURRENT ROUND</h3>
        <div>
          <p className="text-2xl font-bold text-green-600">
            {metrics.current_round.round_number ?? 'N/A'}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${metrics.current_round.is_active ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            <span className="text-xs font-semibold">
              {metrics.current_round.is_active ? 'ACTIVE' : 'INACTIVE'}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-2">Status: {metrics.current_round.status}</p>
        </div>
      </div>

      {/* Privacy Budget */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-gray-600 text-sm font-semibold mb-4">PRIVACY BUDGET</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm">ε Spent</span>
            <span className="font-bold">{metrics.privacy.total_epsilon_spent.toFixed(3)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm">ε Budget</span>
            <span className="font-bold">{metrics.privacy.round_budget.toFixed(1)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              className={`h-2 rounded-full transition-all ${
                budgetStatus === 'critical' ? 'bg-red-500' : budgetStatus === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(budgetUsed, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">{budgetUsed.toFixed(1)}% used</p>
        </div>
      </div>
    </div>
  );
};

export default HospitalDashboardMetrics;
