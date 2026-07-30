import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { RadicacionLotePage } from '../RadicacionLotePage';
import { previsionalesService } from '@/services/previsionales';
import api from '@/lib/api';
import type { IncapacidadPrevisional, LotePrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    obtenerLote: vi.fn(),
    listarIncapacidadesDelLote: vi.fn(),
    exportarArpis: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  default: { post: vi.fn() },
}));

const mockLote: LotePrevisional = {
  id: 'lote-001',
  nombre_archivo: 'lote_afp.xlsx',
  estado: 'CARGADO',
  fecha_cargue: '2026-07-29T10:00:00Z',
  cargado_por_id: 'user-001',
  total_filas: 3,
  total_incapacidades: 3,
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
    valor_auditado: 100000,
    diferencia_valor_afp: 0,
    errores_carga: null,
    created_at: '2026-07-29T10:00:00Z',
    updated_at: '2026-07-29T10:00:00Z',
    ...overrides,
  };
}

const mockIncapacidades: IncapacidadPrevisional[] = [
  makeIncapacidad({ id: 'inc-sin-siniestro', numero_siniestro: null }),
  makeIncapacidad({ id: 'inc-con-errores', errores_carga: { fila: 5, mensaje: 'Fecha inválida' } }),
];

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/previsionales/lotes/lote-001']}>
        <Routes>
          <Route path="/previsionales/lotes/:loteId" element={<RadicacionLotePage />} />
          <Route path="/previsionales/siniestros/nuevo" element={<div>Registrar Siniestro</div>} />
          <Route
            path="/previsionales/incapacidades/:incapacidadId/auditoria"
            element={<div>Auditoría de Incapacidad</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RadicacionLotePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previsionalesService.obtenerLote).mockResolvedValue(mockLote);
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue(
      mockIncapacidades
    );
  });

  it('renders the lot header and the incapacidades table', async () => {
    renderPage();

    expect(await screen.findByText('lote_afp.xlsx')).toBeInTheDocument();
    expect(screen.getByText('CARGADO')).toBeInTheDocument();
    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith(
        'lote-001',
        {}
      );
    });
    expect(await screen.findByText('2 incapacidades')).toBeInTheDocument();
    expect(screen.getAllByText('123456789').length).toBeGreaterThan(0);
  });

  it('highlights sin_siniestro rows amber and error rows red', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText('123456789').length).toBe(2);
    });

    // "Sin siniestro" text also appears in the legend and the filter label,
    // so pick the occurrence that lives inside a table row.
    const sinSiniestroRow = screen
      .getAllByText('Sin siniestro')
      .map((el) => el.closest('tr'))
      .find((tr): tr is HTMLTableRowElement => tr !== null);
    expect(sinSiniestroRow).toHaveClass('bg-amber-50');

    const errorRow = screen.getByText('Error').closest('tr');
    expect(errorRow).toHaveClass('bg-red-50');
  });

  it('toggling a filter checkbox refetches with the right filtros', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith(
        'lote-001',
        {}
      );
    });

    const filterLabel = screen
      .getAllByText('Sin siniestro')
      .map((el) => el.closest('label'))
      .find((label): label is HTMLLabelElement => label !== null);
    await user.click(filterLabel!);

    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith('lote-001', {
        sin_siniestro: true,
      });
    });
  });

  it('exports ARPIS and triggers a browser download', async () => {
    const user = userEvent.setup();
    const blob = new Blob(['x'], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    vi.mocked(previsionalesService.exportarArpis).mockResolvedValue(blob);
    window.URL.createObjectURL = vi.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = vi.fn();

    renderPage();
    await screen.findByText('lote_afp.xlsx');

    await user.click(screen.getByRole('button', { name: /exportar arpis/i }));

    await waitFor(() => {
      expect(previsionalesService.exportarArpis).toHaveBeenCalledWith('lote-001');
    });
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(blob);
    expect(window.URL.revokeObjectURL).toHaveBeenCalled();
  });

  it('"Actualizar lote" shows a graceful message on the documented 501 stub', async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockRejectedValue({
      response: { status: 501, data: { detail: 'Re-cruce de siniestros no implementado' } },
    });

    renderPage();
    await screen.findByText('lote_afp.xlsx');

    await user.click(screen.getByRole('button', { name: /actualizar lote/i }));

    expect(
      await screen.findByText(/esta función aún no está disponible/i)
    ).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/previsionales/lotes/lote-001/actualizar');
  });

  it('"Crear Siniestros" navigates to the manual siniestro registration route', async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('lote_afp.xlsx');

    await user.click(screen.getByRole('button', { name: /crear siniestros/i }));

    expect(await screen.findByText('Registrar Siniestro')).toBeInTheDocument();
  });

  it('the "Auditar" link on a row navigates to the audit screen with loteId in the query', async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('lote_afp.xlsx');

    const auditarLinks = await screen.findAllByRole('link', { name: /auditar/i });
    expect(auditarLinks.length).toBe(mockIncapacidades.length);
    expect(auditarLinks[0]).toHaveAttribute(
      'href',
      `/previsionales/incapacidades/${mockIncapacidades[0].id}/auditoria?loteId=${mockIncapacidades[0].lote_id}`
    );

    await user.click(auditarLinks[0]);

    expect(await screen.findByText('Auditoría de Incapacidad')).toBeInTheDocument();
  });
});
