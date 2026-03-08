import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import RoundPolicyForm from '../components/RoundPolicyForm';
import adminService, { AdminStats, RoundPolicyRequest, RoundAnalyticsResponse } from '../services/adminService';
import aggregationService from '../services/aggregationService';
import { TrainingRound } from '../types/aggregation';


const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats>({
    totalHospitals: 0,
    approvedHospitals: 0,
    activeRounds: 0,
    pendingApprovals: 0,
    totalAggregations: 0,
    averageGlobalLoss: null,
    participationHeatmap: []
  });
  const [loading, setLoading] = useState(true);
  const [creatingRound, setCreatingRound] = useState(false);
  const [createError, setCreateError] = useState('');
  const [createdRound, setCreatedRound] = useState<any>(null);
  
  // Rounds table
  const [rounds, setRounds] = useState<TrainingRound[]>([]);
  const [roundsLoading, setRoundsLoading] = useState(false);
  const [togglingTraining, setTogglingTraining] = useState<number | null>(null);
  const [toggleError, setToggleError] = useState<string>('');
  const [restarting, setRestarting] = useState<number | null>(null);
  const [deletingRound, setDeletingRound] = useState<number | null>(null);
  const [selectedRoundId, setSelectedRoundId] = useState<number | null>(null);
  const [roundAnalytics, setRoundAnalytics] = useState<RoundAnalyticsResponse | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  useEffect(() => {
    // ProtectedRoute already guards access; just fetch stats
    const fetchStats = async () => {
      try {
        const data = await adminService.getAdminStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
      } finally {
        setLoading(false);
      }
    };

    const fetchRounds = async () => {
      try {
        setRoundsLoading(true);
        const roundsData = await aggregationService.getTrainingRounds();
        setRounds(roundsData);
      } catch (error) {
        console.error('Failed to fetch rounds:', error);
      } finally {
        setRoundsLoading(false);
      }
    };

    fetchStats();
    fetchRounds();
  }, []);

  useEffect(() => {
    if (rounds.length > 0 && selectedRoundId === null) {
      setSelectedRoundId(rounds[0].id);
    }
  }, [rounds, selectedRoundId]);

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!selectedRoundId) {
        setRoundAnalytics(null);
        return;
      }
      try {
        setAnalyticsLoading(true);
        const data = await adminService.getRoundAnalytics(selectedRoundId);
        setRoundAnalytics(data);
      } catch (error) {
        console.error('Failed to fetch round analytics:', error);
        setRoundAnalytics(null);
      } finally {
        setAnalyticsLoading(false);
      }
    };

    fetchAnalytics();
  }, [selectedRoundId]);

  const handleCreateRound = async (policy: RoundPolicyRequest) => {
    setCreateError('');
    setCreatedRound(null);

    setCreatingRound(true);
    try {
      const result = await adminService.createRound(policy);
      setCreatedRound(result);
      // Refresh rounds list
      const roundsData = await aggregationService.getTrainingRounds();
      setRounds(roundsData);
    } catch (error: any) {
      setCreateError(error?.response?.data?.detail || 'Failed to create round');
    } finally {
      setCreatingRound(false);
    }
  };

  const handleToggleTraining = async (roundNumber: number, currentStatus: boolean) => {
    setTogglingTraining(roundNumber);
    setToggleError('');
    try {
      if (currentStatus) {
        await adminService.disableTraining(roundNumber);
      } else {
        await adminService.enableTraining(roundNumber);
      }
      // Refresh rounds list
      const roundsData = await aggregationService.getTrainingRounds();
      setRounds(roundsData);
    } catch (error: any) {
      console.error('Failed to toggle training:', error);
      const errorMsg = error?.response?.data?.detail || 'Failed to toggle training';
      setToggleError(errorMsg);
    } finally {
      setTogglingTraining(null);
    }
  };

  const handleRestartRound = async (roundNumber: number) => {
    setRestarting(roundNumber);
    setToggleError('');
    try {
      await adminService.restartRound(roundNumber);
      // Refresh rounds list
      const roundsData = await aggregationService.getTrainingRounds();
      setRounds(roundsData);
    } catch (error: any) {
      console.error('Failed to restart round:', error);
      const errorMsg = error?.response?.data?.detail || 'Failed to restart round';
      setToggleError(errorMsg);
    } finally {
      setRestarting(null);
    }
  };

  const handleDeleteRound = async (roundNumber: number, status: string) => {
    if (status === 'TRAINING' || status === 'AGGREGATING') {
      setToggleError(`Cannot delete Round ${roundNumber} while it is ${status}.`);
      return;
    }

    const confirmed = window.confirm(
      `Delete Round ${roundNumber}? This removes round data, weights, and masks from the central server.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingRound(roundNumber);
    setToggleError('');
    try {
      await adminService.deleteRound(roundNumber);
      const roundsData = await aggregationService.getTrainingRounds();
      setRounds(roundsData);
    } catch (error: any) {
      console.error('Failed to delete round:', error);
      const errorMsg = error?.response?.data?.detail || 'Failed to delete round';
      setToggleError(errorMsg);
    } finally {
      setDeletingRound(null);
    }
  };


  return (
    <ConsoleLayout title="System Administrator" subtitle="Central Control Center">
      <div className="max-w-7xl mx-auto">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Total Hospitals</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalHospitals}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-2xl">🏥</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Verified Hospitals</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.approvedHospitals}</p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-lg">
                <span className="text-emerald-600 text-2xl">✅</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Pending Approvals</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.pendingApprovals}</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-2xl">⏳</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Active Rounds</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.activeRounds}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <span className="text-green-600 text-2xl">🔄</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Total Aggregations</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalAggregations}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-2xl">📊</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Average Global Loss</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.averageGlobalLoss !== null && stats.averageGlobalLoss !== undefined
                    ? stats.averageGlobalLoss.toFixed(4)
                    : 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-indigo-100 rounded-lg">
                <span className="text-indigo-600 text-2xl">📉</span>
              </div>
            </div>
          </div>
        </div>

        {/* Participation Heatmap */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Participation Heatmap</h2>
          {stats.participationHeatmap && stats.participationHeatmap.length > 0 ? (
            <div className="space-y-3">
              {stats.participationHeatmap.map((row) => (
                <div key={row.round_number} className="flex items-center gap-4">
                  <div className="w-20 text-sm text-gray-600">Round {row.round_number}</div>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full"
                      style={{ width: `${Math.min(100, row.participants * 10)}%` }}
                    />
                  </div>
                  <div className="w-24 text-sm text-gray-600 text-right">{row.participants} hospitals</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No participation data available.</p>
          )}
        </div>

        {/* Round Analytics */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Round Analytics</h2>
          <div className="flex flex-col md:flex-row md:items-center gap-4 mb-4">
            <label className="text-sm text-gray-600">Select Round</label>
            <select
              value={selectedRoundId ?? ''}
              onChange={(e) => setSelectedRoundId(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              {rounds.map((round) => (
                <option key={round.id} value={round.id}>
                  Round {round.round_number}
                </option>
              ))}
            </select>
          </div>

          {analyticsLoading ? (
            <p className="text-sm text-gray-600">Loading analytics...</p>
          ) : !roundAnalytics ? (
            <p className="text-sm text-gray-600">No analytics available.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs text-gray-600 mb-1">Contributing Hospitals</p>
                <p className="text-lg font-semibold text-gray-900">{roundAnalytics.num_hospitals}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs text-gray-600 mb-1">Avg Loss</p>
                <p className="text-sm text-gray-900">
                  {roundAnalytics.avg_loss !== null ? roundAnalytics.avg_loss.toFixed(4) : 'N/A'}
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-xs text-gray-600 mb-1">Std Dev (Loss)</p>
                <p className="text-sm text-gray-900">
                  {roundAnalytics.std_loss !== null ? roundAnalytics.std_loss.toFixed(4) : 'N/A'}
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg md:col-span-3">
                <p className="text-xs text-gray-600 mb-2">Contributing Regions</p>
                <div className="flex flex-wrap gap-2">
                  {roundAnalytics.contributing_regions.length > 0 ? (
                    roundAnalytics.contributing_regions.map((region) => (
                      <span key={region.region} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {region.region} ({region.count})
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-500">No regions reported</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Federated Round</h2>
          <RoundPolicyForm
            onSubmit={handleCreateRound}
            loading={creatingRound}
            error={createError}
          />

          {createdRound && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-900 mb-2">✓ Round Created Successfully</p>
              <p className="text-sm text-green-700">Round Number: <span className="font-mono font-bold">#{createdRound.round_number}</span></p>
              <p className="text-sm text-green-700">Target Column: <span className="font-mono">{createdRound.target_column}</span></p>
              <p className="text-sm text-green-700">Status: <span className="font-mono">{createdRound.status}</span></p>
              {createdRound.is_emergency && (
                <p className="text-sm text-green-700 mt-2">🚨 Emergency Round: All verified hospitals included</p>
              )}
              {createdRound.selection_criteria && (
                <p className="text-sm text-green-700 mt-2">
                  Selection: {createdRound.selection_criteria} {createdRound.selection_criteria === 'MANUAL' ? '' : `= ${createdRound.selection_value}`}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {toggleError && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <p className="font-semibold">Error</p>
            <p className="text-sm">{toggleError}</p>
          </div>
        )}

        {/* Training Rounds Table */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Training Rounds Status</h3>
            {rounds.some(r => r.status === 'TRAINING') && (
              <p className="text-sm text-blue-600 mt-1">
                🔄 Currently Running: Round {rounds.find(r => r.status === 'TRAINING')?.round_number}
              </p>
            )}
          </div>

          {roundsLoading ? (
            <div className="p-6 text-center text-gray-600">Loading rounds...</div>
          ) : rounds.length === 0 ? (
            <div className="p-6 text-center text-gray-600">No training rounds yet</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Round #</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Policy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hospitals</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target Column</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aggregation</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created At</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {rounds.map((round) => {
                    const isTraining = round.status === 'TRAINING';
                    const isClosed = round.status === 'CLOSED';
                    const isAggregating = round.status === 'AGGREGATING';
                    const activeTrainingRound = rounds.find(r => r.status === 'TRAINING');
                    const canEnable = !isTraining && (!activeTrainingRound || activeTrainingRound.round_number === round.round_number);
                    const canDelete = !isTraining && !isAggregating;
                    
                    return (
                      <tr key={round.id} className={isTraining ? 'bg-blue-50' : ''}>
                        <td className="px-6 py-4 text-sm font-medium">
                          {round.round_number}
                          {isTraining && <span className="ml-2 text-blue-600 font-bold">● ACTIVE</span>}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              round.status === 'CLOSED'
                                ? 'bg-gray-100 text-gray-800'
                                : round.status === 'TRAINING'
                                ? 'bg-blue-100 text-blue-800'
                                : round.status === 'AGGREGATING'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {round.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm font-semibold text-purple-700">
                          {round.model_type || 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <div className="text-xs">
                            <div className="font-medium text-gray-700">{round.participation_policy || 'ALL'}</div>
                            {round.selection_criteria && (
                              <div className="text-gray-500">
                                {round.selection_criteria}
                                {round.selection_value && ` (${round.selection_value})`}
                                {round.is_emergency && <span className="ml-1 text-red-600 font-bold">🔴 EMERGENCY</span>}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm max-w-md">
                          {round.hospital_names && round.hospital_names.length > 0 ? (
                            <div className="space-y-1">
                              {round.hospital_names.map((name, idx) => (
                                <div key={idx} className="inline-block bg-blue-100 text-blue-700 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap mr-2 mb-1">
                                  {name}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-500 italic">No hospitals</span>
                          )}
                          <div className="text-xs text-gray-500 mt-1">
                            Total: {round.hospital_names?.length || 0} hospitals
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm">{round.target_column || 'N/A'}</td>
                        <td className="px-6 py-4 text-sm">
                          <div className="inline-flex items-center" title={(round.aggregation_strategy || 'fedavg') === 'pfl' ? 'Personalized FL — Backbone shared, local head private' : 'Standard FL — Full model aggregation'}>
                            <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                              (round.aggregation_strategy || 'fedavg') === 'pfl'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {(round.aggregation_strategy || 'fedavg') === 'pfl' ? 'PFL' : 'FedAvg'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm space-x-2">
                          {isTraining ? (
                            <button
                              onClick={() => handleToggleTraining(round.round_number, true)}
                              disabled={togglingTraining === round.round_number}
                              className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 inline-block"
                            >
                              {togglingTraining === round.round_number ? '...' : '⏹️ Stop'}
                            </button>
                          ) : (
                            <>
                              <button
                                onClick={() => handleToggleTraining(round.round_number, false)}
                                disabled={togglingTraining === round.round_number || !canEnable}
                                title={!canEnable ? 'Another round is currently training' : 'Start training'}
                                className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed inline-block"
                              >
                                {togglingTraining === round.round_number ? '...' : '▶️ Start'}
                              </button>
                              {isClosed && (
                                <button
                                  onClick={() => handleRestartRound(round.round_number)}
                                  disabled={restarting === round.round_number}
                                  className="px-3 py-1 bg-indigo-600 text-white text-xs rounded hover:bg-indigo-700 disabled:opacity-50 inline-block"
                                >
                                  {restarting === round.round_number ? '...' : '🔄 Restart'}
                                </button>
                              )}
                            </>
                          )}
                          <button
                            onClick={() => handleDeleteRound(round.round_number, round.status)}
                            disabled={deletingRound === round.round_number || !canDelete}
                            title={!canDelete ? 'Cannot delete while training or aggregating' : 'Delete round'}
                            className="px-3 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed inline-block"
                          >
                            {deletingRound === round.round_number ? '...' : '🗑️ Delete'}
                          </button>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {round.started_at ? new Date(round.started_at).toLocaleString() : 'Not started'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Admin Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Model Governance */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Governance</h2>
            <p className="text-gray-600 text-sm mb-4">
              Review, approve, or reject federated learning models. Manage model versions and cryptographic signing.
            </p>
            <button
              onClick={() => navigate('/governance')}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
            >
              Manage Models
            </button>
          </div>

          {/* Federated Aggregation */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Federated Aggregation</h2>
            <p className="text-gray-600 text-sm mb-4">
              Trigger FedAvg aggregation, manage training rounds, and coordinate weight collection across hospitals.
            </p>
            <button
              onClick={() => navigate('/aggregation')}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-md shadow hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-400 transition"
            >
              Run Aggregation
            </button>
          </div>

          {/* Hospital Management */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Hospital Management</h2>
            <p className="text-gray-600 text-sm mb-4">
              View all registered hospitals, verify accounts, manage permissions, and monitor activities.
            </p>
            <button
                onClick={() => navigate('/hospitals-manage')}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md shadow hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
            >
              View Hospitals
            </button>
          </div>

          {/* System Monitoring */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Monitoring</h2>
            <p className="text-gray-600 text-sm mb-4">
              Monitor system health, view audit logs, track all communications, and ensure compliance.
            </p>
            <button
              onClick={() => navigate('/monitoring')}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-md shadow hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-400 transition"
            >
              View Logs
            </button>
          </div>
        </div>

        {/* Communication Section */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Communication Hub</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-600 cursor-pointer">
              <h3 className="font-semibold text-gray-900">Broadcast Announcements</h3>
              <p className="text-sm text-gray-600 mt-1">Send system-wide messages to all hospitals</p>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-600 cursor-pointer">
              <h3 className="font-semibold text-gray-900">Hospital Notifications</h3>
              <p className="text-sm text-gray-600 mt-1">Send targeted notifications to specific hospitals</p>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-600 cursor-pointer">
              <h3 className="font-semibold text-gray-900">Message Center</h3>
              <p className="text-sm text-gray-600 mt-1">View all historical communications and status</p>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="mt-8 bg-green-50 border border-green-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-2">✅ System Status: Operational</h3>
          <p className="text-green-700 text-sm">
            All services are running. Last sync: Just now | Database: Connected | API: Responsive
          </p>
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default AdminDashboard;
