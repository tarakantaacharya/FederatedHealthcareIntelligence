export interface Hospital {
  id: number;
  hospital_name: string;
  hospital_id: string;
  contact_email: string;
  location: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at?: string;
}

export interface RegisterFormData {
  hospital_name: string;
  hospital_id: string;
  contact_email: string;
  location: string;
  password: string;
  confirm_password: string;
}

export interface LoginFormData {
  hospital_id: string;
  password: string;
}
