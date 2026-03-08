import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  title: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: (number | null)[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }>;
  horizontal?: boolean;
  stacked?: boolean;
  yAxisLabel?: string;
  height?: number;
}

export const BarChart: React.FC<BarChartProps> = ({ title, labels, datasets, horizontal = false, stacked = false, yAxisLabel, height = 280 }) => {
  const data = {
    labels,
    datasets: datasets.map((ds, idx) => ({
      ...ds,
      backgroundColor: ds.backgroundColor || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx % 4],
      borderColor: ds.borderColor || ['#2563eb', '#059669', '#d97706', '#dc2626'][idx % 4],
      borderWidth: 1,
    })),
  };

  const options: any = {
    indexAxis: horizontal ? 'y' : 'x',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        stacked,
        title: {
          display: horizontal && !!yAxisLabel,
          text: yAxisLabel,
        },
      },
      y: {
        stacked,
        beginAtZero: true,
        title: {
          display: !horizontal && !!yAxisLabel,
          text: yAxisLabel,
        },
      },
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">{title}</h3>
      <div style={{ height: `${height}px` }}>
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

