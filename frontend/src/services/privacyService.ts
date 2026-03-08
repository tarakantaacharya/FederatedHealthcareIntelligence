import axios from 'axios';
import {
  PrivacyPolicy,
  EpsilonMetrics,
  PrivacyAuditLog,
  PrivacyComplianceReport,
  TrainingConfirmationRequest,
  TrainingConfirmationResponse,
  PrivacyPolicyRequest,
  PrivacyViolation,
  AdminPrivacyDashboard,
  ParameterComplianceCheck,
  LocalTrainingConstraints
} from '../types/privacy';

/**
 * Privacy Service
 * 
 * Handles all privacy governance and differential privacy API calls
 * Including policy management, epsilon tracking, compliance reporting, and audit logging
 */
export class PrivacyService {
  private static API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  /**
   * Get the current privacy policy
   * Available to all authenticated users
   */
  static async getPrivacyPolicy(): Promise<PrivacyPolicy> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/policy`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch privacy policy:', error);
      throw error;
    }
  }

  /**
   * Get epsilon usage metrics for current hospital and round
   */
  static async getEpsilonMetrics(): Promise<EpsilonMetrics> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/metrics`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch epsilon metrics:', error);
      throw error;
    }
  }

  /**
   * Get privacy audit logs for current hospital
   */
  static async getPrivacyAuditLogs(limit: number = 50): Promise<PrivacyAuditLog[]> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/audit-logs`,
        {
          params: { limit },
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.audit_logs || [];
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
      throw error;
    }
  }

  /**
   * Get privacy compliance report for current hospital
   */
  static async getComplianceReport(): Promise<PrivacyComplianceReport> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/compliance-report`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch compliance report:', error);
      throw error;
    }
  }

  /**
   * Check if training parameters comply with policy
   */
  static async checkParameterCompliance(
    localEpochs: number,
    batchSize: number
  ): Promise<ParameterComplianceCheck> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${this.API_URL}/api/privacy/check-compliance`,
        {
          local_epochs: localEpochs,
          batch_size: batchSize
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to check parameter compliance:', error);
      throw error;
    }
  }

  /**
   * Confirm training with privacy policy acknowledged
   * Returns confirmation or raises exception if policy violated
   */
  static async confirmTraining(
    request: TrainingConfirmationRequest
  ): Promise<TrainingConfirmationResponse> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${this.API_URL}/api/privacy/confirm-training`,
        request,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to confirm training:', error);
      throw error;
    }
  }

  /**
   * Get local training constraints (helper method)
   * Derived from privacy policy
   */
  static async getLocalTrainingConstraints(): Promise<LocalTrainingConstraints> {
    try {
      const policy = await this.getPrivacyPolicy();
      return {
        maxEpochs: policy.max_local_epochs,
        maxBatchSize: policy.max_batch_size,
        enforced: true,
        reason: 'Privacy policy enforces differential privacy constraints'
      };
    } catch (error) {
      console.error('Failed to get training constraints:', error);
      // Return safe defaults
      return {
        maxEpochs: 3,
        maxBatchSize: 32,
        enforced: true,
        reason: 'Default security constraints (policy unavailable)'
      };
    }
  }

  /**
   * Admin: Get system-wide privacy dashboard
   */
  static async getAdminPrivacyDashboard(): Promise<AdminPrivacyDashboard> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/admin-dashboard`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to fetch admin dashboard:', error);
      throw error;
    }
  }

  /**
   * Admin: Get all privacy violations
   */
  static async getAllPrivacyViolations(limit: number = 100): Promise<PrivacyViolation[]> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/violations`,
        {
          params: { limit },
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data.violations || [];
    } catch (error) {
      console.error('Failed to fetch privacy violations:', error);
      throw error;
    }
  }

  /**
   * Admin: Update privacy policy
   */
  static async updatePrivacyPolicy(
    policyUpdate: PrivacyPolicyRequest
  ): Promise<PrivacyPolicy> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.put(
        `${this.API_URL}/api/privacy/policy/update`,
        policyUpdate,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to update privacy policy:', error);
      throw error;
    }
  }

  /**
   * Admin: Resolve a privacy violation
   */
  static async resolveViolation(violationId: number): Promise<PrivacyViolation> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${this.API_URL}/api/privacy/violations/${violationId}/resolve`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to resolve violation:', error);
      throw error;
    }
  }

  /**
   * Get privacy policy for specific round (historical)
   */
  static async getPolicyForRound(roundNumber: number): Promise<PrivacyPolicy> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/policy/round/${roundNumber}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch policy for round ${roundNumber}:`, error);
      throw error;
    }
  }

  /**
   * Export privacy compliance report as PDF
   */
  static async exportComplianceReportPDF(): Promise<Blob> {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${this.API_URL}/api/privacy/compliance-report/export-pdf`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          },
          responseType: 'blob'
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to export compliance report:', error);
      throw error;
    }
  }

  /**
   * Health check for privacy service
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.API_URL}/api/privacy/health`, {
        timeout: 5000
      });
      return response.data?.status === 'healthy';
    } catch (error) {
      console.error('Privacy service health check failed:', error);
      return false;
    }
  }
}

export default PrivacyService;
