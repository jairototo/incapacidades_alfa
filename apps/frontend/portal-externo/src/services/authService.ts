import api from '@/lib/api';
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '@/types/auth';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    const { data } = await api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  async logout(refreshToken: string): Promise<void> {
    try { await api.post('/auth/logout', { refresh_token: refreshToken }); }
    catch (e) { console.error('logout error', e); }
  },
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const { data } = await api.post<RefreshTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
    return data;
  },
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },
};
