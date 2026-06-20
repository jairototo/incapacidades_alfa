import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useEmpleadosDeMiEmpresa } from '@/services/empresaEmpleadoService';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

vi.mock('@/lib/api', () => ({ default: { get: vi.fn() } }));

const wrapper = ({ children }: { children: ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
};

describe('useEmpleadosDeMiEmpresa', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: '1', username: 'e', email: 'e', nombre_completo: 'E', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1', created_at: 'x' } as any,
    });
  });

  it('calls the nested company endpoint with search params', async () => {
    (api.get as any).mockResolvedValue({
      data: [{ id: 'e1', numero_documento: '1', tipo_documento: 'CC', nombres: 'Ana', apellidos: 'G', estado: 'ACTIVO', created_at: 'x' }],
    });
    const { result } = renderHook(() => useEmpleadosDeMiEmpresa('ana'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith('/empresas/emp-1/empleados', {
      params: { search: 'ana', estado: 'ACTIVO', limit: 50 },
    });
    expect(result.current.data?.[0].nombres).toBe('Ana');
  });

  it('omits an empty search', async () => {
    (api.get as any).mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useEmpleadosDeMiEmpresa(''), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith('/empresas/emp-1/empleados', {
      params: { search: undefined, estado: 'ACTIVO', limit: 50 },
    });
  });

  it('is disabled when the user has no empresa_id', () => {
    useAuthStore.setState({ user: { empresa_id: null } as any });
    const { result } = renderHook(() => useEmpleadosDeMiEmpresa(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
    expect(api.get).not.toHaveBeenCalled();
  });
});
