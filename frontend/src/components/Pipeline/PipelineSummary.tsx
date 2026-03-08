import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * Pipeline Summary Dashboard
 * 
 * Shows aggregated pipeline status across all datasets
 * for a hospital, with quick stats and dataset list.
 */

interface PipelineSummaryData {
  hospital_id: number;
  total_datasets: number;
  ready_for_training: number;
  failed_pipelines: number;
  average_progress: number;
  stages_distribution: {
    upload: number;
    validation: number;
    cleaning: number;
    feature_engineering: number;
    harmonization: number;
    ready_for_training: number;
  };
  pipelines: any[];
}

interface PipelineSummaryProps {
  hospitalId: number;
}

export const PipelineSummary: React.FC<PipelineSummaryProps> = ({ hospitalId }) => {
  const [summary, setSummary] = useState<PipelineSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchPipelineSummary();
    const interval = setInterval(fetchPipelineSummary, 10000);
    return () => clearInterval(interval);
  }, [hospitalId]);

  const fetchPipelineSummary = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `http://localhost:8000/api/pipelines/hospital/${hospitalId}/summary`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSummary(response.data);
      setError('');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch pipeline summary';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-500 py-6">Loading pipeline summary...</div>;
  }

  if (error) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded text-yellow-700">
        ⚠️ {error}
      </div>
    );
  }

  if (!summary) {
    return <div className="text-gray-500">No summary data available</div>;
  }

  const readyPercentage =
    summary.total_datasets > 0
      ? Math.round((summary.ready_for_training / summary.total_datasets) * 100)
      : 0;

  return (
    <div className="space-y-6">
      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Datasets */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <p className="text-xs text-gray-500 font-medium">Total Datasets</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{summary.total_datasets}</p>
          <p className="text-xs text-gray-600 mt-2">
            {summary.total_datasets === 1 ? '1 dataset' : `${summary.total_datasets} datasets`}
          </p>
        </div>

        {/* Ready for Training */}
        <div className="bg-green-50 p-4 rounded-lg border border-green-300 shadow-sm">
          <p className="text-xs text-green-600 font-medium">✅ Ready for Training</p>
          <p className="text-3xl font-bold text-green-700 mt-1">{summary.ready_for_training}</p>
          <p className="text-xs text-green-600 mt-2">{readyPercentage}% of datasets</p>
        </div>

        {/* Average Progress */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-300 shadow-sm">
          <p className="text-xs text-blue-600 font-medium">📊 Avg Progress</p>
          <p className="text-3xl font-bold text-blue-700 mt-1">{summary.average_progress}%</p>
          <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${summary.average_progress}%` }}
            />
          </div>
        </div>

        {/* Failed Pipelines */}
        <div
          className={`p-4 rounded-lg border shadow-sm ${
            summary.failed_pipelines > 0
              ? 'bg-red-50 border-red-300'
              : 'bg-gray-50 border-gray-300'
          }`}
        >
          <p
            className={`text-xs font-medium ${
              summary.failed_pipelines > 0 ? 'text-red-600' : 'text-gray-600'
            }`}
          >
            ❌ Failed Pipelines
          </p>
          <p
            className={`text-3xl font-bold mt-1 ${
              summary.failed_pipelines > 0 ? 'text-red-700' : 'text-gray-700'
            }`}
          >
            {summary.failed_pipelines}
          </p>
          <p className={`text-xs mt-2 ${
              summary.failed_pipelines > 0 ? 'text-red-600' : 'text-gray-600'
            }`}
          >
            {summary.failed_pipelines === 0 ? 'All clear' : 'Needs attention'}
          </p>
        </div>
      </div>

      {/* Stage Distribution */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4">📈 Stage Completion</h4>
        <div className="space-y-3">
          {[
            { name: 'Upload', key: 'upload', color: 'bg-purple-500' },
            { name: 'Validation', key: 'validation', color: 'bg-blue-500' },
            { name: 'Cleaning', key: 'cleaning', color: 'bg-green-500' },
            { name: 'Feature Engineering', key: 'feature_engineering', color: 'bg-yellow-500' },
            { name: 'Harmonization', key: 'harmonization', color: 'bg-indigo-500' },
            { name: 'Ready for Training', key: 'ready_for_training', color: 'bg-emerald-500' }
          ].map(({ name, key, color }) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-gray-700">{name}</p>
                <p className="text-sm font-semibold text-gray-900">
                  {summary.stages_distribution[key as keyof typeof summary.stages_distribution]}/{summary.total_datasets}
                </p>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`${color} h-2 rounded-full transition-all duration-300`}
                  style={{
                    width: `${
                      summary.total_datasets > 0
                        ? (summary.stages_distribution[
                            key as keyof typeof summary.stages_distribution
                          ] /
                            summary.total_datasets) *
                          100
                        : 0
                    }%`
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dataset List */}
      {summary.pipelines && summary.pipelines.length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">📋 All Datasets</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Dataset ID</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Progress</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Status</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Ready</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {summary.pipelines.map((pipeline) => (
                  <tr key={pipeline.dataset_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-mono text-gray-700">{pipeline.dataset_id}</td>
                    <td className="px-3 py-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${pipeline.overall_progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{pipeline.overall_progress}%</p>
                    </td>
                    <td className="px-3 py-2">
                      {pipeline.is_ready ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                          ✅ Ready
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                          ⏳ Processing
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {pipeline.is_ready ? (
                        <span className="text-green-600 font-bold">✓</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
