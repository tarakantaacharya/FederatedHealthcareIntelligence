import React, { useState, useEffect } from 'react';
import tftForecastService, { TFTForecastResponse, TFTForecastRequest } from '../services/tftForecastService';
import mlPredictionService, { MLPredictionResponse, MLPredictionRequest } from '../services/mlPredictionService';
import trainingService from '../services/trainingService';
import { BarChart } from './Charts/BarChart';

const PredictionsPanel: React.FC = () => {
  const [models, setModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [modelType, setModelType] = useState<'TFT' | 'ML_REGRESSION'>('TFT');
  
  const [tftForecast, setTftForecast] = useState<TFTForecastResponse | null>(null);
  const [mlPrediction, setMlPrediction] = useState<MLPredictionResponse | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [mlFeatures, setMlFeatures] = useState<Record<string, number>>({});
  const [predictionLength, setPredictionLength] = useState(72);

  const mlChartLabels: string[] = [];
  const mlChartValues: number[] = [];

  if (mlPrediction?.model_accuracy) {
    const { r2, rmse, mape, mae } = mlPrediction.model_accuracy;
    if (r2 !== null && r2 !== undefined) {
      mlChartLabels.push('R2 (%)');
      mlChartValues.push(Number((Math.max(0, r2) * 100).toFixed(2)));
    }
    if (rmse !== null && rmse !== undefined) {
      mlChartLabels.push('RMSE');
      mlChartValues.push(Number(rmse.toFixed(2)));
    }
    if (mae !== null && mae !== undefined) {
      mlChartLabels.push('MAE');
      mlChartValues.push(Number(mae.toFixed(2)));
    }
    if (mape !== null && mape !== undefined) {
      mlChartLabels.push('MAPE (%)');
      mlChartValues.push(Number(mape.toFixed(2)));
    }
  }

  if (mlPrediction?.confidence_interval) {
    mlChartLabels.push('CI Lower', 'Prediction', 'CI Upper');
    mlChartValues.push(
      Number(mlPrediction.confidence_interval.lower.toFixed(2)),
      Number(mlPrediction.prediction.toFixed(2)),
      Number(mlPrediction.confidence_interval.upper.toFixed(2))
    );
  }

  // Load models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const modelsData = await trainingService.getModels();
        setModels(modelsData);
        if (modelsData.length > 0) {
          setSelectedModel(modelsData[0]);
          const arch = modelsData[0].model_architecture as 'TFT' | 'ML_REGRESSION' || 'TFT';
          setModelType(arch);
        }
      } catch (err) {
        console.error('Error loading models:', err);
      }
    };
    loadModels();
  }, []);

  // Generate TFT forecast
  const handleGenerateTftForecast = async () => {
    if (!selectedModel) {
      setError('No model selected');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const request: TFTForecastRequest = {
        model_id: selectedModel.id,
        prediction_length: predictionLength,
        encoder_sequence: undefined  // Use dataset data
      };

      const result = await tftForecastService.forecast(request);
      setTftForecast(result);
      setSuccess('Forecast generated successfully');
      
      // Auto-save
      await tftForecastService.saveForecast({
        model_id: selectedModel.id,
        forecast_data: result.horizons,
        prediction_length: predictionLength,
        dataset_id: selectedModel.dataset_id
      });
      setSuccess('Forecast generated and saved');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  // Generate ML prediction
  const handleGenerateMlPrediction = async () => {
    if (!selectedModel) {
      setError('No model selected');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const request: MLPredictionRequest = {
        model_id: selectedModel.id,
        features: mlFeatures
      };

      const result = await mlPredictionService.predict(request);
      setMlPrediction(result);
      setSuccess('Prediction generated successfully');
      
      // Auto-save
      await mlPredictionService.savePrediction({
        model_id: selectedModel.id,
        features: mlFeatures,
        prediction: result.prediction,
        dataset_id: selectedModel.dataset_id
      });
      setSuccess('Prediction generated and saved');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate prediction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Generate Predictions</h2>

      {/* Model Selection */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <label className="block text-sm font-semibold mb-2">Select Model:</label>
        <select
          value={selectedModel?.id || ''}
          onChange={(e) => {
            const model = models.find(m => m.id === parseInt(e.target.value));
            setSelectedModel(model);
            if (model?.model_architecture) setModelType(model.model_architecture);
          }}
          className="w-full px-3 py-2 border rounded-lg"
        >
          <option value="">Choose a model...</option>
          {models.map(model => (
            <option key={model.id} value={model.id}>
              {model.id} - {model.model_architecture || 'Unknown'} ({model.training_type})
            </option>
          ))}
        </select>
      </div>

      {/* TFT Forecasting */}
      {modelType === 'TFT' && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-bold mb-3 text-blue-900">TFT Time-Series Forecast</h3>
          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Prediction Length (hours):</label>
            <input
              type="number"
              value={predictionLength}
              onChange={(e) => setPredictionLength(parseInt(e.target.value))}
              min="6"
              max="168"
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <button
            onClick={handleGenerateTftForecast}
            disabled={loading || !selectedModel}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg"
          >
            {loading ? 'Generating...' : 'Generate Forecast'}
          </button>

          {tftForecast && (
            <div className="mt-4 p-3 bg-white border-l-4 border-blue-500 rounded">
              <h4 className="font-bold mb-2">Forecast Results:</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(tftForecast.horizons).map(([horizon, data]) => (
                  <div key={horizon} className="p-2 bg-gray-50 rounded">
                    <p className="font-semibold">{horizon}</p>
                    <p className="text-xs">p50: {data.p50.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">
                      [{data.p10.toFixed(2)}, {data.p90.toFixed(2)}]
                    </p>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-2 bg-green-50 rounded text-sm">
                <p><strong>MAPE:</strong> {tftForecast.quality_metrics.mape.toFixed(2)}%</p>
                <p><strong>Trend Alignment:</strong> {tftForecast.quality_metrics.trend_alignment.toFixed(2)}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ML Predictions */}
      {modelType === 'ML_REGRESSION' && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-bold mb-3 text-green-900">ML Regression Prediction</h3>
          <div className="mb-4">
            <label className="block text-sm font-semibold mb-2">Input Features:</label>
            <div className="space-y-2">
              {selectedModel?.features?.map((feature: string) => (
                <div key={feature}>
                  <label className="text-sm text-gray-600">{feature}:</label>
                  <input
                    type="number"
                    value={mlFeatures[feature] || ''}
                    onChange={(e) => setMlFeatures({ ...mlFeatures, [feature]: parseFloat(e.target.value) })}
                    placeholder={`Enter ${feature}`}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={handleGenerateMlPrediction}
            disabled={loading || !selectedModel}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg"
          >
            {loading ? 'Predicting...' : 'Generate Prediction'}
          </button>

          {mlPrediction && (
            <div className="mt-4 space-y-4">
              <div className="p-4 bg-white border-l-4 border-green-500 rounded">
                <h4 className="font-bold mb-2">Prediction Result:</h4>
                <p className="text-2xl font-bold text-green-600">{mlPrediction.prediction.toFixed(2)}</p>
                <p className="text-xs text-gray-600 mt-2">Target: {mlPrediction.target_column}</p>
              </div>

              {mlPrediction.ai_summary && (
                <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded">
                  <h4 className="font-bold mb-2 text-blue-900">AI Analysis</h4>
                  <p className="text-sm text-blue-800 whitespace-pre-wrap">{mlPrediction.ai_summary}</p>
                </div>
              )}

              {mlPrediction.model_accuracy && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {mlPrediction.model_accuracy.r2 !== null && mlPrediction.model_accuracy.r2 !== undefined && (
                    <div className="p-3 bg-blue-50 rounded border border-blue-100">
                      <p className="text-xs text-gray-600">R2 Score</p>
                      <p className="text-lg font-bold text-blue-700">{(Math.max(0, mlPrediction.model_accuracy.r2) * 100).toFixed(1)}%</p>
                    </div>
                  )}
                  {mlPrediction.model_accuracy.rmse !== null && mlPrediction.model_accuracy.rmse !== undefined && (
                    <div className="p-3 bg-green-50 rounded border border-green-100">
                      <p className="text-xs text-gray-600">RMSE</p>
                      <p className="text-lg font-bold text-green-700">{mlPrediction.model_accuracy.rmse.toFixed(4)}</p>
                    </div>
                  )}
                  {mlPrediction.model_accuracy.mape !== null && mlPrediction.model_accuracy.mape !== undefined && (
                    <div className="p-3 bg-yellow-50 rounded border border-yellow-100">
                      <p className="text-xs text-gray-600">MAPE (%)</p>
                      <p className="text-lg font-bold text-yellow-700">{mlPrediction.model_accuracy.mape.toFixed(2)}</p>
                    </div>
                  )}
                  {mlPrediction.model_accuracy.mae !== null && mlPrediction.model_accuracy.mae !== undefined && (
                    <div className="p-3 bg-orange-50 rounded border border-orange-100">
                      <p className="text-xs text-gray-600">MAE</p>
                      <p className="text-lg font-bold text-orange-700">{mlPrediction.model_accuracy.mae.toFixed(4)}</p>
                    </div>
                  )}
                </div>
              )}

              {mlPrediction.confidence_interval && (
                <div className="p-4 bg-cyan-50 border border-cyan-200 rounded">
                  <h4 className="font-bold mb-2 text-cyan-900">95% Confidence Interval</h4>
                  <p className="text-sm text-cyan-800">
                    Lower: {mlPrediction.confidence_interval.lower.toFixed(4)} | 
                    Predicted: {mlPrediction.prediction.toFixed(4)} | 
                    Upper: {mlPrediction.confidence_interval.upper.toFixed(4)}
                  </p>
                </div>
              )}

              {mlChartLabels.length > 0 && (
                <BarChart
                  title="Graph Chart Analysis"
                  labels={mlChartLabels}
                  datasets={[
                    {
                      label: 'ML Prediction Insights',
                      data: mlChartValues,
                      backgroundColor: '#22c55e',
                      borderColor: '#16a34a'
                    }
                  ]}
                  yAxisLabel="Value"
                  height={260}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Status Messages */}
      {error && <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-600 text-red-700">{error}</div>}
      {success && <div className="mt-4 p-3 bg-green-100 border-l-4 border-green-600 text-green-700">{success}</div>}
    </div>
  );
};

export default PredictionsPanel;
