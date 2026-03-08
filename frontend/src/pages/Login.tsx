import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import authService from '../services/authService';
import { formatErrorMessage } from '../utils/errorMessage';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const [formData, setFormData] = useState({
    hospital_id: '',
    password: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authService.login({
        hospital_id: formData.hospital_id,
        password: formData.password
      });

      // Get token from response (authService.login already stores it in localStorage)
      const token = response.access_token;
      
      // Login via context to set user state
      if (token) {
        login(token);
      }

      // Route based on role
      if (token) {
        try {
          const base64Url = token.split('.')[1];
          const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
          const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
          }).join(''));
          const payload = JSON.parse(jsonPayload);
          
          if (payload.role === 'ADMIN') {
            navigate('/admin-dashboard');
          } else {
            navigate('/dashboard');
          }
        } catch (e) {
          navigate('/dashboard');
        }
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Hospital Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Federated Healthcare Intelligence Platform
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {formatErrorMessage(error)}
            </div>
          )}

          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="hospital_id" className="block text-sm font-medium text-gray-700 mb-1">
                Hospital ID
              </label>
              <input
                id="hospital_id"
                name="hospital_id"
                type="text"
                required
                value={formData.hospital_id}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="CGH-001"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="Enter password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Sign In'}
            </button>
          </div>

          <div className="text-center">
            <Link to="/register" className="text-sm text-blue-600 hover:underline">
              Don't have an account? Register here
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
