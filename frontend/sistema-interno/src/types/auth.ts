import { RolUsuario, EstadoUsuario } from './enums';

/**
 * Usuario autenticado
 */
export interface User {
  id: string;
  username: string;
  email: string;
  nombres: string;
  apellidos: string;
  rol: RolUsuario;
  estado: EstadoUsuario;
  created_at: string;
  updated_at: string;
}

/**
 * Tokens JWT
 */
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Login request
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Login response
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

/**
 * Refresh token response
 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}
