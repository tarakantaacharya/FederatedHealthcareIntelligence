/**
 * Multi-Model Comparison Table
 * Shows all candidate models, metrics, and which one was selected
 */

import React from 'react';

interface ModelMetrics {
  r2: number;
  rmse: number;
  mae: number;
  mape: number;
}

interface MultiModelComparisonProps {
  candidateModels: string[];
  bestModel: string;
  metrics: Record<string, ModelMetrics>;
  selectionStrategy: string;
  ensembleModels?: string[];
}

export const MultiModelComparison: React.FC<MultiModelComparisonProps> = ({
  candidateModels,
  bestModel,
  metrics,
  selectionStrategy,
  ensembleModels = []
}) => {
  const modelOrder = [...candidateModels].sort(
    (a, b) => (metrics[b]?.r2 || 0) - (metrics[a]?.r2 || 0)
  );

  const getModelBadge = (modelName: string) => {
    if (modelName === bestModel) {
      return (
        <span className="ml-2 bg-gold px-2 py-1 rounded-full text-xs font-bold text-white">
          ⭐ SELECTED
        </span>
      );
    }
    if (ensembleModels.includes(modelName)) {
      return (
        <span className="ml-2 bg-purple-500 px-2 py-1 rounded-full text-xs font-bold text-white">
          📊 ENSEMBLE
        </span>
      );
    }
    return null;
  };

  const getModelColor = (modelName: string): string => {
    const modelColors: Record<string, string> = {
      linear: 'bg-blue-50',
      random_forest: 'bg-green-50',
      gradient_boosting: 'bg-yellow-50',
      ridge: 'bg-purple-50',
      lasso: 'bg-pink-50',
      xgboost: 'bg-orange-50'
    };
    return modelColors[modelName] || 'bg-gray-50';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-800">Multi-Model Training Results</h2>
        <p className="text-sm text-gray-600">
          Selection Strategy: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{selectionStrategy}</span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b-2 border-gray-300">
              <th className="text-left p-3 font-bold text-gray-700">Model</th>
              <th className="text-center p-3 font-bold text-gray-700">R²</th>
              <th className="text-center p-3 font-bold text-gray-700">RMSE</th>
              <th className="text-center p-3 font-bold text-gray-700">MAE</th>
              <th className="text-center p-3 font-bold text-gray-700">MAPE (%)</th>
              <th className="text-center p-3 font-bold text-gray-700">Status</th>
            </tr>
          </thead>
          <tbody>
            {modelOrder.map((modelName, idx) => {
              const m = metrics[modelName];
              if (!m) return null;

              return (
                <tr
                  key={modelName}
                  className={`${getModelColor(modelName)} border-b border-gray-200 hover:opacity-75 transition`}
                >
                  <td className="p-3 font-medium text-gray-800">
                    {modelName.replace('_', ' ').toUpperCase()}
                    {getModelBadge(modelName)}
                  </td>
                  <td className="p-3 text-center">
                    <span className="font-bold text-lg">{m.r2.toFixed(4)}</span>
                  </td>
                  <td className="p-3 text-center">{m.rmse.toFixed(4)}</td>
                  <td className="p-3 text-center">{m.mae.toFixed(4)}</td>
                  <td className="p-3 text-center">{m.mape.toFixed(2)}</td>
                  <td className="p-3 text-center">
                    {modelName === bestModel && '🥇 Best'}
                    {ensembleModels.includes(modelName) && modelName !== bestModel && '📊 Ensemble'}
                    {!candidateModels.includes(modelName) && ''}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <p className="text-sm text-gray-600">Best Model</p>
          <p className="text-lg font-bold text-green-700">
            {bestModel.replace('_', ' ').toUpperCase()}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            R² = {metrics[bestModel]?.r2.toFixed(4)}
          </p>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <p className="text-sm text-gray-600">Total Models</p>
          <p className="text-lg font-bold text-purple-700">{candidateModels.length}</p>
          <p className="text-xs text-gray-600 mt-1">
            Ensemble: {ensembleModels.length || 'Not used'}
          </p>
        </div>
      </div>

      {/* Feature Importance Hint */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200 text-sm">
        <p className="text-gray-700">
          💡 The selected model has been saved with all feature information. Use it for predictions!
        </p>
      </div>
    </div>
  );
};
