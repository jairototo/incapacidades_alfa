import api from '@/lib/api';
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '@/types/auth';

/**
 * Servicio de autenticación
 */
export const authService = {
  /**
   * Login - Autenticar usuario
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const { data } = await api.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return data;
  },

  /**
   * Logout - Cerrar sesión
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Error en logout:', error);
    }
  },

  /**
   * Refresh token - Obtener nuevo access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const { data } = await api.post<RefreshTokenResponse>('/auth/refresh', null, {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    return data;
  },

  /**
   * Obtener usuario actual
   */
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  /**
   * Cambiar contraseña
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
