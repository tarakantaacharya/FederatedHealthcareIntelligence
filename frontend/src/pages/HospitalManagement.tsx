import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import adminService, { Hospital } from '../services/adminService';
import { formatErrorMessage } from '../utils/errorMessage';

const HospitalManagement: React.FC = () => {
  const navigate = useNavigate();
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    // ProtectedRoute already guards access; just load data
    fetchHospitals();
  }, []);

  const fetchHospitals = async () => {
    try {
      const data = await adminService.getAllHospitals();
      setHospitals(data);
    } catch (err: any) {
      setError('Failed to load hospitals');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (hospitalId: number) => {
    setActionLoading(hospitalId);
    try {
      await adminService.verifyHospital(String(hospitalId));
      await fetchHospitals();
    } catch (err: any) {
      setError('Failed to verify hospital');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeactivate = async (hospitalId: number) => {
    setActionLoading(hospitalId);
    try {
      await adminService.deactivateHospital(String(hospitalId));
      await fetchHospitals();
    } catch (err: any) {
      setError('Failed to deactivate hospital');
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivate = async (hospitalId: number) => {
    setActionLoading(hospitalId);
    try {
      await adminService.activateHospital(String(hospitalId));
      await fetchHospitals();
    } catch (err: any) {
      setError('Failed to activate hospital');
    } finally {
      setActionLoading(null);
    }
  };

  const handleFederatedToggle = async (hospitalId: number, allow: boolean) => {
    setActionLoading(hospitalId);
    try {
      await adminService.setFederatedAccess(String(hospitalId), allow);
      await fetchHospitals();
    } catch (err: any) {
      setError('Failed to update federated access');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <ConsoleLayout title="Hospital Management" subtitle="View and manage all registered hospitals">
      <div className="max-w-7xl mx-auto">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {/* Hospitals Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">Registered Hospitals ({hospitals.length})</h2>
          </div>

          {loading ? (
            <div className="p-6 text-center text-gray-600">Loading hospitals...</div>
          ) : hospitals.length === 0 ? (
            <div className="p-6 text-center text-gray-600">No hospitals registered yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Hospital ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Verified
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Federated Access
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {hospitals.map((hospital) => (
                    <tr key={hospital.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {hospital.hospital_id}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {hospital.hospital_name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {hospital.location}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {hospital.contact_email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            hospital.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {hospital.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            hospital.is_verified
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {hospital.is_verified ? '✓ Verified' : '⏳ Pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(hospital.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            hospital.is_allowed_federated
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {hospital.is_allowed_federated ? 'Allowed' : 'Blocked'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <div className="flex flex-wrap gap-2">
                          {!hospital.is_verified && (
                            <button
                              onClick={() => handleVerify(hospital.id)}
                              disabled={actionLoading === hospital.id}
                              className="px-3 py-1 bg-blue-600 text-white rounded text-xs disabled:opacity-50"
                            >
                              Verify
                            </button>
                          )}
                          {hospital.is_active ? (
                            <button
                              onClick={() => handleDeactivate(hospital.id)}
                              disabled={actionLoading === hospital.id}
                              className="px-3 py-1 bg-red-600 text-white rounded text-xs disabled:opacity-50"
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              onClick={() => handleActivate(hospital.id)}
                              disabled={actionLoading === hospital.id}
                              className="px-3 py-1 bg-green-600 text-white rounded text-xs disabled:opacity-50"
                            >
                              Activate
                            </button>
                          )}
                          <button
                            onClick={() => navigate(`/hospitals-manage/${hospital.id}`)}
                            className="px-3 py-1 bg-indigo-600 text-white rounded text-xs"
                          >
                            View Hospital
                          </button>
                          <button
                            onClick={() => handleFederatedToggle(hospital.id, !hospital.is_allowed_federated)}
                            disabled={actionLoading === hospital.id}
                            className="px-3 py-1 bg-slate-700 text-white rounded text-xs disabled:opacity-50"
                          >
                            {hospital.is_allowed_federated ? 'Block Federated' : 'Allow Federated'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Hospital Management Guide</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• <strong>Active hospitals</strong> can upload datasets and participate in training</li>
            <li>• <strong>Verified hospitals</strong> have been approved by the central admin</li>
            <li>• Only verified and active hospitals can participate in federated rounds</li>
            <li>• All hospitals shown above are registered in the system</li>
          </ul>
        </div>
      </div>
    </ConsoleLayout>
  );
};

export default HospitalManagement;
