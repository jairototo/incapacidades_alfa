import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { LiquidacionPrevisionalPage } from '../LiquidacionPrevisionalPage';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional, LotePrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    obtenerLote: vi.fn(),
    listarIncapacidadesDelLote: vi.fn(),
    liquidarLote: vi.fn(),
  },
}));

const mockLote: LotePrevisional = {
  id: 'lote-001',
  nombre_archivo: 'lote_afp.xlsx',
  estado: 'CARGADO',
  fecha_cargue: '2026-07-29T10:00:00Z',
  cargado_por_id: 'user-001',
  total_filas: 2,
  total_incapacidades: 2,
  observaciones: null,
  created_at: '2026-07-29T10:00:00Z',
  updated_at: '2026-07-29T10:00:00Z',
};

function makeIncapacidad(
  overrides: Partial<IncapacidadPrevisional> = {}
): IncapacidadPrevisional {
  return {
    id: 'inc-001',
    lote_id: 'lote-001',
    tipo_identificacion: 'CC',
    identificacion: '123456789',
    radicado: 'RAD-001',
    radicado_normalizado: 'RAD-001',
    tipo_ingreso: 'INICIAL',
    fecha_inicial: '2026-01-01',
    fecha_final: '2026-01-10',
    dia_181_alfa: null,
    dia_181_afp: null,
    dia_181_arpis: null,
    fecha_crie: null,
    fecha_radicacion_afp: null,
    fecha_radicacion_alfa: null,
    numero_siniestro: 'SIN-001',
    valor_afp: 100000,
    cie10: null,
    observacion: null,
    observacion_causal: null,
    aval: null,
    motivo_no_aval: null,
    estado: 'CON_SINIESTRO',
    prorroga_de_id: null,
    incapacidad_origen_id: null,
    es_duplicado_interno: false,
    valor_auditado: null,
    diferencia_valor_afp: null,
    errores_carga: null,
    created_at: '2026-07-29T10:00:00Z',
    updated_at: '2026-07-29T10:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/previsionales/lotes/lote-001/liquidacion']}>
        <Routes>
          <Route
            path="/previsionales/lotes/:loteId/liquidacion"
            element={<LiquidacionPrevisionalPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LiquidacionPrevisionalPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previsionalesService.obtenerLote).mockResolvedValue(mockLote);
  });

  it('renders the lot header and the incapacidades table', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ id: 'inc-001', identificacion: '123456789', radicado: 'RAD-001' }),
    ]);

    renderPage();

    expect(await screen.findByText(/liquidación — lote_afp\.xlsx/i)).toBeInTheDocument();
    expect(screen.getByText('CARGADO')).toBeInTheDocument();
    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith('lote-001');
    });
    expect(await screen.findByText('123456789')).toBeInTheDocument();
    expect(screen.getByText('RAD-001')).toBeInTheDocument();
  });

  it('shows "Pendiente de liquidar" instead of raw null before the first liquidar call', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ valor_auditado: null, diferencia_valor_afp: null }),
    ]);

    renderPage();

    const pendientes = await screen.findAllByText('Pendiente de liquidar');
    // Una ocurrencia para valor_auditado, otra para diferencia_valor_afp.
    expect(pendientes.length).toBe(2);
    expect(screen.queryByText('null')).not.toBeInTheDocument();
    expect(screen.queryByText('NaN')).not.toBeInTheDocument();
  });

  it('clicking "Liquidar lote" calls the service, shows the returned count, and refetches the table', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote)
      .mockResolvedValueOnce([
        makeIncapacidad({ valor_auditado: null, diferencia_valor_afp: null }),
      ])
      .mockResolvedValueOnce([
        makeIncapacidad({ valor_auditado: 95000, diferencia_valor_afp: -5000 }),
      ]);
    vi.mocked(previsionalesService.liquidarLote).mockResolvedValue({ liquidadas: 1 });

    renderPage();
    await screen.findAllByText('Pendiente de liquidar');

    await user.click(screen.getByRole('button', { name: /liquidar lote/i }));

    expect(await screen.findByText(/se liquidaron 1 incapacidades/i)).toBeInTheDocument();
    expect(previsionalesService.liquidarLote).toHaveBeenCalledWith('lote-001');
    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText('$ 95.000')).toBeInTheDocument();
  });

  it('highlights the diferencia_valor_afp row/cell in blue when nonzero, matching Task 5.3', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ id: 'inc-dif', valor_auditado: 95000, diferencia_valor_afp: -5000 }),
    ]);

    renderPage();

    const difCell = await screen.findByText('-$ 5.000');
    const row = (await screen.findByText('123456789')).closest('tr');
    expect(row).toHaveClass('bg-blue-50');
    expect(difCell).toHaveClass('text-blue-700');
  });

  it('a liquidar failure shows a clear error message', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ valor_auditado: null, diferencia_valor_afp: null }),
    ]);
    vi.mocked(previsionalesService.liquidarLote).mockRejectedValue({
      response: { status: 500, data: { detail: 'Error inesperado al liquidar' } },
    });

    renderPage();
    await screen.findAllByText('Pendiente de liquidar');

    await user.click(screen.getByRole('button', { name: /liquidar lote/i }));

    expect(await screen.findByText('Error inesperado al liquidar')).toBeInTheDocument();
  });

  it('shows a note explaining the per-segment breakdown is not available', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);

    renderPage();

    expect(
      await screen.findByText(/desglose por segmento no disponible/i)
    ).toBeInTheDocument();
  });
});
