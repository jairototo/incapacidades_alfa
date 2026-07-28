import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpleadosPage } from '../EmpleadosPage';
import { empleadoService } from '@/services/empleadoService';
import { empresaService } from '@/services/empresaService';
import { useAuthStore } from '@/store/authStore';
import { RolUsuario } from '@/types/enums';

vi.mock('@/services/empleadoService');
vi.mock('@/services/empresaService');

function renderPage(initialRoute = '/empleados') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <EmpleadosPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function setUser(rol: RolUsuario) {
  useAuthStore.setState({
    isAuthenticated: true,
    user: { id: '1', username: 'u', email: 'u@u.com', nombres: 'U', apellidos: 'U', rol, estado: 'ACTIVO' as any, created_at: '', updated_at: '' },
    accessToken: 't', refreshToken: 'r',
  });
}

describe('EmpleadosPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(empleadoService.list).mockResolvedValue([
      { id: '1', numero_documento: '123', tipo_documento: 'CC', nombres: 'Ana', apellidos: 'Gómez', cargo: 'Analista', estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' },
    ]);
    vi.mocked(empresaService.list).mockResolvedValue([
      { id: 'e1', nit: '900111', razon_social: 'Empresa A', estado: 'ACTIVA', created_at: '2026-01-01T00:00:00Z' },
    ]);
  });

  it('renders the employee list', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
  });

  it('pre-fills the empresa filter from ?empresa_id= query param', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage('/empleados?empresa_id=e1');
    await waitFor(() =>
      expect(empleadoService.list).toHaveBeenCalledWith(
        expect.objectContaining({ empresa_id: 'e1' })
      )
    );
  });

  it('shows "Crear empleado" and "Cargar masivo" for AUDITOR but not LIQUIDADOR', async () => {
    setUser(RolUsuario.AUDITOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /crear empleado/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cargar masivo/i })).toBeInTheDocument();
  });

  it('hides "Crear empleado" and "Cargar masivo" for LIQUIDADOR', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /crear empleado/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cargar masivo/i })).not.toBeInTheDocument();
  });
});
