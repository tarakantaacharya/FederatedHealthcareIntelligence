import React from 'react';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ScatterChartProps {
  title: string;
  datasets: Array<{
    label: string;
    data: Array<{ x: number; y: number }>;
    backgroundColor?: string;
    borderColor?: string;
  }>;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
}

const ScatterChart: React.FC<ScatterChartProps> = ({ title, datasets, xAxisLabel, yAxisLabel, height = 300 }) => {
  const data = {
    datasets: datasets.map((ds, idx) => ({
      ...ds,
      backgroundColor: ds.backgroundColor || ['rgba(59, 130, 246, 0.5)', 'rgba(16, 185, 129, 0.5)', 'rgba(245, 158, 11, 0.5)'][idx % 3],
      borderColor: ds.borderColor || ['#3b82f6', '#10b981', '#f59e0b'][idx % 3],
      pointRadius: 5,
      pointHoverRadius: 7,
    })),
  };

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: title,
        font: { size: 14, weight: 'bold' },
      },
    },
    scales: {
      x: {
        title: {
          display: !!xAxisLabel,
          text: xAxisLabel,
        },
      },
      y: {
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel,
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px` }}>
      <Scatter data={data} options={options} />
    </div>
  );
};

export default ScatterChart;
