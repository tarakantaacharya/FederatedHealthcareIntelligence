import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * Data Pipeline Status Panel
 * 
 * Shows dataset readiness status using quality metrics from preprocessing.
 */

interface DQMetrics {
  rows: number;
  columns: number;
  has_issues: boolean;
  missing_values: { [key: string]: number };
  duplicates: {
    count: number;
    percentage: number;
  };
}

interface PipelinePanelProps {
  datasetId: number;
  onReadinessChange?: (ready: boolean) => void;
}

export const PipelinePanel: React.FC<PipelinePanelProps> = ({ 
  datasetId,
  onReadinessChange
}) => {
  const [metrics, setMetrics] = useState<DQMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchValidationStatus();
  }, [datasetId]);

  const fetchValidationStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `http://localhost:8000/api/preprocessing/${datasetId}/quality-report`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMetrics(response.data);
      onReadinessChange?.(!response.data.has_issues);
      setError('');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to load pipeline status';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateDataset = async () => {
    try {
      setValidating(true);
      setError('');
      // Fetch fresh validation metrics
      await fetchValidationStatus();
    } catch (err: any) {
      setError('Validation failed');
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading pipeline status...</div>;
  }

  if (error) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700">
        <p className="font-semibold">⚠️ Status Unavailable</p>
        <p className="text-sm mt-1">{error}</p>
      </div>
    );
  }

  if (!metrics || metrics.rows === undefined || metrics.columns === undefined) {
    return <div className="text-gray-500 text-center py-8">No validation data available</div>;
  }

  const totalMissing = Object.values(metrics.missing_values || {}).reduce((a: number, b: number) => a + b, 0);

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className={`p-4 rounded-lg border ${
        !metrics.has_issues
          ? 'bg-green-50 border-green-200'
          : 'bg-yellow-50 border-yellow-200'
      }`}>
        <p className={`font-semibold text-sm mb-1 ${
          !metrics.has_issues ? 'text-green-900' : 'text-yellow-900'
        }`}>
          {!metrics.has_issues ? '✓ Dataset Quality Clean' : '⚠️ Quality Issues Detected'}
        </p>
        <p className={`text-xs ${
          !metrics.has_issues ? 'text-green-700' : 'text-yellow-700'
        }`}>
          The dataset is {!metrics.has_issues ? '' : 'not '}suitable for federated training
        </p>
      </div>

      {/* Quality Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-xs text-gray-600">Total Rows</p>
          <p className="text-lg font-bold text-blue-900">{(metrics.rows || 0).toLocaleString()}</p>
        </div>
        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-xs text-gray-600">Total Columns</p>
          <p className="text-lg font-bold text-blue-900">{metrics.columns || 0}</p>
        </div>

        <div className={`p-3 rounded border ${
          totalMissing === 0
            ? 'bg-green-50 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <p className="text-xs text-gray-600">Missing Values</p>
          <p className={`text-lg font-bold ${
            totalMissing === 0
              ? 'text-green-700'
              : 'text-yellow-700'
          }`}>
            {totalMissing}
          </p>
        </div>

        <div className={`p-3 rounded border ${
          (metrics.duplicates?.percentage ?? 0) < 5
            ? 'bg-green-50 border-green-200'
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <p className="text-xs text-gray-600">Duplicates</p>
          <p className={`text-lg font-bold ${
            (metrics.duplicates?.percentage ?? 0) < 5
              ? 'text-green-700'
              : 'text-yellow-700'
          }`}>
            {((metrics.duplicates?.percentage ?? 0).toFixed(1))}%
          </p>
        </div>
      </div>

      {/* Quality Issues Breakdown */}
      {metrics.has_issues && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="font-semibold text-sm text-yellow-900 mb-2">Issues to Address:</p>
          <ul className="space-y-1 text-xs text-yellow-800">
            {Object.keys(metrics.missing_values || {}).length > 0 && (
              <li>• {Object.keys(metrics.missing_values).length} columns have missing values ({totalMissing} total)</li>
            )}
            {(metrics.duplicates?.count ?? 0) > 0 && (
              <li>• {metrics.duplicates?.count} duplicate rows ({((metrics.duplicates?.percentage ?? 0).toFixed(1))}%)</li>
            )}
          </ul>
        </div>
      )}

      {/* Recommendation */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded">
        <p className="text-xs font-semibold text-blue-900 mb-2">💡 Recommendation:</p>
        <p className="text-xs text-blue-800">
          {!metrics.has_issues
            ? 'This dataset is ready for federated training. You can proceed to use it for model training.'
            : 'Use the Data Preprocessing tab to clean missing values and remove duplicates before training.'}
        </p>
      </div>

      {/* Refresh Button */}
      <button
        onClick={handleValidateDataset}
        disabled={validating || loading}
        className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
      >
        {validating ? (
          <>
            <span className="inline-block animate-spin">⏳</span>
            Refreshing Status...
          </>
        ) : (
          <>
            <span>🔄</span>
            Refresh Pipeline Status
          </>
        )}
      </button>
    </div>
  );
};
