import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { formatErrorMessage } from '../utils/errorMessage';

const AdminLogin: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    admin_id: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/admin/login`,
        {
          admin_id: formData.admin_id,
          password: formData.password,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const { access_token } = response.data;

      // Use AuthContext to store token and parse role from JWT
      login(access_token);

      // Redirect to admin dashboard
      navigate('/admin-dashboard');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-slate-900">Central Server</h1>
          <p className="text-slate-600 mt-1 text-sm">Administrator Login</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-6 shadow-sm">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              {formatErrorMessage(error)}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Admin ID Field */}
            <div>
              <label htmlFor="admin_id" className="block text-sm font-medium text-gray-700 mb-2">
                Admin ID
              </label>
              <input
                id="admin_id"
                name="admin_id"
                type="text"
                required
                value={formData.admin_id}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition"
                placeholder="ADMIN-001"
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition"
                placeholder="Enter your password"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red-600 text-white font-semibold py-2 rounded-md hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Logging in...' : 'Admin Login'}
            </button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          {/* Hospital Login Link */}
          <div className="text-center">
            <p className="text-gray-600 text-sm">
              Hospital staff login?{' '}
              <Link to="/login" className="text-blue-600 font-semibold hover:text-blue-700 transition">
                Go to Hospital Login
              </Link>
            </p>
          </div>
        </div>

        {/* Footer Links */}
        <div className="text-center space-y-3">
          <Link
            to="/"
            className="inline-block text-sm text-gray-600 hover:text-gray-900 transition"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
