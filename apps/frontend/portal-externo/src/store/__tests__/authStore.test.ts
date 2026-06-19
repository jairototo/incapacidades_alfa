import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import type { LoginResponse } from '@/types/auth';

const baseUser = {
  id: '1', username: 'empresa1', email: 'e@e.com', nombre_completo: 'Empresa Uno',
  rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1',
  empresa: { id: 'emp-1', nit: '900', razon_social: 'ACME', estado: 'ACTIVA' },
  created_at: '2026-01-01',
};

describe('authStore', () => {
  beforeEach(() => { useAuthStore.getState().logout(); localStorage.clear(); });

  it('stores tokens and user on login', () => {
    const resp = { access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900, user: baseUser } as LoginResponse;
    useAuthStore.getState().login(resp, baseUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(localStorage.getItem('access_token')).toBe('a');
  });

  it('clears everything on logout', () => {
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
