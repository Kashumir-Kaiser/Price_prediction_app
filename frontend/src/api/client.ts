/**
 * API client for backend communication
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '@/store/useAuthStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - add JWT token
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor - handle 401
apiClient.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout and redirect
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Health check
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (username: string, email: string, password: string) => {
    const response = await axios.post(`${API_BASE_URL}/auth/register`, {
      username,
      email,
      password,
    });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  getOverviewStats: async () => {
    const response = await apiClient.get('/admin/stats/overview');
    return response.data;
  },

  getTrafficStats: async () => {
    const response = await apiClient.get('/admin/stats/traffic');
    return response.data;
  },

  getEndpointStats: async () => {
    const response = await apiClient.get('/admin/stats/endpoints');
    return response.data;
  },

  getUserStats: async () => {
    const response = await apiClient.get('/admin/stats/users');
    return response.data;
  },

  getErrorLogs: async () => {
    const response = await apiClient.get('/admin/stats/errors');
    return response.data;
  },

  getUsers: async () => {
    const response = await apiClient.get('/admin/users');
    return response.data;
  },

  deactivateUser: async (userId: number) => {
    const response = await apiClient.patch(`/admin/users/${userId}/deactivate`);
    return response.data;
  },
};

// Prices API
export const pricesApi = {
  getCryptoLatest: async () => {
    const response = await apiClient.get('/prices/crypto/latest');
    return response.data;
  },

  getCryptoHistory: async (
    symbol: string,
    timeframe: string = '1Day',
    start?: string,
    end?: string
  ) => {
    const response = await apiClient.get('/prices/crypto/history', {
      params: { symbol, timeframe, start, end },
    });
    return response.data;
  },

  getStockLatest: async (symbol: string) => {
    const response = await apiClient.get('/prices/stocks/latest', {
      params: { symbol },
    });
    return response.data;
  },

  getStockHistory: async (symbol: string, start?: string, end?: string) => {
    const response = await apiClient.get('/prices/stocks/history', {
      params: { symbol, start, end },
    });
    return response.data;
  },

  getStockFinancials: async (symbol: string, period?: string) => {
    const response = await apiClient.get('/prices/stocks/financials', {
      params: { symbol, period },
    });
    return response.data;
  },
};

// Predictions API
export const predictionsApi = {
  getCryptoPrediction: async (symbol: string, model: string = 'rf') => {
    const response = await apiClient.get('/predictions/crypto', {
      params: { symbol, model },
    });
    return response.data;
  },

  getStockPrediction: async (symbol: string, model: string = 'rf') => {
    const response = await apiClient.get('/predictions/stock', {
      params: { symbol, model },
    });
    return response.data;
  },

  triggerRetrain: async (symbol: string, assetType: string) => {
    const response = await apiClient.post('/predictions/retrain', null, {
      params: { symbol, asset_type: assetType },
    });
    return response.data;
  },
};

// React Query hooks
export const useMarketData = () => {
  return {
    fetchCryptoHistory: pricesApi.getCryptoHistory,
    fetchStockHistory: pricesApi.getStockHistory,
    fetchCryptoPrediction: predictionsApi.getCryptoPrediction,
    fetchStockPrediction: predictionsApi.getStockPrediction,
  };
};