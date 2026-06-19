import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { RefreshTokenResponse } from '@/types/auth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let queue: Array<(token: string | null) => void> = [];

const flushQueue = (token: string | null) => {
  queue.forEach((cb) => cb(token));
  queue = [];
};

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;
    const isRefreshCall = original?.url?.includes('/auth/refresh');

    if (status !== 401 || original?._retry || isRefreshCall) {
      return Promise.reject(error);
    }
    original._retry = true;

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      forceLogout();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push((token) => {
          if (!token) return reject(error);
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await axios.post<RefreshTokenResponse>(
        `${api.defaults.baseURL}/auth/refresh`,
        { refresh_token: refreshToken },
      );
      localStorage.setItem('access_token', data.access_token);
      flushQueue(data.access_token);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    } catch (e) {
      flushQueue(null);
      forceLogout();
      return Promise.reject(e);
    } finally {
      isRefreshing = false;
    }
  },
);

function forceLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  if (window.location.pathname !== '/login') window.location.href = '/login';
}

export default api;
