import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface HospitalParticipation {
  hospital_id: string;
  hospital_name?: string;
  has_trained: boolean;
  has_uploaded_weights: boolean;
  has_uploaded_mask: boolean;
  eligible_for_aggregation: boolean;
}

interface ParticipationMatrixData {
  round_number: number;
  round_id: number;
  status: string;
  hospitals: HospitalParticipation[];
  eligible_hospitals: number;
  total_hospitals: number;
  eligible_for_aggregation: boolean;
  min_hospitals_required: number;
}

interface ParticipationMatrixProps {
  roundId?: number;
  onEligibilityChange?: (eligible: boolean, count: number) => void;
}

export interface ParticipationMatrixHandle {
  refetch: () => Promise<void>;
}

/**
 * ParticipationMatrix (Central)
 * Displays participation status of all hospitals
 * - Fetches /round/{id}/participation
 * - Shows table with hospital participation data
 * - Color-coded eligibility status
 * - Auto-refetch after training/weight/mask actions
 */
export const ParticipationMatrix = React.forwardRef<
  ParticipationMatrixHandle,
  ParticipationMatrixProps
>(({ roundId, onEligibilityChange }, ref) => {
  const [data, setData] = useState<ParticipationMatrixData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<string>('');

  const fetchParticipation = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      const endpoint = roundId
        ? `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/rounds/${roundId}/participation`
        : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/rounds/active/participation`;

      const response = await axios.get(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const matrixData = response.data;
      setData(matrixData);
      setLastFetch(new Date().toLocaleTimeString());

      // Notify parent of eligibility change
      if (onEligibilityChange) {
        onEligibilityChange(
          matrixData.eligible_for_aggregation,
          matrixData.eligible_hospitals
        );
      }
    } catch (err) {
      setError('Failed to fetch participation data');
      console.error('Error fetching participation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParticipation();

    // Refetch every 3 seconds for real-time updates
    const interval = setInterval(fetchParticipation, 3000);
    return () => clearInterval(interval);
  }, [roundId]);

  // Public refetch method for parent components
  React.useImperativeHandle(
    ref,
    () => ({
      refetch: fetchParticipation
    })
  );

  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm font-medium">Error Loading Participation</p>
        <p className="text-red-700 text-xs mt-1">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm">No participation data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Hospital Participation Matrix
          </h3>
          <p className="text-sm text-gray-600 mt-1">Round #{data.round_number}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            {data.eligible_hospitals}/{data.total_hospitals}
          </div>
          <p className="text-xs text-gray-600">Eligible for Aggregation</p>
        </div>
      </div>

      {/* Eligibility Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-3 rounded">
          <p className="text-xs font-semibold text-blue-900 uppercase">Total Hospitals</p>
          <p className="text-2xl font-bold text-blue-700">{data.total_hospitals}</p>
        </div>
        <div className="bg-green-50 p-3 rounded">
          <p className="text-xs font-semibold text-green-900 uppercase">Eligible</p>
          <p className="text-2xl font-bold text-green-700">{data.eligible_hospitals}</p>
        </div>
        <div className="bg-orange-50 p-3 rounded">
          <p className="text-xs font-semibold text-orange-900 uppercase">In Progress</p>
          <p className="text-2xl font-bold text-orange-700">
            {data.total_hospitals - data.eligible_hospitals}
          </p>
        </div>
        <div className="bg-purple-50 p-3 rounded">
          <p className="text-xs font-semibold text-purple-900 uppercase">Required Min</p>
          <p className="text-2xl font-bold text-purple-700">{data.min_hospitals_required}</p>
        </div>
      </div>

      {/* Eligibility Status */}
      {data.eligible_for_aggregation ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p className="text-green-900 text-sm font-medium">
            ✅ Minimum hospitals ({data.min_hospitals_required}) reached - Ready for aggregation
          </p>
        </div>
      ) : (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-900 text-sm font-medium">
            ❌ {data.min_hospitals_required - data.eligible_hospitals} more hospitals needed for aggregation
          </p>
        </div>
      )}

      {/* Participation Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Hospital ID</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Trained</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Weights</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Mask</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.hospitals.map((hospital, idx) => (
              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-900">
                  {hospital.hospital_name || hospital.hospital_id}
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-block w-3 h-3 rounded-full ${
                      hospital.has_trained ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    title={hospital.has_trained ? 'Trained' : 'Not trained'}
                  ></span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-block w-3 h-3 rounded-full ${
                      hospital.has_uploaded_weights ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    title={
                      hospital.has_uploaded_weights
                        ? 'Weights uploaded'
                        : 'Weights not uploaded'
                    }
                  ></span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-block w-3 h-3 rounded-full ${
                      hospital.has_uploaded_mask ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    title={
                      hospital.has_uploaded_mask ? 'Mask uploaded' : 'Mask not uploaded'
                    }
                  ></span>
                </td>
                <td className="px-4 py-3 text-center">
                  {hospital.eligible_for_aggregation ? (
                    <span className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                      ✓ Eligible
                    </span>
                  ) : hospital.has_trained ? (
                    <span className="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                      ⚠ Partial
                    </span>
                  ) : (
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-semibold">
                      ○ Pending
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600">
        <p className="font-semibold text-gray-700 mb-2">Status Legend:</p>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500"></span>
            <span>Complete</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-gray-300"></span>
            <span>Pending</span>
          </div>
        </div>
      </div>

      {/* Auto-refresh indicator */}
      <p className="text-xs text-gray-500 mt-4">
        Last updated: {lastFetch || 'Loading...'} (auto-refresh every 3 seconds)
      </p>
    </div>
  );
});

ParticipationMatrix.displayName = 'ParticipationMatrix';
export default ParticipationMatrix;
