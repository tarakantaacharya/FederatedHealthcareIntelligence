import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import datasetService from '../services/datasetService';
import authService from '../services/authService';
import { Dataset } from '../types/dataset';
import { formatErrorMessage } from '../utils/errorMessage';

const DatasetUpload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchDatasets();
  }, [navigate]);

  const fetchDatasets = async () => {
    try {
      const data = await datasetService.getDatasets();
      setDatasets(data);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];

    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file');
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setError('');
      setSuccess('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      await datasetService.uploadDataset(file);
      setSuccess('Dataset uploaded successfully!');
      setFile(null);

      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      fetchDatasets();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Upload failed. Please try again.';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (datasetId: number) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) {
      return;
    }

    try {
      await datasetService.deleteDataset(datasetId);
      setSuccess('Dataset deleted successfully');
      setError('');
      fetchDatasets();
    } catch (err: any) {
      console.error('Delete error:', err);
      setError(err.response?.data?.detail || 'Failed to delete dataset');
      setSuccess('');
    }
  };

  return (
    <ConsoleLayout title="Datasets" subtitle="Upload and manage datasets">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Dataset Management</h2>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Upload New Dataset</h3>

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

          <form onSubmit={handleUpload}>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select CSV File
              </label>
              <input
                id="file-input"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
              />
              {file && (
                <p className="text-sm text-blue-600 mt-2">File ready: {file.name}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload Dataset'}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b flex justify-between items-center">
            <h3 className="text-lg font-semibold">My Datasets</h3>
            <button
              onClick={fetchDatasets}
              disabled={loading}
              className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md hover:bg-slate-100 disabled:opacity-50"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-600">Loading datasets...</div>
          ) : datasets.length === 0 ? (
            <div className="p-6 text-center text-gray-600">
              No datasets uploaded yet. Upload your first dataset above.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rows</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Columns</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Normalized</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Uploaded</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {datasets.map((dataset) => (
                    <tr key={dataset.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {dataset.filename}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {datasetService.formatFileSize(dataset.file_size_bytes)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.num_rows || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.num_columns || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {dataset.is_normalized ? (
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Yes</span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">No</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(dataset.uploaded_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <button
                          onClick={() => navigate(`/schema-mapping/${dataset.id}`)}
                          className="bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700"
                        >
                          Map Schema
                        </button>
                        <button
                          onClick={() => handleDelete(dataset.id)}
                          className="bg-red-600 text-white px-3 py-1.5 rounded-md hover:bg-red-700"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default DatasetUpload;
