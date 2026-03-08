/**
 * Governance Service (Phase 29)
 * API calls for model governance and approval
 */
import api from "./api";

/**
 * Approve and sign a federated global model
 * @param payload - Approval request data
 */
export const approveModel = (payload: {
  round_number: number;
  model_hash: string;
  mape: number;
  num_participants?: number;
  policy_version?: string;
}) =>
  api.post("/api/governance/approve", payload);

/**
 * Get governance status for rounds or specific model
 * @param round_number - Optional round number filter
 * @param model_hash - Optional model hash filter
 */
export const getGovernanceStatus = (
  round_number?: number,
  model_hash?: string
) => {
  const params = new URLSearchParams();
  if (round_number) params.append("round_number", round_number.toString());
  if (model_hash) params.append("model_hash", model_hash);
  return api.get(`/api/governance/status?${params.toString()}`);
};

/**
 * Get global models pending governance approval
 */
export const getPendingModels = () =>
  api.get("/api/governance/pending");

/**
 * Get approved global models
 */
export const getApprovedModels = () =>
  api.get("/api/governance/approved");

/**
 * Get current governance policy information
 */
export const getPolicyInfo = () =>
  api.get("/api/governance/policy");
