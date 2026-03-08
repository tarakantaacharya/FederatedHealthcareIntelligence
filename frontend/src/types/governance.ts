/**
 * Governance-aligned types for Results Intelligence dashboard
 * Phase 42+: Governance-grade intelligence module with strict data provenance
 */

/**
 * Local model evaluation metrics response
 */
export interface LocalModelMetrics {
  success: boolean;
  metrics: {
    accuracy: number | null;
    loss: number | null;
    mape: number | null;
    rmse: number | null;
    r2: number | null;
  };
  round_number: number;
  created_at: string | null;
  model_hash: string | null;
  reason: string | null;
}

/**
 * Approved global model response
 */
export interface ApprovedGlobalModel {
  success: boolean;
  model: {
    model_hash: string;
    round_number: number;
    created_at: string | null;
    training_started_at: string | null;
  };
  governance: {
    approved: boolean;
    approved_by: string | null;
    approval_timestamp: string | null;
    policy_version: string;
    signature: string | null;
  };
  reason: string | null;
}

/**
 * Round governance summary with DP, participation, and aggregation metadata
 */
export interface RoundGovernanceSummary {
  round_number: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  participating_hospital_ids: number[];
  participating_hospitals_count: number;
  privacy: {
    avg_dp_epsilon: number | null;
    min_dp_epsilon: number | null;
    max_dp_epsilon: number | null;
    epsilon_per_hospital: Record<number, number>;
  };
  error: string | null;
}

/**
 * TFT horizon analytics with volume validation
 */
export interface HorizonAnalytics {
  horizon_key: string;
  has_data: boolean;
  volume: number;
  mae: number | null;
  rmse: number | null;
  mean_prediction: number;
  median_prediction: number;
  std_prediction: number;
  min_prediction: number;
  max_prediction: number;
  reason: string | null;
}

/**
 * Drift analysis using PSI (Population Stability Index)
 */
export interface DriftAnalysis {
  hospital_id: number;
  baseline_round: number;
  current_round?: number;
  psi: number | null;
  drift_level: 'STABLE' | 'MODERATE_DRIFT' | 'SIGNIFICANT_DRIFT' | 'INSUFFICIENT_DATA' | 'UNKNOWN';
  sample_size: number;
  baseline_size?: number;
  reason: string | null;
}

/**
 * Categorized prediction metrics (Risk vs Confidence)
 */
export interface PredictionMetricsCategory {
  risk: {
    value: number | null;
    category: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
    threshold_min: number;
    threshold_max: number;
  };
  confidence: {
    value: number | null;
    category: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | 'UNKNOWN';
    threshold_min: number;
    threshold_max: number;
  };
}

/**
 * Available horizons detected dynamically from database
 */
export interface AvailableHorizon {
  horizon_key: string; // e.g., "6h", "12h", "24h"
  hours: number;
}
