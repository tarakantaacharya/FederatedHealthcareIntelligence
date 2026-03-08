import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import datasetService from '../services/datasetService';
import mappingService from '../services/mappingService';
import { formatErrorMessage } from '../utils/errorMessage';

interface CanonicalField {
  field_name: string;
}

const SchemaMapping: React.FC = () => {
  const navigate = useNavigate();
  const { datasetId } = useParams<{ datasetId: string }>();
  const numericDatasetId = Number(datasetId);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [autoMapping, setAutoMapping] = useState(false);
  const [datasetColumns, setDatasetColumns] = useState<string[]>([]);
  const [canonicalFields, setCanonicalFields] = useState<string[]>([]);
  const [draftMappings, setDraftMappings] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const mappedCount = useMemo(
    () => Object.values(draftMappings).filter((value) => Boolean(value)).length,
    [draftMappings]
  );

  const loadPageData = async () => {
    if (!numericDatasetId) {
      setError('Invalid dataset ID');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const [datasetDetail, mappingData, canonicalResponse] = await Promise.all([
        datasetService.getDatasetById(numericDatasetId),
        mappingService.getDatasetMappings(numericDatasetId),
        api.get('/api/canonical-fields')
      ]);

      const columns = datasetDetail.column_names || [];
      const savedMappings = (mappingData.mappings || []).reduce<Record<string, string>>((acc, item) => {
        acc[item.original_column] = item.canonical_field;
        return acc;
      }, {});

      const initialDraft = columns.reduce<Record<string, string>>((acc, column) => {
        acc[column] = savedMappings[column] || '';
        return acc;
      }, {});

      setDatasetColumns(columns);
      setDraftMappings(initialDraft);
      setCanonicalFields((canonicalResponse.data?.fields || []).map((field: CanonicalField) => field.field_name));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load mapping data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    loadPageData();
  }, [datasetId, navigate]);

  const handleFieldChange = (column: string, canonicalField: string) => {
    setDraftMappings((prev) => ({ ...prev, [column]: canonicalField }));
  };

  const handleSaveMappings = async () => {
    if (!numericDatasetId) return;

    const payloadMappings = Object.entries(draftMappings).reduce<Record<string, string>>((acc, [column, field]) => {
      if (field) {
        acc[column] = field;
      }
      return acc;
    }, {});

    if (Object.keys(payloadMappings).length === 0) {
      setError('Please map at least one column before saving');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await mappingService.saveManualMapping({
        dataset_id: numericDatasetId,
        mappings: payloadMappings
      });
      setSuccess(`Saved ${Object.keys(payloadMappings).length} column mappings`);
      await loadPageData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save manual mappings');
    } finally {
      setSaving(false);
    }
  };

  const handleAutoMap = async () => {
    if (!numericDatasetId) return;

    setAutoMapping(true);
    setError('');
    setSuccess('');

    try {
      const result = await mappingService.autoMapDataset(numericDatasetId);
      setSuccess(`Auto-map complete: ${result.mapped_count}/${result.total_columns} columns mapped`);
      await loadPageData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Auto-mapping failed');
    } finally {
      setAutoMapping(false);
    }
  };

  if (!datasetId) {
    return <div>Invalid dataset ID</div>;
  }

  return (
    <ConsoleLayout title="Schema Mapping" subtitle={`Dataset ${datasetId}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Manual Column Mapping</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6 text-gray-600">Loading mapping configuration...</div>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Total Columns</p>
                  <p className="text-2xl font-bold">{datasetColumns.length}</p>
                </div>
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Mapped</p>
                  <p className="text-2xl font-bold text-green-600">{mappedCount}</p>
                </div>
                <div className="border rounded p-3">
                  <p className="text-sm text-gray-600">Unmapped</p>
                  <p className="text-2xl font-bold text-yellow-600">{Math.max(datasetColumns.length - mappedCount, 0)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow mb-6">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-semibold">Map Dataset Columns</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dataset Column</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Canonical Field</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {datasetColumns.map((column) => (
                      <tr key={column}>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{column}</td>
                        <td className="px-6 py-4 text-sm text-gray-700">
                          <select
                            value={draftMappings[column] || ''}
                            onChange={(event) => handleFieldChange(column, event.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          >
                            <option value="">Select canonical field...</option>
                            {canonicalFields.map((field) => (
                              <option key={field} value={field}>{field}</option>
                            ))}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleAutoMap}
                disabled={autoMapping || saving}
                className="bg-purple-600 text-white px-5 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {autoMapping ? 'Auto-Mapping...' : 'Auto-Map Suggestions'}
              </button>
              <button
                onClick={handleSaveMappings}
                disabled={saving || autoMapping}
                className="bg-blue-600 text-white px-5 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Manual Mappings'}
              </button>
              <button
                onClick={() => navigate('/training')}
                className="bg-green-600 text-white px-5 py-2 rounded-md hover:bg-green-700"
              >
                Proceed to Training
              </button>
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default SchemaMapping;
