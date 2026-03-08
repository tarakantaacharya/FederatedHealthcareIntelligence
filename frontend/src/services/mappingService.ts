import api from './api';
import { AutoMapResponse, DatasetMappingResponse, ManualMappingRequest } from '../types/mapping';

class MappingService {
  /**
   * Perform auto-mapping for dataset columns
   */
  async autoMapDataset(datasetId: number): Promise<AutoMapResponse> {
    const response = await api.post<AutoMapResponse>(`/api/mapping/auto-map/${datasetId}`);
    return response.data;
  }

  /**
   * Save manual mappings
   */
  async saveManualMapping(request: ManualMappingRequest): Promise<void> {
    await api.post('/api/mapping/manual', request);
  }

  async getDatasetMappings(datasetId: number): Promise<DatasetMappingResponse> {
    const response = await api.get<DatasetMappingResponse>(`/api/mapping/dataset/${datasetId}`);
    return response.data;
  }
}

export default new MappingService();