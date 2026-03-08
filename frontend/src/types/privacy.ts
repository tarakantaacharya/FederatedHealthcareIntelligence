/**
 * Privacy Governance Type Definitions
 * 
 * Covers:
 * - Private Policy schema and settings
 * - Epsilon metrics and usage tracking
 * - Access control levels
 * - Audit logs and blockchain entries
 */

export interface PrivacyPolicy {
  id?: number;
  epsilon_per_round: number;
  clip_norm: number;
  noise_multiplier: number;
  max_local_epochs: number;
  max_batch_size: number;
  dp_mode: 'batch_only' | 'per_sample';
  strict_dp_enabled: boolean;
  policy_version: number;
  timestamp: string;
  policy_status: 'active' | 'draft' | 'deprecated';
  created_at?: string;
  updated_at?: string;
}

export interface EpsilonMetrics {
  id?: number;
  hospital_id: string;
  round_number: number;
  current_round_epsilon: number;
  cumulative_epsilon: number;
  max_allowed_epsilon: number;
  epsilon_remaining: number;
  epsilon_utilization_percent: number;
  dp_mode: string;
  strict_dp_available: boolean;
  rounds_completed: number;
  timestamp: string;
}

export interface PrivacyAuditLog {
  id?: number;
  hospital_id: string;
  action: 'policy_view' | 'training_start' | 'training_complete' | 'epsilon_exceeded' | 'parameter_violation';
  details: string;
  epsilon_used?: number;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

export interface BlockchainPrivacyRecord {
  id?: number;
  hospital_id: string;
  round_number: number;
  epsilon_used: number;
  policy_hash: string;
  transaction_hash?: string;
  blockchain_timestamp?: number;
  created_at?: string;
}

export interface PrivacyComplianceReport {
  hospital_id: string;
  report_date: string;
  total_rounds: number;
  total_epsilon_used: number;
  epsilon_budget: number;
  compliance_status: 'compliant' | 'at_risk' | 'non_compliant';
  violations: PrivacyViolation[];
  audit_logs: PrivacyAuditLog[];
}

export interface PrivacyViolation {
  id?: number;
  hospital_id: string;
  violation_type: 'parameter_exceeds_policy' | 'epsilon_budget_exceeded' | 'unauthorized_access' | 'policy_bypass_attempted';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: string;
  resolved_at?: string;
}

export interface PrivacyPolicyRequest {
  epsilon_per_round: number;
  clip_norm: number;
  noise_multiplier: number;
  max_local_epochs: number;
  max_batch_size: number;
  dp_mode: 'batch_only' | 'per_sample';
  policy_status?: 'draft' | 'active';
}

export interface PrivacyPolicyResponse extends PrivacyPolicy {
  message?: string;
}

export interface EpsilonMetricsRequest {
  hospital_id?: string;
  round_number?: number;
}

export interface EpsilonMetricsResponse extends EpsilonMetrics {
  message?: string;
}

export interface TrainingConfirmationRequest {
  hospital_id: string;
  training_type: 'local' | 'federated';
  local_epochs?: number;
  batch_size?: number;
  dataset_id: number;
  model_version?: string;
}

export interface TrainingConfirmationResponse {
  confirmed: boolean;
  message: string;
  policy_applied?: PrivacyPolicy;
  epsilon_allocated?: number;
  constraints?: {
    max_local_epochs: number;
    max_batch_size: number;
  };
  warnings?: string[];
}

export interface PrivacySettingsUpdateRequest {
  policy_name?: string;
  epsilon_per_round?: number;
  clip_norm?: number;
  noise_multiplier?: number;
  max_local_epochs?: number;
  max_batch_size?: number;
  strict_dp_enabled?: boolean;
}

export interface AdminPrivacyDashboard {
  total_hospitals: number;
  compliant_hospitals: number;
  at_risk_hospitals: number;
  non_compliant_hospitals: number;
  total_epsilon_allocated: number;
  total_epsilon_used: number;
  average_rounds_completed: number;
  recent_violations: PrivacyViolation[];
  policy_status: PrivacyPolicy;
  compliance_trend: ComplianceTrendPoint[];
}

export interface ComplianceTrendPoint {
  date: string;
  compliant_count: number;
  at_risk_count: number;
  non_compliant_count: number;
}

export interface PrivacyGovernancePageProps {
  mode: 'hospital' | 'admin' | 'audit';
  hospitalId?: string;
  roundNumber?: number;
}

/**
 * Local training constraints that must be enforced
 * These are derived from PrivacyPolicy to ensure UI consistency
 */
export interface LocalTrainingConstraints {
  maxEpochs: number;
  maxBatchSize: number;
  enforced: boolean;
  reason: string;
}

/**
 * Response for checking parameter compliance
 */
export interface ParameterComplianceCheck {
  compliant: boolean;
  violatedParameters: string[];
  message: string;
  suggestions?: string[];
}
