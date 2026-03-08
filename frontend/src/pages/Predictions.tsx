import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import predictionService from '../services/predictionService';

interface PredictionItem {
  id: number;
  dataset_name?: string;
  model_type: string;
  round_number?: number;
  target_column?: string;
  prediction_timestamp?: string;
  created_at: string;
  forecast_horizon: number;
}

interface PredictionListResponse {
  items: PredictionItem[];
  total: number;
  limit: number;
  offset: number;
}

const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const itemsPerPage = 20;

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchPredictions();
  }, [currentPage]);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      setError('');
      const offset = currentPage * itemsPerPage;
      const response: PredictionListResponse = await predictionService.listPredictions(
        itemsPerPage,
        offset
      );
      setPredictions(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch predictions');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (predictionId: number) => {
    navigate(`/prediction-detail/${predictionId}`);
  };

  const handleExport = async (predictionId: number, format: 'json' | 'csv' | 'pdf') => {
    try {
      const result = await predictionService.exportPrediction(predictionId, format);
      // In a real implementation, this would trigger a file download
      console.log('Export successful:', result);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const toggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === predictions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(predictions.map(p => p.id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) {
      alert('Please select at least one prediction to delete');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ${selectedIds.size} prediction(s)? This cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      setError('');
      const result = await predictionService.deleteSelectedPredictions(Array.from(selectedIds));
      setSelectedIds(new Set());
      await fetchPredictions();
      alert(`Successfully deleted ${result.deleted_count} prediction(s)`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete predictions');
      console.error('Error deleting predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const getModelTypeBadge = (modelType: string) => {
    const bgColor = modelType === 'FEDERATED' ? 'bg-blue-100' : 'bg-green-100';
    const textColor = modelType === 'FEDERATED' ? 'text-blue-800' : 'text-green-800';
    return (
      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${bgColor} ${textColor}`}>
        {modelType}
      </span>
    );
  };

  const totalPages = Math.ceil(total / itemsPerPage);

  return (
    <ConsoleLayout title="Predictions">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Predictions</h1>
            <p className="text-gray-600 mt-1">View and manage your saved predictions</p>
          </div>
          {!loading && predictions.length > 0 && selectedIds.size > 0 && (
            <button
              onClick={handleDeleteSelected}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
            >
              Delete Selected ({selectedIds.size})
            </button>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!loading && predictions.length === 0 && (
          <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8m0 8l-9-2m9 2l9-2m-9-8l9 2m-9-2L3 7m9 2v0" />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No predictions yet</h3>
            <p className="mt-1 text-sm text-gray-600">Generate a forecast to see it here</p>
          </div>
        )}

        {/* Predictions Table */}
        {!loading && predictions.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === predictions.length && predictions.length > 0}
                      onChange={toggleSelectAll}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Round
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Target
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {predictions.map((prediction) => (
                  <tr
                    key={prediction.id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm w-12"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={selectedIds.has(prediction.id)}
                        onChange={() => toggleSelect(prediction.id)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded cursor-pointer"
                      />
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600 cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      #{prediction.id}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      {prediction.dataset_name || 'N/A'}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      {getModelTypeBadge(prediction.model_type)}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      {prediction.round_number ? `Round ${prediction.round_number}` : 'N/A'}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      {prediction.target_column || 'N/A'}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 cursor-pointer"
                      onClick={() => handleViewDetails(prediction.id)}
                    >
                      {formatDate(prediction.prediction_timestamp || prediction.created_at)}
                    </td>
                    <td
                      className="px-6 py-4 whitespace-nowrap text-sm space-x-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="inline-block relative group">
                        <button className="text-gray-600 hover:text-gray-900 font-medium">
                          Export ▼
                        </button>
                        <div className="hidden group-hover:block absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                          <button
                            onClick={() => handleExport(prediction.id, 'json')}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            JSON
                          </button>
                          <button
                            onClick={() => handleExport(prediction.id, 'csv')}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            CSV
                          </button>
                          <button
                            onClick={() => handleExport(prediction.id, 'pdf')}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            PDF Report
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  disabled={currentPage === 0}
                  onClick={() => setCurrentPage(currentPage - 1)}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  disabled={currentPage >= totalPages - 1}
                  onClick={() => setCurrentPage(currentPage + 1)}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing <span className="font-medium">{currentPage * itemsPerPage + 1}</span> to{' '}
                    <span className="font-medium">
                      {Math.min((currentPage + 1) * itemsPerPage, total)}
                    </span>{' '}
                    of <span className="font-medium">{total}</span> results
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      disabled={currentPage === 0}
                      onClick={() => setCurrentPage(currentPage - 1)}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Previous</span>
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </button>
                    {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                      const pageNum = i;
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            currentPage === pageNum
                              ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum + 1}
                        </button>
                      );
                    })}
                    <button
                      disabled={currentPage >= totalPages - 1}
                      onClick={() => setCurrentPage(currentPage + 1)}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Next</span>
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default Predictions;
