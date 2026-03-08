import React from 'react';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
);

interface RadarChartProps {
  title: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }>;
  height?: number;
}

const RadarChart: React.FC<RadarChartProps> = ({ title, labels, datasets, height = 300 }) => {
  const data = {
    labels,
    datasets: datasets.map((ds, idx) => ({
      ...ds,
      backgroundColor: ds.backgroundColor || ['rgba(59, 130, 246, 0.2)', 'rgba(16, 185, 129, 0.2)', 'rgba(245, 158, 11, 0.2)'][idx % 3],
      borderColor: ds.borderColor || ['#3b82f6', '#10b981', '#f59e0b'][idx % 3],
      borderWidth: 2,
      pointBackgroundColor: ds.borderColor || ['#3b82f6', '#10b981', '#f59e0b'][idx % 3],
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: ds.borderColor || ['#3b82f6', '#10b981', '#f59e0b'][idx % 3],
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
      r: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 0.2,
        },
      },
    },
  };

  return (
    <div style={{ height: `${height}px` }}>
      <Radar data={data} options={options} />
    </div>
  );
};

export default RadarChart;
