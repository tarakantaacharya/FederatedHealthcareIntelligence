/**
 * Model Governance Page (Phase 29)
 * Admin-only approval and signing of federated models
 */
import React, { useState, useEffect } from "react";
import ConsoleLayout from '../components/ConsoleLayout';
import ClearModelsModal from '../components/ClearModelsModal';
import modelClearingService from '../services/modelClearingService';
import {
  approveModel,
  getGovernanceStatus,
  getPolicyInfo,
  getPendingModels,
  getApprovedModels,
} from "../services/governanceService";

interface PolicyInfo {
  current_version: string;
  policies: {
    [key: string]: {
      description: string;
      rules: {
        min_accuracy: number;
        min_participants: number;
      };
    };
  };
}

interface GovernanceRecord {
  id: number;
  round_number: number;
  model_hash: string;
  approved: boolean;
  approved_by: string | null;
  signature: string | null;
  policy_version: string;
  rejection_reason: string | null;
  created_at: string;
}

interface GovernanceStatus {
  total_evaluations: number;
  approved_count: number;
  rejected_count: number;
  records: GovernanceRecord[];
}

interface PendingModel {
  model_id: number;
  round_number: number;
  model_hash: string;
  model_type: string;
  accuracy: number | null;
  loss: number | null;
  num_participants: number;
  created_at: string;
}

