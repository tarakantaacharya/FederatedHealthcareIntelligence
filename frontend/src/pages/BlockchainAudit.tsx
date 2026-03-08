import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import blockchainService, { BlockchainLogEntry } from '../services/blockchainService';

const BlockchainAudit: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [logs, setLogs] = useState<BlockchainLogEntry[]>([]);
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [hospitalId, setHospitalId] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchLogs();
  }, [navigate]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      // Determine which endpoint to call based on role
      const isAdmin = user?.role === 'ADMIN';
      const data = isAdmin 
        ? await blockchainService.getAdminChain(0, 200)
        : await blockchainService.getHospitalChain(0, 200);
      
      setLogs(data.logs);
      setIsValid(data.is_valid);
      setHospitalId(data.hospital_id || '');
    } catch (err: any) {
      // Silent fallback - no error banner displayed
      console.error('[BlockchainAudit] Error fetching logs:', err);
      setLogs([]);
      setIsValid(false);
    } finally {
      setLoading(false);
    }
  };

  const isAdmin = user?.role === 'ADMIN';
  const pageTitle = isAdmin ? 'Global Audit Chain' : 'My Audit Chain';
  const pageSubtitle = isAdmin 
    ? 'Complete blockchain audit log' 
    : 'Your hospital blockchain events';

  return (
    <ConsoleLayout title={pageTitle} subtitle={pageSubtitle}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{pageTitle}</h2>
            <p className="text-sm text-gray-600 mt-1">{pageSubtitle}</p>
          </div>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-md hover:bg-slate-50 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {/* Chain Status Card */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Chain Status</h3>
            <div className="text-sm">
              {isValid === null ? (
                <span className="text-slate-600">Unknown</span>
              ) : isValid ? (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  ✓ Valid
                </span>
              ) : (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                  Verifying...
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Hospital ID Card for Hospital Users */}
        {!isAdmin && hospitalId && (
          <div className="bg-blue-50 rounded-lg border border-blue-200 p-6 mb-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Your Hospital ID</h3>
            <p className="text-lg font-mono text-blue-700 break-all">{hospitalId}</p>
          </div>
        )}

        {/* Audit Events Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              {isAdmin ? 'All Audit Events' : 'Your Blockchain Events'}
            </h3>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-600">Loading blockchain records...</div>
          ) : logs.length === 0 ? (
            <div className="p-6 text-center text-gray-600">No blockchain events recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Block ID</th>
                    {isAdmin && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hospital</th>}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Round</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hash</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((entry, idx) => (
                    <tr key={`${entry.block_hash}-${idx}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">#{idx + 1}</td>
                      {isAdmin && (
                        <td className="px-6 py-4 text-sm text-gray-700">
                          {entry.hospital_id || 'GLOBAL'}
                          {entry.hospital_name ? ` (${entry.hospital_name})` : ''}
                        </td>
                      )}
                      <td className="px-6 py-4 text-sm text-gray-700">Block</td>
                      <td className="px-6 py-4 text-sm text-gray-700">Round {entry.round_id}</td>
                      <td className="px-6 py-4 text-xs font-mono text-gray-600 break-all max-w-xs">
                        {entry.block_hash.substring(0, 16)}...
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Model Hash Details (for admin reference) */}
        {isAdmin && logs.length > 0 && (
          <div className="mt-6 bg-slate-50 rounded-lg p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Model Hash Reference</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {logs.map((entry, idx) => (
                <div key={`model-hash-${idx}`} className="text-xs">
                  <span className="font-semibold text-gray-700">Round {entry.round_id}:</span>{' '}
                  <span className="text-gray-600 font-mono break-all">{entry.model_hash}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default BlockchainAudit;
