import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import predictionService from '../services/predictionService';
import trainingService from '../services/trainingService';
import { ForecastResponse } from '../types/predictions';
import { TrainedModel } from '../types/training';
import { formatErrorMessage } from '../utils/errorMessage';

const STANDARD_HORIZONS = ['6h', '12h', '24h', '48h', '72h', '168h'];

const PredictionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [models, setModels] = useState<TrainedModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<number | null>(null);
  const [forecastHorizon, setForecastHorizon] = useState(24);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchModels();
  }, [navigate]);

  const fetchModels = async () => {
    try {
      const modelsData = await trainingService.getModels();
      setModels(modelsData);
      if (modelsData.length > 0) {
        setSelectedModel(modelsData[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const handleGenerateForecast = async () => {
    if (!selectedModel) {
      setError('Please select a model');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await predictionService.generateForecast({
        model_id: selectedModel,
        forecast_horizon: forecastHorizon
      });
      setForecast(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Forecast generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ConsoleLayout title="Prediction Dashboard" subtitle="Forecast generation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Resource Demand Forecasting
        </h2>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Generate Forecast</h3>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {formatErrorMessage(error)}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Model
              </label>
              <select
                value={selectedModel || ''}
                onChange={(e) => setSelectedModel(parseInt(e.target.value))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Choose model...</option>
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    Model #{model.id} - {model.model_type} (Round {model.round_number})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Forecast Horizon (hours)
              </label>
              <input
                type="number"
                value={forecastHorizon}
                onChange={(e) => setForecastHorizon(parseInt(e.target.value))}
                min="1"
                max="168"
                className="block w-full px-3 py-2 border border-gray-300 rounded-md"
              />
              <p className="text-xs text-gray-500 mt-1">Standard horizons: 6h, 12h, 24h, 48h, 72h, 168h</p>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleGenerateForecast}
                disabled={loading || !selectedModel}
                className="w-full bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate Forecast'}
              </button>
            </div>
          </div>
        </div>

        {forecast && (
          <>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Forecast Quality Metrics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Target Variable</p>
                  <p className="text-lg font-bold">{forecast.target_variable}</p>
                </div>
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">MAPE</p>
                  <p className={`text-lg font-bold ${predictionService.getQualityColor(forecast.quality_metrics.mape)}`}>
                    {predictionService.formatMAPE(forecast.quality_metrics.mape)}
                  </p>
                </div>
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Bias</p>
                  <p className="text-lg font-bold">
                    {forecast.quality_metrics.bias?.toFixed(2) || 'N/A'}
                  </p>
                </div>
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Trend Alignment</p>
                  <p className="text-lg font-bold text-blue-600">
                    {forecast.quality_metrics.trend_alignment?.toFixed(2) || 'N/A'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Multi-Horizon Forecasts</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {forecast.horizon_forecasts &&
                  STANDARD_HORIZONS.map((key) => {
                    const point = forecast.horizon_forecasts?.[key];
                    if (!point) return null;
                  return (
                    <div key={key} className="border rounded p-4">
                      <p className="text-sm text-gray-600">Horizon</p>
                      <p className="text-lg font-bold">{key}</p>
                      <p className="text-sm text-gray-600 mt-2">Prediction</p>
                      <p className="text-lg font-semibold">
                        {point ? point.prediction.toFixed(2) : 'N/A'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        95% CI: {point ? point.lower_bound.toFixed(2) : 'N/A'} - {point ? point.upper_bound.toFixed(2) : 'N/A'}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-semibold">Detailed Forecast</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hours Ahead</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prediction</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">95% CI Lower</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">95% CI Upper</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {forecast.forecasts?.map((point, idx) => (
                      <tr key={idx}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(point.timestamp).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {point.hour_ahead}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {point.prediction.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {point.lower_bound.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {point.upper_bound.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default PredictionDashboard;
