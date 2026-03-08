import api from './api';

export interface BlockchainLogEntry {
  round_id: number;
  model_hash: string;
  block_hash: string;
  timestamp: string;
  prev_block_hash?: string;
  hospital_id?: string;
  hospital_name?: string;
}

export interface BlockchainLogResponse {
  start_index: number;
  count: number;
  logs: BlockchainLogEntry[];
  is_valid: boolean;
  hospital_id?: string;
}

class BlockchainService {
  /**
   * Retrieve full blockchain logs (admin only)
   */
  async getAdminChain(startIndex: number = 0, count: number = 100): Promise<BlockchainLogResponse> {
    const response = await api.get<BlockchainLogResponse>('/api/blockchain/admin-chain', {
      params: { start_index: startIndex, count },
    });
    return response.data;
  }

  /**
   * Retrieve hospital-specific blockchain events
   */
  async getHospitalChain(startIndex: number = 0, count: number = 100): Promise<BlockchainLogResponse> {
    const response = await api.get<BlockchainLogResponse>('/api/blockchain/my-chain', {
      params: { start_index: startIndex, count },
    });
    return response.data;
  }

  /**
   * Retrieve local audit chain logs (legacy - for backward compatibility)
   */
  async getLogs(startIndex: number = 0, count: number = 100): Promise<BlockchainLogResponse> {
    const response = await api.get<BlockchainLogResponse>('/api/blockchain/logs', {
      params: { start_index: startIndex, count },
    });
    return response.data;
  }
}

export default new BlockchainService();
