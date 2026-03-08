# Privacy Governance Integration Guide

## Overview

This guide shows how to integrate the privacy governance components into existing frontend pages in the Federated Healthcare platform.

## Components & Services

### Available Components

1. **PrivacyGovernancePanel** - Main UI component displaying privacy status, parameters, and epsilon metrics

### Available Services

1. **PrivacyService** - Handles all backend API calls for privacy management

## Integration Points

### 1. Training Start Page Integration

**File:** `frontend/src/pages/Training/TrainingStart.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import PrivacyGovernancePanel from '../components/PrivacyGovernancePanel';
import PrivacyService from '../services/privacyService';
import { LocalTrainingConstraints } from '../types/privacy';

export const TrainingStartPage: React.FC = () => {
  const [constraints, setConstraints] = useState<LocalTrainingConstraints | null>(null);
  const [epochs, setEpochs] = useState(0);
  const [batchSize, setBatchSize] = useState(32);
  const [trainingActive, setTrainingActive] = useState(false);

  useEffect(() => {
    loadTrainingConstraints();
  }, []);

  const loadTrainingConstraints = async () => {
    try {
      const c = await PrivacyService.getLocalTrainingConstraints();
      setConstraints(c);
      // Set defaults based on constraints
      setEpochs(Math.min(3, c.maxEpochs));
      setBatchSize(Math.min(32, c.maxBatchSize));
    } catch (error) {
      console.error('Failed to load constraints:', error);
    }
  };

  const handleStartTraining = async () => {
    try {
      // Check compliance before starting
      const compliance = await PrivacyService.checkParameterCompliance(epochs, batchSize);
      
      if (!compliance.compliant) {
        alert(`\u274c Parameter violation: ${compliance.message}`);
        return;
      }

      // Confirm training with privacy policy
      const confirmation = await PrivacyService.confirmTraining({
        hospital_id: 'CURRENT_HOSPITAL', // Get from auth context
        training_type: 'local',
        local_epochs: epochs,
        batch_size: batchSize,
        dataset_id: 1,
        model_version: '1.0'
      });

      if (confirmation.confirmed) {
        setTrainingActive(true);
        // Start training with confirmed parameters
        startTrainingWithConstraints(epochs, batchSize);
      } else {
        alert(confirmation.message);
      }
    } catch (error) {
      console.error('Training confirmation failed:', error);
      alert('Failed to confirm training with privacy policy');
    }
  };

  const startTrainingWithConstraints = (maxEpochs: number, maxBatch: number) => {
    // Your existing training logic here
    console.log(`Starting training with epochs=${maxEpochs}, batch_size=${maxBatch}`);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Start Training</h1>

      {/* Privacy Governance Panel */}
      <PrivacyGovernancePanel
        mode="local"
        trainingActive={trainingActive}
        currentEpochs={epochs}
        currentBatchSize={batchSize}
      />

      {/* Training Parameters */}
      {constraints && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
          <h2 className="text-xl font-semibold">Training Parameters</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Local Epochs (max {constraints.maxEpochs})
            </label>
            <input
              type="number"
              min="1"
              max={constraints.maxEpochs}
              value={epochs}
              onChange={(e) => setEpochs(Math.min(parseInt(e.target.value) || 0, constraints.maxEpochs))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Batch Size (max {constraints.maxBatchSize})
            </label>
            <input
              type="number"
              min="1"
              max={constraints.maxBatchSize}
              value={batchSize}
              onChange={(e) => setBatchSize(Math.min(parseInt(e.target.value) || 0, constraints.maxBatchSize))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={handleStartTraining}
            disabled={trainingActive}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition"
          >
            {trainingActive ? "Training in Progress..." : "Start Training with Privacy Protection"}
          </button>
        </div>
      )}
    </div>
  );
};

export default TrainingStartPage;
```

### 2. Dashboard Integration

