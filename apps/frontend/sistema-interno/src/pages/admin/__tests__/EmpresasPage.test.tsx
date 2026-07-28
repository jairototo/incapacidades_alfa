import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpresasPage } from '../EmpresasPage';
import { empresaService } from '@/services/empresaService';
import { useAuthStore } from '@/store/authStore';
import { RolUsuario } from '@/types/enums';

vi.mock('@/services/empresaService');

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <EmpresasPage />
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

describe('EmpresasPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(empresaService.list).mockResolvedValue([
      { id: '1', nit: '900123456', razon_social: 'Empresa Uno', estado: 'ACTIVA', ciudad: 'Bogotá', created_at: '2026-01-01T00:00:00Z' },
    ]);
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
  });

  it('renders the list of empresas', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
  });

  it('shows "Crear empresa" for ADMIN but not for AUDITOR/LIQUIDADOR', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /crear empresa/i })).toBeInTheDocument();
  });

  it('does not show "Crear empresa" for AUDITOR', async () => {
    setUser(RolUsuario.AUDITOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /crear empresa/i })).not.toBeInTheDocument();
  });

  it('filters by NIT and re-fetches', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/buscar por nit/i), { target: { value: '900123456' } });
    fireEvent.click(screen.getByRole('button', { name: /buscar/i }));

    await waitFor(() =>
      expect(empresaService.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ nit: '900123456' })
      )
    );
  });

  it('creating an empresa shows the password reveal dialog with the generated credentials', async () => {
    setUser(RolUsuario.ADMIN);
    vi.mocked(empresaService.create).mockResolvedValue({
      id: '2', nit: '900555555', razon_social: 'Nueva SAS', estado: 'ACTIVA',
      email_contacto: 'nueva@empresa.com', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
      usuario_generado: { username: '900555555', password: 'GenPass123x' },
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^crear empresa$/i }));
    fireEvent.change(screen.getByLabelText(/^nit$/i), { target: { value: '900555555' } });
    fireEvent.change(screen.getByLabelText(/razón social/i), { target: { value: 'Nueva SAS' } });
    fireEvent.change(screen.getByLabelText(/correo/i), { target: { value: 'nueva@empresa.com' } });
    fireEvent.click(screen.getByRole('button', { name: /^guardar$/i }));

    await waitFor(() => expect(screen.getByText('GenPass123x')).toBeInTheDocument());
  });
});
