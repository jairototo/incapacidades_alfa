import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditoresPage } from '../AuditoresPage';
import { auditorService } from '@/services/auditorService';

vi.mock('@/services/auditorService', () => ({
  auditorService: {
    reporte: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    deactivate: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('AuditoresPage', () => {
  beforeEach(() => {
    vi.mocked(auditorService.reporte).mockResolvedValue([
      {
        id: 'aud-1', username: 'auditor.cali', email: 'camila.restrepo@segurosalfa-test.com.co',
        nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali',
        incapacidades_asignadas_activas: 3, estado: 'ACTIVO',
      },
    ]);
  });

  it('lists auditors with their sucursal and active workload', async () => {
    renderWithClient(<AuditoresPage />);

    await waitFor(() => {
      expect(screen.getByText('Camila Restrepo Vargas')).toBeInTheDocument();
    });
    expect(screen.getByText('Cali')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('opens the create-auditor dialog', async () => {
    renderWithClient(<AuditoresPage />);

    await waitFor(() => screen.getByText('Camila Restrepo Vargas'));
    screen.getByRole('button', { name: /nuevo auditor/i }).click();

    expect(await screen.findByLabelText(/nombre completo/i)).toBeInTheDocument();
  });

  it('asks for confirmation before deactivating an auditor and skips it when cancelled', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderWithClient(<AuditoresPage />);

    await waitFor(() => screen.getByText('Camila Restrepo Vargas'));
    screen.getByRole('button', { name: /desactivar/i }).click();

    expect(confirmSpy).toHaveBeenCalledWith(expect.stringContaining('Camila Restrepo Vargas'));
    expect(auditorService.deactivate).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('deactivates the auditor once the confirmation is accepted', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    vi.mocked(auditorService.deactivate).mockResolvedValue({
      id: 'aud-1', username: 'auditor.cali', email: 'camila.restrepo@segurosalfa-test.com.co',
      nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali',
      incapacidades_asignadas_activas: 3, estado: 'INACTIVO',
    });
    renderWithClient(<AuditoresPage />);

    await waitFor(() => screen.getByText('Camila Restrepo Vargas'));
    screen.getByRole('button', { name: /desactivar/i }).click();

    await waitFor(() => expect(auditorService.deactivate).toHaveBeenCalledWith('aud-1'));

    confirmSpy.mockRestore();
  });

  it('shows an inline error banner when creating an auditor fails', async () => {
    vi.mocked(auditorService.create).mockRejectedValue({
      response: { data: { detail: 'El username ya está en uso' } },
    });
    renderWithClient(<AuditoresPage />);

    await waitFor(() => screen.getByText('Camila Restrepo Vargas'));
    screen.getByRole('button', { name: /nuevo auditor/i }).click();
    await screen.findByLabelText(/nombre completo/i);

    screen.getByRole('button', { name: /guardar/i }).click();

    expect(await screen.findByText('El username ya está en uso')).toBeInTheDocument();
  });
});
