import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface PrivacyPolicy {
  epsilon_per_round: number;
  clip_norm: number;
  noise_multiplier: number;
  max_local_epochs: number;
  max_batch_size: number;
  dp_mode: string;
  strict_dp_enabled: boolean;
  timestamp: string;
  policy_status: string;
}

interface EpsilonMetrics {
  current_round_epsilon: number;
  cumulative_epsilon: number;
  max_allowed_epsilon: number;
  epsilon_remaining: number;
  epsilon_utilization_percent: number;
  round_number: number;
  rounds_completed: number;
  dp_mode: string;
  strict_dp_available: boolean;
}

interface PrivacyGovernancePanelProps {
  mode: 'local' | 'federated';
  trainingActive?: boolean;
  currentEpochs?: number;
  currentBatchSize?: number;
}

/**
 * Privacy Governance Panel Component
 * 
 * Displays:
 * - DP Mode (Batch-Level Only)
 * - Privacy Parameters (epsilon, clip_norm, noise_multiplier, etc.)
 * - Epsilon Usage Metrics
 * - Strict DP Status (Always Disabled)
 * - Training Enforcement Banner
 */
export const PrivacyGovernancePanel: React.FC<PrivacyGovernancePanelProps> = ({
  mode,
  trainingActive = false,
  currentEpochs = 0,
  currentBatchSize = 0
}) => {
  const [policy, setPolicy] = useState<PrivacyPolicy | null>(null);
  const [metrics, setMetrics] = useState<EpsilonMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchPrivacyData();
  }, []);

  const fetchPrivacyData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');

      // Fetch policy
      const policyRes = await axios.get(`${API_URL}/api/privacy/policy`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPolicy(policyRes.data);

      // Fetch epsilon metrics
      const metricsRes = await axios.get(`${API_URL}/api/privacy/metrics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMetrics(metricsRes.data);

      setError(null);
    } catch (err) {
      console.error('Failed to fetch privacy data:', err);
      setError('Failed to load privacy governance data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="animate-pulse">Loading privacy governance data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  const isWithinBounds = () => {
    if (!policy) return false;
    return (
      currentEpochs <= policy.max_local_epochs &&
      currentBatchSize <= policy.max_batch_size
    );
  };

  const getEpsilonBarColor = () => {
    if (!metrics) return 'bg-green-500';
    const utilization = metrics.epsilon_utilization_percent;
    if (utilization < 50) return 'bg-green-500';
    if (utilization < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-4">
      {/* 🔐 Privacy Governance Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="text-2xl">🔐</div>
          <div>
            <h3 className="font-bold text-lg text-blue-900">Privacy Governance</h3>
            <p className="text-sm text-blue-700">
              {mode === 'federated' ? 'Federated Training' : 'Local Training'} - 
              Batch-Level DP Enforced
            </p>
          </div>
        </div>
      </div>

      {/* DP Mode Status */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">DP Mode Status</h4>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">DP Mode:</span>
            <span className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              ✓ Batch-Level (Production Validated)
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Strict Per-Sample DP:</span>
            <span className="inline-block bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
              ✗ Disabled
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Enforcement Level:</span>
            <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
              MANDATORY
            </span>
          </div>
        </div>
      </div>

      {/* Privacy Parameters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Privacy Parameters</h4>
        
        {policy && (
          <div className="space-y-3">
            {/* Epsilon Per Round */}
            <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Epsilon per Round:</span>
              <span className="font-mono font-semibold text-gray-900">
                {policy.epsilon_per_round}
              </span>
            </div>

            {/* Clip Norm */}
            <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Clipping Threshold:</span>
              <span className="font-mono font-semibold text-gray-900">
                {policy.clip_norm}
              </span>
            </div>

            {/* Noise Multiplier */}
            <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-gray-600">Noise Multiplier:</span>
              <span className="font-mono font-semibold text-gray-900">
                {policy.noise_multiplier}
              </span>
            </div>

            {/* Constraints */}
            <div className="border-t pt-3 mt-3">
              {/* Mode Indicator */}
              <div className={`mb-3 p-3 rounded-lg border-2 ${
                mode === 'federated' 
                  ? 'bg-blue-50 border-blue-300' 
                  : 'bg-green-50 border-green-300'
              }`}>
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {mode === 'federated' ? '🔒' : '✏️'}
                  </span>
                  <div>
                    <p className={`font-semibold ${
                      mode === 'federated' ? 'text-blue-900' : 'text-green-900'
                    }`}>
                      {mode === 'federated' 
                        ? 'Parameter Control: LOCKED' 
                        : 'Parameter Control: FLEXIBLE'}
                    </p>
                    <p className={`text-xs ${
                      mode === 'federated' ? 'text-blue-700' : 'text-green-700'
                    }`}>
                      {mode === 'federated'
                        ? 'Controlled by central privacy policy (coordination required)'
                        : 'User-selected parameters (experimentation mode)'}
                    </p>
                  </div>
                </div>
              </div>

              <div className={`flex justify-between items-center p-2 rounded mb-2 ${
                mode === 'federated' ? 'bg-gray-100' : 'bg-green-50'
              }`}>
                <span className="text-gray-600 flex items-center gap-2">
                  {mode === 'federated' && '🔒'}
                  Max Local Epochs:
                </span>
                <span className={`font-mono font-semibold ${
                  mode === 'federated' ? 'text-gray-600' : 'text-green-700'
                }`}>
                  {mode === 'federated' ? (
                    `${policy.max_local_epochs} (enforced)`
                  ) : (
                    `${policy.max_local_epochs} (advisory)`
                  )}
                  {mode === 'local' && currentEpochs > 0 && (
                    <span className="text-blue-600 ml-2">
                      {`(current: ${currentEpochs})`}
                    </span>
                  )}
                </span>
              </div>

              <div className={`flex justify-between items-center p-2 rounded ${
                mode === 'federated' ? 'bg-gray-100' : 'bg-green-50'
              }`}>
                <span className="text-gray-600 flex items-center gap-2">
                  {mode === 'federated' && '🔒'}
                  Max Batch Size:
                </span>
                <span className={`font-mono font-semibold ${
                  mode === 'federated' ? 'text-gray-600' : 'text-green-700'
                }`}>
                  {mode === 'federated' ? (
                    `${policy.max_batch_size} (enforced)`
                  ) : (
                    `${policy.max_batch_size} (advisory)`
                  )}
                  {mode === 'local' && currentBatchSize > 0 && (
                    <span className="text-blue-600 ml-2">
                      {`(current: ${currentBatchSize})`}
                    </span>
                  )}
                </span>
              </div>
            </div>

            {/* Parameters Status */}
            {mode === 'local' && currentEpochs > 0 && (
              <div className="mt-2 p-3 rounded-lg bg-green-50 border border-green-200 text-sm">
                <p className="text-green-800 font-semibold mb-1">
                  ✓ Local Mode: User-Controlled Parameters
                </p>
                <p className="text-green-700 text-xs">
                  You can adjust epochs and batch size freely. Advisory limits shown for reference.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Epsilon Usage Dashboard */}
      {metrics && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Epsilon Usage</h4>
          
          <div className="space-y-3">
            {/* Current Round Epsilon */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Current Round:</span>
                <span className="text-sm font-semibold text-gray-900">
                  {metrics.current_round_epsilon} / {metrics.max_allowed_epsilon}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getEpsilonBarColor()}`}
                  style={{ width: `${(metrics.current_round_epsilon / metrics.max_allowed_epsilon) * 100}%` }}
                />
              </div>
            </div>

            {/* Cumulative Epsilon */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-600">Cumulative (Rounds 1-{metrics.round_number}):</span>
                <span className="text-sm font-semibold text-gray-900">
                  {metrics.cumulative_epsilon.toFixed(2)} / {metrics.max_allowed_epsilon}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getEpsilonBarColor()}`}
                  style={{ width: `${(metrics.cumulative_epsilon / metrics.max_allowed_epsilon) * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Utilization: {metrics.epsilon_utilization_percent.toFixed(1)}%
              </p>
            </div>

            {/* Epsilon Remaining */}
            <div className="bg-blue-50 p-2 rounded">
              <div className="flex justify-between">
                <span className="text-sm text-blue-700">Remaining Budget:</span>
                <span className="text-sm font-semibold text-blue-900">
                  {metrics.epsilon_remaining.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Training Confirmation Banner */}
      {trainingActive && policy && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-2xl">✓</div>
            <div>
              <h5 className="font-bold text-green-900">Privacy Policy Enforced</h5>
              <div className="text-sm text-green-700 mt-1 space-y-1">
                <p>✓ DP Mode: Batch-Level</p>
                <p>✓ Epsilon: {policy.epsilon_per_round}</p>
                <p>✓ Clip Norm: {policy.clip_norm}</p>
                <p>✓ Noise Multiplier: {policy.noise_multiplier}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Read-Only Notice for Federated */}
      {mode === 'federated' && (
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🔒</span>
            <div>
              <p className="font-bold text-blue-900 mb-1">
                Federated Mode: Central Policy Enforced
              </p>
              <p className="text-sm text-blue-700">
                All privacy parameters are controlled by the central server for coordination across hospitals.
                Local overrides are <strong>not permitted</strong>.
              </p>
              <ul className="mt-2 text-xs text-blue-600 space-y-1">
                <li>✓ Max epochs: {policy?.max_local_epochs} (enforced)</li>
                <li>✓ Max batch size: {policy?.max_batch_size} (enforced)</li>
                <li>✓ Batch-level DP: Always active</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Local Mode Edit Notice */}
      {mode === 'local' && (
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">✏️</span>
            <div>
              <p className="font-bold text-green-900 mb-1">
                Local Mode: Flexible Parameter Control
              </p>
              <p className="text-sm text-green-700 mb-2">
                You can adjust training parameters freely for local experimentation.
                Advisory limits are shown for reference.
              </p>
              <ul className="text-xs text-green-600 space-y-1">
                <li>✓ Epochs: User-controlled (advisory max: {policy?.max_local_epochs})</li>
                <li>✓ Batch size: User-controlled (advisory max: {policy?.max_batch_size})</li>
                <li>✓ Batch-level DP: Always active</li>
                <li>✓ Epsilon tracking: Enabled</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrivacyGovernancePanel;
