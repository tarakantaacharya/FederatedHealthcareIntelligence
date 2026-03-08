import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Healthcare Federation</h1>
        <div className="flex items-center gap-4">
          {user?.hospital_name && <span className="text-sm">Welcome, {user.hospital_name}</span>}
          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};
