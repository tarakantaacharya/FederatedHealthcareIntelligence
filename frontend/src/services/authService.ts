import api from './api';

export interface RegisterData {
  hospital_name: string;
  hospital_id: string;
  contact_email: string;
  location?: string;
  password: string;
}

export interface LoginData {
  hospital_id: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  hospital_id: string;
  hospital_name: string;
  verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  pending_verification?: boolean;
}

export interface HospitalInfo {
  id: number;
  hospital_name: string;
  hospital_id: string;
  contact_email: string;
  location: string | null;
  is_active: boolean;
  is_verified: boolean;
  verification_status?: "PENDING" | "VERIFIED" | "REJECTED";
  created_at: string;
}

class AuthService {
  /**
   * Register a new hospital
   */
  async register(data: RegisterData): Promise<HospitalInfo> {
    const response = await api.post<HospitalInfo>('/api/auth/register', data);
    return response.data;
  }

  /**
   * Login hospital and store token
   */
  async login(data: LoginData): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/api/auth/login', data);

    // Store token in localStorage
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('hospital_id', response.data.hospital_id);
      localStorage.setItem('hospital_name', response.data.hospital_name);
      localStorage.setItem('verification_status', response.data.verification_status);
    }

    return response.data;
  }

  /**
   * Logout - remove token from storage
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('hospital_id');
    localStorage.removeItem('hospital_name');
    localStorage.removeItem('verification_status');
  }

  /**
   * Get current authenticated hospital info
   */
  async getCurrentHospital(): Promise<HospitalInfo> {
    const response = await api.get<HospitalInfo>('/api/auth/me');
    return response.data;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  /**
   * Get stored token
   */
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Get stored hospital info with verification status
   */
  getHospitalInfo(): {
    hospital_id: string;
    hospital_name: string;
    verification_status: "PENDING" | "VERIFIED" | "REJECTED";
  } | null {
    const hospital_id = localStorage.getItem('hospital_id');
    const hospital_name = localStorage.getItem('hospital_name');
    const verification_status = (localStorage.getItem('verification_status') || 'VERIFIED') as
      | 'PENDING'
      | 'VERIFIED'
      | 'REJECTED';

    if (hospital_id && hospital_name) {
      return { hospital_id, hospital_name, verification_status };
    }

    return null;
  }
}

export default new AuthService();
