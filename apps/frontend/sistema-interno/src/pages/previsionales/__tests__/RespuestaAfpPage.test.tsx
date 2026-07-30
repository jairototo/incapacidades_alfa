import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { RespuestaAfpPage } from '../RespuestaAfpPage';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional, LotePrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    obtenerLote: vi.fn(),
    listarIncapacidadesDelLote: vi.fn(),
    descargarRespuesta: vi.fn(),
  },
}));

const mockLote: LotePrevisional = {
  id: 'lote-001',
  nombre_archivo: 'lote_afp.xlsx',
  estado: 'LIQUIDADO',
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
    estado: 'AVALADO',
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

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/previsionales/lotes/lote-001/respuesta']}>
        <Routes>
          <Route path="/previsionales/lotes/:loteId/respuesta" element={<RespuestaAfpPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RespuestaAfpPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previsionalesService.obtenerLote).mockResolvedValue(mockLote);
  });

  it('renders the lot header', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/respuesta afp — lote_afp\.xlsx/i)).toBeInTheDocument();
    expect(screen.getByText('LIQUIDADO')).toBeInTheDocument();
    expect(screen.getByText('ID del lote: lote-001')).toBeInTheDocument();
  });

  it('shows the readiness summary counting only non-duplicate rows', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ id: 'inc-001', aval: 'SI' }),
      makeIncapacidad({ id: 'inc-002', aval: null }),
      // Duplicado interno: excluido tanto del conteo como del excel real.
      makeIncapacidad({ id: 'inc-003', aval: null, es_duplicado_interno: true }),
    ]);

    renderPage();

    expect(await screen.findByText('1 de 2 incapacidades tienen aval registrado.')).toBeInTheDocument();
    expect(
      screen.getByText(/generar la respuesta ahora dejará las columnas/i)
    ).toBeInTheDocument();
  });

  it('does not show the "premature" warning when every row has an aval', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ id: 'inc-001', aval: 'SI' }),
      makeIncapacidad({ id: 'inc-002', aval: 'NO', motivo_no_aval: 'No cumple requisitos' }),
    ]);

    renderPage();

    expect(await screen.findByText('2 de 2 incapacidades tienen aval registrado.')).toBeInTheDocument();
    expect(
      screen.queryByText(/generar la respuesta ahora dejará las columnas/i)
    ).not.toBeInTheDocument();
  });

  it('clicking "Descargar respuesta" calls the service and triggers a browser download with the expected filename', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
    const blob = new Blob(['x'], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    vi.mocked(previsionalesService.descargarRespuesta).mockResolvedValue(blob);

    window.URL.createObjectURL = vi.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = vi.fn();
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    await user.click(screen.getByRole('button', { name: /descargar respuesta/i }));

    await waitFor(() => {
      expect(previsionalesService.descargarRespuesta).toHaveBeenCalledWith('lote-001');
    });
    expect(window.URL.createObjectURL).toHaveBeenCalledWith(blob);
    expect(window.URL.revokeObjectURL).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(await screen.findByText('Respuesta generada')).toBeInTheDocument();

    clickSpy.mockRestore();
  });

  it('disables the download button while the request is in flight', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
    window.URL.createObjectURL = vi.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = vi.fn();

    let resolveDescarga: (blob: Blob) => void;
    vi.mocked(previsionalesService.descargarRespuesta).mockReturnValue(
      new Promise((resolve) => {
        resolveDescarga = resolve;
      })
    );

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    const button = screen.getByRole('button', { name: /descargar respuesta/i });
    await user.click(button);

    expect(button).toBeDisabled();

    resolveDescarga!(new Blob(['x']));
    await waitFor(() => expect(button).not.toBeDisabled());
  });

  it('a 404 (lot or archived file not found) shows a clear, distinct message', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
    vi.mocked(previsionalesService.descargarRespuesta).mockRejectedValue({
      response: { status: 404, data: { detail: 'Lote no encontrado' } },
    });

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    await user.click(screen.getByRole('button', { name: /descargar respuesta/i }));

    expect(await screen.findByText('Lote o archivo original no encontrado')).toBeInTheDocument();
    expect(screen.getByText('Lote no encontrado')).toBeInTheDocument();
  });

  it('a 400 (corrupt archived file) shows a clear, distinct message', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
    vi.mocked(previsionalesService.descargarRespuesta).mockRejectedValue({
      response: { status: 400, data: { detail: 'El archivo archivado no es un excel válido' } },
    });

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    await user.click(screen.getByRole('button', { name: /descargar respuesta/i }));

    expect(
      await screen.findByText('El archivo original archivado no es válido')
    ).toBeInTheDocument();
    expect(screen.getByText('El archivo archivado no es un excel válido')).toBeInTheDocument();
  });

  it('an unexpected error status shows the generic fallback message', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
    vi.mocked(previsionalesService.descargarRespuesta).mockRejectedValue({
      response: { status: 500, data: { detail: 'Error inesperado' } },
    });

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    await user.click(screen.getByRole('button', { name: /descargar respuesta/i }));

    expect(await screen.findByText('No se pudo generar la respuesta')).toBeInTheDocument();
    expect(screen.getByText('Error inesperado')).toBeInTheDocument();
  });

  it('renders navigation links back to the lot and to start a new lot', async () => {
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);

    renderPage();
    await screen.findByText(/respuesta afp — lote_afp\.xlsx/i);

    expect(screen.getByRole('link', { name: /volver al lote/i })).toHaveAttribute(
      'href',
      '/previsionales/lotes/lote-001'
    );
    expect(screen.getByRole('link', { name: /cargar un nuevo lote/i })).toHaveAttribute(
      'href',
      '/previsionales/carga'
    );
  });
});
