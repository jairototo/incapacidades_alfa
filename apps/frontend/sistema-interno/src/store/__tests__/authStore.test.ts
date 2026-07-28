import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore, useCanPerform } from '../authStore';
import { renderHook } from '@testing-library/react';
import { RolUsuario } from '@/types/enums';
import type { User } from '@/types/auth';

function setUser(rol: RolUsuario) {
  const user: User = {
    id: '1',
    username: 'test',
    email: 'test@test.com',
    nombres: 'Test',
    apellidos: 'User',
    rol,
    estado: 'ACTIVO' as any,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
  useAuthStore.setState({ isAuthenticated: true, user, accessToken: 't', refreshToken: 'r' });
}

describe('useCanPerform — Empresas/Empleados matrix', () => {
  beforeEach(() => {
    useAuthStore.setState({ isAuthenticated: false, user: null, accessToken: null, refreshToken: null });
  });

  it('LIQUIDADOR can read but not write Empresas/Empleados', () => {
    setUser(RolUsuario.LIQUIDADOR);
    const { result: read1 } = renderHook(() => useCanPerform('empresa.read'));
    const { result: read2 } = renderHook(() => useCanPerform('empleado.read'));
    const { result: write1 } = renderHook(() => useCanPerform('empresa.create'));
    const { result: write2 } = renderHook(() => useCanPerform('empleado.create'));
    expect(read1.current).toBe(true);
    expect(read2.current).toBe(true);
    expect(write1.current).toBe(false);
    expect(write2.current).toBe(false);
  });

  it('AUDITOR can read Empresas and read+write Empleados, but not write Empresas', () => {
    setUser(RolUsuario.AUDITOR);
    const { result: empresaRead } = renderHook(() => useCanPerform('empresa.read'));
    const { result: empresaCreate } = renderHook(() => useCanPerform('empresa.create'));
    const { result: empleadoCreate } = renderHook(() => useCanPerform('empleado.create'));
    const { result: empleadoDelete } = renderHook(() => useCanPerform('empleado.delete'));
    expect(empresaRead.current).toBe(true);
    expect(empresaCreate.current).toBe(false);
    expect(empleadoCreate.current).toBe(true);
    expect(empleadoDelete.current).toBe(true);
  });

  it('READONLY has no Empresas/Empleados access at all', () => {
    setUser(RolUsuario.READONLY);
    const { result: empresaRead } = renderHook(() => useCanPerform('empresa.read'));
    const { result: empleadoRead } = renderHook(() => useCanPerform('empleado.read'));
    expect(empresaRead.current).toBe(false);
    expect(empleadoRead.current).toBe(false);
  });

  it('ADMIN can do everything via the wildcard', () => {
    setUser(RolUsuario.ADMIN);
    const { result } = renderHook(() => useCanPerform('empresa.delete'));
    expect(result.current).toBe(true);
  });
});
