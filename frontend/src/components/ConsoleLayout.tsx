import React, { useMemo } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import FederatedCopilotPanel from './FederatedCopilotPanel';

interface ConsoleLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

interface NavItem {
  label: string;
  path: string;
}

const ConsoleLayout: React.FC<ConsoleLayoutProps> = ({ title, subtitle, children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = user?.role || 'HOSPITAL';

  const navItems: NavItem[] = useMemo(() => {
    if (role === 'ADMIN') {
      return [
        { label: 'Overview', path: '/admin-dashboard' },
        { label: 'Results Intel', path: '/admin/results-intelligence' },
        { label: 'Rounds History', path: '/rounds-history/central' },
        { label: 'Aggregation', path: '/aggregation' },
        { label: 'Global Model', path: '/global-model' },
        { label: 'Blockchain Audit', path: '/blockchain-audit' },
      ];
    }

    return [
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Datasets', path: '/datasets' },
      { label: 'Training', path: '/training' },
      { label: 'Rounds History', path: '/rounds-history/hospital' },
      { label: 'Global Model', path: '/global-model' },
      { label: 'Generate Prediction', path: '/prediction' },
      { label: 'Predictions', path: '/predictions' },
      { label: 'Results Intel', path: '/results-intelligence' },
      { label: 'Blockchain Audit', path: '/blockchain-audit' },
    ];
  }, [role]);

  const handleLogout = () => {
    logout();
    navigate(role === 'ADMIN' ? '/admin-login' : '/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 min-h-screen bg-white border-r border-slate-200">
          <div className="h-14 flex items-center px-4 border-b border-slate-200">
            <div className="text-sm font-semibold">Federated Console</div>
          </div>
          <nav className="p-2 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded text-sm ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`
                }
              >
                <span className="h-2 w-2 rounded-full border border-slate-400" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main */}
        <div className="flex-1">
          {/* Top bar */}
          <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-900">{title}</div>
              {subtitle && <div className="text-xs text-slate-500">{subtitle}</div>}
            </div>
            <div className="flex items-center gap-3">
              <NotificationBell />
              <div className="text-right">
                <div className="text-xs font-medium text-slate-900">{user?.hospital_name || user?.admin_name || 'User'}</div>
                <div className="text-[11px] text-slate-500">{user?.hospital_id || role}</div>
              </div>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </header>

          {/* Content */}
          <main className="p-6">{children}</main>
          <FederatedCopilotPanel />
        </div>
      </div>
    </div>
  );
};

export default ConsoleLayout;
