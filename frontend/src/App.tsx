import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminLogin from './pages/AdminLogin';
import Training from './pages/Training';
import TrainingStatus from './pages/TrainingStatus';
import Aggregation from './pages/Aggregation';
import AggregationRoundDetail from './pages/AggregationRoundDetail';
import GlobalModel from './pages/GlobalModel';
import Models from './pages/Models';
import Prediction from './pages/Prediction';
import Predictions from './pages/Predictions';
import PredictionDetail from './pages/PredictionDetail';
import BlockchainAudit from './pages/BlockchainAudit';
import ResultsIntelligenceDashboard from './pages/ResultsIntelligenceDashboard';
import Landing from './pages/Landing';
import HospitalManagement from './pages/HospitalManagement';
import CentralHospitalProfile from './pages/CentralHospitalProfile';
import ModelGovernance from './pages/ModelGovernance';
import SystemMonitoring from './pages/SystemMonitoring';
import DatasetManagement from './pages/DatasetManagement';
import VerificationStatus from './pages/VerificationStatus';
import SchemaMapping from './pages/SchemaMapping';
import CentralRoundsHistory from './pages/CentralRoundsHistory';
import CentralRoundHistoryDetail from './pages/CentralRoundHistoryDetail';
import HospitalRoundsHistory from './pages/HospitalRoundsHistory';
import HospitalRoundHistoryDetail from './pages/HospitalRoundHistoryDetail';

const RootRoute: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Landing />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-100">
          <Routes>
            <Route path="/" element={<RootRoute />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/admin-login" element={<AdminLogin />} />
            
            {/* Verification status page - for pending hospitals */}
            <Route path="/verification-status" element={
              <VerificationStatus />
            } />
            
            {/* Admin routes - require ADMIN role */}
            <Route path="/admin-dashboard" element={
              <ProtectedRoute role="ADMIN">
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/aggregation" element={
              <ProtectedRoute role="ADMIN">
                <Aggregation />
              </ProtectedRoute>
            } />
            <Route path="/aggregation/round/:roundNumber" element={
              <ProtectedRoute role="ADMIN">
                <AggregationRoundDetail />
              </ProtectedRoute>
            } />
            <Route path="/hospitals-manage" element={
              <ProtectedRoute role="ADMIN">
                <HospitalManagement />
              </ProtectedRoute>
            } />
            <Route path="/hospitals-manage/:hospitalId" element={
              <ProtectedRoute role="ADMIN">
                <CentralHospitalProfile />
              </ProtectedRoute>
            } />
            <Route path="/governance" element={
              <ProtectedRoute role="ADMIN">
                <ModelGovernance />
              </ProtectedRoute>
            } />
            <Route path="/monitoring" element={
              <ProtectedRoute role="ADMIN">
                <SystemMonitoring />
              </ProtectedRoute>
            } />
            <Route path="/rounds-history/central" element={
              <ProtectedRoute role="ADMIN">
                <CentralRoundsHistory />
              </ProtectedRoute>
            } />
            <Route path="/rounds-history/central/:roundNumber" element={
              <ProtectedRoute role="ADMIN">
                <CentralRoundHistoryDetail />
              </ProtectedRoute>
            } />
            <Route path="/admin/results-intelligence" element={
              <ProtectedRoute role="ADMIN">
                <ResultsIntelligenceDashboard />
              </ProtectedRoute>
            } />
            
            {/* Hospital routes - require HOSPITAL or higher role */}
            <Route path="/dashboard" element={
              <ProtectedRoute role="HOSPITAL">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/training" element={
              <ProtectedRoute role="HOSPITAL">
                <Training />
              </ProtectedRoute>
            } />
            <Route path="/training-status" element={
              <ProtectedRoute>
                <TrainingStatus />
              </ProtectedRoute>
            } />
            <Route path="/datasets" element={
              <ProtectedRoute role="HOSPITAL">
                <DatasetManagement />
              </ProtectedRoute>
            } />
            <Route path="/schema-mapping/:datasetId" element={
              <ProtectedRoute role="HOSPITAL">
                <SchemaMapping />
              </ProtectedRoute>
            } />
            <Route path="/models" element={
              <ProtectedRoute role="HOSPITAL">
                <Models />
              </ProtectedRoute>
            } />
            <Route path="/prediction" element={
              <ProtectedRoute role="HOSPITAL">
                <Prediction />
              </ProtectedRoute>
            } />
            <Route path="/predictions" element={
              <ProtectedRoute role="HOSPITAL">
                <Predictions />
              </ProtectedRoute>
            } />
            <Route path="/results-intelligence" element={
              <ProtectedRoute role="HOSPITAL">
                <ResultsIntelligenceDashboard />
              </ProtectedRoute>
            } />
            <Route path="/rounds-history/hospital" element={
              <ProtectedRoute role="HOSPITAL">
                <HospitalRoundsHistory />
              </ProtectedRoute>
            } />
            <Route path="/rounds-history/hospital/:roundNumber" element={
              <ProtectedRoute role="HOSPITAL">
                <HospitalRoundHistoryDetail />
              </ProtectedRoute>
            } />
            <Route path="/prediction-detail/:predictionId" element={
              <ProtectedRoute role="HOSPITAL">
                <PredictionDetail />
              </ProtectedRoute>
            } />

            {/* Shared routes */}
            <Route path="/global-model" element={
              <ProtectedRoute>
                <GlobalModel />
              </ProtectedRoute>
            } />
            <Route path="/blockchain-audit" element={
              <ProtectedRoute>
                <BlockchainAudit />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
