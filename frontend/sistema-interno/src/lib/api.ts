import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';

// En desarrollo usa el proxy de Vite (/api/v1)
// En producción usa la URL completa del backend
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

/**
 * Cliente Axios configurado con interceptores JWT
 */
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Agregar JWT token
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Refresh token automático
 */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Si el error es 401 y no es un retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const { refreshToken } = useAuthStore.getState();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Llamar al endpoint de refresh (body JSON, NO header)
        const { data } = await axios.post(
          `${API_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        // Actualizar el access token en el store (esto también actualiza localStorage)
        useAuthStore.getState().updateAccessToken(data.access_token);

        // Reintentar la petición original con el nuevo token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        
        return api(originalRequest);
      } catch (refreshError) {
        // CRÍTICO: Limpiar TANTO localStorage COMO Zustand store
        useAuthStore.getState().logout();
        
        // Redirigir al login
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
