import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import MLPrediction from '../components/MLPrediction';
import TFTForecast from '../components/TFTForecast';
import authService from '../services/authService';
import predictionService from '../services/predictionService';
import modelUpdateService from '../services/modelUpdateService';
import datasetService from '../services/datasetService';
import { GlobalModel } from '../types/modelUpdates';
import { Dataset } from '../types/dataset';
import { PredictionHistoryItem } from '../types/predictions';
import { formatErrorMessage } from '../utils/errorMessage';

type TabType = 'LOCAL' | 'FEDERATED';
const STANDARD_HORIZONS = ['6h', '12h', '24h', '48h', '72h', '168h'];

const Prediction: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const typeParam = searchParams.get('type');
  
  const [models, setModels] = useState<GlobalModel[]>([]);
  const [selectedTab, setSelectedTab] = useState<TabType>(
    typeParam === 'global' ? 'FEDERATED' : 'LOCAL'
  );
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [datasetsById, setDatasetsById] = useState<Record<number, string>>({});

  const filteredModels = useMemo(() => {
    if (selectedTab === 'LOCAL') {
      return models.filter(model => model.training_type === 'LOCAL');
    }

    // FEDERATED tab → ONLY aggregated global models
    return models.filter(model => model.is_global === true);
  }, [models, selectedTab]);

  useEffect(() => {
    // Update tab when URL parameter changes
    if (typeParam === 'global') {
      setSelectedTab('FEDERATED');
    } else if (typeParam === 'local') {
      setSelectedTab('LOCAL');
    }
  }, [typeParam]);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const [modelsData, datasets] = await Promise.all([
          modelUpdateService.getAvailableModels(),
          datasetService.getDatasets().catch(() => [] as Dataset[]),
        ]);
        
        setModels(modelsData);
        const datasetMap = datasets.reduce<Record<number, string>>((acc, dataset) => {
          acc[dataset.id] = dataset.filename;
          return acc;
        }, {});
        setDatasetsById(datasetMap);
        
        // Set initial selected model based on available tab
        const localModels = modelsData.filter(m => (m.training_type || 'FEDERATED') === 'LOCAL');
        const federatedModels = modelsData.filter(m => (m.training_type || 'FEDERATED') === 'FEDERATED');
        
        if (localModels.length > 0) {
          const latest = [...localModels].sort((a, b) => b.round_number - a.round_number)[0];
          setSelectedModelId(latest.id);
          setSelectedTab('LOCAL');
        } else if (federatedModels.length > 0) {
          const latest = [...federatedModels].sort((a, b) => b.round_number - a.round_number)[0];
          setSelectedModelId(latest.id);
          setSelectedTab('FEDERATED');
        }

        try {
          const historyResponse = await predictionService.getPredictionHistory();
          setHistory(historyResponse.items);
        } catch (historyErr) {
          console.warn('Failed to load prediction history:', historyErr);
        }
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('Failed to load models.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const hasLocalModels = models.some(m => (m.training_type || 'FEDERATED') === 'LOCAL');
  const hasFederatedModels = models.some(m => (m.training_type || 'FEDERATED') === 'FEDERATED');

  const selectedModel = useMemo(
    () => filteredModels.find((model) => model.id === selectedModelId) ?? null,
    [filteredModels, selectedModelId]
  );

  const getDatasetLabel = (model: GlobalModel): string => {
    if (typeof model.dataset_id === 'number') {
      if (model.dataset_id === 0) {
        return 'Federated Global Dataset';
      }
      return datasetsById[model.dataset_id] || 'Dataset name unavailable';
    }
    return model.training_type === 'LOCAL' ? 'Dataset not linked' : 'Federated Global Dataset';
  };

  const getModelDatasetLabel = (model: GlobalModel): string => {
    const architecture = model.model_architecture || 'TFT';
    return `Model ${model.id} - ${architecture} | Dataset: ${getDatasetLabel(model)} (Round ${model.round_number})`;
  };

  const localModelsByDataset = useMemo(() => {
    const groups: Record<string, GlobalModel[]> = {};
    filteredModels.forEach((model) => {
      const key = getDatasetLabel(model);
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(model);
    });

    Object.values(groups).forEach((items) => {
      items.sort((a, b) => {
        if (b.round_number !== a.round_number) {
          return b.round_number - a.round_number;
        }
        return b.id - a.id;
      });
    });

    return groups;
  }, [filteredModels, datasetsById]);

  const federatedModelsByDataset = useMemo(() => {
    const groups: Record<string, GlobalModel[]> = {};
    filteredModels.forEach((model) => {
      const key = getDatasetLabel(model);
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(model);
    });

    Object.values(groups).forEach((items) => {
      items.sort((a, b) => {
        if (b.round_number !== a.round_number) {
          return b.round_number - a.round_number;
        }
        return b.id - a.id;
      });
    });

    return groups;
  }, [filteredModels, datasetsById]);


  function getHorizonValue(
      data: any,
      key: string
    ): string {
      // TFT format
      if (data?.horizons?.[key]?.p50 !== undefined) {
        return data.horizons[key].p50.toFixed(2);
      }

      // Baseline format
      if (data?.horizon_forecasts?.[key]?.prediction !== undefined) {
        return data.horizon_forecasts[key].prediction.toFixed(2);
      }

      return 'N/A';
    }

  function getDisplayHorizons(data: any): string[] {
    const tftKeys = data?.horizons ? Object.keys(data.horizons) : [];
    const baselineKeys = data?.horizon_forecasts ? Object.keys(data.horizon_forecasts) : [];
    const available = new Set([...tftKeys, ...baselineKeys]);

    const ordered = STANDARD_HORIZONS.filter((key) => available.has(key));
    return ordered.length > 0 ? ordered : STANDARD_HORIZONS;
  }

  function getHorizonDetailEntries(data: any): string[] {
    return getDisplayHorizons(data).map((horizonKey) => `${horizonKey}: ${getHorizonValue(data, horizonKey)}`);
  }

  return (
    <ConsoleLayout title="Prediction" subtitle="Global model inference">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Prediction</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {/* Tab Selection */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex space-x-8">
            {hasLocalModels && (
              <button
                onClick={() => {
                  setSelectedTab('LOCAL');
                  const localModels = models.filter(m => (m.training_type || 'FEDERATED') === 'LOCAL');
                  if (localModels.length > 0) {
                    const latest = [...localModels].sort((a, b) => b.round_number - a.round_number)[0];
                    setSelectedModelId(latest.id);
                  }
                  setError('');
                }}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'LOCAL'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                Local Predictions
              </button>
            )}
            {hasFederatedModels && (
              <button
                onClick={() => {
                  setSelectedTab('FEDERATED');
                  const federatedModels = models.filter(m => (m.training_type || 'FEDERATED') === 'FEDERATED');
                  if (federatedModels.length > 0) {
                    const latest = [...federatedModels].sort((a, b) => b.round_number - a.round_number)[0];
                    setSelectedModelId(latest.id);
                  }
                  setError('');
                }}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'FEDERATED'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                Federated Predictions
              </button>
            )}
          </div>
        </div>

        {/* Empty State Messages */}
        {!hasLocalModels && !hasFederatedModels && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold text-yellow-900 mb-2">No Models Available</h3>
            <p className="text-yellow-700">
              No local or federated models are available for predictions. 
              Please train a model first or wait for federated training to complete.
            </p>
          </div>
        )}

        {/* LOCAL Tab Content */}
        {selectedTab === 'LOCAL' && hasLocalModels ? (
          <>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-medium text-blue-900">📊 Local Predictions</h3>
              <p className="text-sm text-blue-700 mt-1">
                Generate predictions using locally trained models. These models are trained only on your hospital's data.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Model Selection</h3>
              {loading ? (
                <p className="text-gray-600">Loading models...</p>
              ) : (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-2">
                    Showing {filteredModels.length} local model(s) across {Object.keys(localModelsByDataset).length} dataset(s)
                  </p>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Local Model</label>
                  <select
                    value={selectedModelId ?? ''}
                    onChange={(e) => setSelectedModelId(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select model</option>
                    {Object.entries(localModelsByDataset).map(([datasetLabel, items]) => (
                      <optgroup key={datasetLabel} label={`Dataset: ${datasetLabel}`}>
                        {items.map((model) => (
                          <option key={model.id} value={model.id}>
                            {`Model ${model.id} - ${model.model_architecture || 'TFT'} (Round ${model.round_number})`}
                            {model.target_column && ` → predicts: ${model.target_column}`}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {selectedModel && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6">
                <h3 className="text-sm font-medium text-indigo-900">Selected Model + Dataset</h3>
                <p className="text-sm text-indigo-700 mt-1">
                  <span className="font-semibold">Model:</span> {selectedModel.model_architecture || 'TFT'} (ID {selectedModel.id}, Round {selectedModel.round_number})
                </p>
                <p className="text-sm text-indigo-700 mt-1">
                  <span className="font-semibold">Dataset:</span> {getDatasetLabel(selectedModel)}
                </p>
              </div>
            )}

            {/* Render appropriate component based on model architecture */}
            {selectedModel && (
              <>
                {/* Get selected model architecture */}
                {(() => {
                  if (selectedModel.model_architecture === 'ML_REGRESSION') {
                    return <MLPrediction model={selectedModel} />;
                  } else if (selectedModel.model_architecture === 'TFT') {
                    return <TFTForecast model={selectedModel} />;
                  } else {
                    // Default to TFT for backward compatibility
                    return <TFTForecast model={selectedModel} />;
                  }
                })()}
              </>
            )}
          </>
        ) : selectedTab === 'LOCAL' && !hasLocalModels ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Local Models</h3>
            <p className="text-gray-600">
              You don't have any local models yet. Train a model locally in the Training page to start making predictions.
            </p>
          </div>
        ) : null}

        {/* FEDERATED Tab Content */}
        {selectedTab === 'FEDERATED' && hasFederatedModels ? (
          <>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-medium text-purple-900">🌐 Federated Predictions</h3>
              <p className="text-sm text-purple-700 mt-1">
                Generate predictions using globally aggregated models. These models are trained collaboratively across all participating hospitals.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Model Selection</h3>
              {loading ? (
                <p className="text-gray-600">Loading models...</p>
              ) : (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-2">
                    Showing {filteredModels.length} federated model(s) across {Object.keys(federatedModelsByDataset).length} dataset group(s)
                  </p>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Federated Model</label>
                  <select
                    value={selectedModelId ?? ''}
                    onChange={(e) => setSelectedModelId(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select model</option>
                    {Object.entries(federatedModelsByDataset).map(([datasetLabel, items]) => (
                      <optgroup key={datasetLabel} label={`Dataset: ${datasetLabel}`}>
                        {items.map((model) => (
                          <option key={model.id} value={model.id}>
                            {`Model ${model.id} - ${model.model_architecture || 'TFT'} (Round ${model.round_number})`}
                            {model.target_column && ` → predicts: ${model.target_column}`}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {selectedModel && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6">
                <h3 className="text-sm font-medium text-indigo-900">Selected Model + Dataset</h3>
                <p className="text-sm text-indigo-700 mt-1">
                  <span className="font-semibold">Model:</span> {selectedModel.model_architecture || 'TFT'} (ID {selectedModel.id}, Round {selectedModel.round_number})
                </p>
                <p className="text-sm text-indigo-700 mt-1">
                  <span className="font-semibold">Dataset:</span> {getDatasetLabel(selectedModel)}
                </p>
              </div>
            )}

            {/* Render appropriate component based on model architecture */}
            {selectedModel && (
              <>
                {/* Get selected model architecture */}
                {(() => {
                  if (selectedModel.model_architecture === 'ML_REGRESSION') {
                    return <MLPrediction model={selectedModel} />;
                  } else if (selectedModel.model_architecture === 'TFT') {
                    return <TFTForecast model={selectedModel} />;
                  } else {
                    // Default to TFT for backward compatibility
                    return <TFTForecast model={selectedModel} />;
                  }
                })()}
              </>
            )}
          </>
        ) : selectedTab === 'FEDERATED' && !hasFederatedModels ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Federated Models</h3>
            <p className="text-gray-600">
              No federated models are available yet. Participate in federated training rounds to access globally aggregated models.
            </p>
          </div>
        ) : null}

        {history.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Saved Predictions</h3>
            <div className="space-y-4">
              {history.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-gray-500">Saved: {new Date(item.created_at).toLocaleString()}</p>
                      <p className="text-sm text-gray-700">
                        Round {item.round_number ?? 'N/A'} · Target {item.target_column ?? 'N/A'}
                      </p>
                      <p className="text-sm text-gray-700">
                        Model: {item.model_type ?? 'N/A'} · Dataset: {item.dataset_name ?? 'N/A'}
                      </p>
                    </div>
                    <div className="text-right">
                      {item.forecast_horizon === 0 ? (
                        <>
                          <p className="text-sm text-gray-500">Prediction</p>
                          <p className="text-sm font-semibold text-gray-800">
                            {"prediction" in item.forecast_data
                              ? (typeof item.forecast_data.prediction === 'number'
                                  ? item.forecast_data.prediction.toFixed(2)
                                  : 'N/A')
                              : 'N/A'}
                          </p>
                        </>
                      ) : (
                        <>
                          <p className="text-sm text-gray-500">Horizon predictions (p50)</p>
                          <p className="text-sm font-semibold text-gray-800">
                            {getHorizonDetailEntries(item.forecast_data)
                              .join(' / ')}
                          </p>
                        </>
                      )}
                    </div>
                  </div>

                  {item.schema_validation && (
                    <details className="mt-3">
                      <summary className="text-sm text-blue-700 cursor-pointer">View schema validation</summary>
                      <div className="mt-2 text-sm text-gray-700">
                        <p>Schema match: {item.schema_validation.schema_match === null ? 'N/A' : item.schema_validation.schema_match ? 'Yes' : 'No'}</p>
                        <p>Target: {item.schema_validation.model_schema?.target_column ?? 'N/A'}</p>
                        {item.schema_validation.warnings?.length ? (
                          <ul className="list-disc list-inside mt-1">
                            {item.schema_validation.warnings.map((warning, idx) => (
                              <li key={idx}>{warning}</li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    </details>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default Prediction;
