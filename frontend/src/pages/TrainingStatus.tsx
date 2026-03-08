import React, { useEffect, useState } from 'react';
import ConsoleLayout from '../components/ConsoleLayout';
import trainingService from '../services/trainingService';
import { TrainingStatusItem } from '../types/training';
import { formatErrorMessage } from '../utils/errorMessage';

const TrainingStatus: React.FC = () => {
  const [items, setItems] = useState<TrainingStatusItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const data = await trainingService.getTrainingStatus();
        setItems(data);
        setError('');
      } catch (err) {
        setError(formatErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  const formatNumber = (value: number | null) => {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(4);
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      TRAINING_COMPLETE: 'bg-blue-100 text-blue-800',
      MASK_UPLOADED: 'bg-purple-100 text-purple-800',
      WEIGHTS_UPLOADED: 'bg-green-100 text-green-800',
      AGGREGATED: 'bg-emerald-100 text-emerald-800'
    };
    const style = styles[status] || 'bg-gray-100 text-gray-800';
    return <span className={`px-2 py-1 rounded text-xs font-semibold ${style}`}>{status}</span>;
  };

  return (
    <ConsoleLayout title="Training Status" subtitle="Structured training lifecycle updates">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Training Status Table</h3>
          </div>

          {loading ? (
            <div className="p-6 text-gray-600">Loading training status...</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-gray-600">No training status records available.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dataset</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Round</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Architecture</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Loss</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {items.map((item) => (
                    <tr key={item.model_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.dataset_name || `Dataset ${item.dataset_id ?? 'N/A'}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.round_number ?? 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.training_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.model_architecture}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatNumber(item.loss)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {statusBadge(item.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'N/A'}
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

export default TrainingStatus;
