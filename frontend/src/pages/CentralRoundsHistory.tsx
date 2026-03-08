import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import roundService from '../services/roundService';
import type { CentralRoundHistoryItem } from '../types/rounds';
import { formatErrorMessage } from '../utils/errorMessage';

const CentralRoundsHistory: React.FC = () => {
  const navigate = useNavigate();
  const [rounds, setRounds] = useState<CentralRoundHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await roundService.getCentralRoundHistory();
        setRounds(data);
      } catch (err) {
        setError(formatErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <ConsoleLayout title="Rounds History" subtitle="Central view of completed federated rounds">
      <div className="max-w-7xl mx-auto">
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {formatErrorMessage(error)}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Completed Rounds ({rounds.length})</h2>
          </div>

          {loading ? (
            <div className="p-6 text-gray-600 text-center">Loading round history...</div>
          ) : rounds.length === 0 ? (
            <div className="p-6 text-gray-600 text-center">No completed rounds found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Round</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Hospitals</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Target</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Model Type</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Duration</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Completed</th>
                    <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {rounds.map((round) => (
                    <tr key={round.round_number} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-semibold text-gray-900">Round {round.round_number}</td>
                      <td className="px-6 py-4">{round.num_participating_hospitals}</td>
                      <td className="px-6 py-4">{round.target_column}</td>
                      <td className="px-6 py-4">{round.model_type}</td>
                      <td className="px-6 py-4">{round.duration_hours !== null ? `${round.duration_hours} h` : 'N/A'}</td>
                      <td className="px-6 py-4">{round.completed_at ? new Date(round.completed_at).toLocaleString() : 'N/A'}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => navigate(`/rounds-history/central/${round.round_number}`)}
                          className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                        >
                          View History
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default CentralRoundsHistory;
