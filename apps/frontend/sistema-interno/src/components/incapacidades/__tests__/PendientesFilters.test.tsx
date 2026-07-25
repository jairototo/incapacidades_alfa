import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PendientesFilters } from '../PendientesFilters';
import { auditorService } from '@/services/auditorService';

vi.mock('@/services/auditorService', () => ({
  auditorService: { listActivos: vi.fn() },
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('PendientesFilters — auditor asignado', () => {
  beforeEach(() => {
    vi.mocked(auditorService.listActivos).mockResolvedValue([
      { id: 'aud-1', username: 'auditor.cali', email: 'camila.restrepo@segurosalfa-test.com.co', nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali', incapacidades_asignadas_activas: 2, estado: 'ACTIVO' },
    ]);
  });

  it('renders an auditor filter populated from auditorService', async () => {
    renderWithClient(<PendientesFilters onSearch={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/auditor asignado/i)).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/auditor asignado/i));
    expect(await screen.findByText('Camila Restrepo Vargas')).toBeInTheDocument();
  });
});
