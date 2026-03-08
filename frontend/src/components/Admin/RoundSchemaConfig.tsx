/**
 * Round Schema Configuration Component (ADMIN)
 * Central server creates and locks the governance contract for federated rounds
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CanonicalField {
  id: number;
  field_name: string;
  expected_data_type: string;
  description: string;
}

interface RoundSchemaConfigProps {
  roundId: number;
  onSchemaCreated: (schema: any) => void;
  onError: (error: string) => void;
}

export const RoundSchemaConfig: React.FC<RoundSchemaConfigProps> = ({
  roundId,
  onSchemaCreated,
  onError
}) => {
  const [modelArchitecture, setModelArchitecture] = useState<'ML_REGRESSION' | 'TFT'>('ML_REGRESSION');
  const [targetColumn, setTargetColumn] = useState('');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [canonicalFields, setCanonicalFields] = useState<CanonicalField[]>([]);
  const [lookback, setLookback] = useState(7);
  const [horizon, setHorizon] = useState(1);
  const [minSamples, setMinSamples] = useState(100);
  const [maxMissingRate, setMaxMissingRate] = useState(0.05);
  const [loading, setLoading] = useState(false);
  const [fieldsLoading, setFieldsLoading] = useState(true);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    fetchCanonicalFields();
  }, []);

  const fetchCanonicalFields = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/canonical-fields`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCanonicalFields(response.data.canonical_fields || []);
    } catch (err) {
      onError('Failed to load canonical fields');
    } finally {
      setFieldsLoading(false);
    }
  };

  const handleFeatureToggle = (fieldName: string) => {
    setSelectedFeatures(prev =>
      prev.includes(fieldName)
        ? prev.filter(f => f !== fieldName)
        : [...prev, fieldName]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!targetColumn) {
      onError('Target column is required');
      return;
    }

    if (selectedFeatures.length === 0) {
      onError('At least one feature is required');
      return;
    }

    if (selectedFeatures.includes(targetColumn)) {
      onError('Target column cannot be in feature list');
      return;
    }

    if (modelArchitecture === 'TFT') {
      if (lookback < 1 || horizon < 1) {
        onError('Lookback and horizon must be >= 1');
        return;
      }
    }

    setLoading(true);
    try {
      // Build feature_types mapping
      const featureTypes: Record<string, string> = {};
      selectedFeatures.forEach(field => {
        const fieldDef = canonicalFields.find(f => f.field_name === field);
        if (fieldDef) {
          featureTypes[field] = fieldDef.expected_data_type;
        }
      });

      // Add target type
      const targetFieldDef = canonicalFields.find(f => f.field_name === targetColumn);
      const targetType = targetFieldDef?.expected_data_type || 'float';

      const response = await axios.post(
        `${API_URL}/api/rounds/${roundId}/schema`,
        {
          model_architecture: modelArchitecture,
          target_column: targetColumn,
          feature_schema: selectedFeatures,
          feature_types: featureTypes,
          sequence_required: modelArchitecture === 'TFT',
          lookback: modelArchitecture === 'TFT' ? lookback : undefined,
          horizon: modelArchitecture === 'TFT' ? horizon : undefined,
          validation_rules: {
            min_samples: minSamples,
            max_missing_rate: maxMissingRate
          }
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      onSchemaCreated(response.data);
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to create schema');
    } finally {
      setLoading(false);
    }
  };

  if (fieldsLoading) {
    return <div className="text-center py-4">Loading canonical fields...</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-2 text-red-600">ADMIN: Create Round Schema</h2>
      <p className="text-sm text-gray-600 mb-4">
        🔐 This schema will lock the training configuration for all hospitals in this round.
        Once created, hospitals cannot modify target, features, or architecture.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
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
                checked={modelArchitecture === 'ML_REGRESSION'}
                onChange={(e) => setModelArchitecture('ML_REGRESSION')}
                className="mr-2"
              />
              <span className="text-sm">ML Regression</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="architecture"
                value="TFT"
                checked={modelArchitecture === 'TFT'}
                onChange={(e) => setModelArchitecture('TFT')}
                className="mr-2"
              />
              <span className="text-sm">TFT (Time Series)</span>
            </label>
          </div>
        </div>

        {/* Target Column Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Column (Locked for hospitals)
          </label>
          <select
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-red-50 border-red-200"
          >
            <option value="">-- Select target --</option>
            {canonicalFields.map(field => (
              <option key={field.id} value={field.field_name}>
                {field.field_name} ({field.expected_data_type})
              </option>
            ))}
          </select>
        </div>

        {/* Feature Schema Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Feature Schema ({selectedFeatures.length} selected - Locked for hospitals)
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border border-gray-300 p-3 rounded bg-red-50">
            {canonicalFields
              .filter(f => f.field_name !== targetColumn)
              .map(field => (
                <label key={field.id} className="flex items-start">
                  <input
                    type="checkbox"
                    checked={selectedFeatures.includes(field.field_name)}
                    onChange={() => handleFeatureToggle(field.field_name)}
                    className="mr-2 mt-1"
                  />
                  <div className="text-sm">
                    <div className="font-medium">{field.field_name}</div>
                    <div className="text-xs text-gray-600">{field.expected_data_type}</div>
                  </div>
                </label>
              ))}
          </div>
        </div>

        {/* TFT Parameters */}
        {modelArchitecture === 'TFT' && (
          <div className="grid grid-cols-2 gap-3 p-3 bg-blue-50 rounded border border-blue-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lookback (Locked)
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
                Horizon (Locked)
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

        {/* Validation Rules */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Validation Rules (Optional)
          </label>
          <div className="grid grid-cols-2 gap-3 p-3 bg-gray-50 rounded">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Min Samples
              </label>
              <input
                type="number"
                min="1"
                value={minSamples}
                onChange={(e) => setMinSamples(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Max Missing Rate
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={maxMissingRate}
                onChange={(e) => setMaxMissingRate(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-md text-white font-bold transition ${
            loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-600 hover:bg-red-700'
          }`}
        >
          {loading ? 'Creating Schema...' : '🔒 Lock Round Schema'}
        </button>

        <p className="text-xs text-gray-600 text-center mt-3">
          ⚠️ Once created, this schema is immutable. Hospitals must match it to participate.
        </p>
      </form>
    </div>
  );
};
