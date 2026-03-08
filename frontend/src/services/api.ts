import axios from 'axios';

const API_BASE_URL =
  process.env.NODE_ENV === 'development'
    ? ''
    : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

console.log('[API] Configuring API with base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`[API] Request to ${config.method?.toUpperCase()} ${config.url} with auth`);
    } else {
      console.warn(`[API] Request to ${config.method?.toUpperCase()} ${config.url} WITHOUT auth token`);
    }
    return config;
  },
  (error) => {
    console.error('[API] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response from ${response.config.method?.toUpperCase()} ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(`[API] Response error ${error.response.status} from ${error.config?.method?.toUpperCase()} ${error.config?.url}:`, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('[API] No response received:', error.request);
      console.error('[API] This usually means the backend is not running or CORS is blocking the request');
    } else {
      // Something else happened
      console.error('[API] Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
