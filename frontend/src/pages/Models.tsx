import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import modelUpdateService from '../services/modelUpdateService';
import trainingService from '../services/trainingService';
import { TrainedModel } from '../types/training';
import { AggregatedWeightsPreviewResponse } from '../types/modelUpdates';
import { formatErrorMessage } from '../utils/errorMessage';

type ModelTab = 'LOCAL' | 'GLOBAL';

const getArchitectureBadgeColor = (architecture?: string): string => {
  if (architecture === 'TFT') {
    return 'bg-purple-100 text-purple-800';
  } else if (architecture === 'ML_REGRESSION') {
    return 'bg-blue-100 text-blue-800';
  }
  // Default
  return 'bg-gray-100 text-gray-800';
};

const getArchitectureLabel = (architecture?: string): string => {
  if (architecture === 'TFT') {
    return 'TFT';
  } else if (architecture === 'ML_REGRESSION') {
    return 'ML_REGRESSION';
  }
  return 'Unknown';
};

const Models: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const typeParam = searchParams.get('type');
  
  const [models, setModels] = useState<TrainedModel[]>([]);
  const [selectedTab, setSelectedTab] = useState<ModelTab>(
    typeParam === 'global' ? 'GLOBAL' : 'LOCAL'
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [weightsLoadingModelId, setWeightsLoadingModelId] = useState<number | null>(null);
  const [weightsModalOpen, setWeightsModalOpen] = useState(false);
  const [weightsPayload, setWeightsPayload] = useState<AggregatedWeightsPreviewResponse | null>(null);

  const handleSeeAggregatedWeights = async (modelId: number) => {
    setError('');
    setWeightsLoadingModelId(modelId);
    try {
      const payload = await modelUpdateService.getAggregatedWeightsPreview(modelId);
      setWeightsPayload(payload);
      setWeightsModalOpen(true);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Failed to load aggregated weights.';
      setError(detail);
    } finally {
      setWeightsLoadingModelId(null);
    }
  };

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    const fetchModels = async () => {
      try {
        const modelsData = await trainingService.getModels();
        setModels(modelsData);
      } catch (err) {
        console.error('Failed to load models:', err);
        setError('Failed to load models.');
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [navigate]);

  useEffect(() => {
    // Update tab when URL parameter changes
    if (typeParam === 'global') {
      setSelectedTab('GLOBAL');
    } else if (typeParam === 'local') {
      setSelectedTab('LOCAL');
    }
  }, [typeParam]);

  const filteredModels = useMemo(() => {
    return models.filter(model => {
      const trainingType = model.training_type || 'FEDERATED';
      return trainingType === selectedTab;
    });
  }, [models, selectedTab]);

  const hasLocalModels = models.some(m => (m.training_type || 'FEDERATED') === 'LOCAL');
  const hasGlobalModels = models.some(m => (m.training_type || 'FEDERATED') === 'GLOBAL');
  const hasFederatedModels = models.some(m => (m.training_type || 'FEDERATED') === 'FEDERATED');

  return (
    <ConsoleLayout title="Models" subtitle="View your trained models">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Model Management</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <p className="text-gray-600">Loading models...</p>
          </div>
        ) : (
          <>
            {/* Tab Navigation */}
            <div className="mb-6 border-b border-gray-200">
              <div className="flex space-x-8">
                {hasLocalModels && (
                  <button
                    onClick={() => setSelectedTab('LOCAL')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      selectedTab === 'LOCAL'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    }`}
                  >
                    Local Models
                    <span className="ml-2 inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {models.filter(m => (m.training_type || 'FEDERATED') === 'LOCAL').length}
                    </span>
                  </button>
                )}
                {(hasGlobalModels || hasFederatedModels) && (
                  <button
                    onClick={() => setSelectedTab('GLOBAL')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      selectedTab === 'GLOBAL'
                        ? 'border-purple-600 text-purple-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    }`}
                  >
                    Global Models
                    <span className="ml-2 inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                      {models.filter(m => (m.training_type || 'FEDERATED') === 'GLOBAL' || (m.training_type || 'FEDERATED') === 'FEDERATED').length}
                    </span>
                  </button>
                )}
              </div>
            </div>

            {/* Content Sections */}
            {selectedTab === 'LOCAL' && hasLocalModels ? (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-blue-900">📊 Local Models</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    Models trained only on your hospital's data. Use these for local predictions and analysis.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredModels.map((model) => (
                    <div
                      key={model.id}
                      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 cursor-pointer"
                      onClick={() => navigate(`/prediction?model=${model.id}&type=local`)}
                    >
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-gray-900">Round {model.round_number}</h4>
                          <span className={`text-xs px-2 py-1 rounded font-medium ${getArchitectureBadgeColor(model.model_architecture ?? undefined)}`}>
                            {getArchitectureLabel(model.model_architecture ?? undefined)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{model.model_type}</p>
                      </div>

                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Loss:</span>
                          <span className="font-medium text-gray-900">
                            {model.local_loss?.toFixed(4) ?? 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Model Type:</span>
                          <span className="font-medium text-gray-900">
                            {model.model_type || 'N/A'}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-gray-500">
                        {model.created_at ? new Date(model.created_at).toLocaleDateString() : 'N/A'}
                      </p>

                      <button className="mt-4 w-full bg-blue-600 text-white py-2 px-3 rounded hover:bg-blue-700 text-sm font-medium">
                        Make Prediction →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ) : selectedTab === 'LOCAL' ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Local Models</h3>
                <p className="text-gray-600">
                  You don't have any local models yet. 
                  <button 
                    onClick={() => navigate('/training')}
                    className="text-blue-600 hover:text-blue-700 font-medium ml-1"
                  >
                    Train a model locally
                  </button>
                </p>
              </div>
            ) : null}

            {selectedTab === 'GLOBAL' && (hasGlobalModels || hasFederatedModels) ? (
              <div className="space-y-6">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-purple-900">🌐 Global Models</h3>
                  <p className="text-sm text-purple-700 mt-1">
                    Aggregated models from federated learning rounds. Use these for collaborative predictions.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredModels
                    .filter(m => (m.training_type || 'FEDERATED') === 'FEDERATED')
                    .map((model) => (
                      <div
                        key={model.id}
                        className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 cursor-pointer"
                        onClick={() => navigate(`/prediction?model=${model.id}&type=global`)}
                      >
                        <div className="mb-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-gray-900">Round {model.round_number}</h4>
                            <span className={`text-xs px-2 py-1 rounded font-medium ${getArchitectureBadgeColor(model.model_architecture ?? undefined)}`}>
                              {getArchitectureLabel(model.model_architecture ?? undefined)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{model.model_type}</p>
                        </div>

                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Loss:</span>
                            <span className="font-medium text-gray-900">
                              {model.local_loss?.toFixed(4) || 'N/A'}
                            </span>
                          </div>
                          {model.aggregation_strategy && (
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Aggregation:</span>
                              <span className={`text-xs px-2 py-1 rounded font-medium ${
                                (model.aggregation_strategy || 'fedavg') === 'pfl'
                                  ? 'bg-purple-100 text-purple-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}>
                                {(model.aggregation_strategy || 'fedavg') === 'pfl' ? 'PFL' : 'FedAvg'}
                              </span>
                            </div>
                          )}
                        </div>

                        <button className="mt-4 w-full bg-purple-600 text-white py-2 px-3 rounded hover:bg-purple-700 text-sm font-medium">
                          Make Prediction →
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSeeAggregatedWeights(model.id);
                          }}
                          disabled={weightsLoadingModelId === model.id}
                          className="mt-2 w-full border border-purple-300 text-purple-700 py-2 px-3 rounded hover:bg-purple-50 text-sm font-medium disabled:opacity-60"
                        >
                          {weightsLoadingModelId === model.id ? 'Loading...' : 'See Aggregated Weights'}
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            ) : selectedTab === 'GLOBAL' ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Global Models</h3>
                <p className="text-gray-600">
                  No federated models are available yet. 
                  <button 
                    onClick={() => navigate('/rounds')}
                    className="text-blue-600 hover:text-blue-700 font-medium ml-1"
                  >
                    Check federated rounds
                  </button>
                </p>
              </div>
            ) : null}
          </>
        )}

        {weightsModalOpen && weightsPayload && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
            <div className="bg-white rounded-lg w-full max-w-4xl max-h-[85vh] overflow-hidden shadow-xl">
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Aggregated Weights Proof</h3>
                <button
                  onClick={() => setWeightsModalOpen(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  Close
                </button>
              </div>

              <div className="p-6 space-y-4 overflow-y-auto max-h-[70vh]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div><span className="text-gray-600">Round:</span> <span className="font-medium">{weightsPayload.round_number}</span></div>
                  <div><span className="text-gray-600">Model ID:</span> <span className="font-medium">{weightsPayload.model_id}</span></div>
                  <div><span className="text-gray-600">Approved:</span> <span className="font-medium">{weightsPayload.approved ? 'Yes' : 'No'}</span></div>
                  <div><span className="text-gray-600">Distributed:</span> <span className="font-medium">{weightsPayload.distributed_to_hospital ? 'Yes' : 'No'}</span></div>
                  <div className="md:col-span-2 break-all"><span className="text-gray-600">Model Hash:</span> <span className="font-medium">{weightsPayload.model_hash || 'N/A'}</span></div>
                  <div><span className="text-gray-600">Policy Version:</span> <span className="font-medium">{weightsPayload.policy_version || 'N/A'}</span></div>
                  <div><span className="text-gray-600">Signature:</span> <span className="font-medium">{weightsPayload.signature || 'N/A'}</span></div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Aggregated Weights JSON</h4>
                  <pre className="bg-gray-900 text-green-200 p-4 rounded text-xs overflow-auto max-h-[45vh]">
                    {JSON.stringify(weightsPayload.weights_json, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default Models;
