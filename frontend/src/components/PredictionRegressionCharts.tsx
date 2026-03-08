import React, { useMemo } from 'react';
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
  ChartOptions,
  ScatterController,
} from 'chart.js';
import { Bar, Line, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ScatterController,
  Title,
  Tooltip,
  Legend
);

interface PredictionRegressionChartsProps {
  predictedValues: number[];
  actualValues: number[];
  metrics: {
    r2?: number | null;
    mae?: number | null;
    mse?: number | null;
    rmse?: number | null;
    loss?: number | null;
    mape?: number | null;
    bias?: number | null;
    trend_alignment?: number | null;
  };
  confidenceInterval?: {
    lower: number[];
    upper: number[];
  };
  isTFT?: boolean;
}

const PredictionRegressionCharts: React.FC<PredictionRegressionChartsProps> = ({
  predictedValues,
  actualValues,
  metrics,
  confidenceInterval,
  isTFT = false,
}) => {
  const hasPredictedSeries = predictedValues.length > 0;
  const alignedCount = Math.min(predictedValues.length, actualValues.length);
  const hasAlignedSeries = alignedCount > 0;

  const alignedPredicted = useMemo(
    () => predictedValues.slice(0, alignedCount),
    [predictedValues, alignedCount]
  );
  const alignedActual = useMemo(
    () => actualValues.slice(0, alignedCount),
    [actualValues, alignedCount]
  );

  const residuals = useMemo(
    () => alignedActual.map((value, index) => value - alignedPredicted[index]),
    [alignedActual, alignedPredicted]
  );

  const indexLabels = useMemo(
    () => (hasAlignedSeries ? Array.from({ length: alignedCount }, (_, idx) => `${idx + 1}`) : predictedValues.map((_, idx) => `${idx + 1}`)),
    [hasAlignedSeries, alignedCount, predictedValues]
  );

  const actualVsPredictedData = {
    labels: indexLabels,
    datasets: [
      {
        label: 'Predicted Values',
        data: hasAlignedSeries ? alignedPredicted : predictedValues,
        borderColor: 'rgb(8, 145, 178)',
        backgroundColor: 'rgba(8, 145, 178, 0.16)',
        pointRadius: 2,
        tension: 0.25,
      },
      ...(hasAlignedSeries
        ? [
            {
              label: 'Actual Values',
              data: alignedActual,
              borderColor: 'rgb(234, 88, 12)',
              backgroundColor: 'rgba(234, 88, 12, 0.18)',
              pointRadius: 2,
              tension: 0.25,
            },
          ]
        : []),
      ...(isTFT && confidenceInterval && confidenceInterval.lower.length > 0
        ? [
            {
              label: 'Upper Bound (90th %ile)',
              data: confidenceInterval.upper,
              borderColor: 'rgba(59, 130, 246, 0.4)',
              backgroundColor: 'rgba(59, 130, 246, 0.08)',
              borderDash: [5, 5],
              pointRadius: 0,
              tension: 0.25,
              fill: false,
            },
            {
              label: 'Lower Bound (10th %ile)',
              data: confidenceInterval.lower,
              borderColor: 'rgba(59, 130, 246, 0.4)',
              backgroundColor: 'rgba(59, 130, 246, 0.12)',
              borderDash: [5, 5],
              pointRadius: 0,
              tension: 0.25,
              fill: '-1',
            },
          ]
        : []),
    ],
  };

  const lineOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Sample Index',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Value',
        },
      },
    },
  };

  const residualScatterData = {
    datasets: [
      {
        label: 'Residuals (Actual - Predicted)',
        data: alignedPredicted.map((predicted, idx) => ({
          x: predicted,
          y: residuals[idx],
        })),
        backgroundColor: 'rgba(2, 132, 199, 0.65)',
        pointRadius: 4,
      },
    ],
  };

  const predictedOnlyScatterData = {
    datasets: [
      {
        label: 'Predicted Values (Actual Not Available)',
        data: predictedValues.map((predicted, idx) => ({
          x: idx + 1,
          y: predicted,
        })),
        backgroundColor: 'rgba(8, 145, 178, 0.7)',
        pointRadius: 4,
      },
    ],
  };

  const scatterOptions: ChartOptions<'scatter'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Predicted Values',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Residual Error',
        },
      },
    },
  };

  const predictedOnlyScatterOptions: ChartOptions<'scatter'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Sample Index',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Predicted Value',
        },
      },
    },
  };

  const histogramData = useMemo(() => {
    if (!residuals.length) {
      return { labels: [], values: [] };
    }

    const min = Math.min(...residuals);
    const max = Math.max(...residuals);
    const bins = 10;
    const width = max === min ? 1 : (max - min) / bins;
    const counts = new Array(bins).fill(0);

    residuals.forEach((value) => {
      const index = Math.min(Math.floor((value - min) / width), bins - 1);
      counts[index] += 1;
    });

    const labels = counts.map((_, idx) => {
      const start = min + idx * width;
      const end = start + width;
      return `${start.toFixed(2)} to ${end.toFixed(2)}`;
    });

    return { labels, values: counts };
  }, [residuals]);

  const histogramChartData = {
    labels: histogramData.labels,
    datasets: [
      {
        label: 'Error Frequency',
        data: histogramData.values,
        backgroundColor: 'rgba(21, 128, 61, 0.7)',
        borderColor: 'rgb(21, 128, 61)',
        borderWidth: 1,
      },
    ],
  };

  const predictionMagnitudeHistogram = useMemo(() => {
    if (!predictedValues.length) {
      return { labels: [], values: [] };
    }

    const min = Math.min(...predictedValues);
    const max = Math.max(...predictedValues);
    const bins = Math.min(10, Math.max(3, predictedValues.length));
    const width = max === min ? 1 : (max - min) / bins;
    const counts = new Array(bins).fill(0);

    predictedValues.forEach((value) => {
      const index = Math.min(Math.floor((value - min) / width), bins - 1);
      counts[index] += 1;
    });

    const labels = counts.map((_, idx) => {
      const start = min + idx * width;
      const end = start + width;
      return `${start.toFixed(2)} to ${end.toFixed(2)}`;
    });

    return { labels, values: counts };
  }, [predictedValues]);

  const predictionMagnitudeChartData = {
    labels: predictionMagnitudeHistogram.labels,
    datasets: [
      {
        label: 'Prediction Frequency',
        data: predictionMagnitudeHistogram.values,
        backgroundColor: 'rgba(8, 145, 178, 0.72)',
        borderColor: 'rgb(8, 145, 178)',
        borderWidth: 1,
      },
    ],
  };

  const histogramOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Error Bins',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Frequency',
        },
        beginAtZero: true,
      },
    },
  };

  const metricItems = [
    { label: 'R2', value: metrics.r2 },
    { label: 'MAE', value: metrics.mae },
    { label: 'RMSE', value: metrics.rmse },
    { label: 'MSE', value: metrics.mse },
    { label: 'MAPE', value: metrics.mape },
    ...(isTFT
      ? [
          { label: 'Bias', value: metrics.bias },
          { label: 'Trend Align', value: metrics.trend_alignment },
        ]
      : []),
  ].filter((item) => typeof item.value === 'number' && Number.isFinite(item.value));

  const metricData = {
    labels: metricItems.map((item) => item.label),
    datasets: [
      {
        label: 'Metric Value',
        data: metricItems.map((item) => Number(item.value)),
        backgroundColor: [
          'rgba(37, 99, 235, 0.75)',
          'rgba(234, 88, 12, 0.75)',
          'rgba(16, 185, 129, 0.75)',
          'rgba(244, 63, 94, 0.75)',
          'rgba(202, 138, 4, 0.75)',
        ],
      },
    ],
  };

  const metricOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Value',
        },
      },
    },
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-5">
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          {isTFT ? 'Multi-Horizon Forecast Chart' : 'Actual vs Predicted Line Chart'}
        </h3>
        <div className="h-80">
          {hasPredictedSeries ? (
            <Line data={actualVsPredictedData} options={lineOptions} />
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-gray-500 border border-dashed border-gray-300 rounded-lg">
              No prediction series available for this record.
            </div>
          )}
        </div>
        {isTFT && confidenceInterval && confidenceInterval.lower.length > 0 && (
          <p className="mt-3 text-sm text-sky-700">
            Confidence bands show 10th and 90th percentile uncertainty ranges for TFT forecast.
          </p>
        )}
        {!hasAlignedSeries && !isTFT && (
          <p className="mt-3 text-sm text-amber-700">
            Actual values are unavailable for this record. Showing predicted series only.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            {hasAlignedSeries ? 'Residual Plot' : 'Predicted Value Scatter'}
          </h3>
          <div className="h-72">
            {hasPredictedSeries ? (
              hasAlignedSeries ? (
                <Scatter data={residualScatterData} options={scatterOptions} />
              ) : (
                <Scatter data={predictedOnlyScatterData} options={predictedOnlyScatterOptions} />
              )
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-gray-500 border border-dashed border-gray-300 rounded-lg">
                Residual view requires at least prediction values.
              </div>
            )}
          </div>
          {hasPredictedSeries && !hasAlignedSeries && (
            <p className="mt-3 text-sm text-amber-700">
              Actual values are unavailable for this record, so this view shows prediction behavior instead of residual error.
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            {hasAlignedSeries ? 'Error Distribution Chart' : 'Prediction Distribution Chart'}
          </h3>
          <div className="h-72">
            {hasPredictedSeries ? (
              hasAlignedSeries ? (
                <Bar data={histogramChartData} options={histogramOptions} />
              ) : (
                <Bar data={predictionMagnitudeChartData} options={histogramOptions} />
              )
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-gray-500 border border-dashed border-gray-300 rounded-lg">
                Distribution chart requires at least prediction values.
              </div>
            )}
          </div>
          {hasPredictedSeries && !hasAlignedSeries && (
            <p className="mt-3 text-sm text-amber-700">
              Error distribution needs actual values. Showing the prediction magnitude distribution for quick inspection.
            </p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-5">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Metrics Visualization</h3>
        <div className="h-64">
          {metricItems.length > 0 ? (
            <Bar data={metricData} options={metricOptions} />
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-gray-500">
              No regression metrics available for charting.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionRegressionCharts;