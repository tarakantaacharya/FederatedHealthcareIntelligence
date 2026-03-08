import React, { useRef, useState, useEffect } from 'react';
import { ActiveRoundCard } from '../components/ActiveRoundCard';
import { ParticipationMatrix } from '../components/ParticipationMatrix';
import { ModelStatusBadge, ModelStatusIndicator } from '../components/ModelStatusBadge';
import { AggregationControlPanel } from '../components/AggregationControlPanel';
import RoundService from '../services/roundService';

/**
 * EXAMPLE: Phase 41 UI Components Integration
 * 
 * This example demonstrates how to:
 * 1. Display active round info (Hospital)
 * 2. Show participation matrix (Central)
 * 3. Display model eligibility status (Hospital/Central)
 * 4. Control aggregation (Central)
 * 5. Handle refetch lifecycle
 * 6. Manage state synchronization across components
 */

interface TrainingRound {
  id: number;
  round_number: number;
  target_column: string;
  status: 'planning' | 'in_progress' | 'completed';
  architecture_version: string;
}

interface ModelStatus {
  id: number;
  is_trained: boolean;
  weights_uploaded: boolean;
  mask_uploaded: boolean;
  eligible: boolean;
}

export function Phase41ExampleDashboard() {
  const activeRoundRef = useRef<any>(null);
  const participationRef = useRef<any>(null);
  const aggregationRef = useRef<any>(null);

  const [roundId, setRoundId] = useState<number | null>(null);
  const [trainingDisabled, setTrainingDisabled] = useState(false);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [isHospitalView, setIsHospitalView] = useState(true);
  const [actionLog, setActionLog] = useState<
    Array<{ time: string; action: string; status: 'success' | 'error' }>
  >([]);

  // =========================================================================
  // PHASE 41: Action handlers with refetch lifecycle
  // =========================================================================

  /**
   * After training completes - refetch all components
   */
  const handleTrainingComplete = async () => {
    logAction('Training completed', 'success');

    // Refetch all components to get latest state
    activeRoundRef.current?.refetch();
    participationRef.current?.refetch();
    aggregationRef.current?.refetch();

    // Update model status
    await updateModelStatus();
  };

  /**
   * After weights uploaded - refetch components
   */
  const handleWeightsUploaded = async () => {
    logAction('Weights uploaded', 'success');

    // Refetch to show updated participation
    activeRoundRef.current?.refetch();
    participationRef.current?.refetch();
    aggregationRef.current?.refetch();

    // Update model status
    await updateModelStatus();
  };

  /**
   * After mask uploaded - refetch components
   */
  const handleMaskUploaded = async () => {
    logAction('Mask uploaded', 'success');

    // Final refetch - model should now be eligible
    activeRoundRef.current?.refetch();
    participationRef.current?.refetch();
    aggregationRef.current?.refetch();

    // Update model status
    await updateModelStatus();
  };

  /**
   * After aggregation - refetch all components
   */
  const handleAggregationComplete = (success: boolean, message: string) => {
    if (success) {
      logAction('Aggregation completed', 'success');
    } else {
      logAction(`Aggregation failed: ${message}`, 'error');
    }

    // Refetch all components after aggregation
    participationRef.current?.refetch();
    aggregationRef.current?.refetch();
  };

  /**
   * Update model status from backend
   */
  const updateModelStatus = async () => {
    try {
      // Mock: In real implementation, fetch from /api/models/{id}/status
      const mockStatus: ModelStatus = {
        id: 1,
        is_trained: true,
        weights_uploaded: true,
        mask_uploaded: true,
        eligible: true
      };
      setModelStatus(mockStatus);
    } catch (error) {
      console.error('Failed to update model status:', error);
    }
  };

  /**
   * Fetch active round and set ID
   */
  useEffect(() => {
    const fetchRound = async () => {
      try {
        const response = await RoundService.getActiveRound();
        setRoundId(response.data.id);
      } catch (error) {
        console.error('Failed to fetch active round:', error);
      }
    };
    fetchRound();
  }, []);

  /**
   * Log action with timestamp
   */
  const logAction = (action: string, status: 'success' | 'error') => {
    const time = new Date().toLocaleTimeString();
    setActionLog((prev) => [
      ...prev.slice(-9), // Keep last 10 items
      { time, action, status }
    ]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <h1 className="text-3xl font-bold text-gray-900">Phase 41 Dashboard</h1>
          <p className="text-gray-600 mt-2">Round-Centric Federated Learning Governance</p>

          {/* View Toggle */}
          <div className="mt-4 flex gap-4">
            <button
              onClick={() => setIsHospitalView(true)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isHospitalView
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🏥 Hospital View
            </button>
            <button
              onClick={() => setIsHospitalView(false)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                !isHospitalView
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🏛️ Central View
            </button>
          </div>
        </div>

        {/* Hospital View */}
        {isHospitalView && (
          <div className="space-y-6">
            {/* Active Round Card */}
            <ActiveRoundCard
              ref={activeRoundRef}
              onRoundChange={(round: TrainingRound | null) => {
                if (round) setRoundId(round.id);
              }}
              disableTraining={setTrainingDisabled}
            />

            {/* Training Workflow */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Workflow</h3>

              <div className="space-y-4">
                {/* Step 1: Training */}
                <div className="border-2 border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Step 1: Train Model</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Requires active training round with target column defined
                  </p>
                  <button
                    onClick={handleTrainingComplete}
                    disabled={trainingDisabled}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      !trainingDisabled
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    }`}
                  >
                    🤖 Train Local Model
                  </button>
                </div>

                {/* Model Status */}
                {modelStatus && (
                  <div className="border-2 border-green-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Model Status</h4>
                    <ModelStatusIndicator
                      isTrained={modelStatus.is_trained}
                      weightsUploaded={modelStatus.weights_uploaded}
                      maskUploaded={modelStatus.mask_uploaded}
                      compact={false}
                    />
                  </div>
                )}

                {/* Step 2: Upload Weights */}
                <div className="border-2 border-yellow-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Step 2: Upload Weights</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Validates checkpoint integrity and computes SHA256
                  </p>
                  <button
                    onClick={handleWeightsUploaded}
                    disabled={trainingDisabled || !modelStatus?.is_trained}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      !trainingDisabled && modelStatus?.is_trained
                        ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                        : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    }`}
                  >
                    ⬆️ Upload Weights
                  </button>
                </div>

                {/* Step 3: Upload Mask */}
                <div className="border-2 border-purple-200 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Step 3: Upload Mask</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Requires weights to be uploaded first
                  </p>
                  <button
                    onClick={handleMaskUploaded}
                    disabled={trainingDisabled || !modelStatus?.weights_uploaded}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      !trainingDisabled && modelStatus?.weights_uploaded
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    }`}
                  >
                    🎭 Upload Mask (MPC)
                  </button>
                </div>

                {/* Eligibility Status */}
                {modelStatus && (
                  <div
                    className={`rounded-lg p-4 text-center ${
                      modelStatus.eligible
                        ? 'bg-green-50 border-2 border-green-200'
                        : 'bg-gray-50 border-2 border-gray-200'
                    }`}
                  >
                    {modelStatus.eligible ? (
                      <p className="text-green-900 font-semibold">
                        ✅ Ready for Aggregation
                      </p>
                    ) : (
                      <p className="text-gray-900 font-semibold">
                        ⏳ Waiting for Aggregation
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Central Coordinator View */}
        {!isHospitalView && roundId && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Participation Matrix */}
            <ParticipationMatrix
              ref={participationRef}
              roundId={roundId}
              onEligibilityChange={(eligible: boolean, count: number) => {
                logAction(
                  `Eligibility changed: ${count} hospitals eligible`,
                  'success'
                );
              }}
            />

            {/* Aggregation Control */}
            <AggregationControlPanel
              ref={aggregationRef}
              roundId={roundId}
              onAggregationStart={() => {
                logAction('Aggregation started', 'success');
              }}
              onAggregationComplete={handleAggregationComplete}
            />
          </div>
        )}

        {/* Action Log */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Action Log</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto bg-gray-50 p-3 rounded">
            {actionLog.length === 0 ? (
              <p className="text-sm text-gray-600">No actions logged yet</p>
            ) : (
              actionLog.map((entry, idx) => (
                <div key={idx} className="flex gap-3 text-sm">
                  <span className="font-mono text-gray-600 flex-shrink-0">{entry.time}</span>
                  <span
                    className={`${
                      entry.status === 'success'
                        ? 'text-green-700 font-medium'
                        : 'text-red-700 font-medium'
                    }`}
                  >
                    {entry.status === 'success' ? '✓' : '✕'} {entry.action}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Component Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Component Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-blue-50 p-3 rounded">
              <p className="font-semibold text-blue-900">ActiveRoundCard</p>
              <p className="text-blue-700">Refetch: 5s</p>
            </div>
            <div className="bg-green-50 p-3 rounded">
              <p className="font-semibold text-green-900">ParticipationMatrix</p>
              <p className="text-green-700">Refetch: 3s</p>
            </div>
            <div className="bg-yellow-50 p-3 rounded">
              <p className="font-semibold text-yellow-900">ModelStatusBadge</p>
              <p className="text-yellow-700">Manual refresh</p>
            </div>
            <div className="bg-purple-50 p-3 rounded">
              <p className="font-semibold text-purple-900">AggregationPanel</p>
              <p className="text-purple-700">Refetch: 2s</p>
            </div>
          </div>
        </div>

        {/* Documentation Link */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">📖 Documentation</h3>
          <p className="text-blue-800 text-sm mb-3">
            See <strong>PHASE_41_UI_COMPONENTS.md</strong> for complete integration guide
          </p>
          <ul className="text-sm text-blue-800 space-y-1 ml-4">
            <li>✓ Component reference and props</li>
            <li>✓ Integration examples</li>
            <li>✓ Refetch lifecycle patterns</li>
            <li>✓ Backend API requirements</li>
            <li>✓ Error handling strategies</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Phase41ExampleDashboard;
