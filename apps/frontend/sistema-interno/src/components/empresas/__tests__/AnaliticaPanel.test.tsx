import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnaliticaPanel } from '../AnaliticaPanel';
import { empresaService } from '@/services/empresaService';

vi.mock('@/services/empresaService');

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AnaliticaPanel />
    </QueryClientProvider>
  );
}

describe('AnaliticaPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shows "No hay datos para mostrar" when both datasets are empty', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
    renderPanel();
    await waitFor(() => expect(screen.getAllByText(/no hay datos/i).length).toBeGreaterThan(0));
  });

  it('renders empresa names from the top_empresas payload', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({
      top_empresas: [{ empresa_id: '1', razon_social: 'Empresa Líder SAS', nit: '900111222', total_radicadas: 42 }],
      tendencia_mensual: [{ periodo: '2026-07', total: 10 }],
    });
    renderPanel();
    await waitFor(() => expect(screen.getByText('Empresa Líder SAS')).toBeInTheDocument());
  });

  it('shows a retry button on error and refetches on click', async () => {
    vi.mocked(empresaService.getAnalitica).mockRejectedValueOnce(new Error('network error'));
    renderPanel();
    await waitFor(() => expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument());

    vi.mocked(empresaService.getAnalitica).mockResolvedValueOnce({ top_empresas: [], tendencia_mensual: [] });
    fireEvent.click(screen.getByRole('button', { name: /reintentar/i }));
    await waitFor(() => expect(empresaService.getAnalitica).toHaveBeenCalledTimes(2));
  });

  it('toggles collapsed state and persists it to localStorage', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
    renderPanel();
    await waitFor(() => expect(screen.getAllByText(/no hay datos/i).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole('button', { name: /analítica de empresas/i }));
    expect(localStorage.getItem('analitica-empresas-collapsed')).toBe('true');
    expect(screen.queryByText(/no hay datos/i)).not.toBeInTheDocument();
  });
});
