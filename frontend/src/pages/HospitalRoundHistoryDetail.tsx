import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import roundService from '../services/roundService';
import type { HospitalRoundHistoryDetail } from '../types/rounds';
import { formatErrorMessage } from '../utils/errorMessage';

const pct = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0.00%';
  return `${Number(value).toFixed(3)}%`;
};

const num = (value: number | null | undefined, d: number = 4) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '0.0';
  return Number(value).toFixed(d);
};

const HospitalRoundHistoryDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { roundNumber } = useParams();
  const [detail, setDetail] = useState<HospitalRoundHistoryDetail | null>(null);
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
        const data = await roundService.getHospitalRoundHistoryDetail(rn);
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
    <ConsoleLayout title="Round History" subtitle="Hospital round detail">
      <div className="max-w-7xl mx-auto space-y-6">
        <button
          onClick={() => navigate('/rounds-history/hospital')}
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
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Round {detail.round_number} - Your Participation</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div><span className="text-gray-500">Target Column:</span> <span className="font-semibold">{detail.target_column}</span></div>
                <div><span className="text-gray-500">Model Type:</span> <span className="font-semibold">{detail.hospital_contribution.types.join(', ') || detail.model_type}</span></div>
                <div><span className="text-gray-500">Duration:</span> <span className="font-semibold">{detail.duration_hours !== null ? `${detail.duration_hours} h` : 'N/A'}</span></div>
                <div><span className="text-gray-500">Your Contribution:</span> <span className="font-semibold text-purple-700">{pct(detail.hospital_contribution.contribution_percentage)}</span></div>
                <div><span className="text-gray-500">Your Local Loss:</span> <span className="font-semibold">{num(detail.hospital_contribution.local_loss)}</span></div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Features Used In This Round</h3>
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
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Global Metrics For This Round</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-gray-500">Loss:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_loss)}</span></div>
                <div><span className="text-gray-500">MAPE:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_mape)}</span></div>
                <div><span className="text-gray-500">RMSE:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_rmse)}</span></div>
                <div><span className="text-gray-500">R²:</span> <span className="font-semibold">{num(detail.global_model_metrics.average_r2)}</span></div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Datasets Involved</h3>
              {detail.datasets_involved.length === 0 ? (
                <p className="text-sm text-gray-500">No dataset metadata found for this round.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Dataset ID</th>
                        <th className="px-4 py-2 text-left">Filename</th>
                        <th className="px-4 py-2 text-left">Rows</th>
                        <th className="px-4 py-2 text-left">Columns</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {detail.datasets_involved.map((ds) => (
                        <tr key={ds.dataset_id}>
                          <td className="px-4 py-2">{ds.dataset_id}</td>
                          <td className="px-4 py-2">{ds.filename}</td>
                          <td className="px-4 py-2">{ds.num_rows ?? 'N/A'}</td>
                          <td className="px-4 py-2">{ds.num_columns ?? 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
              <strong>Extra insight:</strong> You submitted {detail.extra.total_models_submitted_by_hospital} model artifact(s) across {detail.extra.dataset_count} dataset(s) in this round.
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default HospitalRoundHistoryDetailPage;
