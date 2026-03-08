/**
 * TFT Forecast Component
 * STRICTLY for TFT models - multi-horizon time-series forecasting
 * NO ML_REGRESSION logic
 */
import React, { useState } from 'react';
import tftForecastService from '../services/tftForecastService';
import type {
  TFTForecastRequest,
  TFTForecastResponse
} from '../services/tftForecastService';
import { formatErrorMessage } from '../utils/errorMessage';

interface TFTForecastProps {
  model: any;  // Model from model list (MUST be TFT)
  onForecastComplete?: (result: TFTForecastResponse) => void;
}

const TFTForecast: React.FC<TFTForecastProps> = ({ model, onForecastComplete }) => {
  const resolvedModelId = model?.id ?? model?.model_id;
  const [predictionLength, setPredictionLength] = useState<number>(72);
  const [forecast, setForecast] = useState<TFTForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState<string | null>(null);

  const handleForecast = async () => {
    setError(null);
    setForecast(null);
    setSelectedHorizon(null);
    setLoading(true);

    try {
      if (!resolvedModelId) {
        setError('Invalid model selection: missing model ID. Please reselect a model.');
        setLoading(false);
        return;
      }

      const request: TFTForecastRequest = {
        model_id: resolvedModelId,
        prediction_length: predictionLength
      };

      const result = await tftForecastService.forecast(request);
      setForecast(result);
      
      // Set default selected horizon to first available
      const horizonKeys = tftForecastService.getHorizonKeys(result.horizons);
      if (horizonKeys.length > 0) {
        setSelectedHorizon(horizonKeys[0]);
      } else {
        setError('No forecast horizons available in response');
      }
      
      if (onForecastComplete) {
        onForecastComplete(result);
      }
    } catch (err: any) {
      setError(formatErrorMessage(err, 'Forecasting failed'));
      setForecast(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveForecast = async () => {
    if (!forecast) return;

    if (!resolvedModelId) {
      alert('Invalid model selection: missing model ID. Please reselect a model.');
      return;
    }

    try {
      await tftForecastService.saveForecast({
        model_id: resolvedModelId,
        dataset_id: forecast.used_dataset_id ?? model.dataset_id,
        forecast_data: forecast,
        prediction_length: predictionLength
      });
      
      alert('Forecast saved successfully!');
    } catch (err: any) {
      alert(`Failed to save: ${formatErrorMessage(err, 'Failed to save forecast')}`);
    }
  };

  const horizonKeys = forecast ? tftForecastService.getHorizonKeys(forecast.horizons) : [];
  const selectedHorizonData = selectedHorizon && forecast ? forecast.horizons[selectedHorizon] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              TFT Multi-Horizon Forecast
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Model: {resolvedModelId ?? 'N/A'} | Target: {model.target_column || model.training_schema?.target_column || 'Unknown'}
            </p>
            <div className="flex gap-2 mt-2">
              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                TFT
              </span>
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {model.training_type || 'FEDERATED'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Forecast Configuration */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">
          Forecast Configuration
        </h4>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prediction Horizon (hours)
            </label>
            <select
              value={predictionLength}
              onChange={(e) => setPredictionLength(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value={6}>6 hours</option>
              <option value={12}>12 hours</option>
              <option value={24}>24 hours</option>
              <option value={48}>48 hours</option>
              <option value={72}>72 hours (3 days)</option>
              <option value={168}>168 hours (7 days)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Select maximum forecast horizon. Model will generate predictions for multiple time points.
            </p>
          </div>

          <button
            onClick={handleForecast}
            disabled={loading}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Generating Forecast...' : 'Generate Multi-Horizon Forecast'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Forecast Results */}
      {forecast && (
        <div className="space-y-6">
          {/* Horizon Tabs */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h4 className="text-md font-semibold text-gray-900 mb-4">
              Forecast Horizons
            </h4>
            
            <div className="flex flex-wrap gap-2 mb-6">
              {horizonKeys.map(horizon => (
                <button
                  key={horizon}
                  onClick={() => setSelectedHorizon(horizon)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedHorizon === horizon
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {horizon}
                </button>
              ))}
            </div>

            {/* Selected Horizon Details */}
            {selectedHorizonData && (
              <div className="space-y-4">
                {/* Forecast Value with Confidence Band */}
                <div className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg text-white">
                  <p className="text-sm font-medium opacity-90">
                    {selectedHorizon} Forecast - {forecast.target_column}
                  </p>
                  <p className="text-4xl font-bold mt-2">
                    {tftForecastService.formatForecast(selectedHorizonData.p50, 2)}
                  </p>
                  <p className="text-xs opacity-75 mt-2">
                    Median prediction (P50) at {selectedHorizon} ahead
                  </p>
                </div>

                {/* Confidence Interval */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600 mb-1">Lower Bound (P10)</p>
                    <p className="text-xl font-bold text-gray-900">
                      {tftForecastService.formatForecast(selectedHorizonData.p10, 2)}
                    </p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-md">
                    <p className="text-xs text-purple-600 mb-1">Median (P50)</p>
                    <p className="text-xl font-bold text-purple-900">
                      {tftForecastService.formatForecast(selectedHorizonData.p50, 2)}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600 mb-1">Upper Bound (P90)</p>
                    <p className="text-xl font-bold text-gray-900">
                      {tftForecastService.formatForecast(selectedHorizonData.p90, 2)}
                    </p>
                  </div>
                </div>

                {/* Horizon Metadata */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600">Forecast Timestamp</p>
                    <p className="text-sm font-medium text-gray-900">
                      {new Date(selectedHorizonData.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600">Confidence Level</p>
                    <p className="text-sm font-medium text-gray-900">
                      {(selectedHorizonData.confidence_level * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quality Metrics */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h4 className="text-md font-semibold text-gray-900 mb-4">
              Forecast Quality Metrics
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-md">
                <p className="text-sm text-gray-700 mb-1">MAPE</p>
                <p className={`text-2xl font-bold ${tftForecastService.getQualityColor(forecast.quality_metrics.mape)}`}>
                  {tftForecastService.formatMAPE(forecast.quality_metrics.mape)}
                </p>
                <p className="text-xs text-gray-600 mt-1">Mean Absolute % Error</p>
              </div>
              
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-md">
                <p className="text-sm text-gray-700 mb-1">Bias</p>
                <p className="text-2xl font-bold text-blue-900">
                  {forecast.quality_metrics.bias.toFixed(2)}
                </p>
                <p className="text-xs text-gray-600 mt-1">Forecast bias</p>
              </div>
              
              <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-md">
                <p className="text-sm text-gray-700 mb-1">Trend Alignment</p>
                <p className="text-2xl font-bold text-purple-900">
                  {(forecast.quality_metrics.trend_alignment * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-gray-600 mt-1">Trend correlation</p>
              </div>
            </div>
          </div>

          {/* Forecast Sequence Summary */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h4 className="text-md font-semibold text-gray-900 mb-4">
              Complete Forecast Sequence
            </h4>
            
            <div className="p-4 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700 mb-2">
                Forecast includes {forecast.forecast_sequence.length} time points:
              </p>
              <div className="flex flex-wrap gap-2">
                {forecast.forecast_sequence.slice(0, 10).map((value, idx) => (
                  <span key={idx} className="px-2 py-1 bg-white rounded text-xs font-medium">
                    {tftForecastService.formatForecast(value, 1)}
                  </span>
                ))}
                {forecast.forecast_sequence.length > 10 && (
                  <span className="px-2 py-1 text-xs text-gray-500">
                    ... and {forecast.forecast_sequence.length - 10} more
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <button
            onClick={handleSaveForecast}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
          >
            Save Forecast
          </button>
        </div>
      )}
    </div>
  );
};

export default TFTForecast;