**File:** `frontend/src/pages/Dashboard/Dashboard.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import PrivacyGovernancePanel from '../components/PrivacyGovernancePanel';
import PrivacyService from '../services/privacyService';
import { EpsilonMetrics } from '../types/privacy';

export const Dashboard: React.FC = () => {
  const [epsilonMetrics, setEpsilonMetrics] = useState<EpsilonMetrics | null>(null);

  useEffect(() => {
    refreshEpsilonMetrics();
  }, []);

  const refreshEpsilonMetrics = async () => {
    try {
      const metrics = await PrivacyService.getEpsilonMetrics();
      setEpsilonMetrics(metrics);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Hospital Dashboard</h1>

      {/* Privacy Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {epsilonMetrics && (
          <>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-900">Current Round Epsilon</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {epsilonMetrics.current_round_epsilon} / {epsilonMetrics.max_allowed_epsilon}
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900">Cumulative Epsilon</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {epsilonMetrics.cumulative_epsilon.toFixed(2)}
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-900">Utilization</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {epsilonMetrics.epsilon_utilization_percent.toFixed(1)}%
              </p>
            </div>
          </>
        )}
      </div>

      {/* Full Privacy Governance Panel */}
      <PrivacyGovernancePanel mode="federated" />

      {/* Rest of dashboard content */}
    </div>
  );
};

export default Dashboard;
```

### 3. Federated Training Round Page Integration

**File:** `frontend/src/pages/Training/RoundDetails.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import PrivacyGovernancePanel from '../components/PrivacyGovernancePanel';
import PrivacyService from '../services/privacyService';

export const RoundDetailsPage: React.FC<{ roundNumber: number }> = ({ roundNumber }) => {
  const [historicalPolicy, setHistoricalPolicy] = useState(null);

  useEffect(() => {
    loadRoundPolicy();
  }, [roundNumber]);

  const loadRoundPolicy = async () => {
    try {
      const policy = await PrivacyService.getPolicyForRound(roundNumber);
      setHistoricalPolicy(policy);
    } catch (error) {
      console.error(`Failed to load policy for round ${roundNumber}:`, error);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Round {roundNumber} Details</h1>

      {/* Federated Mode - Read-only Privacy Governance */}
      <PrivacyGovernancePanel mode="federated" />

      {/* Historical Policy Info */}
      {historicalPolicy && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Round {roundNumber} Privacy Configuration</h3>
          <pre className="text-sm text-gray-700 bg-white p-4 rounded border border-gray-300 overflow-auto">
            {JSON.stringify(historicalPolicy, null, 2)}
          </pre>
        </div>
      )}

      {/* Rest of round details */}
    </div>
  );
};

export default RoundDetailsPage;
```

### 4. Compliance Report Page Integration

