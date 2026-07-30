import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { AuditoriaPrevisionalPage } from '../AuditoriaPrevisionalPage';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional, SenalAuditoriaPrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    listarIncapacidadesDelLote: vi.fn(),
    obtenerSenales: vi.fn(),
    patchIncapacidad: vi.fn(),
    registrarAval: vi.fn(),
    duplicarIncapacidad: vi.fn(),
  },
}));

function makeIncapacidad(overrides: Partial<IncapacidadPrevisional> = {}): IncapacidadPrevisional {
  return {
    id: 'inc-b',
    lote_id: 'lote-001',
    tipo_identificacion: 'CC',
    identificacion: '222222222',
    radicado: 'RAD-B',
    radicado_normalizado: 'RAD-B',
    tipo_ingreso: 'INICIAL',
    fecha_inicial: '2026-01-01',
    fecha_final: '2026-01-10',
    dia_181_alfa: null,
    dia_181_afp: '2026-01-15',
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

function makeSenal(overrides: Partial<SenalAuditoriaPrevisional> = {}): SenalAuditoriaPrevisional {
  return {
    id: 'senal-ab',
    incapacidad_previsional_id: 'inc-b',
    codigo: 'AB',
    nombre: 'Dia 181 (auditado)',
    estado: 'OK',
    valor: null,
    detalle: null,
    created_at: '2026-07-29T10:00:00Z',
    updated_at: '2026-07-29T10:00:00Z',
    ...overrides,
  };
}

const mockLote: IncapacidadPrevisional[] = [
  makeIncapacidad({ id: 'inc-dup', es_duplicado_interno: true, identificacion: '000000000' }),
  makeIncapacidad({ id: 'inc-a', identificacion: '111111111', radicado: 'RAD-A' }),
  makeIncapacidad({ id: 'inc-b', identificacion: '222222222', radicado: 'RAD-B' }),
  makeIncapacidad({ id: 'inc-c', identificacion: '333333333', radicado: 'RAD-C' }),
];

function renderPage(initialEntry = '/previsionales/incapacidades/inc-b/auditoria?loteId=lote-001') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route
            path="/previsionales/incapacidades/:incapacidadId/auditoria"
            element={<AuditoriaPrevisionalPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AuditoriaPrevisionalPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue(mockLote);
    vi.mocked(previsionalesService.obtenerSenales).mockResolvedValue([]);
  });

  it('renders the incapacidad data and the señales panel', async () => {
    vi.mocked(previsionalesService.obtenerSenales).mockResolvedValue([
      makeSenal({ id: 's1', codigo: 'AB', estado: 'OK' }),
      makeSenal({ id: 's2', codigo: 'AJ', estado: 'PENDIENTE', nombre: 'CI' }),
      makeSenal({ id: 's3', codigo: 'AD', estado: 'ALERTA', detalle: 'Fila repetida en el lote' }),
    ]);

    renderPage();

    expect(await screen.findByText(/auditoría — 222222222/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith('lote-001');
    });
    await waitFor(() => {
      expect(previsionalesService.obtenerSenales).toHaveBeenCalledWith('inc-b');
    });

    expect(await screen.findByTestId('senales-previsionales-details')).toBeInTheDocument();
    expect(screen.getByTestId('estado-badge-AB')).toHaveTextContent('OK');
    expect(screen.getByTestId('estado-badge-AJ')).toHaveTextContent('PENDIENTE');
    expect(screen.getByTestId('estado-badge-AD')).toHaveTextContent('ALERTA');
    // PENDIENTE must be visually distinct from OK -- different badge classes.
    expect(screen.getByTestId('estado-badge-AB').className).not.toBe(
      screen.getByTestId('estado-badge-AJ').className
    );
  });

  it('shows the "not yet audited" message when señales is an empty array', async () => {
    vi.mocked(previsionalesService.obtenerSenales).mockResolvedValue([]);
    renderPage();

    expect(await screen.findByTestId('senales-vacio')).toHaveTextContent(/aún no ha sido auditado/i);
  });

  it('shows an explanatory message and does not fetch anything when loteId is missing', async () => {
    renderPage('/previsionales/incapacidades/inc-b/auditoria');

    expect(await screen.findByText(/falta el contexto del lote/i)).toBeInTheDocument();
    expect(previsionalesService.listarIncapacidadesDelLote).not.toHaveBeenCalled();
    expect(previsionalesService.obtenerSenales).not.toHaveBeenCalled();
  });

  it('saves dia_181_alfa via PATCH with the entered value', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.patchIncapacidad).mockResolvedValue(
      makeIncapacidad({ dia_181_alfa: '2026-02-01' })
    );
    renderPage();

    await screen.findByText(/auditoría — 222222222/i);

    const input = screen.getByLabelText('dia_181_alfa') as HTMLInputElement;
    await user.type(input, '2026-02-01');
    await user.click(screen.getByRole('button', { name: /guardar/i }));

    await waitFor(() => {
      expect(previsionalesService.patchIncapacidad).toHaveBeenCalledWith('inc-b', {
        dia_181_alfa: '2026-02-01',
      });
    });
    expect(await screen.findByTestId('alfa-guardado')).toBeInTheDocument();
  });

  it('"No avalar" requires a motivo before submitting', async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(/auditoría — 222222222/i);

    await user.click(screen.getByTestId('btn-no-avalar'));
    await user.click(screen.getByRole('button', { name: /confirmar no aval/i }));

    expect(await screen.findByText(/el motivo es obligatorio/i)).toBeInTheDocument();
    expect(previsionalesService.registrarAval).not.toHaveBeenCalled();
  });

  it('registers aval SI directly on "Avalar"', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.registrarAval).mockResolvedValue(
      makeIncapacidad({ aval: 'SI' })
    );
    renderPage();
    await screen.findByText(/auditoría — 222222222/i);

    await user.click(screen.getByTestId('btn-avalar'));

    await waitFor(() => {
      expect(previsionalesService.registrarAval).toHaveBeenCalledWith('inc-b', { aval: 'SI' });
    });
    expect(await screen.findByTestId('aval-badge-si')).toHaveTextContent('AVALADO');
  });

  it('registers aval NO with the typed motivo', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.registrarAval).mockResolvedValue(
      makeIncapacidad({ aval: 'NO', motivo_no_aval: 'Fechas inconsistentes con ARPIS' })
    );
    renderPage();
    await screen.findByText(/auditoría — 222222222/i);

    await user.click(screen.getByTestId('btn-no-avalar'));
    await user.type(screen.getByLabelText(/motivo/i), 'Fechas inconsistentes con ARPIS');
    await user.click(screen.getByRole('button', { name: /confirmar no aval/i }));

    await waitFor(() => {
      expect(previsionalesService.registrarAval).toHaveBeenCalledWith('inc-b', {
        aval: 'NO',
        motivo: 'Fechas inconsistentes con ARPIS',
      });
    });
    expect(await screen.findByTestId('aval-badge-no')).toHaveTextContent('NO AVALADO');
    expect(screen.getByText(/fechas inconsistentes con arpis/i)).toBeInTheDocument();
  });

  it('shows a graceful message when the backend rejects aval past the audit stage', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.registrarAval).mockRejectedValue({
      response: { status: 400, data: { detail: 'La incapacidad ya fue liquidada' } },
    });
    renderPage();
    await screen.findByText(/auditoría — 222222222/i);

    await user.click(screen.getByTestId('btn-avalar'));

    expect(await screen.findByText(/no se pudo registrar el aval/i)).toBeInTheDocument();
    expect(screen.getByText(/la incapacidad ya fue liquidada/i)).toBeInTheDocument();
  });

  it('opens the Duplicar dialog and submits with the entered dates', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.duplicarIncapacidad).mockResolvedValue(
      makeIncapacidad({ id: 'inc-b-dup', es_duplicado_interno: true, incapacidad_origen_id: 'inc-b' })
    );
    renderPage();
    await screen.findByText(/auditoría — 222222222/i);

    await user.click(screen.getByTestId('btn-duplicar'));

    const fechaInicial = await screen.findByLabelText(/fecha inicial/i);
    const fechaFinal = screen.getByLabelText(/fecha final/i);
    await user.type(fechaInicial, '2026-03-01');
    await user.type(fechaFinal, '2026-03-10');
    await user.click(screen.getByRole('button', { name: /^duplicar$/i }));

    await waitFor(() => {
      expect(previsionalesService.duplicarIncapacidad).toHaveBeenCalledWith('inc-b', {
        fecha_inicial: '2026-03-01',
        fecha_final: '2026-03-10',
      });
    });
    expect(await screen.findByTestId('duplicar-confirmacion')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ir al duplicado/i })).toBeInTheDocument();
  });

  it('shows prev/next navigation when loteId is present and skips es_duplicado_interno rows', async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByTestId('nav-posicion')).toHaveTextContent('Registro 2 de 3');
    expect(screen.getByTestId('btn-anterior')).not.toBeDisabled();
    expect(screen.getByTestId('btn-siguiente')).not.toBeDisabled();

    await user.click(screen.getByTestId('btn-siguiente'));

    expect(await screen.findByText(/auditoría — 333333333/i)).toBeInTheDocument();
    expect(await screen.findByTestId('nav-posicion')).toHaveTextContent('Registro 3 de 3');
    // Last non-duplicate record -> no "Siguiente".
    expect(screen.getByTestId('btn-siguiente')).toBeDisabled();

    await user.click(screen.getByTestId('btn-anterior'));
    expect(await screen.findByText(/auditoría — 222222222/i)).toBeInTheDocument();

    await user.click(screen.getByTestId('btn-anterior'));
    expect(await screen.findByText(/auditoría — 111111111/i)).toBeInTheDocument();
    expect(await screen.findByTestId('nav-posicion')).toHaveTextContent('Registro 1 de 3');
    // First record -> no "Anterior". The internal duplicate (inc-dup) is
    // excluded from the sequence entirely.
    expect(screen.getByTestId('btn-anterior')).toBeDisabled();
  });
});
