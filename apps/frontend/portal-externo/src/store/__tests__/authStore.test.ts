import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAuthStore, useIsEmpresaHabilitada } from '@/store/authStore';
import type { LoginResponse, User } from '@/types/auth';

const baseUser: User = {
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

  it('updateAccessToken updates store state and localStorage', () => {
    const resp = { access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900, user: baseUser } as LoginResponse;
    useAuthStore.getState().login(resp, baseUser);
    useAuthStore.getState().updateAccessToken('new-token');
    expect(useAuthStore.getState().accessToken).toBe('new-token');
    expect(localStorage.getItem('access_token')).toBe('new-token');
  });

  it('useIsEmpresaHabilitada is true for EMPRESA with empresa_id', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { ...baseUser } as any });
    const { result } = renderHook(() => useIsEmpresaHabilitada());
    expect(result.current).toBe(true);
  });

  it('useIsEmpresaHabilitada is false when empresa_id is missing', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { ...baseUser, empresa_id: null } as any });
    const { result } = renderHook(() => useIsEmpresaHabilitada());
    expect(result.current).toBe(false);
  });
});
