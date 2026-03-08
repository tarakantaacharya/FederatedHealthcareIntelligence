import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import roundService from '../services/roundService';
import type { CentralRoundHistoryDetail } from '../types/rounds';
import { formatErrorMessage } from '../utils/errorMessage';

const pct = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0.00%';
  return `${Number(value).toFixed(3)}%`;
};

const num = (value: number | null | undefined, d: number = 4) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0.0';
  return Number(value).toFixed(d);
};

const CentralRoundHistoryDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { roundNumber } = useParams();
  const [detail, setDetail] = useState<CentralRoundHistoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const rn = Number(roundNumber);
    if (!rn) {
      setError('Invalid round number');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await roundService.getCentralRoundHistoryDetail(rn);
        setDetail(data);
      } catch (err) {
        setError(formatErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [roundNumber]);

  return (
    <ConsoleLayout title="Round History" subtitle="Central round detail">
      <div className="max-w-7xl mx-auto space-y-6">
        <button
          onClick={() => navigate('/rounds-history/central')}
          className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
        >
          Back to Rounds History
        </button>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {formatErrorMessage(error)}
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">Loading round history...</div>
        ) : !detail ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">No data found.</div>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Round {detail.round_number} Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div><span className="text-gray-500">Hospitals:</span> <span className="font-semibold">{detail.num_participating_hospitals}</span></div>
                <div><span className="text-gray-500">Target Column:</span> <span className="font-semibold">{detail.target_column}</span></div>
                <div><span className="text-gray-500">Model Type:</span> <span className="font-semibold">{detail.model_type}</span></div>
                <div><span className="text-gray-500">Aggregation:</span> <span className="font-semibold">{detail.aggregation_strategy}</span></div>
                <div><span className="text-gray-500">Duration:</span> <span className="font-semibold">{detail.duration_hours !== null ? `${detail.duration_hours} h` : 'N/A'}</span></div>
                <div><span className="text-gray-500">Status:</span> <span className="font-semibold">{detail.status}</span></div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Features Taken</h3>
              {detail.features_taken.length === 0 ? (
                <p className="text-sm text-gray-500">No features recorded.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {detail.features_taken.map((feature) => (
                    <span key={feature} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {feature}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Global Model</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Approved:</span> <span className="font-semibold">{detail.global_model.approved ? 'Yes' : 'No'}</span></div>
                <div><span className="text-gray-500">Model ID:</span> <span className="font-semibold">{detail.global_model.model_id ?? 'N/A'}</span></div>
                <div className="md:col-span-2 break-all"><span className="text-gray-500">Model Hash:</span> <span className="font-semibold">{detail.global_model.model_hash || 'Not available (not approved)'}</span></div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Global Model Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-gray-500">Loss:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_loss)}</span></div>
                <div><span className="text-gray-500">MAPE:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_mape)}</span></div>
                <div><span className="text-gray-500">RMSE:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_rmse)}</span></div>
                <div><span className="text-gray-500">R²:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_r2)}</span></div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Hospital Contribution Distribution</h3>
              {detail.hospital_contribution_distribution.length === 0 ? (
                <p className="text-sm text-gray-500">No contribution data available.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Hospital</th>
                        <th className="px-4 py-2 text-left">Contribution %</th>
                        <th className="px-4 py-2 text-left">Local Loss</th>
                        <th className="px-4 py-2 text-left">Type</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {detail.hospital_contribution_distribution.map((row) => (
                        <tr key={row.hospital_id}>
                          <td className="px-4 py-2">{row.hospital_name} ({row.hospital_code})</td>
                          <td className="px-4 py-2 font-semibold text-purple-700">{pct(row.contribution_percentage)}</td>
                          <td className="px-4 py-2">{num(row.local_loss)}</td>
                          <td className="px-4 py-2">{row.model_types.join(', ') || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default CentralRoundHistoryDetailPage;
