import { useCallback, useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface AuthContext {
  hospital_id: string | null;
  hospital_name: string | null;
  isAuthenticated: boolean;
  login: (hospitalId: string, password: string) => Promise<void>;
  logout: () => void;
  register: (
    hospitalName: string,
    hospitalId: string,
    contactEmail: string,
    location: string,
    password: string
  ) => Promise<void>;
}

export const useAuth = (): AuthContext & { getToken: () => string | null } => {
  const [hospital_id, setHospitalId] = useState<string | null>(null);
  const [hospital_name, setHospitalName] = useState<string | null>(null);

  useEffect(() => {
    const stored_hospital_id = localStorage.getItem('hospital_id');
    const stored_hospital_name = localStorage.getItem('hospital_name');
    if (stored_hospital_id && stored_hospital_name) {
      setHospitalId(stored_hospital_id);
      setHospitalName(stored_hospital_name);
    }
  }, []);

  const login = useCallback(async (hospitalId: string, password: string) => {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hospital_id: hospitalId,
        password,
      }),
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('hospital_id', data.hospital_id);
    localStorage.setItem('hospital_name', data.hospital_name);

    setHospitalId(data.hospital_id);
    setHospitalName(data.hospital_name);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('hospital_id');
    localStorage.removeItem('hospital_name');
    setHospitalId(null);
    setHospitalName(null);
  }, []);

  const register = useCallback(
    async (
      hospitalName: string,
      hospitalId: string,
      contactEmail: string,
      location: string,
      password: string
    ) => {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hospital_name: hospitalName,
          hospital_id: hospitalId,
          contact_email: contactEmail,
          location,
          password,
        }),
      });

      if (!response.ok) throw new Error('Registration failed');
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('hospital_id', data.hospital_id);
      localStorage.setItem('hospital_name', data.hospital_name);

      setHospitalId(data.hospital_id);
      setHospitalName(data.hospital_name);
    },
    []
  );

  const getToken = useCallback(() => {
    return localStorage.getItem('access_token');
  }, []);

  return {
    hospital_id,
    hospital_name,
    isAuthenticated: !!hospital_id,
    login,
    logout,
    register,
    getToken,
  };
};
