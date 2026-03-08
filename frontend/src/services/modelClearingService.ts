import api from './api';

interface ModelSummary {
  local_model_count?: number;
  global_model_count?: number;
  models_by_type: {
    TFT: number;
    ML_REGRESSION: number;
  };
  models_by_training_type?: {
    LOCAL: number;
    FEDERATED: number;
  };
}

interface ClearModelsResponse {
  success: boolean;
  message: string;
  details: {
    deleted_weights_records: number;
    deleted_registry_records: number;
    deleted_files: number;
    failed_file_deletions: number;
    failed_deletion_details: any[];
    deleted_governance_records?: number;
  };
}

class ModelClearingService {
  /**
   * Get summary of local models for current hospital
   */
  async getLocalModelsSummary(): Promise<ModelSummary> {
    try {
      const response = await api.get('/api/models/summary');
      return response.data;
    } catch (error) {
      console.error('Error getting local models summary:', error);
      throw error;
    }
  }

  /**
   * Clear all local models for current hospital
   */
  async clearLocalModels(deleteFiles: boolean = true): Promise<ClearModelsResponse> {
    try {
      const response = await api.delete('/api/models/clear-local', {
        params: { delete_files: deleteFiles },
      });
      return response.data;
    } catch (error) {
      console.error('Error clearing local models:', error);
      throw error;
    }
  }

  /**
   * Get summary of global models (Admin only)
   */
  async getGlobalModelsSummary(): Promise<ModelSummary> {
    try {
      const response = await api.get('/api/governance/models/summary');
      return response.data;
    } catch (error) {
      console.error('Error getting global models summary:', error);
      throw error;
    }
  }

  /**
   * Clear all global models (Admin only)
   */
  async clearGlobalModels(
    deleteFiles: boolean = true,
    clearGovernance: boolean = false
  ): Promise<ClearModelsResponse> {
    try {
      const response = await api.delete('/api/governance/clear-global', {
        params: {
          delete_files: deleteFiles,
          clear_governance: clearGovernance
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error clearing global models:', error);
      throw error;
    }
  }
}

export default new ModelClearingService();
