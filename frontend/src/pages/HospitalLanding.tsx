import React from 'react';
import { useNavigate } from 'react-router-dom';

const HospitalLanding: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-slate-900">Hospital Console</h1>
          <div className="space-x-3">
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 text-slate-700 border border-slate-300 rounded-md hover:bg-slate-100"
            >
              Hospital Login
            </button>
            <button
              onClick={() => navigate('/register')}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
            >
              Register Hospital
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid md:grid-cols-2 gap-8 items-start">
          <div>
            <h2 className="text-3xl font-semibold text-slate-900 mb-4">Hospital Participation</h2>
            <p className="text-base text-slate-600 mb-6">
              Upload datasets, train locally, and contribute weights to federated rounds with privacy protections.
            </p>
            <div className="space-x-3">
              <button
                onClick={() => navigate('/register')}
                className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700"
              >
                Register
              </button>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-2 border border-slate-300 text-slate-700 font-semibold rounded-md hover:bg-slate-100"
              >
                Sign In
              </button>
            </div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-slate-900">Hospital Capabilities</h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              <li>• Dataset management and schema mapping</li>
              <li>• Local model training and weight upload</li>
              <li>• Privacy controls and secure aggregation</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default HospitalLanding;
