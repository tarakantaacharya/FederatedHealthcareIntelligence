import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import aggregationService from '../services/aggregationService';
import roundService from '../services/roundService';
import weightService from '../services/weightService';
import { RoundDetail, HospitalContribution } from '../types/rounds';
import { formatErrorMessage } from '../utils/errorMessage';

const AggregationRoundDetail: React.FC = () => {
  const navigate = useNavigate();
  const { roundNumber } = useParams();
  const parsedRound = roundNumber ? Number(roundNumber) : NaN;

  const [roundDetail, setRoundDetail] = useState<RoundDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [aggregating, setAggregating] = useState(false);

  const [globalModel, setGlobalModel] = useState<any>(null);
  const [globalModelLoading, setGlobalModelLoading] = useState(false);
  const [globalModelError, setGlobalModelError] = useState('');
  const [eligibleForAggregation, setEligibleForAggregation] = useState(false);
  const [weightsModalOpen, setWeightsModalOpen] = useState(false);
  const [participantWeights, setParticipantWeights] = useState<any>(null);
  const [loadingParticipantWeights, setLoadingParticipantWeights] = useState(false);


  
  const fetchRoundDetail = async () => {
    if (!Number.isFinite(parsedRound)) {
      setError('Invalid round number.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const detail = await roundService.getRoundDetails(parsedRound);
      setRoundDetail(detail);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load round details.');
    } finally {
      setLoading(false);
    }
  };

  const fetchGlobalModel = async () => {
    if (!Number.isFinite(parsedRound)) {
      return;
    }

    setGlobalModelLoading(true);
    setGlobalModelError('');

    try {
      const model = await aggregationService.getGlobalModel(parsedRound);
      setGlobalModel(model);
    } catch (err: any) {
      const statusCode = err?.response?.status;
      if (statusCode === 404) {
        setGlobalModel(null);
      } else {
        setGlobalModelError(err?.response?.data?.detail || 'Failed to load global model.');
      }
    } finally {
      setGlobalModelLoading(false);
    }
  };

  useEffect(() => {
    fetchRoundDetail();
    fetchGlobalModel();
  }, [roundNumber]);

  const dedupedContributions = useMemo(() => {
    if (!roundDetail) {
      return [];
    }

    const latestByHospital = new Map<number, HospitalContribution>();

    roundDetail.hospital_contributions.forEach((contribution) => {
      const existing = latestByHospital.get(contribution.hospital_id);
      if (!existing) {
        latestByHospital.set(contribution.hospital_id, contribution);
        return;
      }

      const existingTime = Date.parse(existing.uploaded_at);
      const nextTime = Date.parse(contribution.uploaded_at);

      if (Number.isNaN(existingTime)) {
        latestByHospital.set(contribution.hospital_id, contribution);
        return;
      }

      if (!Number.isNaN(nextTime) && nextTime > existingTime) {
        latestByHospital.set(contribution.hospital_id, contribution);
      }
    });

    return Array.from(latestByHospital.values()).sort((a, b) => {
      const timeA = Date.parse(a.uploaded_at);
      const timeB = Date.parse(b.uploaded_at);
      return (Number.isNaN(timeB) ? 0 : timeB) - (Number.isNaN(timeA) ? 0 : timeA);
    });
  }, [roundDetail]);

  const avgMetrics = useMemo(() => {
    if (!dedupedContributions.length) {
      return {
        avgAccuracy: null,
        avgMape: null,
        avgRmse: null
      };
    }

    const withAccuracy = dedupedContributions.filter((item) => item.accuracy !== null && item.accuracy !== undefined);
    const withMape = dedupedContributions.filter((item) => item.mape !== null && item.mape !== undefined);
    const withRmse = dedupedContributions.filter((item) => item.rmse !== null && item.rmse !== undefined);

    const avg = (items: number[]) => items.reduce((sum, value) => sum + value, 0) / items.length;

    return {
      avgAccuracy: withAccuracy.length ? avg(withAccuracy.map((item) => item.accuracy as number)) : null,
      avgMape: withMape.length ? avg(withMape.map((item) => item.mape as number)) : null,
      avgRmse: withRmse.length ? avg(withRmse.map((item) => item.rmse as number)) : null
    };
  }, [dedupedContributions]);

  const handleAggregate = async () => {
    if (!roundDetail) {
      return;
    }

    setAggregating(true);
    setError('');
    setSuccess('');

    try {
      const result = await aggregationService.performAggregation({
        round_number: roundDetail.round_number
      });
      setSuccess(result.message || 'Aggregation completed.');
      await fetchRoundDetail();
      await fetchGlobalModel();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Aggregation failed.');
    } finally {
      setAggregating(false);
    }
  };

  const handleViewParticipantWeights = async (hospital: HospitalContribution) => {
    if (!Number.isFinite(parsedRound)) {
      setError('Invalid round number.');
      return;
    }

    setLoadingParticipantWeights(true);
    setError('');
    try {
      const data = await weightService.getCentralHospitalWeights(parsedRound, hospital.hospital_id);
      setParticipantWeights(data);
      setWeightsModalOpen(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load participant weight JSON');
    } finally {
      setLoadingParticipantWeights(false);
    }
  };

  const formatDateTime = (value?: string | null) => {
    if (!value) {
      return 'N/A';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  };

  return (
    <ConsoleLayout title="Aggregation Dashboard" subtitle="Round details">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Round {Number.isFinite(parsedRound) ? parsedRound : 'Details'}
            </h2>
            <p className="text-sm text-gray-600">Latest upload per hospital is shown</p>
          </div>
          <button
            onClick={() => navigate('/aggregation')}
            className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md"
          >
            Back to Dashboard
          </button>
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

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6">Loading round details...</div>
        ) : !roundDetail ? (
          <div className="bg-white rounded-lg shadow p-6">Round not found.</div>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow p-6 mb-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Round Summary</h3>
                <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  roundDetail.status === 'TRAINING' ? 'bg-green-100 text-green-800' :
                  roundDetail.status === 'AGGREGATING' ? 'bg-orange-100 text-orange-800' :
                  roundDetail.status === 'OPEN' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {roundDetail.status}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Target</p>
                  <p className="text-lg font-bold text-gray-900">{roundDetail.target_column || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Participating</p>
                  <p className="text-lg font-bold text-gray-900">{dedupedContributions.length}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Avg Loss</p>
                  <p className="text-lg font-bold text-gray-900">
                    {roundDetail.average_loss !== null && roundDetail.average_loss !== undefined
                      ? aggregationService.formatLoss(roundDetail.average_loss)
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Avg MAPE</p>
                  <p className="text-lg font-bold text-gray-900">
                    {roundDetail?.average_mape !== null && roundDetail?.average_mape !== undefined
                      ? (roundDetail.average_mape as any).toFixed(4)
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Avg RMSE</p>
                  <p className="text-lg font-bold text-gray-900">
                    {roundDetail?.average_rmse !== null && roundDetail?.average_rmse !== undefined
                      ? (roundDetail.average_rmse as any).toFixed(4)
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Avg R²</p>
                  <p className="text-lg font-bold text-gray-900">
                    {roundDetail?.average_r2 !== null && roundDetail?.average_r2 !== undefined
                      ? (roundDetail.average_r2 as any).toFixed(4)
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-xs text-gray-600 uppercase">Round</p>
                  <p className="text-lg font-bold text-gray-900">{roundDetail.round_number}</p>
                </div>
              </div>
              
              {/* Aggregation Strategy Display */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-700">Aggregation Strategy:</p>
                    {(roundDetail.aggregation_strategy || 'fedavg') === 'pfl' ? (
                      <div className="mt-1">
                        <span className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-purple-100 text-purple-800">
                          PFL (Personalized Federated Learning)
                        </span>
                        <p className="mt-2 text-xs text-gray-600">
                          ℹ️ In PFL, only shared backbone parameters are aggregated. Local output head remains private to each hospital.
                        </p>
                      </div>
                    ) : (
                      <div className="mt-1">
                        <span className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-blue-100 text-blue-800">
                          FedAvg (Standard Federated Averaging)
                        </span>
                        <p className="mt-2 text-xs text-gray-600">
                          Full model parameters are aggregated across all hospitals.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Actions</h3>
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      fetchRoundDetail();
                      fetchGlobalModel();
                    }}
                    className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md"
                  >
                    Refresh
                  </button>
                    <button
                      onClick={handleAggregate}
                    disabled={
                      aggregating || 
                      dedupedContributions.length < 2 || 
                      (roundDetail.status !== 'AGGREGATING' && roundDetail.status !== 'TRAINING')
                    }
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {aggregating ? 'Aggregating...' : 'Run FedAvg Aggregation'}
                  </button>
                </div>
              </div>
                <p className="text-sm text-gray-600">
                  Aggregation is enabled when the round status is TRAINING or AGGREGATING, and at least 2 hospitals have uploaded weights.
                </p>
                <p className="text-sm mt-2">
                  <strong>Current Status:</strong> {dedupedContributions.length} hospital(s) participating
                  {dedupedContributions.length < 2 && (
                    <span className="ml-2 text-red-600 font-semibold">
                      (Need {2 - dedupedContributions.length} more)
                    </span>
                  )}
                </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Participating Hospitals</h3>
                <span className="text-xs text-gray-500">Latest upload per hospital</span>
              </div>
              {dedupedContributions.length === 0 ? (
                <div className="text-gray-600">No participation data for this round yet.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Hospital</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Loss</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">MAPE</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">RMSE</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">R²</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Uploaded</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {dedupedContributions.map((hospital) => (
                        <tr key={hospital.hospital_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{hospital.hospital_name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {hospital.loss !== null && hospital.loss !== undefined
                              ? aggregationService.formatLoss(hospital.loss)
                              : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {hospital.mape !== null && hospital.mape !== undefined
                              ? hospital.mape.toFixed(4)
                              : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {hospital.rmse !== null && hospital.rmse !== undefined
                              ? hospital.rmse.toFixed(4)
                              : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {hospital.r2 !== null && hospital.r2 !== undefined
                              ? hospital.r2.toFixed(4)
                              : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {formatDateTime(hospital.uploaded_at)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            <button
                              onClick={() => handleViewParticipantWeights(hospital)}
                              disabled={loadingParticipantWeights}
                              className="bg-slate-700 text-white px-3 py-1 rounded text-xs hover:bg-slate-800 disabled:opacity-50"
                            >
                              {loadingParticipantWeights ? 'Loading...' : 'See Weights'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {weightsModalOpen && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
                  <div className="flex items-center justify-between px-6 py-4 border-b">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Participant Uploaded Weights JSON
                    </h3>
                    <button
                      onClick={() => setWeightsModalOpen(false)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      Close
                    </button>
                  </div>
                  <div className="px-6 py-3 border-b bg-gray-50 text-sm text-gray-700">
                    <span className="font-semibold">Hospital:</span> {participantWeights?.hospital_name || 'N/A'}
                    {' | '}
                    <span className="font-semibold">Code:</span> {participantWeights?.hospital_code || 'N/A'}
                    {' | '}
                    <span className="font-semibold">Round:</span> {participantWeights?.round_number ?? 'N/A'}
                  </div>
                  <div className="p-4 overflow-auto max-h-[70vh] bg-gray-50">
                    <pre className="text-xs text-gray-800 whitespace-pre-wrap break-all">
                      {JSON.stringify(participantWeights?.weights_json || participantWeights || {}, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Global Model</h3>
              {globalModelError && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                  {formatErrorMessage(globalModelError)}
                </div>
              )}
              {globalModelLoading ? (
                <div className="text-gray-600">Loading global model...</div>
              ) : !globalModel ? (
                <div className="text-gray-600">No global model available for this round yet.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Model Type</p>
                    <p className="text-lg font-bold text-gray-900">{globalModel.model_type || 'N/A'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Model Hash</p>
                    <p className="text-sm font-mono text-gray-900 break-all">{globalModel.model_hash || 'N/A'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Created At</p>
                    <p className="text-sm font-semibold text-gray-900">{formatDateTime(globalModel.created_at)}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Model Path</p>
                    <p className="text-xs text-gray-900 break-all">{globalModel.model_path || 'N/A'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Local Loss</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {globalModel.local_loss !== null && globalModel.local_loss !== undefined
                        ? aggregationService.formatLoss(globalModel.local_loss)
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs text-gray-600 uppercase">Local Accuracy</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {globalModel.local_accuracy !== null && globalModel.local_accuracy !== undefined
                        ? aggregationService.formatAccuracy(globalModel.local_accuracy)
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Timeline</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase mb-1">Started</p>
                  <p className="font-semibold text-gray-900">{formatDateTime(roundDetail.started_at)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-600 text-xs uppercase mb-1">Completed</p>
                  <p className="font-semibold text-gray-900">
                    {roundDetail.completed_at ? formatDateTime(roundDetail.completed_at) : '—'}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default AggregationRoundDetail;
