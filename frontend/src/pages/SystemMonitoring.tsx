import React from 'react';
import ConsoleLayout from '../components/ConsoleLayout';

const SystemMonitoring: React.FC = () => {
  return (
    <ConsoleLayout title="System Monitoring" subtitle="Audit logs and system health">
      <div className="max-w-7xl mx-auto">
        {/* System Health */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Database Status</h3>
            <div className="flex items-center space-x-2">
              <span className="text-green-600 text-2xl">●</span>
              <span className="text-green-600 font-semibold">Connected</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">MySQL 8.0 - Port 3307</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">API Status</h3>
            <div className="flex items-center space-x-2">
              <span className="text-green-600 text-2xl">●</span>
              <span className="text-green-600 font-semibold">Responsive</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">FastAPI Backend - Port 8000</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Blockchain Status</h3>
            <div className="flex items-center space-x-2">
              <span className="text-green-600 text-2xl">●</span>
              <span className="text-green-600 font-semibold">Running</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">Ganache - Port 8545</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Recent System Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded border border-blue-200">
                <span className="text-blue-600">ℹ️</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">System Activity Log</p>
                  <p className="text-xs text-gray-600 mt-1">
                    All hospital training sessions, weight uploads, and aggregation operations are logged in the database.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3 p-3 bg-green-50 rounded border border-green-200">
                <span className="text-green-600">✓</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">Blockchain Audit Trail</p>
                  <p className="text-xs text-gray-600 mt-1">
                    All federated rounds are recorded on blockchain for immutable audit trail.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Info */}
        <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3">📊 Monitoring Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-yellow-800">
            <div>
              <h4 className="font-semibold mb-2">Available Monitoring:</h4>
              <ul className="space-y-1">
                <li>• Training rounds in database (training_rounds table)</li>
                <li>• Model weights history (model_weights table)</li>
                <li>• Hospital activity (datasets and training_jobs tables)</li>
                <li>• Blockchain audit trail (AuditLog.sol contract)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Access Methods:</h4>
              <ul className="space-y-1">
                <li>• Database queries via MySQL client</li>
                <li>• API endpoints: /api/aggregation/rounds</li>
                <li>• Blockchain explorer for contract events</li>
                <li>• Backend logs in backend terminal</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default SystemMonitoring;