**File:** `frontend/src/pages/Privacy/ComplianceReport.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import PrivacyService from '../services/privacyService';
import { PrivacyComplianceReport } from '../types/privacy';

export const ComplianceReportPage: React.FC = () => {
  const [report, setReport] = useState<PrivacyComplianceReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComplianceReport();
  }, []);

  const loadComplianceReport = async () => {
    try {
      setLoading(true);
      const r = await PrivacyService.getComplianceReport();
      setReport(r);
    } catch (error) {
      console.error('Failed to load compliance report:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = async () => {
    try {
      const pdfBlob = await PrivacyService.exportComplianceReportPDF();
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.pdf`;
      a.click();
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Failed to export compliance report');
    }
  };

  if (loading) {
    return <div className="text-center p-10">Loading compliance report...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Privacy Compliance Report</h1>
        <button
          onClick={exportPDF}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          Export PDF
        </button>
      </div>

      {report && (
        <>
          {/* Compliance Status */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Compliance Status</h2>
            <div className="flex items-center gap-4">
              <span className={`text-3xl font-bold ${
                report.compliance_status === 'compliant' ? 'text-green-600' :
                report.compliance_status === 'at_risk' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {report.compliance_status.toUpperCase()}
              </span>
              <div>
                <p className="text-gray-600">Total Rounds: {report.total_rounds}</p>
                <p className="text-gray-600">Epsilon Used: {report.total_epsilon_used.toFixed(2)} / {report.epsilon_budget}</p>
              </div>
            </div>
          </div>

          {/* Violations */}
          {report.violations.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-red-900 mb-4">Violations ({report.violations.length})</h2>
              <div className="space-y-2">
                {report.violations.map((violation) => (
                  <div key={violation.id} className="bg-white p-3 rounded border border-red-300">
                    <p className="font-semibold text-red-700">{violation.violation_type}</p>
                    <p className="text-sm text-gray-600">{violation.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audit Logs */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Audit Logs</h2>
            <div className="space-y-2">
              {report.audit_logs.slice(0, 20).map((log, idx) => (
                <div key={idx} className="text-sm text-gray-600 p-2 bg-gray-50 rounded">
                  [{log.timestamp}] {log.action}: {log.details}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ComplianceReportPage;
```

## Usage Patterns

### Pattern 1: Checking Compliance Before Action

```typescript
const handleTrainingStart = async () => {
  try {
    const compliance = await PrivacyService.checkParameterCompliance(epochs, batchSize);
    if (!compliance.compliant) {
      showError(`Parameters violate policy: ${compliance.message}`);
      return;
    }
    // Safe to proceed with training
  } catch (error) {
    showError('Failed to validate compliance');
  }
};
```

### Pattern 2: Real-time Constraint Enforcement

```typescript
const handleEpochsChange = (value: number) => {
  const constraints = await PrivacyService.getLocalTrainingConstraints();
  const clamped = Math.min(value, constraints.maxEpochs);
  setEpochs(clamped);
};
```

### Pattern 3: Monitoring Epsilon Budget

```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const metrics = await PrivacyService.getEpsilonMetrics();
    if (metrics.epsilon_utilization_percent > 80) {
      showWarning('Epsilon budget at 80% usage');
    }
  }, 5000); // Poll every 5 seconds

  return () => clearInterval(interval);
}, []);
```

## Type Safety

All API responses are typed with TypeScript interfaces. Always import and use:

```typescript
import { 
  PrivacyPolicy,
  EpsilonMetrics,
  TrainingConfirmationResponse,
  LocalTrainingConstraints
} from '../types/privacy';
```

## Error Handling

```typescript
try {
  const policy = await PrivacyService.getPrivacyPolicy();
  // Use policy
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 403) {
      // Handle authorization error
    } else if (error.response?.status === 422) {
      // Handle validation error
    }
  }
  console.error('Unhandled error:', error);
}
```

## Testing

Test privacy governance with:

```typescript
// Unit test example
describe('PrivacyGovernancePanel', () => {
  test('displays epsilon metrics correctly', async () => {
    const mockMetrics: EpsilonMetrics = {
      current_round_epsilon: 0.3,
      max_allowed_epsilon: 1.0,
      epsilon_utilization_percent: 30,
      // ... other fields
    };

    jest.spyOn(PrivacyService, 'getEpsilonMetrics')
      .mockResolvedValue(mockMetrics);

    const { getByText } = render(
      <PrivacyGovernancePanel mode="federated" />
    );

    expect(getByText(/0.3/)).toBeInTheDocument();
  });
});
```

## Configuration

The Privacy Governance system respects backend configuration:

- **Epsilon Budget**: Configured in backend `config.py`
- **DP Mode**: Always "Batch-Level Only" (strict per-sample DP disabled)
- **Maximum Epochs/Batch Size**: Set by admin policy
- **Strict DP**: Always disabled in production

## Security Notes

1. **Tokens**: Always stored in localStorage and sent as Bearer token
2. **HTTPS Only**: Use HTTPS in production for privacy endpoints
3. **Audit Trails**: All actions logged and immutable
4. **Blockchain Integration**: Critical events stored on-chain

## Next Steps

1. Integrate components into existing pages (Training, Dashboard, Reports)
2. Configure backend API endpoints to match these contracts
3. Test end-to-end with actual privacy enforcement
4. Monitor epsilon metrics in production
5. Set up alerts for privacy violations
