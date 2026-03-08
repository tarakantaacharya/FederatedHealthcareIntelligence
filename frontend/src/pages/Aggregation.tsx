import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import aggregationService from '../services/aggregationService';
import roundService from '../services/roundService';
import { TrainingRound, AggregationResponse } from '../types/aggregation';
import { formatErrorMessage } from '../utils/errorMessage';

const Aggregation: React.FC = () => {
  const navigate = useNavigate();
  const [rounds, setRounds] = useState<TrainingRound[]>([]);
  const [activeRound, setActiveRound] = useState<TrainingRound | null>(null);
  const [aggregating, setAggregating] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [aggResult, setAggResult] = useState<AggregationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Round Creation State
  const [creatingRound, setCreatingRound] = useState(false);
  const [createRoundMessage, setCreateRoundMessage] = useState<string>('');
  const [createRoundError, setCreateRoundError] = useState<string>('');
  const [selectedTargetColumn, setSelectedTargetColumn] = useState<string>('');
  const [createdRound, setCreatedRound] = useState<{ round_number: number; target_column: string } | null>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchActiveRound();
    fetchRounds();
  }, [navigate]);

  const fetchActiveRound = async () => {
    try {
      const activeResponse = await roundService.getActiveRound();
      const activeData = activeResponse.data;
      setActiveRound(activeData as TrainingRound);
    } catch (error) {
      console.error('Failed to fetch active round:', error);
      setActiveRound(null);
    }
  };

  const fetchRounds = async () => {
    try {
      const data = await aggregationService.getTrainingRounds();
      setRounds(data);
    } catch (error) {
      console.error('Failed to fetch rounds:', error);
    } finally {
      setLoading(false);
    }
  };

  const allowedTargets = [
    'bed_occupancy',
    'icu_admissions',
    'er_visits',
    'avg_length_of_stay',
    'icu_ventilator_usage',
    'readmission_rate',
    'mortality_rate',
    'staff_utilization',
    'surgery_volume',
    'infection_rate',
    'ambulance_arrivals',
    'outpatient_volume',
    'lab_test_volume',
    'pharmacy_dispense_rate',
    'critical_case_ratio'
  ];

  const handleAggregate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!activeRound) {
      setError('No active round available.');
      return;
    }

    setAggregating(true);
    setError('');
    setSuccess('');
    setAggResult(null);

    try {
      const result = await aggregationService.performAggregation({
        round_number: activeRound.round_number
      });

      setSuccess(result.message);
      setAggResult(result);
      fetchRounds();
      fetchActiveRound();
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        'Aggregation failed. Ensure at least 2 hospitals have uploaded weights.';
      setError(errorMessage);
    } finally {
      setAggregating(false);
    }
  };

  const handleCreateRound = async (e: React.FormEvent) => {
    e.preventDefault();

    setCreatingRound(true);
    setCreateRoundMessage('');
    setCreateRoundError('');
    setCreatedRound(null);

    if (!selectedTargetColumn) {
      setCreateRoundError('Target column is mandatory.');
      setCreatingRound(false);
      return;
    }

    try {
      const result = await aggregationService.createRound(selectedTargetColumn);
      setCreateRoundMessage(result.message);
      setCreatedRound({
        round_number: result.round_number,
        target_column: result.target_column
      });
      fetchRounds();
      fetchActiveRound();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create round.';
      setCreateRoundError(errorMessage);
    } finally {
      setCreatingRound(false);
    }
  };

  const handleStartRound = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!activeRound) {
      setError('No active round available.');
      return;
    }

    setAggregating(true);
    setError('');
    setSuccess('');

    try {
      const result = await aggregationService.startRound(activeRound.round_number);
      setSuccess(`Round ${activeRound.round_number} started successfully.`);
      fetchRounds();
      fetchActiveRound();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to start round.';
      setError(errorMessage);
    } finally {
      setAggregating(false);
    }
  };

  const handleClearAllRounds = async () => {
    const confirmed = window.confirm(
      '⚠️ WARNING: This will delete ALL federated rounds, weights, and governance records.\n\nThis action cannot be undone. Continue?'
    );

    if (!confirmed) return;

    setClearing(true);
    setError('');
    setSuccess('');

    try {
      const result = await aggregationService.clearAllRounds();
      setSuccess(`✅ ${result.message}\nDeleted: ${result.deleted.rounds} rounds, ${result.deleted.weights} weights, ${result.deleted.governance_records} governance records`);
      fetchRounds();
      fetchActiveRound();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to clear rounds.';
      setError(errorMessage);
    } finally {
      setClearing(false);
    }
  };

  return (
    <ConsoleLayout title="Federated Aggregation" subtitle="FedAvg orchestration">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Federated Aggregation (FedAvg)
        </h2>

        {/* Active Round Status Card */}
        <div className="bg-white rounded-lg shadow p-6 mb-6 border-l-4 border-blue-500">
          <h3 className="text-lg font-semibold mb-4">Active Round</h3>

          {!activeRound ? (
            <div className="bg-gray-50 border border-gray-200 rounded p-4 text-gray-600">
              No active round configured.
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600 mb-1">Round Number</p>
                <p className="text-2xl font-bold text-gray-900">{activeRound.round_number}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600 mb-1">Status</p>
                <p className={`text-2xl font-bold ${
                  activeRound.status === 'TRAINING' ? 'text-green-600' :
                  activeRound.status === 'AGGREGATING' ? 'text-orange-600' :
                  activeRound.status === 'OPEN' ? 'text-yellow-600' :
                  activeRound.status === 'CLOSED' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {activeRound.status}
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm text-gray-600 mb-1">Target Column</p>
                <p className="text-lg font-semibold text-gray-900">
                  {activeRound.target_column || 'N/A'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Aggregation Form - Only show if active round exists */}
        {activeRound && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Perform Masked FedAvg Aggregation</h3>

            <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Minimum 2 hospitals required for aggregation. Round must be in TRAINING or AGGREGATING state.
              </p>
              {activeRound && (
                <p className="text-sm text-blue-800 mt-2">
                  <strong>Current Status:</strong> {activeRound.num_participating_hospitals || 0} hospital(s) participating
                  {activeRound.num_participating_hospitals < 2 && (
                    <span className="ml-2 text-red-600 font-semibold">
                      (Need {2 - (activeRound.num_participating_hospitals || 0)} more)
                    </span>
                  )}
                </p>
              )}
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {formatErrorMessage(error)}
              </div>
            )}

            {success && (
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                {success}
              </div>
            )}

            <form onSubmit={handleAggregate} className="space-y-6">
              <button
                type="submit"
                disabled={
                  aggregating ||
                  (activeRound.num_participating_hospitals || 0) < 2 ||
                  (activeRound.status !== 'AGGREGATING' && activeRound.status !== 'TRAINING')
                }
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {aggregating ? 'Aggregating...' : 'Run FedAvg Aggregation'}
              </button>
            </form>

            {/* Aggregation Results */}
            {aggResult && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-semibold mb-3">Aggregation Results</h4>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Round Number</p>
                    <p className="text-lg font-bold">{aggResult.round_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Hospitals</p>
                    <p className="text-lg font-bold">{aggResult.num_hospitals}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Avg Loss</p>
                    <p className="text-lg font-bold">
                      {aggregationService.formatLoss(aggResult.avg_loss)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Avg MAPE</p>
                    <p className="text-lg font-bold">
                      {aggResult.avg_mape !== null && aggResult.avg_mape !== undefined
                        ? (aggResult.avg_mape as any).toFixed(4)
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Avg RMSE</p>
                    <p className="text-lg font-bold">
                      {aggResult.avg_rmse !== null && aggResult.avg_rmse !== undefined
                        ? (aggResult.avg_rmse as any).toFixed(4)
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Model Hash</p>
                    <p className="text-xs font-mono break-all">{aggResult.model_hash || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Block Hash</p>
                    <p className="text-xs font-mono break-all">{aggResult.blockchain_tx || 'N/A'}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Start Round Section - Only show if status is OPEN */}
        {activeRound && activeRound.status === 'OPEN' && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Enable Round</h3>

            <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
              <p className="text-sm text-blue-800">
                <strong>Admin Only:</strong> Enable round to allow hospitals to begin training.
              </p>
            </div>

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {formatErrorMessage(error)}
              </div>
            )}

            <form onSubmit={handleStartRound} className="space-y-4">
              <button
                type="submit"
                disabled={aggregating}
                className="bg-orange-600 text-white px-6 py-2 rounded-md hover:bg-orange-700 disabled:opacity-50"
              >
                {aggregating ? 'Enabling Round...' : 'Enable Round'}
              </button>
            </form>
          </div>
        )}

        {/* Rounds List */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Federated Rounds Overview</h3>
                <p className="text-sm text-gray-600 mt-1">Select a round to view details</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => fetchRounds()}
                  className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md hover:bg-gray-50"
                >
                  Refresh
                </button>
                <button
                  onClick={handleClearAllRounds}
                  disabled={clearing || rounds.length === 0}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold"
                >
                  {clearing ? 'Clearing...' : 'Clear All'}
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-600">Loading rounds...</div>
          ) : rounds.length === 0 ? (
            <div className="p-6 text-center text-gray-600">
              No aggregation rounds yet.
            </div>
          ) : (
            <div className="divide-y">
              {rounds.map((round) => {
                const statusBadgeColor = {
                  'CLOSED': 'bg-red-100 text-red-800',
                  'AGGREGATING': 'bg-orange-100 text-orange-800',
                  'TRAINING': 'bg-green-100 text-green-800',
                  'OPEN': 'bg-yellow-100 text-yellow-800'
                }[round.status] || 'bg-gray-100 text-gray-800';

                return (
                  <div key={round.id} className="px-6 py-4 flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-center min-w-max">
                        <p className="text-xs text-gray-600 uppercase">Round</p>
                        <p className="text-2xl font-bold text-gray-900">{round.round_number}</p>
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${statusBadgeColor}`}>
                            {round.status}
                          </span>
                          <span 
                            className={`px-3 py-1 text-xs font-semibold rounded-full ${
                              (round.aggregation_strategy || 'fedavg') === 'pfl'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                            title={(round.aggregation_strategy || 'fedavg') === 'pfl' ? 'Personalized FL — Backbone shared, local head private' : 'Standard FL — Full model aggregation'}
                          >
                            {(round.aggregation_strategy || 'fedavg') === 'pfl' ? 'PFL' : 'FedAvg'}
                          </span>
                          {activeRound?.round_number === round.round_number && (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              Current
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">
                          Target: <span className="font-semibold text-gray-900">{round.target_column || 'N/A'}</span>
                        </p>
                        <p className="text-sm text-gray-600">
                          Hospitals: <span className="font-semibold text-gray-900">{round.num_participating_hospitals}</span>
                          {' • '}Avg Loss: <span className="font-semibold text-gray-900">
                            {round.average_loss ? aggregationService.formatLoss(round.average_loss) : 'N/A'}
                          </span>
                          {' • '}Started: <span className="font-semibold text-gray-900">
                            {round.started_at ? new Date(round.started_at).toLocaleDateString() : 'Not started'}
                          </span>
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/aggregation/round/${round.round_number}`)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                    >
                      View Details
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Create Round Section - Moved to bottom */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Round</h3>

          <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
            <p className="text-sm text-blue-800">
              <strong>Admin Only:</strong> Create a new training round to initiate federated learning.
            </p>
          </div>

          {createRoundError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {formatErrorMessage(createRoundError)}
            </div>
          )}

          {createRoundMessage && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
              {createRoundMessage}
            </div>
          )}

          {createdRound && (
            <div className="bg-gray-50 border border-gray-200 text-gray-700 px-4 py-3 rounded mb-4">
              <p>Round number: {createdRound.round_number}</p>
              <p>Target column: {createdRound.target_column}</p>
            </div>
          )}

          <form onSubmit={handleCreateRound} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Column
              </label>
              <select
                value={selectedTargetColumn}
                onChange={(e) => setSelectedTargetColumn(e.target.value)}
                className="block w-full md:w-64 px-3 py-2 border rounded-md border-gray-300"
                disabled={creatingRound}
              >
                <option value="">Select a column...</option>
                {allowedTargets.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={creatingRound || !selectedTargetColumn}
              className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {creatingRound ? 'Creating Round...' : 'Create Round'}
            </button>
          </form>
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default Aggregation;
