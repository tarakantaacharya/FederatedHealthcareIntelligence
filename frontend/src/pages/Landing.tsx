import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">FH</span>
              </div>
              <h1 className="text-2xl font-semibold text-slate-900">
                FedHealth Console
              </h1>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => navigate('/login')}
                className="px-4 py-2 text-slate-700 border border-slate-300 rounded-md hover:bg-slate-100"
              >
                Hospital Login
              </button>
              <button
                onClick={() => navigate('/admin-login')}
                className="px-4 py-2 text-slate-700 border border-slate-300 rounded-md hover:bg-slate-100"
              >
                Admin Login
              </button>
              <button
                onClick={() => navigate('/register')}
                className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700"
              >
                Register Hospital
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h2 className="text-4xl font-bold text-slate-900 leading-tight">
              Privacy-Preserving Federated Healthcare Intelligence
            </h2>
            <p className="text-lg text-slate-600">
              Collaborative machine learning platform enabling hospitals to train models together without sharing sensitive patient data.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => navigate('/register')}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
              >
                Get Started
              </button>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-3 border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition"
              >
                Sign In
              </button>
            </div>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-slate-100 rounded-lg p-8 border border-slate-200">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-3xl font-bold text-blue-600">FedAvg</div>
                <p className="text-sm text-slate-600 mt-1">Aggregation</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-3xl font-bold text-green-600">ε=0.5</div>
                <p className="text-sm text-slate-600 mt-1">Diff. Privacy</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-3xl font-bold text-purple-600">MPC</div>
                <p className="text-sm text-slate-600 mt-1">Secure Compute</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-3xl font-bold text-orange-600">Chain</div>
                <p className="text-sm text-slate-600 mt-1">Audit Trail</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-2xl font-bold text-slate-900 text-center mb-12">
            Platform Capabilities
          </h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="border border-slate-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-slate-900 mb-3">Federated Training</h4>
              <p className="text-slate-600 text-sm">
                Coordinate multi-hospital training rounds with FedAvg aggregation. Local models never leave your infrastructure.
              </p>
            </div>
            <div className="border border-slate-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-slate-900 mb-3">Privacy Protection</h4>
              <p className="text-slate-600 text-sm">
                Differential privacy (ε=0.5), secure multi-party computation, and cryptographic hashing protect sensitive data.
              </p>
            </div>
            <div className="border border-slate-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-slate-900 mb-3">Model Governance</h4>
              <p className="text-slate-600 text-sm">
                Blockchain audit trail, model approval workflows, and drift detection ensure model quality and compliance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-3xl font-bold text-slate-900">20+</div>
            <p className="text-slate-600 mt-2">Core Services</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900">70+</div>
            <p className="text-slate-600 mt-2">API Endpoints</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900">3-Tier</div>
            <p className="text-slate-600 mt-2">Security Stack</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-slate-900">100%</div>
            <p className="text-slate-600 mt-2">Data Privacy</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-white font-bold mb-4">FedHealth</h4>
              <p className="text-sm">Privacy-preserving federated learning for healthcare</p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
                <li><a href="#" className="hover:text-white">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Support</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Status</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Privacy</a></li>
                <li><a href="#" className="hover:text-white">Terms</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2025 FedHealth. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
