import React, { useEffect, useMemo, useState } from 'react';
import ConsoleLayout from '../components/ConsoleLayout';
import { useAuth } from '../context/AuthContext';
import resultsIntelligenceService from '../services/resultsIntelligenceService';
import trainingService from '../services/trainingService';
import { formatErrorMessage } from '../utils/errorMessage';
import { LineChart } from '../components/Charts/LineChart';
import { BarChart } from '../components/Charts/BarChart';
import PieChart from '../components/Charts/PieChart';
import RadarChart from '../components/Charts/RadarChart';
import ScatterChart from '../components/Charts/ScatterChart';
import { Heatmap } from '../components/Charts/Heatmap';

const pct = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
  return `${(value * 100).toFixed(1)}%`;
};

const num = (value: number | null | undefined, digits = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
  return value.toFixed(digits);
};

const MetricCard: React.FC<{ label: string; value: string | number; sub?: string }> = ({ label, value, sub }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <p className="text-xs text-gray-500 uppercase">{label}</p>
    <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
  </div>
);

const BarMeter: React.FC<{ value: number; max?: number }> = ({ value, max = 1 }) => {
  const width = Math.max(0, Math.min(100, (value / (max || 1)) * 100));
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${width}%` }} />
    </div>
  );
};

const ResultsIntelligenceDashboard: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = useMemo(() => {
    if (user?.role) {
      return user.role === 'ADMIN';
    }

    // Fallback for cases where localStorage token is present but context has not hydrated yet.
    const token = localStorage.getItem('access_token');
    if (!token) {
      return false;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload?.role === 'ADMIN';
    } catch {
      return false;
    }
  }, [user?.role]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hospitalData, setHospitalData] = useState<any>(null);
  const [centralData, setCentralData] = useState<any>(null);

  // Model selector states
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);
  const [selectedModelDetails, setSelectedModelDetails] = useState<any>(null);
  const [modelSelectorMode, setModelSelectorMode] = useState(false);

  const [selectedHospitalId, setSelectedHospitalId] = useState<number | null>(null);
  const [selectedHospitalDetail, setSelectedHospitalDetail] = useState<any>(null);
  const [selectedRoundDetail, setSelectedRoundDetail] = useState<any>(null);
  const [selectedPredictionId, setSelectedPredictionId] = useState<number | null>(null);

  // Filter states
  const [filterRoundNumber, setFilterRoundNumber] = useState<string>('');
  const [filterHospitalName, setFilterHospitalName] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Prediction table states
  const [predictionSearch, setPredictionSearch] = useState<string>('');
  const [predictionRiskFilter, setPredictionRiskFilter] = useState<string>('all');
  const [predictionModelFilter, setPredictionModelFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // Model comparison tab state
  const [activeModelTab, setActiveModelTab] = useState<'local' | 'federated'>('local');
  const [activeLocalSubTab, setActiveLocalSubTab] = useState<'ml' | 'tft'>('ml');
  const [activeFederatedSubTab, setActiveFederatedSubTab] = useState<'ml' | 'tft'>('ml');

  // Governance-aligned states
  const [localModelMetrics, setLocalModelMetrics] = useState<any>(null);
  const [approvedGlobalModel, setApprovedGlobalModel] = useState<any>(null);
  const [horizonAnalyticsCache, setHorizonAnalyticsCache] = useState<Record<string, any>>({});
  const [driftAnalysis, setDriftAnalysis] = useState<any>(null);
  const [governanceLoadError, setGovernanceLoadError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      setGovernanceLoadError('');
      try {
        if (isAdmin) {
          const data = await resultsIntelligenceService.getCentralOverview();
          setCentralData(data);
        } else {
          // Load hospital dashboard
          const data = await resultsIntelligenceService.getHospitalOverview();
          setHospitalData(data);

          // Load available models for selector
          try {
            const models = await trainingService.getModels(0, 100);
            setAvailableModels(models);
          } catch (modelsErr: any) {
            console.warn('Failed to load models list:', modelsErr);
          }

          // Load governance-aligned data in parallel for non-admin users
          try {
            const [localMetrics, globalModel, drift] = await Promise.all([
              resultsIntelligenceService.getLocalModelMetrics(),
              resultsIntelligenceService.getApprovedGlobalModel(),
              resultsIntelligenceService.getDriftAnalysis(1),
            ]);
            setLocalModelMetrics(localMetrics);
            setApprovedGlobalModel(globalModel);
            setDriftAnalysis(drift);
          } catch (govErr: any) {
            // Don't fail the entire dashboard if governance data is unavailable
            setGovernanceLoadError('Some governance data unavailable');
            console.warn('Governance data load warning:', govErr);
          }
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load results intelligence dashboard');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [isAdmin]);

  // Load specific model details when selected
  useEffect(() => {
    const loadModelDetails = async () => {
      if (selectedModelId) {
        try {
          const details = await trainingService.getModelById(selectedModelId);
          setSelectedModelDetails(details);
        } catch (err: any) {
          console.error('Failed to load model details:', err);
          setError('Failed to load model details');
        }
      } else {
        setSelectedModelDetails(null);
      }
    };
    loadModelDetails();
  }, [selectedModelId]);

  const ranking = centralData?.global_overview?.hospital_risk_and_performance_ranking || [];

  const localTftInsight = hospitalData?.tft_insight_local || { horizon_performance: [], feature_importance_over_time: [] };
  const federatedTftInsight = hospitalData?.tft_insight_federated || { horizon_performance: [], feature_importance_over_time: [] };
  const localTftTotal = (localTftInsight.horizon_performance || []).reduce((sum: number, horizon: any) => sum + (horizon.count || 0), 0);
  const federatedTftTotal = (federatedTftInsight.horizon_performance || []).reduce((sum: number, horizon: any) => sum + (horizon.count || 0), 0);

  const selectedPrediction = useMemo(() => {
    if (!selectedRoundDetail?.predictions || !selectedPredictionId) return null;
    return selectedRoundDetail.predictions.find((p: any) => p.prediction_id === selectedPredictionId) || null;
  }, [selectedRoundDetail, selectedPredictionId]);

  const handleSelectHospital = async (hospitalId: number) => {
    try {
      setSelectedHospitalId(hospitalId);
      setSelectedRoundDetail(null);
      setSelectedPredictionId(null);
      const detail = await resultsIntelligenceService.getCentralHospitalDetail(hospitalId);
      setSelectedHospitalDetail(detail);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load hospital detail');
    }
  };

  const handleSelectRound = async (hospitalId: number, roundNumber: number) => {
    try {
      setSelectedPredictionId(null);
      const detail = await resultsIntelligenceService.getCentralHospitalRoundDetail(hospitalId, roundNumber);
      setSelectedRoundDetail(detail);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load round detail');
    }
  };

  return (
    <ConsoleLayout
      title={isAdmin ? 'Global Results Intelligence' : 'Results Intelligence'}
      subtitle={isAdmin ? 'Central performance, governance, and traceability monitoring' : 'Local vs federated impact and governance transparency'}
    >
      <div className="max-w-7xl mx-auto space-y-6">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {formatErrorMessage(error)}
          </div>
        )}

        {loading && (
          <div className="bg-white rounded-lg shadow p-6 text-gray-600">Loading dashboard...</div>
        )}

        {/* FILTER CONTROLS FOR ADMIN */}
        {!loading && isAdmin && (
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">Dashboard Filters</h3>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
            </div>
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Filter by Round</label>
                  <input
                    type="text"
                    value={filterRoundNumber}
                    onChange={(e) => setFilterRoundNumber(e.target.value)}
                    placeholder="e.g., 1, 2, 3"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Filter by Hospital</label>
                  <input
                    type="text"
                    value={filterHospitalName}
                    onChange={(e) => setFilterHospitalName(e.target.value)}
                    placeholder="Hospital name"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={() => {
                      setFilterRoundNumber('');
                      setFilterHospitalName('');
                    }}
                    className="w-full bg-gray-600 text-white rounded px-3 py-2 text-sm hover:bg-gray-700"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            )}
            {(filterRoundNumber || filterHospitalName) && (
              <div className="mt-2 text-xs text-gray-600">
                Active filters applied. Charts and tables show filtered data.
              </div>
            )}
          </div>
        )}

        {!loading && !isAdmin && hospitalData && (
          <>
            {/* MODEL SELECTOR TOGGLE */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-gray-900 mb-1">🔍 Model-Specific Analytics</h3>
                  <p className="text-xs text-gray-600">Select a specific trained model to view its detailed metrics and graphs</p>
                </div>
                <button
                  onClick={() => {
                    setModelSelectorMode(!modelSelectorMode);
                    if (modelSelectorMode) {
                      setSelectedModelId(null);
                      setSelectedModelDetails(null);
                    }
                  }}
                  className={`px-4 py-2 rounded font-medium text-sm transition ${
                    modelSelectorMode
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-white text-blue-600 border border-blue-600 hover:bg-blue-50'
                  }`}
                >
                  {modelSelectorMode ? '✓ Model Selector Active' : 'Enable Model Selector'}
                </button>
              </div>

              {modelSelectorMode && (
                <div className="mt-4">
                  <label className="block text-xs font-semibold text-gray-700 mb-2">Select Model:</label>
                  <select
                    value={selectedModelId || ''}
                    onChange={(e) => setSelectedModelId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full md:w-1/2 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">-- Select a Model --</option>
                    {availableModels.map((model: any) => (
                      <option key={model.id} value={model.id}>
                        {model.display_name || `Model ${model.id}`} - {model.model_architecture || model.model_type} 
                        {model.is_global ? ' (Federated)' : ' (Local)'} - Round {model.round_number}
                      </option>
                    ))}
                  </select>
                  {selectedModelDetails && (
                    <div className="mt-3 bg-white border border-gray-200 rounded-lg p-3">
                      <p className="text-xs font-semibold text-gray-900 mb-2">Selected Model Details:</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">Model ID:</span>
                          <span className="ml-1 font-medium text-gray-900">{selectedModelDetails.id}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Round:</span>
                          <span className="ml-1 font-medium text-gray-900">{selectedModelDetails.round_number}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Type:</span>
                          <span className="ml-1 font-medium text-gray-900">
                            {selectedModelDetails.is_global ? '🌐 Federated' : '📊 Local'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Architecture:</span>
                          <span className="ml-1 font-medium text-gray-900">{selectedModelDetails.model_architecture || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* SHOW MODEL-SPECIFIC VIEW OR DEFAULT OVERVIEW */}
            {modelSelectorMode && selectedModelDetails ? (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      📊 Model #{selectedModelDetails.id} - Detailed Analytics
                    </h3>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold ${
                      selectedModelDetails.is_global
                        ? 'bg-green-100 text-green-800'
                        : 'bg-purple-100 text-purple-800'
                    }">
                      {selectedModelDetails.is_global ? '🌐 Federated Model' : '📊 Local Model'}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <MetricCard 
                      label="Loss" 
                      value={num(selectedModelDetails.local_loss, 4)} 
                      sub="Training loss"
                    />
                    {selectedModelDetails.local_r2 !== null && selectedModelDetails.local_r2 !== undefined && (
                      <MetricCard 
                        label="R² Score" 
                        value={pct(selectedModelDetails.local_r2)} 
                        sub="Variance explained"
                      />
                    )}
                    {selectedModelDetails.local_mape !== null && selectedModelDetails.local_mape !== undefined && (
                      <MetricCard 
                        label="MAPE" 
                        value={`${num(selectedModelDetails.local_mape, 2)}%`} 
                        sub="Mean absolute %error"
                      />
                    )}
                    {selectedModelDetails.local_rmse !== null && selectedModelDetails.local_rmse !== undefined && (
                      <MetricCard 
                        label="RMSE" 
                        value={num(selectedModelDetails.local_rmse, 2)} 
                        sub="Root mean squared error"
                      />
                    )}
                    <MetricCard 
                      label="Round" 
                      value={selectedModelDetails.round_number} 
                      sub="Training round"
                    />
                    <MetricCard 
                      label="Architecture" 
                      value={selectedModelDetails.model_architecture || 'ML'} 
                      sub="Model type"
                    />
                    <MetricCard 
                      label="Created" 
                      value={new Date(selectedModelDetails.created_at).toLocaleDateString()} 
                      sub="Training date"
                    />
                  </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-xs text-blue-900 font-semibold mb-2">📘 Model Information</p>
                  <div className="text-xs text-blue-800 space-y-1">
                    <p><span className="font-semibold">Training Type:</span> {selectedModelDetails.training_type || 'Standard'}</p>
                    <p><span className="font-semibold">Model Path:</span> <code className="bg-blue-100 px-1 rounded">{selectedModelDetails.model_path}</code></p>
                    <p><span className="font-semibold">Global Model:</span> {selectedModelDetails.is_global ? 'Yes - This is an aggregated federated model' : 'No - This is a hospital-specific local model'}</p>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* Enhanced Stats Cards with Trends */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow p-4 border border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-blue-600 uppercase font-semibold">Total Predictions</p>
                        <p className="text-3xl font-bold text-blue-900 mt-1">{hospitalData.prediction_overview?.total_predictions ?? 0}</p>
                      </div>
                      <div className="text-blue-500 text-3xl">📊</div>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg shadow p-4 border border-red-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-red-600 uppercase font-semibold">High Risk</p>
                        <p className="text-3xl font-bold text-red-900 mt-1">{hospitalData.prediction_overview?.high_risk_count ?? 0}</p>
                        <p className="text-xs text-red-600 mt-1">Above threshold</p>
                      </div>
                      <div className="text-red-500 text-3xl">⚠️</div>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg shadow p-4 border border-green-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-green-600 uppercase font-semibold">Low Risk</p>
                        <p className="text-3xl font-bold text-green-900 mt-1">{hospitalData.prediction_overview?.low_risk_count ?? 0}</p>
                        <p className="text-xs text-green-600 mt-1">Below threshold</p>
                      </div>
                      <div className="text-green-500 text-3xl">✅</div>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg shadow p-4 border border-purple-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-purple-600 uppercase font-semibold">Avg Confidence</p>
                        <p className="text-3xl font-bold text-purple-900 mt-1">{pct(hospitalData.prediction_overview?.average_confidence_score)}</p>
                        <p className="text-xs text-purple-600 mt-1">Prediction confidence</p>
                      </div>
                      <div className="text-purple-500 text-3xl">🎯</div>
                    </div>
                  </div>
                </div>

                {/* Prediction Analytics Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-4">📊 Risk Distribution</h4>
                    <PieChart
                      title=""
                      labels={['High Risk', 'Low Risk']}
                      data={[
                        hospitalData.prediction_overview?.high_risk_count ?? 0,
                        hospitalData.prediction_overview?.low_risk_count ?? 0
                      ]}
                      height={220}
                    />
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-4">📈 Temporal Prediction Trend</h4>
                    {hospitalData.prediction_results_intelligence?.hospital_level_view?.temporal_prediction_trend?.length > 0 ? (
                      <LineChart
                        title=""
                        labels={(hospitalData.prediction_results_intelligence?.hospital_level_view?.temporal_prediction_trend || []).map((t: any) => t.month)}
                        datasets={[
                          {
                            label: 'Predictions Count',
                            data: (hospitalData.prediction_results_intelligence?.hospital_level_view?.temporal_prediction_trend || []).map((t: any) => t.count),
                            borderColor: '#3b82f6',
                            backgroundColor: '#3b82f6',
                          },
                        ]}
                        yAxisLabel="Count"
                        height={220}
                      />
                    ) : (
                      <div className="text-center py-8 text-gray-400 text-sm">No temporal data available yet</div>
                    )}
                  </div>
                </div>

                {/* Performance Comparison Cards */}
                {hospitalData.model_performance_comparison && (
                  <div className="bg-white rounded-lg shadow p-6 mt-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-4">🎯 Model Performance Comparison</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="border border-gray-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 uppercase">Local R2 Score</p>
                        <p className="text-2xl font-bold text-purple-700 mt-1">
                          {hospitalData.model_performance_comparison.local_accuracy_overall !== null && hospitalData.model_performance_comparison.local_accuracy_overall !== undefined
                            ? (hospitalData.model_performance_comparison.local_accuracy_overall * 100).toFixed(1) + '%'
                            : 'N/A'}
                        </p>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 uppercase">Federated R2 Score</p>
                        <p className="text-2xl font-bold text-blue-700 mt-1">
                          {hospitalData.model_performance_comparison.federated_accuracy_overall !== null && hospitalData.model_performance_comparison.federated_accuracy_overall !== undefined
                            ? (hospitalData.model_performance_comparison.federated_accuracy_overall * 100).toFixed(1) + '%'
                            : 'N/A'}
                        </p>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 uppercase">Federated Gain</p>
                        <p className="text-2xl font-bold text-green-700 mt-1">
                          {hospitalData.model_performance_comparison.federated_gain_delta !== null && hospitalData.model_performance_comparison.federated_gain_delta !== undefined
                            ? (hospitalData.model_performance_comparison.federated_gain_delta >= 0 ? '+' : '') + (hospitalData.model_performance_comparison.federated_gain_delta * 100).toFixed(2) + '%'
                            : 'N/A'}
                        </p>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 uppercase">RMSE</p>
                        <p className="text-2xl font-bold text-indigo-700 mt-1">
                          {hospitalData.model_performance_comparison.federated_rmse_overall !== null && hospitalData.model_performance_comparison.federated_rmse_overall !== undefined
                            ? hospitalData.model_performance_comparison.federated_rmse_overall.toFixed(3)
                            : hospitalData.model_performance_comparison.local_rmse_overall !== null && hospitalData.model_performance_comparison.local_rmse_overall !== undefined
                              ? hospitalData.model_performance_comparison.local_rmse_overall.toFixed(3)
                              : 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Results Intelligence by Component</h3>
                
                {/* PRIMARY TABS: 4 Sections */}
                <div className="flex gap-2 border-b border-gray-200 flex-wrap mb-4">
                  <button
                    onClick={() => { setActiveModelTab('local'); setActiveLocalSubTab('ml'); }}
                    className={`px-4 py-2 font-medium transition ${
                      activeModelTab === 'local' && activeLocalSubTab === 'ml'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    📊 Local ML
                  </button>
                  <button
                    onClick={() => { setActiveModelTab('local'); setActiveLocalSubTab('tft'); }}
                    className={`px-4 py-2 font-medium transition ${
                      activeModelTab === 'local' && activeLocalSubTab === 'tft'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    ⏰ Local TFT
                  </button>
                  <button
                    onClick={() => { setActiveModelTab('federated'); setActiveFederatedSubTab('ml'); }}
                    className={`px-4 py-2 font-medium transition ${
                      activeModelTab === 'federated' && activeFederatedSubTab === 'ml'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    🌐 Federated ML
                  </button>
                  <button
                    onClick={() => { setActiveModelTab('federated'); setActiveFederatedSubTab('tft'); }}
                    className={`px-4 py-2 font-medium transition ${
                      activeModelTab === 'federated' && activeFederatedSubTab === 'tft'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    📈 Federated TFT
                  </button>
                </div>
              </div>

              {/* LOCAL MODEL - ML TAB */}
              {activeModelTab === 'local' && activeLocalSubTab === 'ml' && (
                <div className="space-y-4">
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                    <p className="text-xs font-semibold text-purple-900 mb-1">📊 YOUR HOSPITAL'S LOCAL ML TRAINING</p>
                    <p className="text-xs text-purple-700">Metrics from your hospital's own ML models (Random Forest, XGBoost, etc.) trained on your private data</p>
                  </div>
                  
                  {/* Local ML Predictions */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">📊 Local ML Predictions</h4>
                    {(() => {
                      const localMlPredictions = (hospitalData.recent_predictions || []).filter((pred: any) => {
                        const isLocal = !pred.model_type || pred.model_type.toUpperCase().includes('LOCAL') || pred.model_type === 'N/A';
                        const isMl = !pred.model_architecture || !pred.model_architecture.toUpperCase().includes('TFT');
                        return isLocal && isMl;
                      });
                      
                      return localMlPredictions.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-2 py-2 text-left">ID</th>
                                <th className="px-2 py-2 text-left">Value</th>
                                <th className="px-2 py-2 text-left">Risk</th>
                                <th className="px-2 py-2 text-left">Confidence</th>
                                <th className="px-2 py-2 text-left">Round</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {localMlPredictions.slice(0, 5).map((pred: any) => (
                                <tr key={pred.id} className="hover:bg-gray-50">
                                  <td className="px-2 py-2">#{pred.id}</td>
                                  <td className="px-2 py-2 font-semibold">{pred.prediction_value ? Number(pred.prediction_value).toFixed(2) : 'N/A'}</td>
                                  <td className="px-2 py-2">
                                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                                      pred.risk_label === 'High' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                    }`}>
                                      {pred.risk_label}
                                    </span>
                                  </td>
                                  <td className="px-2 py-2">{pred.confidence_score ? `${(pred.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                                  <td className="px-2 py-2">{pred.round_number ? `R${pred.round_number}` : 'N/A'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {localMlPredictions.length > 5 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">Showing 5 of {localMlPredictions.length} predictions. See full list below.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No local ML predictions found. Train ML models locally to see predictions here.</p>
                      );
                    })()}
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-3">📊 LOCAL ML METRICS</p>
                    <p className="text-sm text-gray-600">Local ML model performance metrics are available via Training History and Models pages.</p>
                  </div>
                </div>
              )}

              {/* LOCAL MODEL - TFT TAB */}
              {activeModelTab === 'local' && activeLocalSubTab === 'tft' && (
                <div className="space-y-4">
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                    <p className="text-xs font-semibold text-purple-900 mb-1">📊 YOUR HOSPITAL'S LOCAL TFT TRAINING</p>
                    <p className="text-xs text-purple-700">TFT temporal metrics from your hospital's own time-series models</p>
                  </div>
                  
                  {/* Local TFT Predictions */}
                  <div className="border border-gray-200 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">⏰ Local TFT Predictions</h4>
                    {(() => {
                      const localTftPredictions = (hospitalData.recent_predictions || []).filter((pred: any) => {
                        const isLocal = !pred.model_type || pred.model_type.toUpperCase().includes('LOCAL') || pred.model_type === 'N/A';
                        const isTft = pred.model_architecture && pred.model_architecture.toUpperCase().includes('TFT');
                        return isLocal && isTft;
                      });
                      
                      return localTftPredictions.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-2 py-2 text-left">ID</th>
                                <th className="px-2 py-2 text-left">Value</th>
                                <th className="px-2 py-2 text-left">Risk</th>
                                <th className="px-2 py-2 text-left">Confidence</th>
                                <th className="px-2 py-2 text-left">Round</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {localTftPredictions.slice(0, 5).map((pred: any) => (
                                <tr key={pred.id} className="hover:bg-gray-50">
                                  <td className="px-2 py-2">#{pred.id}</td>
                                  <td className="px-2 py-2 font-semibold">{pred.prediction_value ? Number(pred.prediction_value).toFixed(2) : 'N/A'}</td>
                                  <td className="px-2 py-2">
                                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                                      pred.risk_label === 'High' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                    }`}>
                                      {pred.risk_label}
                                    </span>
                                  </td>
                                  <td className="px-2 py-2">{pred.confidence_score ? `${(pred.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                                  <td className="px-2 py-2">{pred.round_number ? `R${pred.round_number}` : 'N/A'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {localTftPredictions.length > 5 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">Showing 5 of {localTftPredictions.length} predictions. See full list below.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No local TFT predictions found. Train TFT models locally to see predictions here.</p>
                      );
                    })()}
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-3">⏰ LOCAL TFT TEMPORAL METRICS</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                      <MetricCard label="Horizons Tracked" value={localTftInsight?.horizon_performance?.length ?? 0} sub="Forecast horizons" />
                      <MetricCard label="Total Predictions" value={localTftTotal} sub="Local model predictions" />
                      <MetricCard label="Avg Confidence" value={pct(hospitalData.prediction_overview?.average_confidence_score)} />
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-2">📊 LOCAL HORIZON PERFORMANCE</p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b bg-gray-50">
                            <th className="text-left py-2">Horizon</th>
                            <th className="text-left py-2">Count</th>
                            <th className="text-left py-2">Mean Prediction</th>
                            <th className="text-left py-2">Volatility</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(localTftInsight?.horizon_performance || []).map((h: any) => (
                            <tr key={h.horizon} className="border-b">
                              <td className="py-2 font-medium">{h.horizon}</td>
                              <td className="py-2">{h.count}</td>
                              <td className="py-2">{num(h.mean_prediction, 2)}</td>
                              <td className="py-2">{num(h.volatility, 4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {localTftTotal > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <BarChart
                        title="📊 Local: Mean Predictions by Horizon"
                        labels={(localTftInsight?.horizon_performance || []).map((h: any) => h.horizon)}
                        datasets={[
                          {
                            label: 'Mean Prediction',
                            data: (localTftInsight?.horizon_performance || []).map((h: any) => h.mean_prediction ?? 0),
                            backgroundColor: '#9333ea',
                          },
                        ]}
                        yAxisLabel="Prediction Value"
                        height={250}
                      />

                      <LineChart
                        title="📈 Local: Volatility Across Horizons"
                        labels={(localTftInsight?.horizon_performance || []).map((h: any) => h.horizon)}
                        datasets={[
                          {
                            label: 'Volatility',
                            data: (localTftInsight?.horizon_performance || []).map((h: any) => h.volatility ?? 0),
                            borderColor: '#9333ea',
                            backgroundColor: '#9333ea',
                            fill: false,
                          },
                        ]}
                        yAxisLabel="Volatility Index"
                        height={250}
                      />
                    </div>
                  )}

                  {localTftTotal === 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-600">No local TFT predictions available for this hospital yet.</p>
                    </div>
                  )}

                  {(localTftInsight?.feature_importance_over_time || []).length > 0 && (
                    <div>
                      <BarChart
                        title="🎯 Local TFT Feature Importance"
                        labels={(localTftInsight?.feature_importance_over_time || []).map((f: any) => f.feature)}
                        datasets={[
                          {
                            label: 'Average Importance',
                            data: (localTftInsight?.feature_importance_over_time || []).map((f: any) => f.average_importance ?? 0),
                            backgroundColor: '#9333ea',
                          },
                        ]}
                        yAxisLabel="Importance Score"
                        height={300}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* FEDERATED MODEL - ML TAB */}
              {activeModelTab === 'federated' && activeFederatedSubTab === 'ml' && (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <p className="text-xs font-semibold text-green-900 mb-1">🌐 GLOBAL FEDERATED ML MODEL</p>
                    <p className="text-xs text-green-700">Collaborative ML model trained across multiple hospitals (privacy-preserved)</p>
                  </div>
                  
                  {/* Federated ML Predictions */}
                  <div className="border border-gray-200 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">🌐 Federated ML Predictions</h4>
                    {(() => {
                      const federatedMlPredictions = (hospitalData.recent_predictions || []).filter((pred: any) => {
                        const isFederated = pred.model_type && pred.model_type.toUpperCase().includes('FEDERATED');
                        const isMl = !pred.model_architecture || !pred.model_architecture.toUpperCase().includes('TFT');
                        return isFederated && isMl;
                      });
                      
                      return federatedMlPredictions.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-2 py-2 text-left">ID</th>
                                <th className="px-2 py-2 text-left">Value</th>
                                <th className="px-2 py-2 text-left">Risk</th>
                                <th className="px-2 py-2 text-left">Confidence</th>
                                <th className="px-2 py-2 text-left">Round</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {federatedMlPredictions.slice(0, 5).map((pred: any) => (
                                <tr key={pred.id} className="hover:bg-gray-50">
                                  <td className="px-2 py-2">#{pred.id}</td>
                                  <td className="px-2 py-2 font-semibold">{pred.prediction_value ? Number(pred.prediction_value).toFixed(2) : 'N/A'}</td>
                                  <td className="px-2 py-2">
                                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                                      pred.risk_label === 'High' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                    }`}>
                                      {pred.risk_label}
                                    </span>
                                  </td>
                                  <td className="px-2 py-2">{pred.confidence_score ? `${(pred.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                                  <td className="px-2 py-2">{pred.round_number ? `R${pred.round_number}` : 'N/A'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {federatedMlPredictions.length > 5 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">Showing 5 of {federatedMlPredictions.length} predictions. See full list below.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No federated ML predictions found. Participate in federated rounds with ML models to see predictions here.</p>
                      );
                    })()}
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-3">🌐 FEDERATED ML METRICS</p>
                    <p className="text-sm text-gray-600 mb-4">Federated ML model performance comparison available via Round History and Round Details pages.</p>
                  </div>
                </div>
              )}

              {/* FEDERATED MODEL - TFT TAB */}
              {activeModelTab === 'federated' && activeFederatedSubTab === 'tft' && (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <p className="text-xs font-semibold text-green-900 mb-1">🌐 GLOBAL FEDERATED TFT MODEL</p>
                    <p className="text-xs text-green-700">Collaborative time-series model trained across hospitals (privacy-preserved)</p>
                  </div>
                  
                  {/* Federated TFT Predictions */}
                  <div className="border border-gray-200 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-3">📈 Federated TFT Predictions</h4>
                    {(() => {
                      const federatedTftPredictions = (hospitalData.recent_predictions || []).filter((pred: any) => {
                        const isFederated = pred.model_type && pred.model_type.toUpperCase().includes('FEDERATED');
                        const isTft = pred.model_architecture && pred.model_architecture.toUpperCase().includes('TFT');
                        return isFederated && isTft;
                      });
                      
                      return federatedTftPredictions.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-2 py-2 text-left">ID</th>
                                <th className="px-2 py-2 text-left">Value</th>
                                <th className="px-2 py-2 text-left">Risk</th>
                                <th className="px-2 py-2 text-left">Confidence</th>
                                <th className="px-2 py-2 text-left">Round</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {federatedTftPredictions.slice(0, 5).map((pred: any) => (
                                <tr key={pred.id} className="hover:bg-gray-50">
                                  <td className="px-2 py-2">#{pred.id}</td>
                                  <td className="px-2 py-2 font-semibold">{pred.prediction_value ? Number(pred.prediction_value).toFixed(2) : 'N/A'}</td>
                                  <td className="px-2 py-2">
                                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                                      pred.risk_label === 'High' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                                    }`}>
                                      {pred.risk_label}
                                    </span>
                                  </td>
                                  <td className="px-2 py-2">{pred.confidence_score ? `${(pred.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                                  <td className="px-2 py-2">{pred.round_number ? `R${pred.round_number}` : 'N/A'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {federatedTftPredictions.length > 5 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">Showing 5 of {federatedTftPredictions.length} predictions. See full list below.</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No federated TFT predictions found. Participate in federated rounds with TFT models to see predictions here.</p>
                      );
                    })()}
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-3">⏰ FEDERATED TFT TEMPORAL METRICS</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                      <MetricCard label="Aggregated Horizons" value={federatedTftInsight?.horizon_performance?.length ?? 0} sub="Federated forecast horizons" />
                      <MetricCard label="Total Predictions" value={federatedTftTotal} sub="Federated predictions" />
                      <MetricCard label="Federated Gain" value={num(hospitalData.model_performance_comparison?.federated_gain_delta, 4)} sub="Performance delta" />
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 font-semibold mb-2">📊 FEDERATED HORIZON PERFORMANCE</p>
                    <p className="text-xs text-gray-600 mb-2">Aggregated temporal metrics across federated participating hospitals</p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b bg-gray-50">
                            <th className="text-left py-2">Horizon</th>
                            <th className="text-left py-2">Aggregated Count</th>
                            <th className="text-left py-2">Mean Prediction</th>
                            <th className="text-left py-2">Volatility</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(federatedTftInsight?.horizon_performance || []).map((h: any) => (
                            <tr key={h.horizon} className="border-b">
                              <td className="py-2 font-medium">{h.horizon}</td>
                              <td className="py-2">{h.count}</td>
                              <td className="py-2">{num(h.mean_prediction, 2)}</td>
                              <td className="py-2">{num(h.volatility, 4)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {federatedTftTotal > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <BarChart
                        title="🌐 Federated Mean Predictions by Horizon"
                        labels={(federatedTftInsight?.horizon_performance || []).map((h: any) => h.horizon)}
                        datasets={[
                          {
                            label: 'Federated Mean Prediction',
                            data: (federatedTftInsight?.horizon_performance || []).map((h: any) => h.mean_prediction ?? 0),
                            backgroundColor: '#10b981',
                          },
                        ]}
                        yAxisLabel="Prediction Value"
                        height={250}
                      />

                      <LineChart
                        title="📈 Federated Volatility Trend"
                        labels={(federatedTftInsight?.horizon_performance || []).map((h: any) => h.horizon)}
                        datasets={[
                          {
                            label: 'Federated Volatility',
                            data: (federatedTftInsight?.horizon_performance || []).map((h: any) => h.volatility ?? 0),
                            borderColor: '#10b981',
                            fill: true,
                          },
                        ]}
                        yAxisLabel="Volatility Index"
                        height={250}
                      />
                    </div>
                  )}

                  {federatedTftTotal === 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-600">No federated TFT predictions available for this hospital yet.</p>
                    </div>
                  )}

                  {(federatedTftInsight?.feature_importance_over_time || []).length > 0 && (
                    <div>
                      <BarChart
                        title="🎯 Federated TFT Feature Importance"
                        labels={(federatedTftInsight?.feature_importance_over_time || []).map((f: any) => f.feature)}
                        datasets={[
                          {
                            label: 'Federated Avg Importance',
                            data: (federatedTftInsight?.feature_importance_over_time || []).map((f: any) => f.average_importance ?? 0),
                            backgroundColor: '#10b981',
                          },
                        ]}
                        yAxisLabel="Importance Score"
                        height={300}
                      />
                    </div>
                  )}

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-xs text-blue-900 font-semibold mb-2">🌐 Federated TFT Intelligence</p>
                    <p className="text-xs text-blue-800">These temporal forecasting metrics are aggregated across all participating hospitals using privacy-preserving federated learning. Predictions are made without sharing raw patient data.</p>
                  </div>
                </div>
              )}
            </div>
              </>
            )}
          </>
        )}

        {!loading && !isAdmin && hospitalData && !modelSelectorMode && (
          <>
            {/* Interactive Predictions Table */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">📋 Recent Predictions</h3>
                {hospitalData.recent_predictions && hospitalData.recent_predictions.length > 0 && (
                  <span className="text-sm text-gray-600">Showing {hospitalData.recent_predictions.length} predictions</span>
                )}
              </div>
              
              {hospitalData.recent_predictions && hospitalData.recent_predictions.length > 0 ? (
                <>
                  {/* Search and Filters */}
                  <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <input
                        type="text"
                        placeholder="🔍 Search by ID or value..."
                        value={predictionSearch}
                        onChange={(e) => { setPredictionSearch(e.target.value); setCurrentPage(1); }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <select
                        value={predictionRiskFilter}
                        onChange={(e) => { setPredictionRiskFilter(e.target.value); setCurrentPage(1); }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All Risk Levels</option>
                        <option value="High">High Risk Only</option>
                        <option value="Low">Low Risk Only</option>
                      </select>
                    </div>
                    <div>
                      <select
                        value={predictionModelFilter}
                        onChange={(e) => { setPredictionModelFilter(e.target.value); setCurrentPage(1); }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All Model Types</option>
                        <option value="ML">ML Models (RF, XGB, etc.)</option>
                        <option value="TFT">TFT Models</option>
                        <option value="FEDERATED">Federated Only</option>
                        <option value="LOCAL">Local Only</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">ID</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Prediction Value</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Risk Level</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Confidence</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Model Type</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Round</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase">Created</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(() => {
                          // Apply filters
                          let filtered = hospitalData.recent_predictions.filter((pred: any) => {
                            const searchMatch = predictionSearch === '' || 
                              pred.id.toString().includes(predictionSearch) ||
                              (pred.prediction_value && pred.prediction_value.toString().includes(predictionSearch));
                            const riskMatch = predictionRiskFilter === 'all' || pred.risk_label === predictionRiskFilter;
                            
                            // Model type filter logic
                            let modelMatch = true;
                            if (predictionModelFilter !== 'all') {
                              if (predictionModelFilter === 'ML') {
                                // ML models are those WITHOUT TFT in architecture
                                modelMatch = !pred.model_architecture || !pred.model_architecture.toUpperCase().includes('TFT');
                              } else if (predictionModelFilter === 'TFT') {
                                // TFT models have TFT in architecture
                                modelMatch = pred.model_architecture && pred.model_architecture.toUpperCase().includes('TFT');
                              } else if (predictionModelFilter === 'FEDERATED') {
                                modelMatch = pred.model_type && pred.model_type.toUpperCase().includes('FEDERATED');
                              } else if (predictionModelFilter === 'LOCAL') {
                                modelMatch = !pred.model_type || pred.model_type.toUpperCase().includes('LOCAL') || pred.model_type === 'N/A';
                              }
                            }
                            
                            return searchMatch && riskMatch && modelMatch;
                          });
                          
                          // Apply pagination
                          const startIndex = (currentPage - 1) * itemsPerPage;
                          const endIndex = startIndex + itemsPerPage;
                          const paginatedData = filtered.slice(startIndex, endIndex);
                          const totalPages = Math.ceil(filtered.length / itemsPerPage);
                          
                          return (
                            <>
                              {paginatedData.map((pred: any) => (
                                <tr key={pred.id} className="hover:bg-blue-50 transition-colors cursor-pointer">
                                  <td className="px-4 py-3 text-gray-900 font-medium">#{pred.id}</td>
                                  <td className="px-4 py-3">
                                    <span className="text-gray-900 font-semibold text-base">
                                      {pred.prediction_value !== null && pred.prediction_value !== undefined 
                                        ? Number(pred.prediction_value).toFixed(2) 
                                        : 'N/A'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3">
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                                      pred.risk_label === 'High' 
                                        ? 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300' 
                                        : 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300'
                                    }`}>
                                      {pred.risk_label === 'High' ? '⚠️' : '✅'} {pred.risk_label}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[60px]">
                                        <div 
                                          className="bg-blue-600 h-2 rounded-full transition-all"
                                          style={{ width: `${pred.confidence_score ? pred.confidence_score * 100 : 0}%` }}
                                        />
                                      </div>
                                      <span className="text-gray-700 font-medium">
                                        {pred.confidence_score !== null && pred.confidence_score !== undefined 
                                          ? `${(pred.confidence_score * 100).toFixed(1)}%` 
                                          : 'N/A'}
                                      </span>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3">
                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold shadow-sm ${
                                      pred.model_type === 'FEDERATED' 
                                        ? 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300' 
                                        : 'bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800 border border-purple-300'
                                    }`}>
                                      {pred.model_type === 'FEDERATED' ? '🌐' : '📊'} {pred.model_type || 'LOCAL'}
                                      {pred.model_architecture && pred.model_architecture.toUpperCase().includes('TFT') ? ' (TFT)' : ' (ML)'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-gray-700 font-medium">
                                    {pred.round_number ? `Round ${pred.round_number}` : 'N/A'}
                                  </td>
                                  <td className="px-4 py-3 text-gray-600 text-xs">
                                    {pred.created_at ? new Date(pred.created_at).toLocaleString('en-US', { 
                                      month: 'short', 
                                      day: 'numeric', 
                                      hour: '2-digit', 
                                      minute: '2-digit' 
                                    }) : 'N/A'}
                                  </td>
                                </tr>
                              ))}
                              {paginatedData.length === 0 && (
                                <tr>
                                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                                    <p className="text-sm">No predictions match your filters.</p>
                                  </td>
                                </tr>
                              )}
                              {/* Pagination Controls */}
                              {totalPages > 1 && (
                                <tr>
                                  <td colSpan={7} className="px-4 py-4 bg-gray-50">
                                    <div className="flex items-center justify-between">
                                      <div className="text-sm text-gray-600">
                                        Showing {startIndex + 1}-{Math.min(endIndex, filtered.length)} of {filtered.length}
                                      </div>
                                      <div className="flex gap-2">
                                        <button
                                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                          disabled={currentPage === 1}
                                          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                          ← Previous
                                        </button>
                                        <span className="px-3 py-1 text-sm text-gray-700">
                                          Page {currentPage} of {totalPages}
                                        </span>
                                        <button
                                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                          disabled={currentPage === totalPages}
                                          className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                          Next →
                                        </button>
                                      </div>
                                    </div>
                                  </td>
                                </tr>
                              )}
                            </>
                          );
                        })()}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-gray-300">
                  <div className="text-6xl mb-4">📊</div>
                  <p className="text-lg font-semibold text-gray-700">No predictions found yet</p>
                  <p className="text-sm text-gray-500 mt-2">Generate predictions from your trained models to see results here.</p>
                  <button
                    onClick={() => window.location.href = '/generate-prediction'}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Generate Prediction
                  </button>
                </div>
              )}
            </div>
          </>
        )}

        {!loading && isAdmin && centralData && (
          <>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Round-Level Model Statistics</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Round</th>
                      <th className="text-left py-2">Loss</th>
                      <th className="text-left py-2">Compliance</th>
                      <th className="text-left py-2">DP ε</th>
                      <th className="text-left py-2">MPC</th>
                      <th className="text-left py-2">Blockchain</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(centralData.round_level_model_statistics || []).map((row: any) => (
                      <tr key={row.round_number} className="border-b">
                        <td className="py-2">{row.round_number}</td>
                        <td className="py-2">{num(row.core_performance_metrics?.loss, 4)}</td>
                        <td className="py-2">{pct(row.participation_metrics?.submission_compliance_rate)}</td>
                        <td className="py-2">{num(row.privacy_and_governance_metrics?.dp_epsilon_used, 4)}</td>
                        <td className="py-2">{pct(row.privacy_and_governance_metrics?.mpc_success_confirmation?.success_rate)}</td>
                        <td className="py-2">{row.privacy_and_governance_metrics?.blockchain_hash_recorded ? 'Yes' : 'No'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ROUND PERFORMANCE VISUAL TRENDS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <LineChart
                title="📈 Global Loss Metric Across Rounds"
                labels={(centralData.round_level_model_statistics || []).map((r: any) => `R${r.round_number}`)}
                datasets={[
                  {
                    label: 'Loss',
                    data: (centralData.round_level_model_statistics || []).map((r: any) => r.core_performance_metrics?.loss ?? null),
                    borderColor: '#10b981',
                  },
                ]}
                yAxisLabel="Loss Value"
                height={260}
              />

              <LineChart
                title="📉 Model Loss & Convergence Trend"
                labels={(centralData.round_level_model_statistics || []).map((r: any) => `R${r.round_number}`)}
                datasets={[
                  {
                    label: 'Loss',
                    data: (centralData.round_level_model_statistics || []).map((r: any) => r.core_performance_metrics?.loss ?? null),
                    borderColor: '#ef4444',
                  },
                  {
                    label: 'Convergence Score',
                    data: (centralData.round_level_model_statistics || []).map((r: any) => r.stability_metrics?.convergence_score ?? null),
                    borderColor: '#8b5cf6',
                  },
                ]}
                yAxisLabel="Value"
                height={260}
              />
            </div>

            {/* PARTICIPATION & COMPLIANCE PIE CHART */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PieChart
                title="🥧 Round Completion Status"
                labels={(centralData.global_overview?.federated_round_summary?.participation_rate_heatmap || []).map((r: any) => `Round ${r.round_number}`)}
                data={(centralData.global_overview?.federated_round_summary?.participation_rate_heatmap || []).map((r: any) => r.participation_rate * 100)}
                height={260}
              />

              <BarChart
                title="📊 Submission Compliance Rate by Round"
                labels={(centralData.round_level_model_statistics || []).map((r: any) => `R${r.round_number}`)}
                datasets={[
                  {
                    label: 'Compliance %',
                    data: (centralData.round_level_model_statistics || []).map((r: any) => (r.participation_metrics?.submission_compliance_rate ?? 0) * 100),
                    backgroundColor: '#10b981',
                  },
                ]}
                yAxisLabel="Compliance %"
                height={260}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Automatic Round Health Indicators</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(centralData.automatic_round_health_indicators || []).map((indicator: any) => (
                  <div key={indicator.round_number} className="border rounded p-3">
                    <p className="text-sm font-medium">{indicator.icon} Round {indicator.round_number}: {indicator.label}</p>
                    <ul className="list-disc list-inside text-xs text-gray-600 mt-1">
                      {(indicator.reasons || []).map((reason: string, idx: number) => (
                        <li key={`${indicator.round_number}-${idx}`}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <MetricCard label="Total Rounds" value={centralData.global_overview?.federated_round_summary?.total_rounds ?? 0} />
              <MetricCard label="Active Rounds" value={centralData.global_overview?.federated_round_summary?.active_rounds ?? 0} />
              <MetricCard label="Round Success Rate" value={pct(centralData.global_overview?.federated_round_summary?.round_completion_success_rate)} />
              <MetricCard label="MPC Success Rate" value={pct(centralData.global_overview?.governance_and_compliance_overview?.secure_mpc_success_rate)} />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cross-Round Trend Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="border rounded p-4">
                  <h4 className="font-medium text-sm mb-2">Loss & Participation Trends</h4>
                  <div className="max-h-48 overflow-y-auto space-y-1 text-xs">
                    {(centralData.cross_round_trend_analysis?.loss_trend || []).map((row: any) => {
                      const pRow = (centralData.cross_round_trend_analysis?.participation_trend || []).find((p: any) => p.round_number === row.round_number);
                      return (
                        <div key={row.round_number} className="flex justify-between border-b pb-1">
                          <span>Round {row.round_number}</span>
                          <span>L:{num(row?.loss, 4)} P:{pct(pRow?.compliance_rate)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div className="border rounded p-4">
                  <h4 className="font-medium text-sm mb-2">Aggregation Time per Round (hrs)</h4>
                  <div className="space-y-1 max-h-36 overflow-y-auto">
                    {(centralData.cross_round_trend_analysis?.aggregation_time_per_round || []).map((t: any) => (
                      <div key={t.round_number} className="text-xs flex justify-between">
                        <span>Round {t.round_number}</span>
                        <span>{num(t.aggregation_time_hours, 2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* CROSS-ROUND VISUAL ANALYTICS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <LineChart
                title="📈 Cross-Round Loss & Participation Trends"
                labels={(centralData.cross_round_trend_analysis?.loss_trend || []).map((r: any) => `R${r.round_number}`)}
                datasets={[
                  {
                    label: 'Loss',
                    data: (centralData.cross_round_trend_analysis?.loss_trend || []).map((r: any) => r.loss ?? null),
                    borderColor: '#10b981',
                    fill: true,
                  },
                  {
                    label: 'Participation',
                    data: (centralData.cross_round_trend_analysis?.participation_trend || []).map((r: any) => r.compliance_rate ?? null),
                    borderColor: '#3b82f6',
                    fill: true,
                  },
                ]}
                yAxisLabel="Rate"
                height={260}
              />

              <BarChart
                title="📊 Aggregation Time per Round (Visual)"
                labels={(centralData.cross_round_trend_analysis?.aggregation_time_per_round || []).map((t: any) => `R${t.round_number}`)}
                datasets={[
                  {
                    label: 'Time (hours)',
                    data: (centralData.cross_round_trend_analysis?.aggregation_time_per_round || []).map((t: any) => t.aggregation_time_hours ?? 0),
                    backgroundColor: '#8b5cf6',
                  },
                ]}
                yAxisLabel="Hours"
                height={260}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Federated Round Summary & Participation Heatmap</h3>
              <div className="space-y-3">
                {(centralData.global_overview?.federated_round_summary?.participation_rate_heatmap || []).map((item: any) => (
                  <div key={item.round_number}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Round {item.round_number} ({item.status})</span>
                      <span>{pct(item.participation_rate)}</span>
                    </div>
                    <BarMeter value={item.participation_rate || 0} max={1} />
                  </div>
                ))}
              </div>
            </div>

            {/* HOSPITAL COMPARISON VISUAL ANALYTICS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RadarChart
                title="🎯 Hospital Multi-Metric Comparison (Top 5)"
                labels={['Quality', 'Compliance']}
                datasets={ranking.slice(0, 5).map((hospital: any) => ({
                  label: hospital.hospital_name,
                  data: [
                    hospital.dataset_quality_score ?? 0,
                    hospital.submission_compliance_rate ?? 0,
                  ],
                }))}
                height={280}
              />

              <BarChart
                title="📊 Hospital Dataset Quality Comparison"
                labels={ranking.slice(0, 8).map((h: any) => h.hospital_name)}
                datasets={[
                  {
                    label: 'Dataset Quality Score',
                    data: ranking.slice(0, 8).map((h: any) => (h.dataset_quality_score ?? 0) * 100),
                    backgroundColor: ranking.slice(0, 8).map((h: any) => {
                      const cat = h.contributor_category || h.category;
                      if (cat === 'High Impact Contributor') return '#10b981';
                      if (cat === 'Stable Performer') return '#3b82f6';
                      if (cat === 'Underperforming') return '#f59e0b';
                      return '#94a3b8';
                    }),
                  },
                ]}
                horizontal
                yAxisLabel="Quality %"
                height={280}
              />
            </div>

            {/* PREDICTION VOLUME BAR CHART */}
            <BarChart
              title="📊 Prediction Volume by Hospital"
              labels={(centralData.global_overview?.prediction_volume_analytics?.predictions_per_hospital || []).map((h: any) => h.hospital_name)}
              datasets={[
                {
                  label: 'Total Predictions',
                  data: (centralData.global_overview?.prediction_volume_analytics?.predictions_per_hospital || []).map((h: any) => h.predictions),
                  backgroundColor: '#8b5cf6',
                },
              ]}
              yAxisLabel="Count"
              height={260}
            />

            {/* MONTHLY TREND LINE */}
            <LineChart
              title="📈 Monthly Prediction Volume & Anomaly Detection"
              labels={(centralData.global_overview?.prediction_volume_analytics?.anomaly_detection_signals || []).map((a: any) => a.month)}
              datasets={[
                {
                  label: 'Predictions',
                  data: (centralData.global_overview?.prediction_volume_analytics?.anomaly_detection_signals || []).map((a: any) => a.count),
                  borderColor: '#3b82f6',
                  fill: true,
                },
              ]}
              yAxisLabel="Count"
              height={260}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Hospital Risk & Performance Ranking</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Hospital</th>
                        <th className="text-left py-2">Dataset Quality</th>
                        <th className="text-left py-2">Compliance</th>
                        <th className="text-left py-2">Category</th>
                        <th className="text-left py-2">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ranking.map((row: any) => (
                        <tr key={row.hospital_id} className="border-b">
                          <td className="py-2">{row.hospital_name}</td>
                          <td className="py-2">{pct(row.dataset_quality_score)}</td>
                          <td className="py-2">{pct(row.submission_compliance_rate)}</td>
                          <td className="py-2">{row.contributor_category || row.category}</td>
                          <td className="py-2">
                            <button
                              onClick={() => handleSelectHospital(row.hospital_id)}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              View Hospital
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Prediction Volume Analytics</h3>
                <div className="space-y-3">
                  {(centralData.global_overview?.prediction_volume_analytics?.predictions_per_hospital || []).map((entry: any) => (
                    <div key={entry.hospital_id} className="border rounded p-3">
                      <p className="font-medium text-sm">{entry.hospital_name}</p>
                      <p className="text-xs text-gray-600">Predictions: {entry.predictions} • Medium Risk Frequency: {pct(entry.high_risk_frequency)}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <p className="text-sm font-medium mb-2">Monthly Trend & Anomaly Signals</p>
                  <div className="space-y-2">
                    {(centralData.global_overview?.prediction_volume_analytics?.anomaly_detection_signals || []).map((a: any) => (
                      <div key={a.month} className="flex justify-between text-xs border-b pb-1">
                        <span>{a.month}</span>
                        <span className={a.is_anomaly ? 'text-red-600 font-semibold' : 'text-gray-700'}>
                          {a.count}{a.is_anomaly ? ' (anomaly)' : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Prediction Results Intelligence (Central Aggregated)</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <MetricCard label="Total Predictions" value={centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.total_predictions_across_hospitals ?? 0} />
                <MetricCard label="Federated Gain Index" value={num(centralData.advanced_statistics?.federated_gain_index, 4)} />
                <MetricCard label="Participation Impact" value={num(centralData.advanced_statistics?.participation_impact_score, 4)} />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="border rounded p-4">
                  <h4 className="font-medium text-sm mb-2">Medium Risk Heatmap by Hospital</h4>
                  <div className="space-y-1 max-h-44 overflow-y-auto">
                    {(centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.risk_heatmap_by_hospital || []).map((entry: any) => (
                      <div key={entry.hospital_id} className="text-xs flex justify-between border-b pb-1">
                        <span>{entry.hospital_name}</span>
                        <span>{pct(entry.high_risk_frequency)}{entry.is_outlier ? ' • outlier' : ''}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="border rounded p-4">
                  <h4 className="font-medium text-sm mb-2">Medium-Risk Frequency Trend</h4>
                  <div className="space-y-1 max-h-44 overflow-y-auto">
                    {(centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.high_risk_frequency_trend || []).map((entry: any) => (
                      <div key={entry.month} className="text-xs flex justify-between border-b pb-1">
                        <span>{entry.month}</span>
                        <span>{entry.high_risk_proxy}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* PREDICTION INTELLIGENCE VISUAL DASHBOARDS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <BarChart
                title="🔥 Medium Risk Frequency Heatmap by Hospital"
                labels={(centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.risk_heatmap_by_hospital || []).map((h: any) => h.hospital_name)}
                datasets={[
                  {
                    label: 'Medium Risk %',
                    data: (centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.risk_heatmap_by_hospital || []).map((h: any) => (h.high_risk_frequency ?? 0) * 100),
                    backgroundColor: (centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.risk_heatmap_by_hospital || []).map((h: any) => h.is_outlier ? '#d97706' : '#fbbf24'),
                  },
                ]}
                horizontal
                yAxisLabel="Medium Risk %"
                height={260}
              />

              <LineChart
                title="📈 Medium-Risk Frequency Trend Over Time"
                labels={(centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.high_risk_frequency_trend || []).map((t: any) => t.month)}
                datasets={[
                  {
                    label: 'Medium Risk Predictions',
                    data: (centralData.global_overview?.prediction_results_intelligence?.central_aggregated_view?.high_risk_frequency_trend || []).map((t: any) => t.high_risk_proxy ?? 0),
                    borderColor: '#f59e0b',
                    fill: true,
                  },
                ]}
                yAxisLabel="Count"
                height={260}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Governance & Compliance Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
                <MetricCard label="MPC Success" value={pct(centralData.global_overview?.governance_and_compliance_overview?.secure_mpc_success_rate)} />
                <MetricCard label="Blockchain Coverage" value={pct(centralData.global_overview?.governance_and_compliance_overview?.blockchain_audit_coverage)} />
                <MetricCard label="Failed Validations" value={centralData.global_overview?.governance_and_compliance_overview?.failed_validation_incidents ?? 0} />
                <MetricCard label="Participation Correlation" value={num(centralData.advanced_statistics?.participation_correlation_analysis, 3)} />
              </div>
              <div className="space-y-2">
                {(centralData.global_overview?.governance_and_compliance_overview?.average_dp_epsilon_per_round || []).map((e: any) => (
                  <div key={e.round_number} className="text-xs text-gray-700">Round {e.round_number}: Avg ε = {num(e.average_epsilon, 4)}</div>
                ))}
              </div>
            </div>

            {/* GOVERNANCE VISUAL ANALYTICS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <LineChart
                title="📊 DP Epsilon (ε) Usage per Round"
                labels={(centralData.global_overview?.governance_and_compliance_overview?.average_dp_epsilon_per_round || []).map((e: any) => `R${e.round_number}`)}
                datasets={[
                  {
                    label: 'Average ε',
                    data: (centralData.global_overview?.governance_and_compliance_overview?.average_dp_epsilon_per_round || []).map((e: any) => e.average_epsilon ?? 0),
                    borderColor: '#8b5cf6',
                    fill: true,
                  },
                ]}
                yAxisLabel="Epsilon"
                height={260}
              />

              <PieChart
                title="🔐 Governance Metrics Overview"
                labels={['MPC Success %', 'Blockchain Coverage %']}
                data={[
                  (centralData.global_overview?.governance_and_compliance_overview?.secure_mpc_success_rate ?? 0) * 100,
                  (centralData.global_overview?.governance_and_compliance_overview?.blockchain_audit_coverage ?? 0) * 100,
                ]}
                colors={['#10b981', '#3b82f6']}
                height={260}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Drill-down Chain: Global → Hospital → Round → Prediction → Dataset</h3>

              {!selectedHospitalDetail && (
                <p className="text-sm text-gray-600">Select a hospital from the ranking table to start drill-down analysis.</p>
              )}

              {selectedHospitalDetail && (
                <div className="space-y-4">
                  <div className="border rounded p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Selected Hospital</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {selectedHospitalDetail.hospital?.hospital_name} ({selectedHospitalDetail.hospital?.hospital_id})
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedHospitalId(null);
                          setSelectedHospitalDetail(null);
                          setSelectedRoundDetail(null);
                          setSelectedPredictionId(null);
                        }}
                        className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        Clear
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="border rounded p-4">
                      <h4 className="font-medium mb-2">Round Participation Timeline</h4>
                      <div className="max-h-60 overflow-y-auto space-y-2">
                        {(selectedHospitalDetail.drilldown?.round_participation_timeline || []).map((round: any) => (
                          <div key={round.round_number} className="flex items-center justify-between text-sm border-b pb-1">
                            <span>Round {round.round_number} • {round.status}</span>
                            <button
                              onClick={() => handleSelectRound(selectedHospitalId!, round.round_number)}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Open Round
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="border rounded p-4">
                      <h4 className="font-medium mb-2">Submission Latency Graph (hours)</h4>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {(selectedHospitalDetail.drilldown?.submission_latency_graph || []).map((point: any) => (
                          <div key={`${point.round_number}-${point.submitted_at}`}>
                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                              <span>Round {point.round_number}</span>
                              <span>{num(point.latency_hours, 2)}h</span>
                            </div>
                            <BarMeter value={point.latency_hours || 0} max={72} />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {selectedRoundDetail && (
                    <div className="border rounded p-4">
                      <h4 className="font-medium mb-3">Round {selectedRoundDetail.round?.round_number} Detail</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                        <MetricCard label="Status" value={selectedRoundDetail.round?.status || 'N/A'} />
                        <MetricCard label="Participants" value={selectedRoundDetail.round?.num_participating_hospitals ?? 0} />
                        <MetricCard label="Target" value={selectedRoundDetail.round?.target_column || 'N/A'} />
                      </div>

                      <h5 className="font-medium text-sm mb-2">Predictions in Round</h5>
                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2">Prediction ID</th>
                              <th className="text-left py-2">Value</th>
                              <th className="text-left py-2">Horizon</th>
                              <th className="text-left py-2">Dataset</th>
                              <th className="text-left py-2">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(selectedRoundDetail.predictions || []).map((prediction: any) => (
                              <tr key={prediction.prediction_id} className="border-b">
                                <td className="py-2">#{prediction.prediction_id}</td>
                                <td className="py-2">{num(prediction.prediction_value)}</td>
                                <td className="py-2">{prediction.forecast_horizon}h</td>
                                <td className="py-2">{prediction.dataset?.filename || 'N/A'}</td>
                                <td className="py-2">
                                  <button
                                    onClick={() => setSelectedPredictionId(prediction.prediction_id)}
                                    className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700"
                                  >
                                    View Prediction
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {selectedPrediction && (
                        <div className="mt-4 bg-gray-50 border rounded p-4">
                          <h5 className="font-medium text-sm mb-2">Prediction #{selectedPrediction.prediction_id} → Dataset Drill-down</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                            <div>
                              <p><strong>Prediction Value:</strong> {num(selectedPrediction.prediction_value)}</p>
                              <p><strong>Forecast Horizon:</strong> {selectedPrediction.forecast_horizon}h</p>
                              <p><strong>Created At:</strong> {selectedPrediction.created_at || 'N/A'}</p>
                            </div>
                            <div>
                              <p><strong>Dataset ID:</strong> {selectedPrediction.dataset?.dataset_id ?? 'N/A'}</p>
                              <p><strong>Dataset File:</strong> {selectedPrediction.dataset?.filename || 'N/A'}</p>
                              <p><strong>Rows / Columns:</strong> {selectedPrediction.dataset?.num_rows ?? 'N/A'} / {selectedPrediction.dataset?.num_columns ?? 'N/A'}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default ResultsIntelligenceDashboard;
