import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface TrainingRound {
  id: number;
  round_number: number;
  target_column: string;
  status: 'planning' | 'in_progress' | 'completed';
  architecture_version: string;
  created_at: string;
  updated_at: string;
}

interface ActiveRoundCardProps {
  onRoundChange?: (round: TrainingRound | null) => void;
  disableTraining?: (disabled: boolean) => void;
}

export interface ActiveRoundCardHandle {
  refetch: () => Promise<void>;
}

/**
 * ActiveRoundCard (Hospital)
 * Displays current active training round information
 * - Fetches /round/active
 * - Shows target column, status, architecture version
 * - Disables training if status != 'in_progress'
 */
export const ActiveRoundCard = React.forwardRef<
  ActiveRoundCardHandle,
  ActiveRoundCardProps
>(({ onRoundChange, disableTraining }, ref) => {
  const [round, setRound] = useState<TrainingRound | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActiveRound = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/rounds/active`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const roundData = response.data;
      setRound(roundData);
      
      // Notify parent of round change
      if (onRoundChange) {
        onRoundChange(roundData);
      }

      // Disable training if round is not in progress
      if (disableTraining) {
        disableTraining(roundData.status !== 'in_progress');
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        // No active round
        setRound(null);
        if (onRoundChange) {
          onRoundChange(null);
        }
        if (disableTraining) {
          disableTraining(true);
        }
      } else {
        setError('Failed to fetch active round');
        console.error('Error fetching active round:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveRound();
    
    // Refetch every 5 seconds to keep in sync
    const interval = setInterval(fetchActiveRound, 5000);
    return () => clearInterval(interval);
  }, []);

  // Public refetch method for parent components
  React.useImperativeHandle(
    ref,
    () => ({
      refetch: fetchActiveRound
    })
  );

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">{error}</p>
      </div>
    );
  }

  if (!round) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm font-medium">⚠️ No Active Training Round</p>
        <p className="text-yellow-700 text-xs mt-1">
          Contact central coordinator to start a new training round
        </p>
      </div>
    );
  }

  const statusColor = {
    planning: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-green-100 text-green-800',
    completed: 'bg-gray-100 text-gray-800'
  }[round.status];

  const statusLabel = {
    planning: '📋 Planning',
    in_progress: '▶️ In Progress',
    completed: '✓ Completed'
  }[round.status];

  return (
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Training Round #{round.round_number}
          </h3>
          <p className="text-sm text-gray-600 mt-1">Active Round Configuration</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
          {statusLabel}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Target Column */}
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Target Column</p>
          <p className="text-lg font-mono text-gray-900 mt-1">
            {round.target_column || 'Not set'}
          </p>
        </div>

        {/* Status */}
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Status</p>
          <p className="text-lg font-semibold text-gray-900 mt-1 capitalize">
            {round.status}
          </p>
        </div>

        {/* Architecture Version */}
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Architecture</p>
          <p className="text-lg font-mono text-gray-900 mt-1">
            {round.architecture_version || 'v1.0'}
          </p>
        </div>
      </div>

      {/* Training Status */}
      <div className="mt-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Training Status:</span>
          {round.status === 'in_progress' ? (
            <span className="flex items-center text-sm text-green-700">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></span>
              Ready to train
            </span>
          ) : (
            <span className="flex items-center text-sm text-red-700">
              <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
              Training disabled ({round.status})
            </span>
          )}
        </div>
      </div>

      {/* Refresh Indicator */}
      <p className="text-xs text-gray-500 mt-3">
        Auto-refreshes every 5 seconds
      </p>
    </div>
  );
});

ActiveRoundCard.displayName = 'ActiveRoundCard';
export default ActiveRoundCard;
