import type { AxiosResponse } from 'axios';
import api from './api';
import { 
  WeightUploadRequest, 
  WeightUploadResponse, 
  MaskUploadRequest, 
  MaskUploadResponse,
  MaskGenerationRequest,
  MaskGenerationResponse 
} from '../types/weights';

class WeightService {
  /**
   * Upload model weights to central server
   */
  async uploadWeights(request: WeightUploadRequest): Promise<AxiosResponse<WeightUploadResponse>> {
    const response = await api.post<WeightUploadResponse>('/api/weights/upload', request);
    return response;
  }

  /**
   * Generate MPC mask for a trained model
   */
  async generateMask(request: MaskGenerationRequest): Promise<AxiosResponse<MaskGenerationResponse>> {
    const response = await api.post<MaskGenerationResponse>('/api/weights/masks/generate', request);
    return response;
  }

  /**
   * Upload MPC mask for a round
   */
  async uploadMask(request: MaskUploadRequest): Promise<AxiosResponse<MaskUploadResponse>> {
    const response = await api.post<MaskUploadResponse>('/api/weights/masks/upload', request);
    return response;
  }

  /**
   * Extract weights from model (for inspection)
   */
  async extractWeights(modelId: number): Promise<any> {
    const response = await api.get(`/api/weights/extract/${modelId}`);
    return response.data;
  }

  /**
   * Alias for hospital-side JSON preview after training
   */
  async getHospitalModelWeights(modelId: number): Promise<any> {
    return this.extractWeights(modelId);
  }

  /**
   * Admin: get one participant hospital uploaded central weights JSON for round
   */
  async getCentralHospitalWeights(roundNumber: number, hospitalId: number): Promise<any> {
    const response = await api.get(`/api/weights/central/round/${roundNumber}/hospital/${hospitalId}`);
    return response.data;
  }
}

export default new WeightService();
