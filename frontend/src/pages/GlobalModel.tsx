import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import modelUpdateService from '../services/modelUpdateService';
import type { GlobalModel as GlobalModelType, AggregatedWeightsPreviewResponse } from '../types/modelUpdates';
import { useAuth } from '../context/AuthContext';
import { formatErrorMessage } from '../utils/errorMessage';

type TabType = 'GLOBAL' | 'LOCAL';

const GlobalModel: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [models, setModels] = useState<GlobalModelType[]>([]);
  const [selectedTab, setSelectedTab] = useState<TabType>('GLOBAL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [downloading, setDownloading] = useState(false);
  const [weightsLoadingModelId, setWeightsLoadingModelId] = useState<number | null>(null);
  const [weightsModalOpen, setWeightsModalOpen] = useState(false);
  const [weightsPayload, setWeightsPayload] = useState<AggregatedWeightsPreviewResponse | null>(null);

  useEffect(() => {
    const isAuth = authService.isAuthenticated();
    if (!isAuth) {
      navigate('/login');
      return;
    }
    fetchModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]);

  const fetchModels = async () => {
    try {
      const data = await modelUpdateService.getAvailableModels();
      setModels(data);
    } catch (err) {
      setError('Failed to load models.');
    } finally {
      setLoading(false);
    }
  };

  const filteredModels = useMemo(() => {
    if (selectedTab === 'LOCAL') {
      return models.filter(
        (model) =>
          model.training_type === 'LOCAL'
      );
    }

    // GLOBAL TAB → only true aggregated models
    return models.filter(
      (model) =>
        model.is_global === true && model.hospital_id == null
    );
  }, [models, selectedTab]);

  const handleDownload = async (roundNumber: number) => {
    setDownloading(true);
    setError('');
    setMessage('');

    try {
      const result = await modelUpdateService.downloadGlobalModel(roundNumber);
      setMessage(result.message);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Download failed.';
      setError(errorMessage);
    } finally {
      setDownloading(false);
    }
  };

  const handleSeeAggregatedWeights = async (modelId: number) => {
    setWeightsLoadingModelId(modelId);
    setError('');
    try {
      // Use appropriate endpoint based on user role
      const payload = user?.role === 'ADMIN'
        ? await modelUpdateService.getCentralAggregatedWeightsPreview(modelId)
        : await modelUpdateService.getAggregatedWeightsPreview(modelId);
      setWeightsPayload(payload);
      setWeightsModalOpen(true);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || 'Failed to load aggregated weights.';
      
      // Enhanced error message for distribution/participation requirement
      let userFriendlyMessage = errorDetail;
      if (errorDetail.includes('not distributed to this hospital')) {
        userFriendlyMessage = 
          `⚠️ Access Restricted: You can only view global model weights for rounds where your hospital participated in training. ` +
          `To view these weights, go to Training → Train a model for this round → Upload weights to participate in federated aggregation.`;
      } else if (errorDetail.includes('not governance-approved')) {
        userFriendlyMessage = 
          `⚠️ This global model has not been approved by governance yet. Only approved models can be viewed.`;
      } else if (errorDetail.includes('not available for this round')) {
        userFriendlyMessage = 
          `⚠️ No aggregated global model exists for this round yet. Aggregation may still be in progress.`;
      }
      
      setError(userFriendlyMessage);
    } finally {
      setWeightsLoadingModelId(null);
    }
  };

  const latestModel =
    filteredModels.length > 0
      ? [...filteredModels].sort((a, b) => b.round_number - a.round_number)[0]
      : null;

  return (
    <ConsoleLayout title="Global Model" subtitle="Model distribution">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Models</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {message && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {message}
          </div>
        )}

        {/* TAB SECTION */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex space-x-8">
            <button
              onClick={() => setSelectedTab('GLOBAL')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'GLOBAL'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              Global Models
            </button>

            <button
              onClick={() => setSelectedTab('LOCAL')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'LOCAL'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              Local Models
            </button>
          </div>
        </div>

        {/* INFO BANNER FOR HOSPITAL USERS */}
        {user?.role === 'HOSPITAL' && selectedTab === 'GLOBAL' && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-blue-700">
                  <strong>Access Policy:</strong> You can only view weights for rounds where your hospital participated in training. 
                  To access global model weights, ensure you've trained and uploaded weights for that specific round.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* LATEST MODEL CARD */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">
            Latest {selectedTab === 'GLOBAL' ? 'Global' : 'Local'} Model
          </h3>

          {latestModel ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Round</p>
                <p className="text-lg font-semibold">
                  {latestModel.round_number}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Model Type</p>
                <p className="text-lg font-semibold">
                  {latestModel.model_type}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Created</p>
                <p className="text-lg font-semibold">
                  {new Date(latestModel.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-600">
              No {selectedTab.toLowerCase()} models available.
            </p>
          )}
        </div>

        {/* MODEL HISTORY TABLE */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">
              {selectedTab === 'GLOBAL' ? 'Global' : 'Local'} Model History
            </h3>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-600">
              Loading models...
            </div>
          ) : filteredModels.length === 0 ? (
            <div className="p-6 text-center text-gray-600">
              No models available.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Round
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Model Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Loss
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredModels.map((model) => (
                    <tr key={model.id}>
                      <td className="px-6 py-4 text-sm">
                        Round {model.round_number}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {model.model_type}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {model.loss !== null &&
                        model.loss !== undefined
                          ? model.loss.toFixed(4)
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(model.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {selectedTab === 'GLOBAL' ? (
                          <div className="flex items-center gap-3">
                            {user?.role === 'HOSPITAL' && (
                              <button
                                onClick={() =>
                                  handleDownload(model.round_number)
                                }
                                disabled={downloading}
                                className="text-blue-600 disabled:opacity-50"
                              >
                                {downloading
                                  ? 'Downloading...'
                                  : 'Download'}
                              </button>
                            )}
                            <button
                              onClick={() => handleSeeAggregatedWeights(model.id)}
                              disabled={weightsLoadingModelId === model.id}
                              className="text-purple-600 disabled:opacity-50 hover:text-purple-800 relative group"
                              title={user?.role === 'HOSPITAL' ? 'View weights (requires participation in this round)' : 'View aggregated weights'}
                            >
                              {weightsLoadingModelId === model.id ? 'Loading...' : 'View Weights'}
                              {user?.role === 'HOSPITAL' && (
                                <span className="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-gray-800 rounded-lg whitespace-nowrap z-10">
                                  🔒 Only accessible if you trained for this round
                                </span>
                              )}
                            </button>
                          </div>
                        ) : (
                          <span className="text-gray-400 text-xs">
                            View
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

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
                  {user?.role === 'ADMIN' ? (
                    <div><span className="text-gray-600">Admin View:</span> <span className="font-medium">Central Access</span></div>
                  ) : (
                    <div><span className="text-gray-600">Distributed:</span> <span className="font-medium">{weightsPayload.distributed_to_hospital ? 'Yes' : 'No'}</span></div>
                  )}
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

export default GlobalModel;