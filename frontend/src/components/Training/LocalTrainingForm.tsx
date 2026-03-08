/**
 * LOCAL Training Form Component
 * Hospital-controlled training with full feature selection
 * Supports both ML_REGRESSION and TFT architectures
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Dataset {
  id: number;
  filename: string;
  column_names: string[];
  num_rows: number;
  num_columns: number | null;
  dataset_type?: string; // 'TABULAR' or 'TIME_SERIES'
}

interface LocalTrainingFormProps {
  onTrainingStarted: (result: any) => void;
  onError: (error: string) => void;
}

export const LocalTrainingForm: React.FC<LocalTrainingFormProps> = ({
  onTrainingStarted,
  onError
}) => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedTarget, setSelectedTarget] = useState('');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [architecture, setArchitecture] = useState<'ML_REGRESSION' | 'TFT'>('ML_REGRESSION');
  const [lookback, setLookback] = useState(7);
  const [horizon, setHorizon] = useState(1);
  const [epochs, setEpochs] = useState(10);
  const [batchSize, setBatchSize] = useState(16);
  const [learningRate, setLearningRate] = useState(0.001);
  const [useEnsemble, setUseEnsemble] = useState(false);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/datasets/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDatasets(response.data.datasets || []);
    } catch (err) {
      onError('Failed to load datasets');
    }
  };

  const handleDatasetChange = (datasetId: number) => {
    const dataset = datasets.find(d => d.id === datasetId);
    setSelectedDataset(dataset || null);
    setSelectedTarget('');
    setSelectedFeatures([]);
  };

  const handleFeatureToggle = (feature: string) => {
    setSelectedFeatures(prev =>
      prev.includes(feature)
        ? prev.filter(f => f !== feature)
        : [...prev, feature]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Comprehensive validation
    const errors: string[] = [];

    if (!selectedDataset) {
      errors.push('Please select a dataset');
    }

    if (!selectedTarget) {
      errors.push('Please select a target column');
    }

    if (selectedFeatures.length === 0) {
      errors.push('Please select at least one feature');
    }

    if (selectedFeatures.includes(selectedTarget)) {
      errors.push('Target column cannot be included in features');
    }

    if (epochs < 1 || epochs > 100) {
      errors.push('Epochs must be between 1 and 100');
    }

    // TFT-specific validation
    if (architecture === 'TFT') {
      if (lookback < 1) {
        errors.push('Lookback (encoder length) must be >= 1');
      }
      if (horizon < 1) {
        errors.push('Horizon (prediction length) must be >= 1');
      }
      // Check dataset size
      if (selectedDataset && selectedDataset.num_rows) {
        const totalSeqLength = lookback + horizon;
        if (totalSeqLength > selectedDataset.num_rows) {
          errors.push(`Lookback + Horizon (${totalSeqLength}) exceeds dataset size (${selectedDataset.num_rows})`);
        }
      }
    }

    if (errors.length > 0) {
      onError(errors.join('\n'));
      return;
    }

    setLoading(true);
    try {
      if (!selectedDataset) {
        throw new Error('Dataset validation failed');
      }
      
      const response = await axios.post(
        `${API_URL}/api/training/start`,
        {
          dataset_id: selectedDataset.id,
          target_column: selectedTarget,
          feature_columns: selectedFeatures,
          training_type: 'LOCAL',
          model_architecture: architecture,
          epochs,
          batch_size: batchSize,
          learning_rate: learningRate,
          lookback: architecture === 'TFT' ? lookback : undefined,
          horizon: architecture === 'TFT' ? horizon : undefined,
          use_ensemble: useEnsemble
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      onTrainingStarted(response.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Training failed');
    } finally {
      setLoading(false);
    }
  };

  const availableFeatures = selectedDataset?.column_names.filter(col => col !== selectedTarget) || [];

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4 text-blue-600">LOCAL Training</h2>
      <p className="text-sm text-gray-600 mb-4">
        ✅ This training is fully local. Central server has no influence over your training configuration.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Dataset Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select Dataset
          </label>
          <select
            value={selectedDataset?.id || ''}
            onChange={(e) => handleDatasetChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">-- Choose a dataset --</option>
            {datasets.map(ds => (
              <option key={ds.id} value={ds.id}>
                {ds.filename} ({ds.num_rows} rows, {ds.num_columns} columns)
              </option>
            ))}
          </select>
        </div>

        {selectedDataset && (
          <>
            {/* Target Column */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Column
              </label>
              <select
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">-- Choose target --</option>
                {selectedDataset.column_names.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>

            {/* Feature Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Features ({selectedFeatures.length} selected)
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto border border-gray-300 p-3 rounded">
                {availableFeatures.map(feature => (
                  <label key={feature} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedFeatures.includes(feature)}
                      onChange={() => handleFeatureToggle(feature)}
                      className="mr-2"
                    />
                    <span className="text-sm">{feature}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Model Architecture */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model Architecture
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="architecture"
                    value="ML_REGRESSION"
                    checked={architecture === 'ML_REGRESSION'}
                    onChange={(e) => setArchitecture('ML_REGRESSION')}
                    className="mr-2"
                  />
                  <span className="text-sm">ML Regression (trained 6 models: Linear, RF, GB, Ridge, Lasso, XGBoost)</span>
                </label>
                <label className={`flex items-center ${
                  selectedDataset?.dataset_type === 'TABULAR' ? 'opacity-50 cursor-not-allowed' : ''
                }`}>
                  <input
                    type="radio"
                    name="architecture"
                    value="TFT"
                    checked={architecture === 'TFT'}
                    onChange={(e) => setArchitecture('TFT')}
                    disabled={selectedDataset?.dataset_type === 'TABULAR'}
                    className="mr-2"
                  />
                  <span className="text-sm">TFT (Time Series Forecasting)</span>
                </label>
              </div>

              {selectedDataset?.dataset_type === 'TABULAR' && (
                <p className="text-xs text-amber-600 mt-1">
                  ℹ️ TFT requires a time-series dataset (with timestamp column). This dataset is TABULAR.
                </p>
              )}
            </div>

            {/* TIME_SERIES Mode Info */}
            {selectedDataset && architecture === 'ML_REGRESSION' && selectedDataset.num_rows && (
              <div className={`border-l-4 p-4 rounded ${
                selectedDataset.num_rows > 50
                  ? 'bg-blue-50 border-blue-400'
                  : 'bg-amber-50 border-amber-400'
              }`}>
                <div className="flex items-start gap-2">
                  <span className="text-lg flex-shrink-0">📊</span>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">Time-Series Mode (ML Regression)</p>
                    <p className="text-sm text-gray-700 mt-1">
                      This dataset will be automatically processed with temporal features:
                    </p>
                    <ul className="text-sm text-gray-700 mt-2 ml-4 list-disc">
                      <li><strong>Lag features:</strong> [1, 3, 7] timesteps</li>
                      <li><strong>Rolling means:</strong> windows [3, 7]</li>
                      <li><strong>Split method:</strong> Chronological 80/20 (preserving time order)</li>
                    </ul>
                    <p className="text-xs text-gray-600 mt-2">
                      ℹ️ ML Regression uses engineered temporal features. For full sequence modeling with multi-horizon forecasting, use TFT instead.
                    </p>
                  </div>
                </div>
              </div>
            )}


            {/* TFT Parameters */}
            {architecture === 'TFT' && (
              <div className="grid grid-cols-2 gap-3 p-3 bg-blue-50 rounded">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lookback (encoder length)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={lookback}
                    onChange={(e) => setLookback(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Horizon (prediction length)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={horizon}
                    onChange={(e) => setHorizon(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            )}

            {/* ML Specific Options */}
            {architecture === 'ML_REGRESSION' && (
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={useEnsemble}
                    onChange={(e) => setUseEnsemble(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">
                    Use Ensemble (average top 3 models) instead of selecting best
                  </span>
                </label>
              </div>
            )}

            {/* Training Parameters */}
            <div className="p-4 bg-green-50 border-2 border-green-300 rounded-lg space-y-3">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">✏️</span>
                <div>
                  <p className="font-bold text-green-900">LOCAL Mode: Flexible Parameter Control</p>
                  <p className="text-xs text-green-700">You can freely adjust training parameters for experimentation</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {/* Epochs */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Epochs
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={epochs}
                    onChange={(e) => setEpochs(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-xs text-gray-500 mt-1">Default: 10</p>
                </div>

                {/* Batch Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="256"
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-xs text-gray-500 mt-1">Default: 16</p>
                </div>

                {/* Learning Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Learning Rate
                  </label>
                  <input
                    type="number"
                    min="0.0001"
                    max="1"
                    step="0.0001"
                    value={learningRate}
                    onChange={(e) => setLearningRate(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-xs text-gray-500 mt-1">Default: 0.001</p>
                </div>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 px-4 rounded-md text-white font-medium transition ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? 'Training...' : 'Start Local Training'}
            </button>
          </>
        )}
      </form>
    </div>
  );
};
