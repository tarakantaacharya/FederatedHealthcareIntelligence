import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const { logout, user, isVerified } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // If hospital is not verified, show minimal sidebar (only Profile & Logout)
  if (user?.role === 'HOSPITAL' && !isVerified) {
    return (
      <nav className="sidebar bg-blue-800 text-white p-4 min-h-screen w-64">
        <div className="mb-8">
          <h2 className="text-xl font-bold">Healthcare Fed</h2>
        </div>
        <ul className="space-y-4">
          <li>
            <a href="/hospital-profile" className="hover:bg-blue-700 p-2 block rounded">
              Profile
            </a>
          </li>
          <li>
            <button
              onClick={handleLogout}
              className="w-full text-left hover:bg-blue-700 p-2 block rounded"
            >
              Logout
            </button>
          </li>
        </ul>
        {/* Verification Status Indicator */}
        <div className="absolute bottom-4 left-4 right-4 bg-yellow-900 rounded-lg p-3 text-xs">
          <div className="flex items-center gap-2 text-yellow-200">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
            <span>Verification pending</span>
          </div>
        </div>
      </nav>
    );
  }

  // Full sidebar for verified hospitals or admins
  return (
    <nav className="sidebar bg-blue-800 text-white p-4 min-h-screen w-64">
      <div className="mb-8">
        <h2 className="text-xl font-bold">Healthcare Fed</h2>
      </div>
      <ul className="space-y-4">
        {user?.role === 'HOSPITAL' && (
          <>
            <li>
              <a href="/dashboard" className="hover:bg-blue-700 p-2 block rounded">
                Dashboard
              </a>
            </li>
            <li>
              <a href="/datasets" className="hover:bg-blue-700 p-2 block rounded">
                Datasets
              </a>
            </li>
            <li>
              <a href="/training" className="hover:bg-blue-700 p-2 block rounded">
                Training
              </a>
            </li>
            <li>
              <a href="/global-model" className="hover:bg-blue-700 p-2 block rounded">
                Global Model
              </a>
            </li>
            <li>
              <a href="/prediction" className="hover:bg-blue-700 p-2 block rounded">
                Prediction
              </a>
            </li>
            <li>
              <a href="/blockchain-audit" className="hover:bg-blue-700 p-2 block rounded">
                My Audit
              </a>
            </li>
          </>
        )}

        {user?.role === 'ADMIN' && (
          <>
            <li>
              <a href="/admin-dashboard" className="hover:bg-blue-700 p-2 block rounded">
                Admin Dashboard
              </a>
            </li>
            <li>
              <a href="/hospitals-manage" className="hover:bg-blue-700 p-2 block rounded">
                Manage Hospitals
              </a>
            </li>
            <li>
              <a href="/aggregation" className="hover:bg-blue-700 p-2 block rounded">
                Aggregation
              </a>
            </li>
            <li>
              <a href="/governance" className="hover:bg-blue-700 p-2 block rounded">
                Model Governance
              </a>
            </li>
            <li>
              <a href="/monitoring" className="hover:bg-blue-700 p-2 block rounded">
                Monitoring
              </a>
            </li>
            <li>
              <a href="/blockchain-audit" className="hover:bg-blue-700 p-2 block rounded">
                Global Audit
              </a>
            </li>
          </>
        )}

        <li>
          <a href="/hospital-profile" className="hover:bg-blue-700 p-2 block rounded">
            Profile
          </a>
        </li>

        <li>
          <button
            onClick={handleLogout}
            className="w-full text-left hover:bg-blue-700 p-2 block rounded"
          >
            Logout
          </button>
        </li>
      </ul>
    </nav>
  );
};
