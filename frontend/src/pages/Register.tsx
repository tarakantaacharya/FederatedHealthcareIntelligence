import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/authService';
import { formatErrorMessage } from '../utils/errorMessage';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  
  const [formData, setFormData] = useState({
    hospital_name: '',
    hospital_id: '',
    contact_email: '',
    location: '',
    password: '',
    confirm_password: ''
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
    setSuccess('');

    // Validation
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      await authService.register({
        hospital_name: formData.hospital_name,
        hospital_id: formData.hospital_id,
        contact_email: formData.contact_email,
        location: formData.location || undefined,
        password: formData.password
      });

      setSuccess('Registration successful! Redirecting to login...');
      
      setTimeout(() => {
        navigate('/login');
      }, 2000);
      
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Registration failed. Please try again.';
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
            Hospital Registration
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join the Federated Healthcare Intelligence Network
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {formatErrorMessage(error)}
            </div>
          )}
          
          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              {success}
            </div>
          )}

          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="hospital_name" className="block text-sm font-medium text-gray-700 mb-1">
                Hospital Name *
              </label>
              <input
                id="hospital_name"
                name="hospital_name"
                type="text"
                required
                value={formData.hospital_name}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="City General Hospital"
              />
            </div>

            <div>
              <label htmlFor="hospital_id" className="block text-sm font-medium text-gray-700 mb-1">
                Hospital ID *
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
              <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700 mb-1">
                Contact Email *
              </label>
              <input
                id="contact_email"
                name="contact_email"
                type="email"
                required
                value={formData.contact_email}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="admin@cityhospital.com"
              />
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                id="location"
                name="location"
                type="text"
                value={formData.location}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="New York, USA"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="Minimum 8 characters"
              />
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password *
              </label>
              <input
                id="confirm_password"
                name="confirm_password"
                type="password"
                required
                value={formData.confirm_password}
                onChange={handleChange}
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary focus:border-primary"
                placeholder="Re-enter password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Registering...' : 'Register Hospital'}
            </button>
          </div>

          <div className="text-center">
            <Link to="/login" className="text-sm text-blue-600 hover:underline">
              Already registered? Login here
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
