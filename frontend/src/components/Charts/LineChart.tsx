import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface LineChartProps {
  title: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: (number | null)[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
  }>;
  yAxisLabel?: string;
  height?: number;
}

export const LineChart: React.FC<LineChartProps> = ({ title, labels, datasets, yAxisLabel, height = 280 }) => {
  const data = {
    labels,
    datasets: datasets.map((ds, idx) => ({
      ...ds,
      borderColor: ds.borderColor || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx % 4],
      backgroundColor: ds.backgroundColor || ['rgba(59, 130, 246, 0.1)', 'rgba(16, 185, 129, 0.1)', 'rgba(245, 158, 11, 0.1)', 'rgba(239, 68, 68, 0.1)'][idx % 4],
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
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
        display: false,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: !!yAxisLabel,
          text: yAxisLabel,
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">{title}</h3>
      <div style={{ height: `${height}px` }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