const ModelGovernance: React.FC = () => {
  const [round, setRound] = useState<number>(1);
  const [hash, setHash] = useState<string>("");
  const [mape, setMape] = useState<number>(0.12);
  const [numParticipants, setNumParticipants] = useState<number>(3);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [messageType, setMessageType] = useState<"success" | "error" | "info">("info");
  
  const [policyInfo, setPolicyInfo] = useState<PolicyInfo | null>(null);
  const [governanceStatus, setGovernanceStatus] = useState<GovernanceStatus | null>(null);
  const [pendingModels, setPendingModels] = useState<PendingModel[]>([]);
  const [pendingLoading, setPendingLoading] = useState<boolean>(false);
  const [approvedModels, setApprovedModels] = useState<any[]>([]);
  const [approvedLoading, setApprovedLoading] = useState<boolean>(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearingGlobalModels, setClearingGlobalModels] = useState(false);
  const [clearMessage, setClearMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadPolicyInfo();
    loadGovernanceStatus();
    loadPendingModels();
    loadApprovedModels();
  }, []);

  const loadPolicyInfo = async () => {
    try {
      const response = await getPolicyInfo();
      setPolicyInfo(response.data);
    } catch (error) {
      console.error("Error loading policy info:", error);
    }
  };

  const loadGovernanceStatus = async () => {
    try {
      const response = await getGovernanceStatus();
      setGovernanceStatus(response.data);
    } catch (error) {
      console.error("Error loading governance status:", error);
    }
  };

  const loadPendingModels = async () => {
    setPendingLoading(true);
    try {
      const response = await getPendingModels();
      setPendingModels(response.data?.pending || []);
    } catch (error) {
      console.error("Error loading pending models:", error);
      setPendingModels([]);
    } finally {
      setPendingLoading(false);
    }
  };

  const loadApprovedModels = async () => {
    setApprovedLoading(true);
    try {
      const response = await getApprovedModels();
      setApprovedModels(response.data?.approved || []);
    } catch (error) {
      console.error("Error loading approved models:", error);
      setApprovedModels([]);
    } finally {
      setApprovedLoading(false);
    }
  };

  const executeApproval = async (payload: {
    round_number: number;
    model_hash: string;
    mape: number;
    num_participants: number;
  }) => {
    setLoading(true);
    setMessage("");

    try {
      const response = await approveModel({
        round_number: payload.round_number,
        model_hash: payload.model_hash,
        mape: payload.mape,
        num_participants: payload.num_participants,
        policy_version: "v1",
      });

      const result = response.data;

      if (result.approved) {
        setMessage(
          `✅ Model APPROVED and signed! Signature: ${result.signature?.substring(0, 16)}...`
        );
        setMessageType("success");
      } else {
        setMessage(
          `❌ Model REJECTED: ${result.rejection_reason || "Policy requirements not met"}`
        );
        setMessageType("error");
      }

      await loadGovernanceStatus();
      await loadPendingModels();
      await loadApprovedModels();
    } catch (error: any) {
      setMessage(
        error.response?.data?.detail || "Failed to process governance decision"
      );
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!hash.trim()) {
      setMessage("Please enter a model hash");
      setMessageType("error");
      return;
    }
    await executeApproval({
      round_number: round,
      model_hash: hash,
      mape: mape,
      num_participants: numParticipants,
    });
  };

  const handleApprovePending = async (model: PendingModel) => {
    const resolvedMape = model.loss ?? 0;
    const resolvedParticipants = model.num_participants ?? 0;

    setRound(model.round_number);
    setHash(model.model_hash);
    setMape(resolvedMape);
    setNumParticipants(resolvedParticipants);

    await executeApproval({
      round_number: model.round_number,
      model_hash: model.model_hash,
      mape: resolvedMape,
      num_participants: resolvedParticipants,
    });
  };

  const handleClearGlobalModels = async (deleteFiles: boolean) => {
    setClearingGlobalModels(true);
    try {
      await modelClearingService.clearGlobalModels(deleteFiles, false);
      setClearMessage({ type: 'success', text: 'Global models cleared successfully' });
      await loadGovernanceStatus();
      await loadPendingModels();
      await loadApprovedModels();
      setTimeout(() => setClearMessage(null), 5000);
    } catch (error) {
      setClearMessage({ type: 'error', text: 'Failed to clear global models' });
      setTimeout(() => setClearMessage(null), 5000);
    } finally {
      setClearingGlobalModels(false);
    }
  };

  return (
    <ConsoleLayout title="Model Governance" subtitle="Approval and signing">
      <div className="max-w-6xl mx-auto">
        {/* Clear Message */}
        {clearMessage && (
          <div className={`mb-6 p-4 rounded-lg ${
            clearMessage.type === 'success'
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            <p className={`text-sm font-medium ${
              clearMessage.type === 'success'
                ? 'text-green-800'
                : 'text-red-800'
            }`}>
              {clearMessage.text}
            </p>
          </div>
        )}
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                Model Governance & Approval
              </h1>
              <p className="text-gray-600 mt-2">
                Admin-only interface for approving and cryptographically signing federated models
              </p>
            </div>
            <button
              onClick={() => setShowClearModal(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors whitespace-nowrap"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Clear Global Models
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Approval Form */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-indigo-800 mb-4">Model Approval</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Round Number
                </label>
                <input
                  type="number"
                  className="border border-gray-300 rounded px-4 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter round number"
                  value={round}
                  onChange={(e) => setRound(Number(e.target.value))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model Hash (SHA-256)
                </label>
                <input
                  className="border border-gray-300 rounded px-4 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                  placeholder="Enter model hash"
                  value={hash}
                  onChange={(e) => setHash(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model MAPE (Mean Absolute Percentage Error)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  max="1"
                  className="border border-gray-300 rounded px-4 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter MAPE (lower is better)"
                  value={mape}
                  onChange={(e) => setMape(Number(e.target.value))}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Current value: {(mape * 100).toFixed(2)}% (Lower is better, threshold: 20%)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Number of Participants
                </label>
                <input
                  type="number"
                  className="border border-gray-300 rounded px-4 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter number of hospitals"
                  value={numParticipants}
                  onChange={(e) => setNumParticipants(Number(e.target.value))}
                />
              </div>

               <button
                className={`w-full text-white px-6 py-3 rounded-lg font-semibold transition-colors ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-700"
                }`}
                onClick={handleApprove}
                disabled={loading}
              >
                 {loading ? "Processing..." : "Approve & Sign Model"}
              </button>
            </div>

            {/* Message Display */}
            {message && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  messageType === "success"
                    ? "bg-green-100 border border-green-400 text-green-800"
                    : messageType === "error"
                    ? "bg-red-100 border border-red-400 text-red-800"
                    : "bg-blue-100 border border-blue-400 text-blue-800"
                }`}
              >
                <p className="text-sm">{message}</p>
              </div>
            )}
          </div>

          {/* Policy Information */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-purple-800 mb-4">Governance Policy</h2>

            {policyInfo && (
              <div className="space-y-4">
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-2">
                    Current Policy: {policyInfo.current_version.toUpperCase()}
                  </h3>
                  <p className="text-sm text-gray-700 mb-3">
                    {policyInfo.policies[policyInfo.current_version].description}
                  </p>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between bg-white p-3 rounded">
                      <span className="text-sm font-medium text-gray-700">
                        Maximum MAPE
                      </span>
                      <span className="text-sm font-bold text-orange-700">
                        {"<= "}
                        {(
                          policyInfo.policies[policyInfo.current_version].rules
                            .min_accuracy * 100
                        ).toFixed(0)}
                        %
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-white p-3 rounded">
                      <span className="text-sm font-medium text-gray-700">
                        Minimum Participants
                      </span>
                      <span className="text-sm font-bold text-blue-700">
                        ≥{" "}
                        {
                          policyInfo.policies[policyInfo.current_version].rules
                            .min_participants
                        }{" "}
                        hospitals
                      </span>
                    </div>
                  </div>
                </div>

                 <div className="bg-yellow-50 border border-yellow-300 p-4 rounded-lg">
                   <p className="text-xs text-yellow-800">
                     <strong>Admin Access Required:</strong> Only users with
                     hospital_id starting with "ADMIN" can approve models.
                   </p>
                 </div>
              </div>
            )}
          </div>
        </div>

        {/* Pending Global Models */}
        <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-800">Pending Global Models</h2>
            <button
              className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md"
              onClick={loadPendingModels}
              disabled={pendingLoading}
            >
              {pendingLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {pendingLoading ? (
            <p className="text-sm text-gray-600">Loading pending models...</p>
          ) : pendingModels.length === 0 ? (
            <p className="text-sm text-gray-600">No pending models found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Round</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Model Hash</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Loss</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Participants</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Created</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {pendingModels.map((model) => (
                    <tr key={model.model_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">{model.round_number}</td>
                      <td className="px-4 py-3 text-xs font-mono text-gray-700 break-all">{model.model_hash}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {model.loss !== null && model.loss !== undefined
                          ? (
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-orange-700">
                                  {Number(model.loss).toFixed(4)}
                                </span>
                              </div>
                            )
                          : <span className="text-gray-500">N/A</span>}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{model.num_participants}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(model.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          className={`px-4 py-2 rounded-md text-white font-semibold ${
                            loading ? "bg-gray-400 cursor-not-allowed" : "bg-indigo-600 hover:bg-indigo-700"
                          }`}
                          onClick={() => handleApprovePending(model)}
                          disabled={loading}
                        >
                          Approve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Approved Global Models */}
        <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-green-800">Approved Global Models</h2>
            <button
              className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md"
              onClick={loadApprovedModels}
              disabled={approvedLoading}
            >
              {approvedLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {approvedLoading ? (
            <p className="text-sm text-gray-600">Loading approved models...</p>
          ) : approvedModels.length === 0 ? (
            <p className="text-sm text-gray-600">No approved models yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Round</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Model Hash</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Loss</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">MAPE</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Participants</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Approved By</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Approved</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {approvedModels.map((model) => (
                    <tr key={model.governance_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">{model.round_number}</td>
                      <td className="px-4 py-3 text-xs font-mono text-gray-700 break-all">{model.model_hash}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {model.loss !== null && model.loss !== undefined
                          ? (
                              <span className="font-semibold text-orange-700">
                                {Number(model.loss).toFixed(4)}
                              </span>
                            )
                          : <span className="text-gray-500">N/A</span>}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {model.mape !== null && model.mape !== undefined
                          ? (
                              <span className="font-semibold text-green-700">
                                {(model.mape * 100).toFixed(2)}%
                              </span>
                            )
                          : <span className="text-gray-500">N/A</span>}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{model.num_participants}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{model.approved_by || "N/A"}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-semibold">
                          ✓ Approved
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Governance History */}
        {governanceStatus && (
          <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
            <h2 className="text-2xl font-bold text-green-800 mb-4">Governance History</h2>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Total Evaluations</p>
                <p className="text-3xl font-bold text-blue-700">
                  {governanceStatus.total_evaluations}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Approved</p>
                <p className="text-3xl font-bold text-green-700">
                  {governanceStatus.approved_count}
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg text-center">
                <p className="text-sm text-gray-600">Rejected</p>
                <p className="text-3xl font-bold text-red-700">
                  {governanceStatus.rejected_count}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="table-auto w-full border-collapse text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="border border-gray-300 p-2 text-left">Round</th>
                    <th className="border border-gray-300 p-2 text-left">Model Hash</th>
                    <th className="border border-gray-300 p-2 text-center">Status</th>
                    <th className="border border-gray-300 p-2 text-left">Approved By</th>
                    <th className="border border-gray-300 p-2 text-left">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {governanceStatus.records.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="border border-gray-200 p-2 font-semibold">
                        {record.round_number}
                      </td>
                      <td className="border border-gray-200 p-2 font-mono text-xs">
                        {record.model_hash.substring(0, 16)}...
                      </td>
                      <td className="border border-gray-200 p-2 text-center">
                         {record.approved ? (
                           <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-semibold">
                             APPROVED
                           </span>
                         ) : (
                           <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-semibold">
                             REJECTED
                           </span>
                         )}
                      </td>
                      <td className="border border-gray-200 p-2">
                        {record.approved_by || "N/A"}
                      </td>
                      <td className="border border-gray-200 p-2 text-xs text-gray-600">
                        {new Date(record.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <ClearModelsModal
          isOpen={showClearModal}
          onClose={() => setShowClearModal(false)}
          onConfirm={handleClearGlobalModels}
          title="Clear Global Models"
          scope="global"
          loading={clearingGlobalModels}
        />
      </div>
    </ConsoleLayout>
  );
};

export default ModelGovernance;
