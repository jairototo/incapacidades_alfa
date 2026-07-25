import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditoresPage } from '../AuditoresPage';
import { auditorService } from '@/services/auditorService';

vi.mock('@/services/auditorService', () => ({
  auditorService: {
    listAll: vi.fn(),
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
    vi.mocked(auditorService.listAll).mockResolvedValue([
      {
        id: 'aud-1', username: 'auditor.cali', email: 'camila.restrepo@segurosalfa-test.com.co',
        nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali',
        incapacidades_asignadas_activas: 3, estado: 'ACTIVO',
      },
    ]);
    vi.mocked(auditorService.reporte).mockResolvedValue([]);
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
});
