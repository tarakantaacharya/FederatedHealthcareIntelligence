/**
 * Hospital Verification Status Page
 * Professional SaaS-style verification workflow
 * Shows hospital verification status while application processes registration
 */
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const VerificationStatus: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const verificationStatus = (localStorage.getItem('verification_status') || 'PENDING') as
    | 'PENDING'
    | 'VERIFIED'
    | 'REJECTED';

  useEffect(() => {
    // If somehow verified, redirect to dashboard
    if (verificationStatus === 'VERIFIED') {
      navigate('/dashboard', { replace: true });
    }
  }, [verificationStatus, navigate]);

  const getStatusBadge = () => {
    switch (verificationStatus) {
      case 'PENDING':
        return (
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg">
            <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
            <span className="font-semibold">Under Review</span>
          </div>
        );
      case 'VERIFIED':
        return (
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="font-semibold">Verified</span>
          </div>
        );
      case 'REJECTED':
        return (
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="font-semibold">Registration Rejected</span>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    switch (verificationStatus) {
      case 'PENDING':
        return (
          <div className="text-center space-y-4">
            <p className="text-gray-700 text-lg">
              Your hospital registration is currently under review by the Central Authority.
            </p>
            <p className="text-gray-500">
              This typically takes 1-2 business days. We'll send you an email notification once your
              registration is approved.
            </p>
            <p className="text-gray-500 text-sm">
              Hospital ID: <span className="font-mono text-gray-700">{user?.hospital_id}</span>
            </p>
          </div>
        );
      case 'VERIFIED':
        return (
          <div className="text-center space-y-6">
            <p className="text-gray-700 text-lg">
              🎉 Your hospital has been verified and approved!
            </p>
            <button
              onClick={() => navigate('/dashboard', { replace: true })}
              className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Enter Dashboard
            </button>
          </div>
        );
      case 'REJECTED':
        return (
          <div className="text-center space-y-4">
            <p className="text-gray-700 text-lg">
              Your hospital registration was not approved.
            </p>
            <p className="text-gray-600">
              Please contact the Central Administration for more information about this decision.
            </p>
            <p className="text-gray-500 text-sm">
              Hospital ID: <span className="font-mono text-gray-700">{user?.hospital_id}</span>
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
                />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Hospital Verification</h1>
          </div>

          {/* Status Badge */}
          <div className="flex justify-center">{getStatusBadge()}</div>

          {/* Message */}
          <div>{getStatusMessage()}</div>

          {/* Footer */}
          {verificationStatus === 'PENDING' && (
            <div className="border-t pt-6">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <span>Checking status...</span>
              </div>
            </div>
          )}

          {/* Logout button - always visible */}
          <button
            onClick={() => {
              localStorage.removeItem('access_token');
              localStorage.removeItem('hospital_id');
              localStorage.removeItem('hospital_name');
              localStorage.removeItem('verification_status');
              navigate('/login', { replace: true });
            }}
            className="w-full text-gray-600 hover:text-gray-900 transition-colors text-sm"
          >
            Sign Out
          </button>
        </div>

        {/* Footer text */}
        <div className="text-center mt-6 text-gray-600 text-sm">
          <p>Federated Healthcare Intelligence Platform</p>
        </div>
      </div>
    </div>
  );
};

export default VerificationStatus;
