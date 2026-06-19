export interface EmpresaResumen {
  id: string;
  nit: string;
  razon_social: string;
  email_contacto?: string | null;
  estado: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  nombre_completo: string;
  rol: 'ADMIN' | 'AUDITOR' | 'APROBADOR' | 'EMPRESA' | 'EMPLEADO' | 'READONLY';
  estado: string;
  empresa_id?: string | null;
  empresa?: EmpresaResumen | null;
  ultimo_acceso?: string | null;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
