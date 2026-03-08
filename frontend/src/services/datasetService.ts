import api from './api';
import { Dataset, DatasetDetail, DatasetStatus, DatasetModelSummary } from '../types/dataset';

class DatasetService {
  /**
   * Upload CSV dataset
   */
  async uploadDataset(file: File): Promise<DatasetDetail> {
    console.log('[datasetService.uploadDataset] Starting upload:', file.name);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await api.post<DatasetDetail>('/api/datasets/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('[datasetService.uploadDataset] Upload successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('[datasetService.uploadDataset] Upload failed:', error);
      throw error;
    }
  }

  /**
   * Get all datasets for current hospital
   */
  async getDatasets(skip: number = 0, limit: number = 100): Promise<Dataset[]> {
    console.log('[datasetService.getDatasets] Fetching datasets...');
    const response = await api.get<Dataset[]>('/api/datasets/', {
      params: { skip, limit },
    });
    console.log('[datasetService.getDatasets] Response:', response.data);
    return response.data;
  }

  /**
   * Get dataset details by ID
   */
  async getDatasetById(datasetId: number): Promise<DatasetDetail> {
    console.log('[datasetService.getDatasetById] Fetching dataset:', datasetId);
    try {
      const response = await api.get<DatasetDetail>(`/api/datasets/${datasetId}`);
      console.log('[datasetService.getDatasetById] Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[datasetService.getDatasetById] Failed:', error);
      throw error;
    }
  }

  /**
   * Get dataset details by ID (alias)
   */
  async getDatasetDetail(datasetId: number): Promise<DatasetDetail> {
    return this.getDatasetById(datasetId);
  }

  /**
   * Get dataset intelligence status
   */
  async getDatasetStatus(datasetId: number): Promise<DatasetStatus> {
    const response = await api.get<DatasetStatus>(`/api/datasets/${datasetId}/status`);
    return response.data;
  }

  /**
   * Get trained models for a dataset
   */
  async getDatasetModels(datasetId: number): Promise<DatasetModelSummary[]> {
    const response = await api.get<DatasetModelSummary[]>(`/api/datasets/${datasetId}/models`);
    return response.data;
  }

  /**
   * Delete dataset
   */
  async deleteDataset(datasetId: number): Promise<void> {
    console.log('[datasetService.deleteDataset] Deleting dataset:', datasetId);
    try {
      const response = await api.delete(`/api/datasets/${datasetId}`);
      console.log('[datasetService.deleteDataset] Delete successful, response:', response.data);
      return;
    } catch (error: any) {
      console.error('[datasetService.deleteDataset] Delete failed:', error);
      if (error.response) {
        console.error('[datasetService.deleteDataset] Response status:', error.response.status);
        console.error('[datasetService.deleteDataset] Response data:', error.response.data);
      } else if (error.request) {
        console.error('[datasetService.deleteDataset] No response received');
        console.error('[datasetService.deleteDataset] Request:', error.request);
      }
      throw error;
    }
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}

export default new DatasetService();
