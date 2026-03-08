import React from 'react';

interface HeatmapProps {
  title: string;
  rowLabels: string[];
  columnLabels: string[];
  data: (number | null)[][];
  colorScale?: (value: number | null) => string;
  height?: number;
}

const defaultColorScale = (value: number | null): string => {
  if (value === null || value === undefined) return '#e5e7eb';
  if (value >= 0.9) return '#10b981';
  if (value >= 0.8) return '#84cc16';
  if (value >= 0.7) return '#facc15';
  if (value >= 0.6) return '#fb923c';
  return '#ef4444';
};

export const Heatmap: React.FC<HeatmapProps> = ({ 
  title, 
  rowLabels, 
  columnLabels, 
  data, 
  colorScale = defaultColorScale,
  height = 300 
}) => {
  const cellWidth = 60;
  const cellHeight = 40;
  const labelWidth = 120;
  const headerHeight = 60;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">{title}</h3>
      <div className="overflow-x-auto" style={{ maxHeight: `${height}px` }}>
        <table className="border-collapse text-xs">
          <thead>
            <tr>
              <th className="border border-gray-300 p-2 bg-gray-50" style={{ width: `${labelWidth}px` }}></th>
              {columnLabels.map((col, idx) => (
                <th key={`col-${idx}`} className="border border-gray-300 p-2 bg-gray-50" style={{ width: `${cellWidth}px` }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rowLabels.map((row, rIdx) => (
              <tr key={`row-${rIdx}`}>
                <td className="border border-gray-300 p-2 bg-gray-50 font-medium text-left" style={{ width: `${labelWidth}px` }}>
                  {row}
                </td>
                {columnLabels.map((col, cIdx) => {
                  const value = data[rIdx]?.[cIdx];
                  return (
                    <td
                      key={`cell-${rIdx}-${cIdx}`}
                      className="border border-gray-300 p-2 text-center font-semibold"
                      style={{ 
                        backgroundColor: colorScale(value),
                        color: value !== null && value >= 0.7 ? '#fff' : '#1f2937',
                        width: `${cellWidth}px`,
                        height: `${cellHeight}px`
                      }}
                    >
                      {value !== null && value !== undefined ? value.toFixed(2) : 'N/A'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs">
        <span className="text-gray-600">Scale:</span>
        <div className="flex items-center gap-1">
          {[0.5, 0.65, 0.75, 0.85, 0.95].map((v, idx) => (
            <div key={idx} className="flex flex-col items-center">
              <div className="w-8 h-4" style={{ backgroundColor: colorScale(v) }}></div>
              <span className="text-gray-500 mt-1">{v.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
