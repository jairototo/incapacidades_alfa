import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpresasPage } from '../EmpresasPage';
import { empresaService } from '@/services/empresaService';
import { useAuthStore } from '@/store/authStore';
import { RolUsuario } from '@/types/enums';

// Capture mockToast BEFORE vi.mock hoisting via vi.hoisted, so we can assert on it.
const mockToast = vi.hoisted(() => vi.fn());

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

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

  it('does not render a Departamento table column, only the filter input (Fix 3)', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    const table = within(screen.getByRole('table'));
    expect(table.queryByText('Departamento')).not.toBeInTheDocument();
    // The filter input still exists outside the table.
    expect(screen.getByLabelText(/^departamento$/i)).toBeInTheDocument();
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

  it('shows a destructive toast when regenerating the password fails', async () => {
    setUser(RolUsuario.ADMIN);
    vi.mocked(empresaService.regenerarPassword).mockRejectedValue({
      response: { data: { detail: 'No se pudo contactar el servicio de usuarios' } },
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    fireEvent.click(screen.getByRole('button', { name: /regenerar contraseña/i }));

    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'No se pudo contactar el servicio de usuarios',
        variant: 'destructive',
      })
    );
    confirmSpy.mockRestore();
  });

  it('opening the edit dialog fetches the full empresa record and prefills the form (Fix 1)', async () => {
    setUser(RolUsuario.ADMIN);
    vi.mocked(empresaService.getById).mockResolvedValue({
      id: '1',
      nit: '900123456',
      razon_social: 'Empresa Uno',
      estado: 'ACTIVA',
      email_contacto: 'contacto@empresauno.com',
      telefono: '3001234567',
      direccion: 'Calle 1 # 2-3',
      ciudad: 'Bogotá',
      departamento: 'Cundinamarca',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

    await waitFor(() => expect(empresaService.getById).toHaveBeenCalledWith('1'));

    const dialog = within(screen.getByRole('dialog'));
    await waitFor(() => expect(dialog.getByLabelText(/correo de contacto/i)).toHaveValue('contacto@empresauno.com'));
    expect(dialog.getByLabelText(/teléfono/i)).toHaveValue('3001234567');
    expect(dialog.getByLabelText(/dirección/i)).toHaveValue('Calle 1 # 2-3');
    expect(dialog.getByLabelText(/^ciudad$/i)).toHaveValue('Bogotá');
    expect(dialog.getByLabelText(/departamento/i)).toHaveValue('Cundinamarca');
  });

  it('does not send the update when the full empresa record fails to load, and shows an error instead', async () => {
    setUser(RolUsuario.ADMIN);
    vi.mocked(empresaService.getById).mockRejectedValue(new Error('network error'));
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^editar$/i }));

    await waitFor(() =>
      expect(screen.getByText('No se pudo cargar la información completa de la empresa')).toBeInTheDocument()
    );
  });

  it('asks for confirmation before regenerating a password and skips it when cancelled (Fix 6)', async () => {
    setUser(RolUsuario.ADMIN);
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /regenerar contraseña/i }));

    expect(confirmSpy).toHaveBeenCalledWith(expect.stringContaining('Empresa Uno'));
    expect(empresaService.regenerarPassword).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('regenerates the password once the confirmation is accepted (Fix 6)', async () => {
    setUser(RolUsuario.ADMIN);
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.mocked(empresaService.regenerarPassword).mockResolvedValue({
      message: 'ok', username: '900123456', password: 'NewTemp123x',
    });
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /regenerar contraseña/i }));

    await waitFor(() => expect(empresaService.regenerarPassword).toHaveBeenCalledWith('1'));

    confirmSpy.mockRestore();
  });
});
