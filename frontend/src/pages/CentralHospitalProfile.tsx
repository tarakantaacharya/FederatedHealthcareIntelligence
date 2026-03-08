import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import adminService, { Hospital } from '../services/adminService';
import resultsIntelligenceService from '../services/resultsIntelligenceService';
import { formatErrorMessage } from '../utils/errorMessage';

const pct = (value: any): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
  return `${(Number(value) * 100).toFixed(2)}%`;
};

const safeNum = (value: any, digits: number = 2): string => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
  return Number(value).toFixed(digits);
};

const CentralHospitalProfile: React.FC = () => {
  const navigate = useNavigate();
  const { hospitalId } = useParams();
  const [hospital, setHospital] = useState<Hospital | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const numericId = Number(hospitalId);
    if (!numericId) {
      setError('Invalid hospital id');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError('');

        const [hospitalData, detailData] = await Promise.all([
          adminService.getAdminHospitalById(numericId),
          resultsIntelligenceService.getCentralHospitalDetail(numericId),
        ]);

        setHospital(hospitalData);
        setDetail(detailData);
      } catch (err) {
        setError(formatErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [hospitalId]);

  const roundTimeline = detail?.drilldown?.round_participation_timeline || [];

  const summary = useMemo(() => {
    const totalRounds = roundTimeline.length;
    const participatedRounds = roundTimeline.filter((r: any) => r?.participated).length;
    const activeRounds = roundTimeline.filter((r: any) => {
      const status = String(r?.status || '').toUpperCase();
      return status.includes('ACTIVE') || status.includes('TRAINING') || status.includes('OPEN');
    }).length;

    const contributionWeight =
      detail?.hospital_dashboard?.federated_participation_impact?.average_contribution_weight || 0;

    const localVsFed = detail?.hospital_dashboard?.model_performance_comparison || {};

    return {
      totalRounds,
      participatedRounds,
      inactiveRounds: Math.max(totalRounds - activeRounds, 0),
      activeRounds,
      contributionWeight,
      federatedGain: localVsFed?.federated_gain,
      predictionVolume: detail?.hospital_dashboard?.prediction_results_intelligence?.total_predictions || 0,
      datasetCount: detail?.hospital_dashboard?.dataset_intelligence?.total_datasets || 0,
      timeliness: detail?.hospital_dashboard?.federated_participation_impact?.timeliness_score,
      participationRate: detail?.hospital_dashboard?.federated_participation_impact?.participation_rate,
    };
  }, [detail, roundTimeline]);

  return (
    <ConsoleLayout title="Hospital Profile" subtitle="Central view of hospital biodata and participation status">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <button
            onClick={() => navigate('/hospitals-manage')}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
          >
            Back to Hospitals
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {formatErrorMessage(error)}
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">Loading hospital profile...</div>
        ) : !hospital ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">Hospital not found.</div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Hospital Biodata</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Hospital ID</p>
                  <p className="font-semibold text-gray-900">{hospital.hospital_id}</p>
                </div>
                <div>
                  <p className="text-gray-500">Hospital Name</p>
                  <p className="font-semibold text-gray-900">{hospital.hospital_name}</p>
                </div>
                <div>
                  <p className="text-gray-500">Joined</p>
                  <p className="font-semibold text-gray-900">{new Date(hospital.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-500">Location</p>
                  <p className="font-semibold text-gray-900">{hospital.location || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Contact Email</p>
                  <p className="font-semibold text-gray-900">{hospital.contact_email}</p>
                </div>
                <div>
                  <p className="text-gray-500">Verification</p>
                  <p className="font-semibold text-gray-900">{hospital.is_verified ? 'Verified' : 'Pending'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Current Status</p>
                  <p className="font-semibold text-gray-900">{hospital.is_active ? 'Active' : 'Inactive'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Federated Access</p>
                  <p className="font-semibold text-gray-900">{hospital.is_allowed_federated ? 'Allowed' : 'Blocked'}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Participated Rounds</p>
                <p className="text-2xl font-bold text-blue-700">{summary.participatedRounds}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Total Rounds Tracked</p>
                <p className="text-2xl font-bold text-gray-900">{summary.totalRounds}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Contribution to Global Weights</p>
                <p className="text-2xl font-bold text-purple-700">{pct(summary.contributionWeight)}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Participation Rate</p>
                <p className="text-2xl font-bold text-emerald-700">{pct(summary.participationRate)}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Active Rounds</p>
                <p className="text-2xl font-bold text-green-700">{summary.activeRounds}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Inactive Rounds</p>
                <p className="text-2xl font-bold text-red-700">{summary.inactiveRounds}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Datasets</p>
                <p className="text-2xl font-bold text-indigo-700">{summary.datasetCount}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-500">Predictions</p>
                <p className="text-2xl font-bold text-slate-700">{summary.predictionVolume}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Statistics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Federated Gain</p>
                  <p className="font-semibold text-gray-900">{safeNum(summary.federatedGain, 4)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Timeliness Score</p>
                  <p className="font-semibold text-gray-900">{pct(summary.timeliness)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Round Participation Timeline</h3>
              {roundTimeline.length === 0 ? (
                <p className="text-sm text-gray-500">No round participation timeline available.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Round</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Status</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Participated</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Started</th>
                        <th className="px-4 py-2 text-left font-semibold text-gray-600">Completed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {roundTimeline.map((round: any) => (
                        <tr key={round.round_number}>
                          <td className="px-4 py-2">{round.round_number}</td>
                          <td className="px-4 py-2">{round.status || 'N/A'}</td>
                          <td className="px-4 py-2">
                            <span
                              className={`px-2 py-1 text-xs rounded-full font-semibold ${
                                round.participated
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {round.participated ? 'Yes' : 'No'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-gray-600">{round.started_at ? new Date(round.started_at).toLocaleString() : 'N/A'}</td>
                          <td className="px-4 py-2 text-gray-600">{round.completed_at ? new Date(round.completed_at).toLocaleString() : 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default CentralHospitalProfile;
