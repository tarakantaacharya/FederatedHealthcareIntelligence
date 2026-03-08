import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ConsoleLayout from '../components/ConsoleLayout';
import ClearModelsModal from '../components/ClearModelsModal';
import authService from "../services/authService";
import roundService from "../services/roundService";
import aggregationService from "../services/aggregationService";
import modelUpdateService from "../services/modelUpdateService";
import blockchainService, { BlockchainLogEntry } from "../services/blockchainService";
import datasetService from "../services/datasetService";
import trainingService from "../services/trainingService";
import predictionService from "../services/predictionService";
import modelClearingService from "../services/modelClearingService";
import { useAuth } from "../context/AuthContext";
import { TrainingRound } from "../types/aggregation";
import { GlobalModel } from "../types/modelUpdates";
import { Dataset } from "../types/dataset";
import { TrainedModel } from "../types/training";
import { PredictionHistoryItem } from "../types/predictions";

interface EligibilityStatus {
  is_eligible: boolean;
  reason: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [currentRound, setCurrentRound] = useState<TrainingRound | null>(null);
  const [eligibilityStatus, setEligibilityStatus] = useState<EligibilityStatus | null>(null);
  const [checkingEligibility, setCheckingEligibility] = useState(false);
  const [latestGlobalModel, setLatestGlobalModel] = useState<GlobalModel | null>(null);
  const [lastBlock, setLastBlock] = useState<BlockchainLogEntry | null>(null);
  const [chainValid, setChainValid] = useState<boolean | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<TrainedModel[]>([]);
  const [globalModels, setGlobalModels] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<PredictionHistoryItem[]>([]);
  const [hospitalChain, setHospitalChain] = useState<BlockchainLogEntry[]>([]);
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearingModels, setClearingModels] = useState(false);
  const [clearMessage, setClearMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate("/login");
      return;
    }

    const fetchOverview = async () => {
      try {
        const round = await roundService.getCurrentRound().catch(() => null);
        setCurrentRound(round);

        if (user?.role === 'HOSPITAL') {
          const [datasetsData, modelsData, globalModelsData, predictionHistory, chain] = await Promise.all([
            datasetService.getDatasets().catch(() => []),
            trainingService.getModels().catch(() => []),
            modelUpdateService.getAvailableModels().catch(() => []),
            predictionService.getPredictionHistory(10).catch(() => ({ items: [] })),
            blockchainService.getHospitalChain(0, 20).catch(() => ({ logs: [], is_valid: null }))
          ]);

          setDatasets(datasetsData);
          setModels(modelsData);
          setGlobalModels(globalModelsData.filter((m: any) => m.is_global === true));
          setPredictions(predictionHistory.items || []);
          setChainValid(chain.is_valid ?? null);
          setHospitalChain(chain.logs || []);
          if (chain.logs && chain.logs.length > 0) {
            setLastBlock(chain.logs[chain.logs.length - 1]);
          }

          if (round && round.id) {
            setCheckingEligibility(true);
            try {
              const eligibility = await roundService.checkRoundEligibility(round.id);
              setEligibilityStatus(eligibility);
            } catch (error) {
              console.error('Failed to check eligibility:', error);
              setEligibilityStatus({ is_eligible: false, reason: "Unable to determine eligibility" });
            } finally {
              setCheckingEligibility(false);
            }
          }
        }

        if (user?.role === 'ADMIN') {
          const [logs, latest] = await Promise.all([
            blockchainService.getAdminChain(0, 100).catch(() => ({ logs: [], is_valid: null })),
            aggregationService.getLatestGlobalModel().catch(() => null)
          ]);

          setChainValid(logs.is_valid ?? null);
          if (logs.logs && logs.logs.length > 0) {
            setLastBlock(logs.logs[logs.logs.length - 1]);
          }

          if (latest) {
            setLatestGlobalModel({
              id: latest.id,
              round_number: latest.round_number,
              model_type: latest.model_type,
              accuracy: latest.local_accuracy ?? null,
              loss: latest.local_loss ?? null,
              created_at: latest.created_at
            });
          }
        }
      } catch (error) {
        console.error('Failed to load overview:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, [navigate, user?.role]);

  const handleClearLocalModels = async (deleteFiles: boolean) => {
    setClearingModels(true);
    try {
      await modelClearingService.clearLocalModels(deleteFiles);
      setClearMessage({ type: 'success', text: 'Local models cleared successfully' });
      setModels([]);
      setTimeout(() => setClearMessage(null), 5000);
    } catch (error) {
      setClearMessage({ type: 'error', text: 'Failed to clear local models' });
      setTimeout(() => setClearMessage(null), 5000);
    } finally {
      setClearingModels(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  const localModels = models.filter(
    (model) => (model.training_type === 'LOCAL') || model.round_number === 0
  );

  return (
    <ConsoleLayout title="Overview" subtitle="Hospital operational dashboard">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Clear Models Message */}
        {clearMessage && (
          <div className={`mb-6 p-4 rounded-lg ${
            clearMessage.type === 'success'
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            <p className={`text-sm font-medium ${
              clearMessage.type === 'success'
                ? 'text-green-800'
                : 'text-red-800'
            }`}>
              {clearMessage.text}
            </p>
          </div>
        )}
        {/* Hospital Eligibility Status */}
        {user?.role === 'HOSPITAL' && currentRound && eligibilityStatus && (
          <div className={`mb-6 p-4 rounded-lg border-l-4 ${
            eligibilityStatus.is_eligible
              ? 'bg-green-50 border-green-400'
              : 'bg-red-50 border-red-400'
          }`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {eligibilityStatus.is_eligible ? (
                  <span className="text-2xl">✓</span>
                ) : (
                  <span className="text-2xl">✗</span>
                )}
              </div>
              <div className="ml-3 flex-1">
                <p className={`font-semibold ${
                  eligibilityStatus.is_eligible
                    ? 'text-green-900'
                    : 'text-red-900'
                }`}>
                  {eligibilityStatus.is_eligible ? 'You are eligible for this round' : 'You are not eligible for this round'}
                </p>
                <p className={`text-sm mt-1 ${
                  eligibilityStatus.is_eligible
                    ? 'text-green-700'
                    : 'text-red-700'
                }`}>
                  {eligibilityStatus.reason}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Aggregation Strategy Banner */}
        {user?.role === 'HOSPITAL' && currentRound && (
          <div className={`mb-6 p-4 rounded-lg border-l-4 ${
            (currentRound.aggregation_strategy || 'fedavg') === 'pfl'
              ? 'bg-purple-50 border-purple-300'
              : 'bg-blue-50 border-blue-300'
          }`}>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 text-lg">
                {(currentRound.aggregation_strategy || 'fedavg') === 'pfl' ? '🔐' : '🌐'}
              </div>
              <div className="flex-1">
                <p className={`font-semibold ${
                  (currentRound.aggregation_strategy || 'fedavg') === 'pfl'
                    ? 'text-purple-900'
                    : 'text-blue-900'
                }`}>
                  {(currentRound.aggregation_strategy || 'fedavg') === 'pfl' 
                    ? 'Personalized Federated Learning Active'
                    : 'Standard Federated Averaging Active'}
                </p>
                <p className={`text-sm mt-1 ${
                  (currentRound.aggregation_strategy || 'fedavg') === 'pfl'
                    ? 'text-purple-800'
                    : 'text-blue-800'
                }`}>
                  {(currentRound.aggregation_strategy || 'fedavg') === 'pfl'
                    ? 'Backbone will be shared. Local output head remains private.'
                    : 'Full model will be aggregated across all hospitals.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {user?.role === 'HOSPITAL' ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm">Total Datasets</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{datasets.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm">Local Models</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{localModels.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm">Federated Participations</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{globalModels.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm">Eligibility Status</p>
                <p className={`text-2xl font-bold mt-2 ${eligibilityStatus?.is_eligible ? 'text-green-700' : 'text-red-700'}`}>
                  {eligibilityStatus?.is_eligible ? 'ELIGIBLE' : 'INELIGIBLE'}
                </p>
              </div>
            </div>

            {/* Models Section - Navigation Cards */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Models</h3>
                <button
                  onClick={() => setShowClearModal(true)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Clear Local Models
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div
                  onClick={() => navigate('/models?type=local')}
                  className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer p-6 text-white"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xl font-bold">Local Models</h4>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-blue-100 text-sm mb-4">
                    View and manage models trained on your hospital's data
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold">{localModels.length}</span>
                    <span className="text-blue-200 text-sm">models available →</span>
                  </div>
                </div>

                <div
                  onClick={() => navigate('/models?type=global')}
                  className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer p-6 text-white"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xl font-bold">Global Models</h4>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-purple-100 text-sm mb-4">
                    Access federated models trained collaboratively
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold">{globalModels.length}</span>
                    <span className="text-purple-200 text-sm">models available →</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Predictions Section - Navigation Cards */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Predictions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div
                  onClick={() => navigate('/prediction?type=local')}
                  className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer p-6 text-white"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xl font-bold">Local Predictions</h4>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <p className="text-emerald-100 text-sm mb-4">
                    Generate predictions using your local models
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-emerald-100">Use local model →</span>
                  </div>
                </div>

                <div
                  onClick={() => navigate('/prediction?type=global')}
                  className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer p-6 text-white"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xl font-bold">Global Predictions</h4>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                  </div>
                  <p className="text-indigo-100 text-sm mb-4">
                    Generate predictions using federated global models
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-indigo-100">Use global model →</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Current Round</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Round ID</span>
                    <span className="font-semibold">{currentRound?.round_number ?? 'N/A'}</span>
                  </div>
                  {currentRound?.target_column && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Target Column</span>
                      <span className="font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">
                        {currentRound.target_column}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status</span>
                    <span className="font-semibold">{currentRound?.status ?? 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Blockchain Entries</h3>
                {hospitalChain.length === 0 ? (
                  <p className="text-sm text-gray-600">No blockchain entries available.</p>
                ) : (
                  <ul className="space-y-2 text-xs font-mono break-all">
                    {hospitalChain.slice(0, 3).map((entry, idx) => (
                      <li key={`${entry.block_hash}-${idx}`}>
                        {entry.model_hash}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Your Datasets</h3>
                {datasets.length === 0 ? (
                  <p className="text-sm text-gray-600">No datasets uploaded.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {datasets.slice(0, 5).map((dataset) => (
                      <li key={dataset.id} className="flex justify-between">
                        <span>{dataset.filename}</span>
                        <span className="text-gray-500">{dataset.num_rows ?? 'N/A'} rows</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Local Models</h3>
                {localModels.length === 0 ? (
                  <p className="text-sm text-gray-600">No local models trained.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {localModels.slice(0, 5).map((model) => (
                      <li key={model.id} className="flex justify-between">
                        <span>Model #{model.id}</span>
                        <span className="text-gray-500">Loss {model.local_loss?.toFixed(4) ?? 'N/A'}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Federated Participation</h3>
                {globalModels.length === 0 ? (
                  <p className="text-sm text-gray-600">No federated participation yet.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {globalModels.slice(0, 5).map((model) => (
                      <li key={model.id} className="flex justify-between">
                        <span>Round {model.round_number}</span>
                        <span className="text-gray-500">Model #{model.id}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Predictions</h3>
                {predictions.length === 0 ? (
                  <p className="text-sm text-gray-600">No saved predictions yet.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {predictions.slice(0, 5).map((prediction) => (
                      <li key={prediction.id}>
                        <p className="text-gray-900">{prediction.summary_text || 'Prediction saved'}</p>
                        <p className="text-xs text-gray-500">
                          {prediction.prediction_timestamp ? new Date(prediction.prediction_timestamp).toLocaleString() : prediction.created_at}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Current Round</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Round ID</span>
                  <span className="font-semibold">{currentRound?.round_number ?? 'N/A'}</span>
                </div>
                {currentRound?.target_column && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Target Column</span>
                    <span className="font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">
                      {currentRound.target_column}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">Participating Hospitals</span>
                  <span className="font-semibold">{currentRound?.num_participating_hospitals ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status</span>
                  <span className="font-semibold">{currentRound?.status ?? 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Latest Global Model</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Version</span>
                  <span className="font-semibold">{latestGlobalModel?.round_number ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Model Type</span>
                  <span className="font-semibold">{latestGlobalModel?.model_type ?? 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Timestamp</span>
                  <span className="font-semibold">
                    {latestGlobalModel?.created_at ? new Date(latestGlobalModel.created_at).toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Last Model Hash</h3>
              <p className="text-xs font-mono break-all">
                {lastBlock?.model_hash || 'N/A'}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Blockchain Validity</h3>
              <div className="text-sm">
                {chainValid === null ? (
                  <span className="text-slate-600 font-semibold">Unknown</span>
                ) : chainValid ? (
                  <span className="text-green-600 font-semibold">Valid</span>
                ) : (
                  <span className="text-red-600 font-semibold">Invalid</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <ClearModelsModal
        isOpen={showClearModal}
        onClose={() => setShowClearModal(false)}
        onConfirm={handleClearLocalModels}
        title="Clear Local Models"
        scope="local"
        loading={clearingModels}
      />
    </ConsoleLayout>
  );
};

export default Dashboard;
