import React from 'react';

interface DataTableProps<T> {
  columns: { key: keyof T; label: string }[];
  data: T[];
  onRowClick?: (row: T) => void;
}

export const DataTable = <T extends { id: number }>({
  columns,
  data,
  onRowClick,
}: DataTableProps<T>): JSX.Element => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            {columns.map((col) => (
              <th key={String(col.key)} className="px-6 py-3 text-left">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className="border-t hover:bg-gray-50 cursor-pointer"
            >
              {columns.map((col) => (
                <td key={String(col.key)} className="px-6 py-4">
                  {String(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
