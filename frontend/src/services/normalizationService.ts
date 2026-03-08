import api from './api';
import { NormalizeRequest, NormalizeResponse, NormalizedPreview } from '../types/normalization';

class NormalizationService {
  /**
   * Normalize dataset to canonical schema
   */
  async normalizeDataset(request: NormalizeRequest): Promise<NormalizeResponse> {
    const response = await api.post<NormalizeResponse>('/api/normalization/normalize', request);
    return response.data;
  }

  /**
   * Preview normalized data
   */
  async previewNormalizedData(datasetId: number, numRows: number = 10): Promise<NormalizedPreview> {
    const response = await api.get<NormalizedPreview>(
      `/api/normalization/preview/${datasetId}?num_rows=${numRows}`
    );
    return response.data;
  }
}

export default new NormalizationService();
