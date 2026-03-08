/**
 * FEDERATED Training Form Component
 * Hospital views read-only round schema
 * Can validate dataset and trigger training, but cannot modify schema
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RoundSchema {
  id: number;
  round_id: number;
  model_architecture: string;
  target_column: string;
  feature_schema: string[];
  feature_types?: Record<string, string>;
  sequence_required: boolean;
  lookback?: number;
  horizon?: number;
}

interface RoundInfo {
  round_number: number;
  aggregation_strategy?: string;
  status: string;
  required_hyperparameters?: {
    epochs?: number;
    batch_size?: number;
    learning_rate?: number;
  };
}

interface Dataset {
  id: number;
  filename: string;
  column_names: string[];
  num_rows: number;
  num_columns: number | null;
}

interface FederatedTrainingFormProps {
  roundId: number;
  onTrainingStarted: (result: any) => void;
  onError: (error: string) => void;
}

export const FederatedTrainingForm: React.FC<FederatedTrainingFormProps> = ({
  roundId,
  onTrainingStarted,
  onError
}) => {
  const [schema, setSchema] = useState<RoundSchema | null>(null);
  const [roundInfo, setRoundInfo] = useState<RoundInfo | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [schemaLoading, setSchemaLoading] = useState(true);
  const [trainingLoading, setTrainingLoading] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    fetchSchema();
    fetchRoundInfo();
    fetchDatasets();
  }, [roundId]);

  const fetchSchema = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/rounds/${roundId}/schema`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSchema(response.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to load round schema');
    } finally {
      setSchemaLoading(false);
    }
  };

  const fetchRoundInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/rounds/${roundId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRoundInfo(response.data);
    } catch (err: any) {
      // Silently fail - round info is optional for display
      console.warn('Failed to fetch round info:', err);
    }
  };

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/datasets/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDatasets(response.data.datasets || []);
    } catch (err) {
      // Silently fail
    }
  };

  const validateDataset = async () => {
    if (!selectedDataset) {
      onError('Please select a dataset');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/training/validate-dataset`,
        {
          dataset_id: selectedDataset,
          round_id: roundId
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setValidationResult(response.data);
      
      if (!response.data.is_valid) {
        onError(`Validation failed: ${response.data.errors.join(', ')}`);
      }
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const startTraining = async () => {
    if (!selectedDataset) {
      onError('Please select and validate a dataset first');
      return;
    }

    if (!validationResult?.is_valid) {
      onError('Dataset validation failed. Please fix issues and retry.');
      return;
    }

    setTrainingLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/training/start`,
        {
          dataset_id: selectedDataset,
          training_type: 'FEDERATED',
          round_id: roundId
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      onTrainingStarted(response.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Training failed');
    } finally {
      setTrainingLoading(false);
    }
  };

  if (schemaLoading) {
    return <div className="text-center py-4">Loading round schema...</div>;
  }

  if (!schema) {
    return (
      <div className="bg-red-50 p-4 rounded-lg border border-red-200">
        <p className="text-red-800">❌ Round schema not configured by central server</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold mb-2 text-purple-600">FEDERATED Training</h2>
        <p className="text-sm text-gray-600">
          🔒 Central server has configured the training schema. You cannot modify target, features, or architecture.
        </p>
      </div>

      {/* Aggregation Strategy Banner */}
      {roundInfo && (
        <div className={`border-l-4 p-4 rounded ${
          (roundInfo.aggregation_strategy || 'fedavg') === 'pfl'
            ? 'bg-purple-50 border-purple-500'
            : 'bg-blue-50 border-blue-500'
        }`}>
          {(roundInfo.aggregation_strategy || 'fedavg') === 'pfl' ? (
            <>
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <h3 className="font-bold text-purple-900">🔐 Personalized Federated Learning Active</h3>
              </div>
              <p className="text-sm text-purple-800">
                Only shared backbone parameters will be aggregated.<br/>
                Your local output head remains private and will not be uploaded.
              </p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-bold text-blue-900">🌐 Standard Federated Averaging Active</h3>
              </div>
              <p className="text-sm text-blue-800">
                Full model parameters will be uploaded for central aggregation.
              </p>
            </>
          )}
        </div>
      )}
      {/* TIME_SERIES Mode Information */}
      {schema && schema.model_architecture === 'ML_REGRESSION' && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
          <div className="flex items-start gap-2">
            <span className="text-lg flex-shrink-0">📊</span>
            <div className="flex-1">
              <p className="font-semibold text-blue-900">Time-Series ML Regression Mode</p>
              <p className="text-sm text-blue-800 mt-1">
                This round uses engineered temporal features:
              </p>
              <ul className="text-sm text-blue-800 mt-2 ml-4 list-disc">
                <li><strong>Lag features:</strong> [1, 3, 7] timesteps</li>
                <li><strong>Rolling means:</strong> windows [3, 7]</li>
                <li><strong>Split method:</strong> Chronological 80/20 (preserving time order)</li>
              </ul>
              <p className="text-xs text-blue-600 mt-2">
                ℹ️ Central server enforces these transformations for compliance. Features will be auto-generated during training.
              </p>
            </div>
          </div>
        </div>
      )}
      {/* 

  return (
    <div className="bg-white p-6 rounded-lg shadow-md space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold mb-2 text-purple-600">FEDERATED Training</h2>
        <p className="text-sm text-gray-600">
          🔒 Central server has configured the training schema. You cannot modify target, features, or architecture.
        </p>
      </div>

      {/* Read-Only Schema Card */}
      <div className="bg-purple-50 border-l-4 border-purple-600 p-4 rounded">
        <h3 className="font-bold text-purple-900 mb-3">Round Configuration (Read-Only)</h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium">Round ID:</span> {roundId}
          </div>
          <div>
            <span className="font-medium">Model Architecture:</span>{' '}
            <span className="font-mono bg-purple-100 px-2 py-1 rounded">{schema.model_architecture}</span>
          </div>
          <div>
            <span className="font-medium">Target Column:</span>{' '}
            <span className="font-mono bg-purple-100 px-2 py-1 rounded">{schema.target_column}</span>
          </div>
          <div>
            <span className="font-medium">Required Features:</span> {schema.feature_schema.length}
            <ul className="ml-4 mt-1 space-y-1">
              {schema.feature_schema.map((feature, idx) => (
                <li key={idx} className="text-gray-700">
                  • {feature}
                  {schema.feature_types?.[feature] && (
                    <span className="text-gray-500 text-xs ml-2">({schema.feature_types[feature]})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
          {schema.sequence_required && (
            <div className="bg-yellow-50 p-2 rounded mt-2">
              <span className="font-medium">⏱ Sequence Parameters:</span>
              <div className="ml-2 text-xs mt-1">
                Lookback: {schema.lookback}, Horizon: {schema.horizon}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Training Parameters - Locked */}
      <div className="p-4 bg-blue-50 border-2 border-blue-300 rounded-lg">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🔒</span>
          <div>
            <p className="font-bold text-blue-900">FEDERATED Mode: Parameter Control LOCKED</p>
            <p className="text-xs text-blue-700">All training parameters controlled by central privacy policy</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-gray-100 p-2 rounded">
            <p className="text-gray-600 font-medium">Epochs</p>
            <p className="text-gray-800 font-mono">≤ {roundInfo?.required_hyperparameters?.epochs || 2} (enforced)</p>
          </div>
          <div className="bg-gray-100 p-2 rounded">
            <p className="text-gray-600 font-medium">Batch Size</p>
            <p className="text-gray-800 font-mono">≤ {roundInfo?.required_hyperparameters?.batch_size || 32} (enforced)</p>
          </div>
          <div className="bg-gray-100 p-2 rounded">
            <p className="text-gray-600 font-medium">Learning Rate</p>
            <p className="text-gray-800 font-mono">Policy-controlled</p>
          </div>
        </div>
        
        <p className="text-xs text-blue-600 mt-2">
          ℹ️ These limits ensure privacy coordination across all participating hospitals
        </p>
      </div>

      {/* Dataset Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Your Dataset
        </label>
        <select
          value={selectedDataset || ''}
          onChange={(e) => {
            setSelectedDataset(Number(e.target.value));
            setValidationResult(null);
          }}
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

      {/* Validation Result */}
      {validationResult && (
        <div
          className={`p-4 rounded-lg ${
            validationResult.is_valid
              ? 'bg-green-50 border border-green-300'
              : 'bg-red-50 border border-red-300'
          }`}
        >
          <h4 className="font-bold mb-2">
            {validationResult.is_valid ? '✅ Validation Passed' : '❌ Validation Failed'}
          </h4>
          
          {validationResult.missing_features.length > 0 && (
            <div className="mb-2 text-sm">
              <span className="font-medium">Missing Features:</span>
              <ul className="ml-4 text-red-700">
                {validationResult.missing_features.map((f: string, i: number) => (
                  <li key={i}>• {f}</li>
                ))}
              </ul>
            </div>
          )}

          {validationResult.extra_features.length > 0 && (
            <div className="mb-2 text-sm text-yellow-700">
              <span className="font-medium">Extra Features (will be ignored):</span>
              <ul className="ml-4">
                {validationResult.extra_features.map((f: string, i: number) => (
                  <li key={i}>• {f}</li>
                ))}
              </ul>
            </div>
          )}

          {validationResult.type_mismatches && Object.keys(validationResult.type_mismatches).length > 0 && (
            <div className="text-sm text-yellow-700">
              <span className="font-medium">Type Mismatches (warnings):</span>
              <ul className="ml-4">
                {Object.entries(validationResult.type_mismatches).map(([feature, types]: any, i: number) => (
                  <li key={i}>• {feature}: expected {types[0]}, got {types[1]}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={validateDataset}
          disabled={!selectedDataset || loading}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
            !selectedDataset || loading
              ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
              : 'bg-yellow-500 text-white hover:bg-yellow-600'
          }`}
        >
          {loading ? 'Validating...' : 'Validate Dataset'}
        </button>

        <button
          onClick={startTraining}
          disabled={!validationResult?.is_valid || trainingLoading}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition ${
            !validationResult?.is_valid || trainingLoading
              ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
              : 'bg-purple-600 text-white hover:bg-purple-700'
          }`}
        >
          {trainingLoading ? 'Training...' : 'Train Federated Model'}
        </button>
      </div>
    </div>
  );
};
