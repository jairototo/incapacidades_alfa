import api from '@/lib/api';
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '@/types/auth';

/**
 * Servicio de autenticación basado en OpenAPI specification
 * Endpoints: /api/v1/auth/*
 */
export const authService = {
  /**
   * Login - Autenticar usuario
   * POST /api/v1/auth/login
   * Content-Type: application/x-www-form-urlencoded
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
   * Logout - Cerrar sesión (revoca un refresh token específico)
   * POST /api/v1/auth/logout
   * Requires: RefreshTokenRequest body
   */
  async logout(refreshToken: string): Promise<void> {
    try {
      await api.post('/auth/logout', {
        refresh_token: refreshToken,
      });
    } catch (error) {
      console.error('Error en logout:', error);
    }
  },

  /**
   * Logout All - Cerrar todas las sesiones (incrementa token_version)
   * POST /api/v1/auth/logout-all
   * Invalida todos los tokens del usuario
   */
  async logoutAll(): Promise<void> {
    await api.post('/auth/logout-all');
  },

  /**
   * Refresh token - Obtener nuevo access token
   * POST /api/v1/auth/refresh
   * Body: { refresh_token: string }
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const { data } = await api.post<RefreshTokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return data;
  },

  /**
   * Obtener usuario actual (perfil completo)
   * GET /api/v1/auth/me
   * Returns: UserProfileResponse
   */
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  /**
   * Cambiar contraseña
   * POST /api/v1/auth/change-password
   * Body: { current_password: string, new_password: string }
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
