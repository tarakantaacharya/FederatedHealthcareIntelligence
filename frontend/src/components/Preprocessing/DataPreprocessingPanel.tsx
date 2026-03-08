import React, { useState, useEffect } from 'react';
import preprocessingService, {
  DataQualityResponse,
  ColumnTypeInfo,
  DataPreviewResponse,
  DataCleaningRequest
} from '../../services/preprocessingService';

interface DataPreprocessingPanelProps {
  datasetId: number;
  onPreprocessingComplete?: () => void;
}

export const DataPreprocessingPanel: React.FC<DataPreprocessingPanelProps> = ({
  datasetId,
  onPreprocessingComplete
}) => {
  const [loading, setLoading] = useState(true);
  const [qualityReport, setQualityReport] = useState<DataQualityResponse | null>(null);
  const [columnTypes, setColumnTypes] = useState<Record<string, ColumnTypeInfo> | null>(null);
  const [preview, setPreview] = useState<DataPreviewResponse | null>(null);
  const [isTrained, setIsTrained] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [cleaning, setCleaning] = useState(false);

  // Cleaning options
  const [removeDuplicates, setRemoveDuplicates] = useState(false);
  const [handleMissing, setHandleMissing] = useState<'none' | 'drop' | 'fill'>('none');
  const [fillValue, setFillValue] = useState<string>('0');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [columnRenames, setColumnRenames] = useState<Record<string, string>>({});
  const [typeConversions, setTypeConversions] = useState<Record<string, string>>({});

  const [activeTab, setActiveTab] = useState<'quality' | 'types' | 'preview' | 'clean' | 'rename'>('quality');

  useEffect(() => {
    loadPreprocessingData();
  }, [datasetId]);

  const loadPreprocessingData = async () => {
    try {
      setLoading(true);
      setError('');

      const status = await preprocessingService.getPreprocessingStatus(datasetId);
      
      setQualityReport(status.quality_report || null);
      setColumnTypes(status.column_types || null);
      setIsTrained(status.is_trained);

      // Load preview
      const previewData = await preprocessingService.getPreview(datasetId, 10);
      setPreview(previewData);
    } catch (err: any) {
      console.error('Failed to load preprocessing data:', err);
      setError(err.response?.data?.detail || 'Failed to load preprocessing data');
    } finally {
      setLoading(false);
    }
  };

  const handleClean = async () => {
    try {
      setCleaning(true);
      setError('');
      setSuccess('');

      const operations: DataCleaningRequest = {
        remove_duplicates: removeDuplicates,
      };

      if (handleMissing === 'drop') {
        operations.handle_missing = { strategy: 'drop' };
      } else if (handleMissing === 'fill') {
        operations.handle_missing = { strategy: 'fill', fill_value: parseFloat(fillValue) || 0 };
      }

      if (selectedColumns.length > 0) {
        operations.remove_columns = selectedColumns;
      }

      if (Object.keys(columnRenames).length > 0) {
        operations.rename_columns = columnRenames;
      }

      if (Object.keys(typeConversions).length > 0) {
        operations.convert_types = typeConversions;
      }

      const result = await preprocessingService.cleanDataset(datasetId, operations);

      setSuccess(
        `Dataset cleaned successfully! ${result.operations_applied.length} operations applied. ` +
        (result.created_backup ? '✓ Backup created.' : '')
      );

      // Reload data
      await loadPreprocessingData();

      if (onPreprocessingComplete) {
        onPreprocessingComplete();
      }
    } catch (err: any) {
      console.error('Failed to clean dataset:', err);
      setError(err.response?.data?.detail || 'Failed to clean dataset');
    } finally {
      setCleaning(false);
    }
  };

  const getTypeColor = (type: string): string => {
    switch (type) {
      case 'integer': return 'bg-blue-100 text-blue-800';
      case 'float': return 'bg-green-100 text-green-800';
      case 'string': return 'bg-purple-100 text-purple-800';
      case 'datetime': return 'bg-orange-100 text-orange-800';
      case 'boolean': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading preprocessing data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Alert Messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {success}
        </div>
      )}

      {/* Training Status Warning */}
      {isTrained && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
          ⚠️ This dataset has been trained. Any modifications will automatically create a backup copy.
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('quality')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'quality'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          📊 Quality Report
        </button>
        <button
          onClick={() => setActiveTab('types')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'types'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          🔤 Column Types
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'preview'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          👁️ Preview
        </button>
        <button
          onClick={() => setActiveTab('clean')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'clean'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          🧹 Clean Data
        </button>
        <button
          onClick={() => setActiveTab('rename')}
          className={`px-4 py-2 font-medium transition ${
            activeTab === 'rename'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          ✏️ Rename Columns
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {/* Quality Report Tab */}
        {activeTab === 'quality' && qualityReport && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Rows</p>
                <p className="text-2xl font-bold">{qualityReport.total_rows.toLocaleString()}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Columns</p>
                <p className="text-2xl font-bold">{qualityReport.total_columns}</p>
              </div>
              <div className={`p-4 rounded-lg ${qualityReport.has_issues ? 'bg-red-50' : 'bg-green-50'}`}>
                <p className="text-sm text-gray-600">Quality Status</p>
                <p className="text-2xl font-bold">
                  {qualityReport.has_issues ? '⚠️ Issues' : '✓ Clean'}
                </p>
              </div>
            </div>

            {/* Duplicates */}
            {qualityReport.duplicates.count > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-900 mb-2">Duplicate Rows</h4>
                <p className="text-sm text-yellow-800">
                  Found {qualityReport.duplicates.count} duplicate rows ({qualityReport.duplicates.percentage.toFixed(2)}%)
                </p>
              </div>
            )}

            {/* Missing Values */}
            {Object.keys(qualityReport.missing_values).length > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <h4 className="font-semibold text-orange-900 mb-2">Missing Values</h4>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {Object.entries(qualityReport.missing_values).map(([col, count]) => (
                    <div key={col} className="flex justify-between text-sm">
                      <span className="font-mono">{col}</span>
                      <span className="text-orange-800">
                        {count} missing ({((count / qualityReport.total_rows) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Column Statistics */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Column Statistics</h4>
              <div className="max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-200 sticky top-0">
                    <tr>
                      <th className="text-left p-2">Column</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-right p-2">Unique</th>
                      <th className="text-right p-2">Missing #</th>
                      <th className="text-right p-2">Missing %</th>
                      <th className="text-center p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(qualityReport.columns).map(([col, info]) => (
                      <tr key={col} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="p-2 font-mono text-xs">{col}</td>
                        <td className="p-2">{info.dtype}</td>
                        <td className="p-2 text-right">{info.unique_count}</td>
                        <td className="p-2 text-right font-semibold">
                          {info.missing_count}
                        </td>
                        <td className="p-2 text-right">
                          {info.missing_count > 0 ? (
                            <span className="text-orange-600 font-medium">
                              {info.missing_percentage.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-green-600">0%</span>
                          )}
                        </td>
                        <td className="p-2 text-center">
                          {info.missing_count > 0 ? (
                            <span className="text-orange-600 text-lg">⚠️</span>
                          ) : (
                            <span className="text-green-600 text-lg">✓</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Column Types Tab */}
        {activeTab === 'types' && columnTypes && (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">Detected Column Types</h4>
              <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-200 sticky top-0">
                    <tr>
                      <th className="text-left p-2">Column Name</th>
                      <th className="text-left p-2">Data Type</th>
                      <th className="text-right p-2">Non-Null</th>
                      <th className="text-right p-2">Null</th>
                      <th className="text-right p-2">Unique</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(columnTypes).map(([col, info]) => (
                      <tr key={col} className="border-b border-gray-200">
                        <td className="p-2 font-mono text-xs">{col}</td>
                        <td className="p-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(info.type)}`}>
                            {info.type}
                          </span>
                        </td>
                        <td className="p-2 text-right text-green-600">{info.non_null_count}</td>
                        <td className="p-2 text-right">
                          {info.null_count > 0 ? (
                            <span className="text-orange-600">{info.null_count}</span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                        <td className="p-2 text-right">{info.unique_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Preview Tab */}
        {activeTab === 'preview' && preview && (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">
                Dataset Preview (First {preview.total_rows} rows)
              </h4>
              <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="w-full text-xs border-collapse">
                  <thead className="bg-gray-200 sticky top-0">
                    <tr>
                      <th className="border border-gray-300 p-2 text-left">#</th>
                      {preview.columns.map((col) => (
                        <th key={col} className="border border-gray-300 p-2 text-left font-mono">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.data.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-100">
                        <td className="border border-gray-300 p-2 text-gray-500">{idx + 1}</td>
                        {preview.columns.map((col) => (
                          <td key={col} className="border border-gray-300 p-2 font-mono">
                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Clean Data Tab */}
        {activeTab === 'clean' && (
          <div className="space-y-6">
            {/* Remove Duplicates */}
            <div className="bg-gray-50 rounded-lg p-4">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={removeDuplicates}
                  onChange={(e) => setRemoveDuplicates(e.target.checked)}
                  className="w-5 h-5 text-blue-600"
                />
                <div>
                  <span className="font-medium">Remove Duplicate Rows</span>
                  {qualityReport && qualityReport.duplicates.count > 0 && (
                    <p className="text-sm text-gray-600">
                      Found {qualityReport.duplicates.count} duplicates
                    </p>
                  )}
                </div>
              </label>
            </div>

            {/* Handle Missing Values */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-3">Handle Missing Values</h4>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    value="none"
                    checked={handleMissing === 'none'}
                    onChange={(e) => setHandleMissing('none')}
                    className="w-4 h-4"
                  />
                  <span>Keep as-is</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    value="drop"
                    checked={handleMissing === 'drop'}
                    onChange={(e) => setHandleMissing('drop')}
                    className="w-4 h-4"
                  />
                  <span>Drop rows with missing values</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    value="fill"
                    checked={handleMissing === 'fill'}
                    onChange={(e) => setHandleMissing('fill')}
                    className="w-4 h-4"
                  />
                  <span>Fill missing values with:</span>
                  {handleMissing === 'fill' && (
                    <input
                      type="text"
                      value={fillValue}
                      onChange={(e) => setFillValue(e.target.value)}
                      className="ml-2 px-2 py-1 border border-gray-300 rounded w-24"
                      placeholder="0"
                    />
                  )}
                </label>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleClean}
                disabled={cleaning}
                className="flex-1 bg-blue-600 text-white px-4 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-semibold"
              >
                {cleaning ? 'Cleaning...' : '🧹 Apply Cleaning Operations'}
              </button>
            </div>
          </div>
        )}

        {/* Rename Columns Tab */}
        {activeTab === 'rename' && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                💡 Enter new names for your columns. Leave blank to keep the original name.
              </p>
            </div>

            {preview && preview.columns.length > 0 ? (
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <div className="space-y-3">
                  {preview.columns.map((col, idx) => (
                    <div key={col} className="flex items-center gap-3">
                      <div className="w-6 text-center text-xs text-gray-500 font-semibold">{idx + 1}.</div>
                      <div className="flex-1">
                        <input
                          type="text"
                          defaultValue={columnRenames[col] || ''}
                          placeholder={col}
                          onChange={(e) => {
                            if (e.target.value) {
                              setColumnRenames({ ...columnRenames, [col]: e.target.value });
                            } else {
                              const { [col]: _, ...rest } = columnRenames;
                              setColumnRenames(rest);
                            }
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                      </div>
                      <div className="text-xs text-gray-600 font-mono min-w-fit bg-gray-200 px-2 py-1 rounded">
                        {col}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                No columns available
              </div>
            )}

            {/* Summary */}
            {Object.keys(columnRenames).length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-900 font-semibold">
                  ✓ {Object.keys(columnRenames).length} column(s) will be renamed
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleClean}
                disabled={cleaning || Object.keys(columnRenames).length === 0}
                className="flex-1 bg-blue-600 text-white px-4 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-semibold"
              >
                {cleaning ? 'Renaming...' : '✏️ Apply Column Renames'}
              </button>
              <button
                onClick={() => setColumnRenames({})}
                className="px-4 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Reset
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
