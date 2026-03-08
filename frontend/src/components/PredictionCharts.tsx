import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ForecastPoint {
  timestamp?: string;
  hour_ahead: number;
  prediction: number;
  lower_bound?: number;
  upper_bound?: number;
  confidence_level?: number;
}

interface PredictionChartsProps {
  forecasts: ForecastPoint[];
  metrics?: {
    mape?: number;
    rmse?: number;
    r2?: number;
    mae?: number;
    bias?: number;
    trend_alignment?: number;
  };
  targetColumn?: string;
}

const PredictionCharts: React.FC<PredictionChartsProps> = ({ 
  forecasts, 
  metrics,
  targetColumn = 'Value'
}) => {
  // Forecast Line Chart Data
  const forecastLabels = forecasts.map(f => `${f.hour_ahead}h`);
  const forecastPredictions = forecasts.map(f => f.prediction);
  const forecastLowerBounds = forecasts.map(f => f.lower_bound || f.prediction * 0.95);
  const forecastUpperBounds = forecasts.map(f => f.upper_bound || f.prediction * 1.05);

  const forecastChartData = {
    labels: forecastLabels,
    datasets: [
      {
        label: 'Prediction',
        data: forecastPredictions,
        borderColor: 'rgb(30, 64, 175)',
        backgroundColor: 'rgba(30, 64, 175, 0.1)',
        borderWidth: 3,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.4,
      },
      {
        label: 'Upper Bound',
        data: forecastUpperBounds,
        borderColor: 'rgba(96, 165, 250, 0.5)',
        backgroundColor: 'rgba(96, 165, 250, 0.1)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: '+1',
        tension: 0.4,
      },
      {
        label: 'Lower Bound',
        data: forecastLowerBounds,
        borderColor: 'rgba(96, 165, 250, 0.5)',
        backgroundColor: 'rgba(96, 165, 250, 0.2)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
        tension: 0.4,
      },
    ],
  };

  const forecastChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      },
      title: {
        display: true,
        text: `Multi-Horizon Forecast: ${targetColumn}`,
        font: {
          size: 16,
          weight: 'bold'
        },
        color: '#1e40af'
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        padding: 12,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(2);
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Predicted Value',
          font: {
            size: 13,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Forecast Horizon',
          font: {
            size: 13,
            weight: 'bold'
          }
        },
        grid: {
          display: false
        }
      }
    },
  };

  // Metrics Bar Chart Data
  const metricsChartData = metrics ? {
    labels: ['MAPE (%)', 'R² × 100', 'MAE', 'RMSE'],
    datasets: [
      {
        label: 'Metric Value',
        data: [
          metrics.mape || 0,
          (metrics.r2 || 0) * 100, // Scale R² for visibility
          metrics.mae || 0,
          metrics.rmse || 0,
        ],
        backgroundColor: [
          'rgba(30, 64, 175, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(30, 64, 175)',
          'rgb(16, 185, 129)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2,
      },
    ],
  } : null;

  const metricsChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Model Performance Metrics',
        font: {
          size: 16,
          weight: 'bold'
        },
        color: '#1e40af'
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        padding: 12,
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(2);
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Value',
          font: {
            size: 13,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    },
  };

  // Confidence Visualization Data
  const confidenceLevels = forecasts.map(f => f.confidence_level || 0.95);
  const avgConfidence = confidenceLevels.reduce((a, b) => a + b, 0) / confidenceLevels.length;

  return (
    <div className="space-y-6">
      {/* Forecast Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="h-96">
          <Line data={forecastChartData} options={forecastChartOptions} />
        </div>
      </div>

      {/* Metrics and Statistics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Metrics Bar Chart */}
        {metrics && metricsChartData && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="h-80">
              <Bar data={metricsChartData} options={metricsChartOptions} />
            </div>
          </div>
        )}

        {/* Statistics Summary */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Forecast Statistics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <span className="text-gray-700 font-medium">Average Prediction:</span>
              <span className="text-blue-700 font-bold text-lg">
                {(forecastPredictions.reduce((a, b) => a + b, 0) / forecastPredictions.length).toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <span className="text-gray-700 font-medium">Min Prediction:</span>
              <span className="text-green-700 font-bold text-lg">
                {Math.min(...forecastPredictions).toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
              <span className="text-gray-700 font-medium">Max Prediction:</span>
              <span className="text-orange-700 font-bold text-lg">
                {Math.max(...forecastPredictions).toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
              <span className="text-gray-700 font-medium">Average Confidence:</span>
              <span className="text-purple-700 font-bold text-lg">
                {(avgConfidence * 100).toFixed(1)}%
              </span>
            </div>

            {metrics && metrics.mape !== undefined && (
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-2 border-blue-200">
                <span className="text-gray-700 font-medium">Model Accuracy (MAPE):</span>
                <span className={`font-bold text-lg ${
                  metrics.mape < 10 ? 'text-green-600' : 
                  metrics.mape < 20 ? 'text-yellow-600' : 
                  'text-red-600'
                }`}>
                  {metrics.mape.toFixed(2)}%
                  <span className="text-sm ml-2 font-normal">
                    {metrics.mape < 10 ? '(Excellent)' : 
                     metrics.mape < 20 ? '(Good)' : 
                     '(Needs Improvement)'}
                  </span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detailed Metrics Table */}
      {metrics && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Detailed Performance Metrics</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metric
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Interpretation
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    MAPE (Mean Absolute Percentage Error)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {metrics.mape?.toFixed(2) || '0.00'}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    Lower is better
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    R² Score (Coefficient of Determination)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {metrics.r2?.toFixed(4) || '0.0000'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    Closer to 1.0 is better
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    MAE (Mean Absolute Error)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {metrics.mae?.toFixed(4) || '0.0000'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    Lower is better
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    RMSE (Root Mean Squared Error)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {metrics.rmse?.toFixed(4) || '0.0000'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    Lower is better
                  </td>
                </tr>
                {metrics.bias !== undefined && (
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Bias
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {metrics.bias.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      Positive = Over-prediction, Negative = Under-prediction
                    </td>
                  </tr>
                )}
                {metrics.trend_alignment !== undefined && (
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Trend Alignment
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {metrics.trend_alignment.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      Correlation with actual trend (closer to 1.0 is better)
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionCharts;
