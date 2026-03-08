/**
 * ML Prediction Component
 * STRICTLY for ML_REGRESSION models - single-point predictions
 * NO TFT logic - completely separate from time-series forecasting
 */
import React, { useState, useEffect } from 'react';
import { BarChart } from './Charts/BarChart';
import mlPredictionService, {
  MLPredictionRequest,
  MLPredictionResponse,
  MLModelMetadataResponse
} from '../services/mlPredictionService';
import { formatErrorMessage } from '../utils/errorMessage';

interface MLPredictionProps {
  model: any;  // Model from model list (MUST be ML_REGRESSION)
  onPredictionComplete?: (result: MLPredictionResponse) => void;
}

const MLPrediction: React.FC<MLPredictionProps> = ({ model, onPredictionComplete }) => {
  const resolvedModelId = model?.id ?? model?.model_id;
  const [features, setFeatures] = useState<Record<string, number>>({});
  const [prediction, setPrediction] = useState<MLPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requiredFeatures, setRequiredFeatures] = useState<string[]>([]);
  const [baseFeatures, setBaseFeatures] = useState<string[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);
  const [metadata, setMetadata] = useState<MLModelMetadataResponse | null>(null);
  const [metadataLoading, setMetadataLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>("");

  useEffect(() => {
    let isActive = true;

    const loadMetadata = async () => {
      setMetadataLoading(true);
      setError(null);
      let debug = "";

      try {
        if (!resolvedModelId) {
          throw new Error('Invalid model selection: missing model ID. Please reselect a model.');
        }

        debug += `[MLPrediction] Fetching model metadata for model_id=${resolvedModelId}\n`;
        console.log('[MLPrediction] Fetching model metadata', { modelId: resolvedModelId });
        
        const response = await mlPredictionService.getModelMetadata(resolvedModelId);
        if (!isActive) return;

        debug += `[MLPrediction] Metadata response received:\n`;
        debug += `  Architecture: ${response.model_architecture}\n`;
        debug += `  Training Type: ${response.training_type}\n`;
        debug += `  Target: ${response.target_column}\n`;
        debug += `  Feature Count: ${response.trained_feature_columns?.length || 0}\n`;
        debug += `  Features: ${JSON.stringify(response.trained_feature_columns)}\n`;

        console.log('[MLPrediction] Metadata response:', response);
        
        setMetadata(response);

        const features = response.trained_feature_columns || [];
        setRequiredFeatures(features);
        
        // Extract base features (remove lag and rollmean derived features)
        const extractBaseFeatures = (allFeatures: string[]): string[] => {
          const baseSet = new Set<string>();
          allFeatures.forEach(feature => {
            // Remove _lag_N suffix
            if (feature.includes('_lag_')) {
              const base = feature.split('_lag_')[0];
              baseSet.add(base);
            }
            // Remove _rollmean_N suffix
            else if (feature.includes('_rollmean_')) {
              const base = feature.split('_rollmean_')[0];
              baseSet.add(base);
            }
            // Otherwise it's a base feature
            else {
              baseSet.add(feature);
            }
          });
          return Array.from(baseSet).sort();
        };
        
        const bases = extractBaseFeatures(features);
        setBaseFeatures(bases);
        
        debug += `\n[VALIDATION] Feature validation:\n`;
        debug += `  Required: ${features.length} features (including derived)\n`;
        debug += `  Base features: ${bases.length}\n`;
        debug += `  Base feature names: ${bases.join(', ')}\n`;
        debug += `  Target in features: ${response.target_column && features.includes(response.target_column) ? 'YES (BUG!)' : 'NO (OK)'}\n`;

        // ✅ CRITICAL: Validate that target is NOT in features
        if (response.target_column && features.includes(response.target_column)) {
          debug += `\n[ERROR] TARGET COLUMN IN FEATURES LIST - ARCHITECTURE BUG!\n`;
          console.error('[MLPrediction] BUG: Target column in features list!', {
            target: response.target_column,
            features: features
          });
        }

        // Initialize only base features with zeros
        const initialFeatures: Record<string, number> = {};
        bases.forEach(feature => {
          initialFeatures[feature] = 0;
        });
        setFeatures(initialFeatures);
        
        setDebugInfo(debug);
      } catch (err: any) {
        if (!isActive) return;
        debug += `[ERROR] Metadata fetch failed: ${formatErrorMessage(err, 'Failed to load model metadata')}\n`;
        console.error('[MLPrediction] Metadata fetch failed:', err);
        setMetadata(null);
        setRequiredFeatures([]);
        setBaseFeatures([]);
        setFeatures({});
        setError(formatErrorMessage(err, 'Failed to load model metadata'));
        setDebugInfo(debug);
      } finally {
        if (isActive) setMetadataLoading(false);
      }
    };

    if (resolvedModelId) {
      loadMetadata();
    }

    return () => {
      isActive = false;
    };
  }, [model, resolvedModelId]);

  const handleFeatureChange = (featureName: string, value: string) => {
    const numValue = parseFloat(value) || 0;
    setFeatures(prev => ({
      ...prev,
      [featureName]: numValue
    }));
    setValidationWarnings([]);  // Clear warnings when user edits
  };

  const validateFeatures = async () => {
    try {
      // Send only base features - backend will auto-generate derived features
      const validation = await mlPredictionService.validateFeatures({
        model_id: resolvedModelId,
        features
      });
      
      if (!validation.can_proceed) {
        setValidationWarnings(validation.warnings);
        
        // Build detailed error message
        let errorMsg = 'Cannot proceed with prediction:\n';
        if (validation.missing_features.length > 0) {
          errorMsg += `\n❌ Missing features: ${validation.missing_features.join(', ')}`;
        }
        if (validation.extra_features.length > 0) {
          errorMsg += `\n⚠️ Extra features (will be ignored): ${validation.extra_features.join(', ')}`;
        }
        if (validation.warnings.length > 0) {
          errorMsg += `\n⚠️ Warnings:\n${validation.warnings.map(w => `  • ${w}`).join('\n')}`;
        }
        
        setError(errorMsg);
        return false;
      }
      
      return true;
    } catch (err: any) {
      const errorMsg = formatErrorMessage(err, 'Validation failed');
      setError(`Validation Error: ${errorMsg}`);
      return false;
    }
  };

  const handlePredict = async () => {
    setError(null);
    setPrediction(null);
    setValidationWarnings([]);
    setLoading(true);
    let debug = "[Predict]";

    try {
      if (!resolvedModelId) {
        setError('Invalid model selection: missing model ID. Please reselect a model.');
        setLoading(false);
        return;
      }

      // Validate features first
      debug += ` Validating features...\n`;
      const isValid = await validateFeatures();
      if (!isValid) {
        setLoading(false);
        return;
      }

      // Make prediction - send only base features, backend auto-generates lag/rollmean
      const request: MLPredictionRequest = {
        model_id: resolvedModelId,
        features  // Only base features, no derived features
      };

      debug += ` Sending prediction request with ${Object.keys(features).length} features\n`;
      console.log('[MLPrediction] Prediction payload:', request);

      const result = await mlPredictionService.predict(request);
      
      debug += ` Prediction successful: ${result.prediction}\n`;
      setPrediction(result);
      
      if (onPredictionComplete) {
        onPredictionComplete(result);
      }
    } catch (err: any) {
      const errorMsg = formatErrorMessage(err, 'Prediction failed');
      debug += ` ERROR: ${errorMsg}\n`;
      setError(errorMsg);
      
      // Additional debug info for feature mismatches
      if (errorMsg.includes('Missing required') || errorMsg.includes('features')) {
        debug += `\n[DEBUG] Provided features: ${Object.keys(features).join(', ')}\n`;
        debug += `[DEBUG] Required features: ${requiredFeatures.join(', ')}\n`;
      }
    } finally {
      setLoading(false);
      setDebugInfo(prev => prev + "\n" + debug);
    }
  };

  const handleSavePrediction = async () => {
    if (!prediction) return;

    if (!resolvedModelId) {
      alert('Invalid model selection: missing model ID. Please reselect a model.');
      return;
    }

    try {
    await mlPredictionService.savePrediction({
      model_id: resolvedModelId,
      features: features,
      dataset_id: model.dataset_id ?? undefined,
      prediction: prediction.prediction,
    });
      
      alert('Prediction saved successfully!');
    } catch (err: any) {
      alert(`Failed to save: ${formatErrorMessage(err, 'Failed to save prediction')}`);
    }
  };

  // Display only base feature input fields
  const featureFields = mlPredictionService.buildFeatureFields(baseFeatures);

  const chartLabels: string[] = [];
  const chartData: number[] = [];

  if (prediction?.model_accuracy) {
    const { r2, rmse, mape, mae } = prediction.model_accuracy;
    if (r2 !== null && r2 !== undefined) {
      chartLabels.push('R2 (%)');
      chartData.push(Number((Math.max(0, r2) * 100).toFixed(2)));
    }
    if (rmse !== null && rmse !== undefined) {
      chartLabels.push('RMSE');
      chartData.push(Number(rmse.toFixed(2)));
    }
    if (mae !== null && mae !== undefined) {
      chartLabels.push('MAE');
      chartData.push(Number(mae.toFixed(2)));
    }
    if (mape !== null && mape !== undefined) {
      chartLabels.push('MAPE (%)');
      chartData.push(Number(mape.toFixed(2)));
    }
  }

  if (prediction?.confidence_interval) {
    const ci = prediction.confidence_interval;
    chartLabels.push('CI Lower', 'Prediction', 'CI Upper');
    chartData.push(
      Number(ci.lower.toFixed(2)),
      Number(prediction.prediction.toFixed(2)),
      Number(ci.upper.toFixed(2))
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              ML Regression Prediction
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Model: {resolvedModelId ?? 'N/A'} | Target: {metadata?.target_column || model.target_column || model.training_schema?.target_column || 'Unknown'}
            </p>
            <div className="flex gap-2 mt-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                ML_REGRESSION
              </span>
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {model.training_type || 'LOCAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Input Form */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">
          Input Features ({baseFeatures.length} base features)
        </h4>
        <p className="text-xs text-gray-500 mb-4">
          💡 Enter base feature values only. Lag and rolling mean features will be auto-generated.
        </p>
        
        {metadataLoading ? (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">Loading model metadata...</p>
          </div>
        ) : baseFeatures.length === 0 ? (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              ⚠️ No trained feature columns available for this model.
            </p>
            <p className="text-xs text-yellow-700 mt-2">
              Check browser console and server logs for debug information.
            </p>
            {debugInfo && (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs font-mono text-yellow-700">Show Debug</summary>
                <pre className="mt-2 p-2 bg-yellow-100 rounded text-xs overflow-auto">{debugInfo}</pre>
              </details>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {featureFields.map(field => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={features[field.name] || 0}
                    onChange={(e) => handleFeatureChange(field.name, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={`Enter ${field.label}`}
                  />
                </div>
              ))}
            </div>

            {validationWarnings.length > 0 && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm font-medium text-yellow-800 mb-1">Validation Warnings:</p>
                <ul className="list-disc list-inside text-sm text-yellow-700">
                  {validationWarnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        <button
          onClick={handlePredict}
          disabled={loading || baseFeatures.length === 0}
          className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Predicting...' : 'Generate Prediction'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800 font-semibold mb-2">⚠️ Error</p>
          <p className="text-sm text-red-700 whitespace-pre-wrap">{error}</p>
          {baseFeatures.length === 0 && (
            <p className="text-xs text-red-600 mt-2">
              💡 Tip: The model metadata might not be properly loaded. Check browser console for details.
            </p>
          )}
        </div>
      )}

      {/* Prediction Result */}
      {prediction && (
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Prediction Result
          </h4>
          
          {/* Predicted Value */}
          <div className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg text-white">
            <p className="text-sm font-medium opacity-90">Predicted {prediction.target_column}</p>
            <p className="text-4xl font-bold mt-2">
              {mlPredictionService.formatPrediction(prediction.prediction, 2)}
            </p>
            <p className="text-xs opacity-75 mt-2">
              Single-point regression estimate
            </p>
          </div>

          {/* AI Analysis */}
          {prediction.ai_summary && (
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border-2 border-blue-200">
              <h4 className="font-semibold text-gray-900 mb-2">🤖 AI Analysis</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {prediction.ai_summary}
              </p>
              <div className="mt-3 text-xs text-gray-500">Generated by Gemini AI</div>
            </div>
          )}

          {/* Graphical Analysis */}
          {chartLabels.length > 0 && (
            <div>
              <BarChart
                title="Graphical Analysis"
                labels={chartLabels}
                datasets={[
                  {
                    label: 'Prediction Insights',
                    data: chartData,
                    backgroundColor: '#3b82f6',
                    borderColor: '#2563eb'
                  }
                ]}
                yAxisLabel="Value"
                height={280}
              />
            </div>
          )}

          {/* Performance Metrics */}
          {prediction.model_accuracy && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-900">📊 Performance Metrics</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {prediction.model_accuracy.r2 !== null && prediction.model_accuracy.r2 !== undefined && (
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                    <label className="block text-xs font-medium text-gray-700">R² Score</label>
                    <p className="mt-2 text-2xl font-bold text-blue-600">
                      {(Math.max(0, prediction.model_accuracy.r2) * 100).toFixed(1)}%
                    </p>
                    {prediction.model_accuracy.r2 < 0 && (
                      <p className="mt-1 text-xs text-blue-500">Below baseline</p>
                    )}
                  </div>
                )}
                {prediction.model_accuracy.rmse !== null && prediction.model_accuracy.rmse !== undefined && (
                  <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                    <label className="block text-xs font-medium text-gray-700">RMSE</label>
                    <p className="mt-2 text-2xl font-bold text-green-600">
                      {prediction.model_accuracy.rmse.toFixed(4)}
                    </p>
                    <p className="text-xs text-green-600 mt-1">Lower is better</p>
                  </div>
                )}
                {prediction.model_accuracy.mape !== null && prediction.model_accuracy.mape !== undefined && prediction.model_accuracy.mape > 0 && (
                  <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
                    <label className="block text-xs font-medium text-gray-700">MAPE (%)</label>
                    <p className="mt-2 text-2xl font-bold text-yellow-600">
                      {prediction.model_accuracy.mape.toFixed(2)}
                    </p>
                    <p className="mt-1 text-xs text-yellow-600">
                      {prediction.model_accuracy.mape <= 10 ? '✓ Excellent' : prediction.model_accuracy.mape <= 20 ? '✓ Good' : '⚠ Moderate'}
                    </p>
                  </div>
                )}
                {prediction.model_accuracy.mae !== null && prediction.model_accuracy.mae !== undefined && (
                  <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
                    <label className="block text-xs font-medium text-gray-700">MAE</label>
                    <p className="mt-2 text-2xl font-bold text-orange-600">
                      {prediction.model_accuracy.mae.toFixed(4)}
                    </p>
                    <p className="text-xs text-orange-600 mt-1">Avg error</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Confidence Interval */}
          {prediction.confidence_interval && prediction.confidence_interval.lower !== undefined && (
            <div className="bg-cyan-50 border border-cyan-200 p-4 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">📏 95% Confidence Interval</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-gray-600">Lower Bound</p>
                  <p className="mt-1 text-lg font-bold text-cyan-700">{prediction.confidence_interval.lower.toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Predicted Value</p>
                  <p className="mt-1 text-lg font-bold text-blue-700">{mlPredictionService.formatPrediction(prediction.prediction, 4)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Upper Bound</p>
                  <p className="mt-1 text-lg font-bold text-cyan-700">{prediction.confidence_interval.upper.toFixed(4)}</p>
                </div>
              </div>
              <p className="text-xs text-cyan-600 mt-3">
                Margin of Error: ±{prediction.confidence_interval.margin_of_error?.toFixed(4)}
              </p>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600">Model ID</p>
              <p className="text-sm font-medium text-gray-900">{prediction.model_id}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600">Training Type</p>
              <p className="text-sm font-medium text-gray-900">{prediction.training_type}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600">Features Used</p>
              <p className="text-sm font-medium text-gray-900">{prediction.feature_count}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600">Timestamp</p>
              <p className="text-sm font-medium text-gray-900">
                {new Date(prediction.timestamp).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Input Features Summary */}
          <div className="p-4 bg-gray-50 rounded-md">
            <p className="text-sm font-medium text-gray-900 mb-2">Input Features:</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {Object.entries(prediction.input_features).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600">{key}:</span>
                  <span className="font-medium text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <button
            onClick={handleSavePrediction}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
          >
            Save Prediction
          </button>
        </div>
      )}

      {/* Debug Panel */}
      {debugInfo && (
        <details className="bg-gray-100 rounded p-4">
          <summary className="cursor-pointer font-mono text-xs text-gray-700 font-semibold">Debug Console</summary>
          <pre className="mt-3 p-3 bg-black text-green-400 rounded font-mono text-xs overflow-auto max-h-32">
            {debugInfo}
          </pre>
        </details>
      )}
    </div>
  );
};

export default MLPrediction;
