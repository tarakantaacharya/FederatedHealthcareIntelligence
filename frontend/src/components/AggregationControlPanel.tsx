import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

interface AggregationControlPanelProps {
  roundId?: number;
  onAggregationStart?: () => void;
  onAggregationComplete?: (success: boolean, message: string) => void;
}

export interface AggregationControlPanelHandle {
  refetch: () => Promise<void>;
}

interface AggregationStatus {
  round_id: number;
  eligible_hospitals: number;
  total_hospitals: number;
  min_required: number;
  can_aggregate: boolean;
  hospitals_eligible: string[];
  status_message: string;
}

/**
 * AggregationControlPanel (Central)
 * Controls and monitors model aggregation
 * - Shows eligible_count / total
 * - Disables aggregate button if eligible < threshold
 * - Triggers aggregation
 * - Shows progress/status
 */
export const AggregationControlPanel = React.forwardRef<
  AggregationControlPanelHandle,
  AggregationControlPanelProps
>(({ roundId, onAggregationStart, onAggregationComplete }, ref) => {
  const [status, setStatus] = useState<AggregationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aggregating, setAggregating] = useState(false);
  const [aggregationProgress, setAggregationProgress] = useState(0);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchAggregationStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const endpoint = roundId
        ? `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aggregation/status?round_id=${roundId}`
        : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aggregation/status`;

      const response = await axios.get(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      setStatus(response.data);
    } catch (err) {
      setError('Failed to fetch aggregation status');
      console.error('Error fetching aggregation status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAggregationStatus();

    // Refetch every 2 seconds during normal operation
    const interval = setInterval(fetchAggregationStatus, 2000);
    return () => clearInterval(interval);
  }, [roundId]);

  // Public refetch method for parent components
  React.useImperativeHandle(
    ref,
    () => ({
      refetch: fetchAggregationStatus
    })
  );

  const handleStartAggregation = async () => {
    if (!status?.can_aggregate) {
      setError('Cannot start aggregation: Not enough eligible hospitals');
      return;
    }

    try {
      setAggregating(true);
      setAggregationProgress(0);
      
      // Notify parent
      if (onAggregationStart) {
        onAggregationStart();
      }

      // Simulate progress during aggregation
      progressIntervalRef.current = setInterval(() => {
        setAggregationProgress((prev) => Math.min(prev + 10, 90));
      }, 300);

      const token = localStorage.getItem('access_token');
      const endpoint = roundId
        ? `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aggregation/compute?round_id=${roundId}`
        : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aggregation/compute`;

      const response = await axios.post(
        endpoint,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setAggregationProgress(100);

      // Notify parent of success
      if (onAggregationComplete) {
        onAggregationComplete(true, 'Aggregation completed successfully');
      }

      // Refetch status
      setTimeout(() => {
        fetchAggregationStatus();
      }, 1000);
    } catch (err) {
      const errorMessage = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Aggregation failed'
        : 'Aggregation failed';

      setError(errorMessage);

      // Notify parent of failure
      if (onAggregationComplete) {
        onAggregationComplete(false, errorMessage);
      }
    } finally {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
      setAggregating(false);
      setAggregationProgress(0);
    }
  };

  if (loading && !status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">Failed to load aggregation status</p>
      </div>
    );
  }

  const eligibilityPercentage = Math.round(
    (status.eligible_hospitals / status.total_hospitals) * 100
  );

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Aggregation Control Panel</h3>
        <p className="text-sm text-gray-600 mt-1">Round #{status.round_id}</p>
      </div>

      {/* Status Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6 border border-blue-200">
        <div className="flex items-end justify-between mb-4">
          <div>
            <p className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Eligible Hospitals
            </p>
            <p className="text-4xl font-bold text-blue-900 mt-2">
              {status.eligible_hospitals}
              <span className="text-2xl text-gray-600 font-normal">
                /{status.total_hospitals}
              </span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-blue-600">{eligibilityPercentage}%</p>
            <p className="text-xs text-gray-600 mt-1">Participation Rate</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-blue-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${eligibilityPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Eligibility Check */}
      <div className={`rounded-lg p-4 mb-6 ${status.can_aggregate ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        {status.can_aggregate ? (
          <div>
            <p className="text-green-900 font-semibold">
              ✅ Ready for Aggregation
            </p>
            <p className="text-green-800 text-sm mt-1">
              Minimum requirement ({status.min_required} hospitals) met with{' '}
              {status.eligible_hospitals} eligible hospital(s)
            </p>
          </div>
        ) : (
          <div>
            <p className="text-red-900 font-semibold">
              ❌ Not Ready for Aggregation
            </p>
            <p className="text-red-800 text-sm mt-1">
              {status.min_required - status.eligible_hospitals} more hospital(s) needed
              (minimum: {status.min_required})
            </p>
          </div>
        )}
      </div>

      {/* Aggregation Progress */}
      {aggregating && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-semibold text-gray-700">Aggregation in progress...</p>
            <span className="text-sm font-mono text-gray-600">{aggregationProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${aggregationProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-900 text-sm font-medium">Error</p>
          <p className="text-red-800 text-xs mt-1">{error}</p>
        </div>
      )}

      {/* Eligible Hospitals List */}
      {status.hospitals_eligible.length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-semibold text-gray-700 mb-2">Eligible Hospitals:</p>
          <div className="space-y-1">
            {status.hospitals_eligible.map((hospital, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                <span className="font-mono">{hospital}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4 border-t border-gray-200">
        <button
          onClick={handleStartAggregation}
          disabled={!status.can_aggregate || aggregating}
          className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
            status.can_aggregate && !aggregating
              ? 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
              : 'bg-gray-200 text-gray-600 cursor-not-allowed'
          }`}
        >
          {aggregating ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⟳</span> Aggregating...
            </span>
          ) : (
            '▶ Start Aggregation'
          )}
        </button>

        <button
          onClick={() => {
            setError(null);
            fetchAggregationStatus();
          }}
          className="px-4 py-2 rounded-lg font-semibold bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Status Message */}
      <p className="text-xs text-gray-500 mt-4">{status.status_message}</p>
    </div>
  );
});

AggregationControlPanel.displayName = 'AggregationControlPanel';
export default AggregationControlPanel;
