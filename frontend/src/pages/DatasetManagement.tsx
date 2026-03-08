import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import datasetService from '../services/datasetService';
import { Dataset, DatasetDetail, DatasetStatus, DatasetModelSummary } from '../types/dataset';
import { formatErrorMessage } from '../utils/errorMessage';
import { DataPreprocessingPanel } from '../components/Preprocessing/DataPreprocessingPanel';

const DatasetManagement: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<DatasetDetail | null>(null);
  const [datasetStatus, setDatasetStatus] = useState<DatasetStatus | null>(null);
  const [datasetModels, setDatasetModels] = useState<DatasetModelSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // File upload
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  
  // Tab state
  const [activeDetailTab, setActiveDetailTab] = useState<'details' | 'preprocessing'>('details');

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }
    fetchDatasets();
  }, [navigate]);

  const fetchDatasets = async () => {
    try {
      console.log('[DatasetManagement] Fetching datasets...');
      setLoading(true);
      const data = await datasetService.getDatasets();
      console.log('[DatasetManagement] Datasets fetched:', data.length);
      setDatasets(data);
      setError('');
    } catch (err) {
      console.error('[DatasetManagement] Failed to fetch datasets:', err);
      console.error('[DatasetManagement] Error details:', JSON.stringify(err, null, 2));
      setError(formatErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (datasetId: number) => {
    try {
      console.log('[DatasetManagement] Fetching details for dataset:', datasetId);
      setDetailLoading(true);
      setStatusLoading(true);
      setModelsLoading(true);
      setError('');
      const detail = await datasetService.getDatasetById(datasetId);
      console.log('[DatasetManagement] Details fetched:', detail);
      setSelectedDataset(detail);
      
      const status = await datasetService.getDatasetStatus(datasetId);
      setDatasetStatus(status);

      const models = await datasetService.getDatasetModels(datasetId);
      setDatasetModels(models);
    } catch (err) {
      console.error('[DatasetManagement] Failed to fetch dataset detail:', err);
      console.error('[DatasetManagement] Error details:', JSON.stringify(err, null, 2));
      setError(formatErrorMessage(err));
      setDatasetStatus(null);
      setDatasetModels([]);
    } finally {
      setDetailLoading(false);
      setStatusLoading(false);
      setModelsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setSuccess('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    try {
      console.log('[DatasetManagement] Uploading file:', file.name, file.size);
      setUploading(true);
      setError('');
      setSuccess('');
      const result = await datasetService.uploadDataset(file);
      console.log('[DatasetManagement] Upload successful:', result);
      setSuccess(`Dataset "${file.name}" uploaded successfully!`);
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('dataset-file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      // Refresh datasets list
      await fetchDatasets();
    } catch (err) {
      console.error('[DatasetManagement] Upload failed:', err);
      console.error('[DatasetManagement] Error details:', JSON.stringify(err, null, 2));
      setError(formatErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDataset = async (datasetId: number) => {
    try {
      console.log('[DatasetManagement] Deleting dataset:', datasetId);
      
      // Check if authenticated
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Not authenticated. Please log in again.');
        navigate('/login');
        return;
      }
      
      setDeleting(true);
      setError('');
      setSuccess('');
      
      await datasetService.deleteDataset(datasetId);
      console.log('[DatasetManagement] Delete successful');
      setSuccess('Dataset deleted successfully');
      setShowDeleteConfirm(null);
      
      // Close detail view if deleted dataset was selected
      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null);
      }
      
      // Immediately update UI by removing the deleted dataset from state
      setDatasets(prevDatasets => prevDatasets.filter(ds => ds.id !== datasetId));
      
      // Refresh datasets list in background to ensure consistency
      fetchDatasets().catch(err => {
        console.error('[DatasetManagement] Background refresh failed:', err);
      });
    } catch (err) {
      console.error('[DatasetManagement] Failed to delete dataset:', err);
      console.error('[DatasetManagement] Error details:', JSON.stringify(err, null, 2));
      setError(formatErrorMessage(err));
      setShowDeleteConfirm(null);
    } finally {
      setDeleting(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <ConsoleLayout 
      title="Dataset Management" 
      subtitle="Upload, view, and manage your datasets"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Dataset List & Upload */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Upload Section */}
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
              <h3 className="text-lg font-semibold text-purple-900 mb-4">📤 Upload Dataset</h3>
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select CSV File
                  </label>
                  <input
                    id="dataset-file-input"
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded file:border-0
                      file:text-sm file:font-semibold
                      file:bg-purple-50 file:text-purple-700
                      hover:file:bg-purple-100"
                  />
                  {file && (
                    <p className="mt-2 text-xs text-gray-600">
                      Selected: {file.name} ({formatFileSize(file.size)})
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={uploading || !file}
                  className="w-full bg-purple-600 text-white px-4 py-2 rounded-md disabled:opacity-50 hover:bg-purple-700 font-semibold"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </form>
            </div>

            {/* Datasets List */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📊 Your Datasets ({datasets.length})
              </h3>
              {loading ? (
                <p className="text-gray-500 text-sm">Loading datasets...</p>
              ) : datasets.length === 0 ? (
                <p className="text-gray-500 text-sm">No datasets uploaded yet</p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {datasets.map((dataset) => (
                    <div
                      key={dataset.id}
                      className={`p-3 border rounded-lg cursor-pointer transition ${
                        selectedDataset?.id === dataset.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div 
                          className="flex-1"
                          onClick={() => handleViewDetails(dataset.id)}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-semibold text-sm text-gray-900">
                              {dataset.filename}
                            </p>
                            {dataset.dataset_type && (
                              <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                dataset.dataset_type === 'TIME_SERIES' 
                                  ? 'bg-purple-100 text-purple-700' 
                                  : 'bg-blue-100 text-blue-700'
                              }`}>
                                {dataset.dataset_type === 'TIME_SERIES' ? '📈 Time Series' : '📊 Tabular'}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-600">
                            <span>{dataset.num_rows || 0} rows</span>
                            <span>•</span>
                            <span>{dataset.num_columns || 0} cols</span>
                            <span>•</span>
                            <span>{formatFileSize(dataset.file_size_bytes)}</span>
                          </div>
                          {dataset.is_normalized && (
                            <p className="text-xs text-green-600 mt-1">✓ Normalized</p>
                          )}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowDeleteConfirm(dataset.id);
                          }}
                          className="ml-2 text-red-600 hover:text-red-800"
                          title="Delete dataset"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Dataset Details */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-blue-900">📋 Dataset Details</h3>
              </div>
              
              {/* Tab Navigation */}
              {!detailLoading && selectedDataset && (
                <div className="flex gap-2 mb-4 border-b border-gray-200">
                  <button
                    onClick={() => setActiveDetailTab('details')}
                    className={`px-4 py-2 font-medium transition ${
                      activeDetailTab === 'details'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    Details
                  </button>
                  <button
                    onClick={() => setActiveDetailTab('preprocessing')}
                    className={`px-4 py-2 font-medium transition ${
                      activeDetailTab === 'preprocessing'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    🧹 Data Preprocessing
                  </button>
                </div>
              )}
              
              {detailLoading ? (
                <p className="text-gray-500">Loading details...</p>
              ) : !selectedDataset ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📊</div>
                  <p className="text-gray-500">Select a dataset from the list to view details</p>
                </div>
              ) : activeDetailTab === 'details' ? (
                <div className="space-y-6">
                  
                  {/* Basic Information */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Basic Information</h4>
                    <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Filename</p>
                        <p className="font-medium text-sm">{selectedDataset.filename}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Dataset Type</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded font-medium inline-block ${
                            selectedDataset.dataset_type === 'TIME_SERIES' 
                              ? 'bg-purple-100 text-purple-700' 
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {selectedDataset.dataset_type === 'TIME_SERIES' ? '📈 Time Series' : '📊 Tabular'}
                          </span>
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">File Size</p>
                        <p className="font-medium text-sm">{formatFileSize(selectedDataset.file_size_bytes)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Number of Rows</p>
                        <p className="font-medium text-sm">{selectedDataset.num_rows?.toLocaleString() || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Number of Columns</p>
                        <p className="font-medium text-sm">{selectedDataset.num_columns || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Normalized</p>
                        <p className="font-medium text-sm">
                          {selectedDataset.is_normalized ? (
                            <span className="text-green-600">✓ Yes</span>
                          ) : (
                            <span className="text-gray-500">✗ No</span>
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Uploaded At</p>
                        <p className="font-medium text-sm">{formatDate(selectedDataset.uploaded_at)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Trained Models */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Models</h4>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      {modelsLoading ? (
                        <p className="text-gray-500 text-sm">Loading models...</p>
                      ) : datasetModels.length === 0 ? (
                        <p className="text-gray-500 text-sm">No trained models found for this dataset yet.</p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-sm">
                            <thead className="bg-gray-200">
                              <tr>
                                <th className="text-left p-2 font-semibold">Id</th>
                                <th className="text-left p-2 font-semibold">Model Name</th>
                                <th className="text-left p-2 font-semibold">Type</th>
                                <th className="text-left p-2 font-semibold">TFT/ML</th>
                                <th className="text-left p-2 font-semibold">Timestamp</th>
                              </tr>
                            </thead>
                            <tbody>
                              {datasetModels.map((model) => (
                                <tr key={model.id} className="border-b border-gray-200">
                                  <td className="p-2 text-gray-700">{model.id}</td>
                                  <td className="p-2 font-medium text-gray-900">{model.model_name}</td>
                                  <td className="p-2">
                                    <span className={`text-xs px-2 py-1 rounded font-medium ${
                                      model.type === 'FEDERATED'
                                        ? 'bg-purple-100 text-purple-700'
                                        : 'bg-blue-100 text-blue-700'
                                    }`}>
                                      {model.type}
                                    </span>
                                  </td>
                                  <td className="p-2">
                                    <span className={`text-xs px-2 py-1 rounded font-medium ${
                                      model.architecture === 'TFT'
                                        ? 'bg-indigo-100 text-indigo-700'
                                        : 'bg-emerald-100 text-emerald-700'
                                    }`}>
                                      {model.architecture}
                                    </span>
                                  </td>
                                  <td className="p-2 text-gray-600">{formatDate(model.timestamp)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Dataset Intelligence Status */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Dataset Intelligence</h4>
                    <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                      {statusLoading ? (
                        <p className="text-gray-500 col-span-2">Loading status...</p>
                      ) : !datasetStatus ? (
                        <p className="text-gray-500 col-span-2">No status available</p>
                      ) : (
                        <>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Local Trained</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.trained_local ? (
                                <span className="text-green-600">✓ Yes</span>
                              ) : (
                                <span className="text-gray-500">✗ No</span>
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Federated Trained</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.trained_federated ? (
                                <span className="text-green-600">✓ Yes</span>
                              ) : (
                                <span className="text-gray-500">✗ No</span>
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Mask Uploaded</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.mask_uploaded ? (
                                <span className="text-green-600">✓ Yes</span>
                              ) : (
                                <span className="text-gray-500">✗ No</span>
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Weights Uploaded</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.weights_uploaded ? (
                                <span className="text-green-600">✓ Yes</span>
                              ) : (
                                <span className="text-gray-500">✗ No</span>
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Participated Rounds</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.rounds.length} {datasetStatus.rounds.length === 1 ? 'Round' : 'Rounds'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600 mb-1">Last Training</p>
                            <p className="font-medium text-sm">
                              {datasetStatus.last_trained_at ? new Date(datasetStatus.last_trained_at).toLocaleString() : 'N/A'}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Column Information */}
                  {selectedDataset.column_names && selectedDataset.column_names.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">
                        Columns ({selectedDataset.column_names.length})
                      </h4>
                      <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-200 sticky top-0">
                            <tr>
                              <th className="text-left p-2 font-semibold">#</th>
                              <th className="text-left p-2 font-semibold">Column Name</th>
                              <th className="text-left p-2 font-semibold">Data Type</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedDataset.column_names.map((col, index) => (
                              <tr key={index} className="border-b border-gray-200">
                                <td className="p-2 text-gray-600">{index + 1}</td>
                                <td className="p-2 font-mono">{col}</td>
                                <td className="p-2 text-gray-600">
                                  <span className="px-2 py-1 bg-blue-100 rounded text-xs">
                                    See Preprocessing Tab
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        💡 View detailed data types and quality metrics in the "Data Preprocessing" tab
                      </p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => navigate('/training')}
                      className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 font-semibold"
                    >
                      Use for Training →
                    </button>
                    <button
                      onClick={() => {
                        setSelectedDataset(null);
                        setDatasetModels([]);
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                /* Preprocessing Tab Content */
                <div className="space-y-4">
                  <DataPreprocessingPanel 
                    datasetId={selectedDataset.id}
                    onPreprocessingComplete={() => {
                      // Reload dataset details after preprocessing
                      handleViewDetails(selectedDataset.id);
                    }}
                  />
                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => {
                        setSelectedDataset(null);
                        setDatasetModels([]);
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm !== null && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Confirm Deletion</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this dataset? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  disabled={deleting}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteDataset(showDeleteConfirm)}
                  disabled={deleting}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default DatasetManagement;
