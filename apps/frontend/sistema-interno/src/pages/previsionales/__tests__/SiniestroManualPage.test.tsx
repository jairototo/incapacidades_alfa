import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import { SiniestroManualPage } from '../SiniestroManualPage';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional, SiniestroPrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    listarIncapacidadesDelLote: vi.fn(),
    crearSiniestroManual: vi.fn(),
  },
}));

// Mock the Select component so it renders a native <select> in tests,
// avoiding Radix portal/pointer-events issues in jsdom. Same convention as
// `AuditorApprovalTemplateModal.test.tsx`, adapted to read the real
// `SelectItem` children so the dynamic incapacidad options are testable.
vi.mock('@/components/ui/select', () => ({
  Select: ({
    value,
    onValueChange,
    disabled,
    children,
  }: {
    value?: string;
    onValueChange: (v: string) => void;
    disabled?: boolean;
    children: ReactNode;
  }) => (
    <select
      data-testid="incapacidad-select"
      value={value}
      disabled={disabled}
      onChange={(e) => onValueChange(e.target.value)}
    >
      {children}
    </select>
  ),
  SelectTrigger: () => null,
  SelectValue: () => null,
  SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
    <option value={value}>{children}</option>
  ),
}));

function makeIncapacidad(overrides: Partial<IncapacidadPrevisional> = {}): IncapacidadPrevisional {
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
    numero_siniestro: null,
    valor_afp: 100000,
    cie10: null,
    observacion: null,
    observacion_causal: null,
    aval: null,
    motivo_no_aval: null,
    estado: 'SIN_SINIESTRO',
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

const mockSiniestro: SiniestroPrevisional = {
  id: 'sin-001',
  identificacion: '123456789',
  numero_siniestro: 'SIN-999',
  origen: null,
  estado: null,
  fecha_aviso: null,
  fecha_siniestro: null,
  created_at: '2026-07-29T10:00:00Z',
  updated_at: '2026-07-29T10:00:00Z',
};

function renderPage(initialEntry = '/previsionales/siniestros/nuevo') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/previsionales/siniestros/nuevo" element={<SiniestroManualPage />} />
          <Route path="/previsionales/lotes/:loteId" element={<div>Panel del lote</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SiniestroManualPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([]);
  });

  it('renders the form fields', () => {
    renderPage();

    expect(screen.getByLabelText(/identificación/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/número de siniestro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^origen$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^estado$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/fecha de aviso/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/fecha del siniestro/i)).toBeInTheDocument();
    // No lote in context -> no linking selector.
    expect(screen.queryByTestId('incapacidad-select')).not.toBeInTheDocument();
  });

  it('shows a validation error when identificacion is missing and nothing is linked', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/número de siniestro/i), 'SIN-100');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    expect(
      await screen.findByText(/la identificación es obligatoria/i)
    ).toBeInTheDocument();
    expect(previsionalesService.crearSiniestroManual).not.toHaveBeenCalled();
  });

  it('shows a validation error when numero_siniestro is missing', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/identificación/i), '123456789');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    expect(
      await screen.findByText(/el número de siniestro es obligatorio/i)
    ).toBeInTheDocument();
    expect(previsionalesService.crearSiniestroManual).not.toHaveBeenCalled();
  });

  it('submits a fully manual siniestro (no lote/incapacidad link) with the correct body', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.crearSiniestroManual).mockResolvedValue(mockSiniestro);
    renderPage();

    await user.type(screen.getByLabelText(/identificación/i), '123456789');
    await user.type(screen.getByLabelText(/número de siniestro/i), 'SIN-999');
    await user.type(screen.getByLabelText(/^origen$/i), 'COMUN');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    await waitFor(() => {
      expect(previsionalesService.crearSiniestroManual).toHaveBeenCalledWith({
        identificacion: '123456789',
        numero_siniestro: 'SIN-999',
        origen: 'COMUN',
        estado: undefined,
        fecha_aviso: undefined,
        fecha_siniestro: undefined,
        incapacidad_id: undefined,
      });
    });

    expect(await screen.findByText(/siniestro registrado correctamente/i)).toBeInTheDocument();
    expect(screen.getByText('SIN-999')).toBeInTheDocument();
    // No loteId -> no "volver al lote" action.
    expect(screen.queryByRole('button', { name: /volver al lote/i })).not.toBeInTheDocument();
  });

  it('with a loteId in the query string, linking to an incapacidad locks and prefills identificacion', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.listarIncapacidadesDelLote).mockResolvedValue([
      makeIncapacidad({ id: 'inc-a', identificacion: '111111111', radicado: 'RAD-A' }),
    ]);
    vi.mocked(previsionalesService.crearSiniestroManual).mockResolvedValue(mockSiniestro);

    renderPage('/previsionales/siniestros/nuevo?loteId=lote-001');

    const select = await screen.findByTestId('incapacidad-select');
    await waitFor(() => {
      expect(previsionalesService.listarIncapacidadesDelLote).toHaveBeenCalledWith('lote-001');
    });

    await user.selectOptions(select, 'inc-a');

    const identificacionInput = screen.getByLabelText(/identificación/i) as HTMLInputElement;
    expect(identificacionInput.value).toBe('111111111');
    expect(identificacionInput).toBeDisabled();

    await user.type(screen.getByLabelText(/número de siniestro/i), 'SIN-555');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    await waitFor(() => {
      expect(previsionalesService.crearSiniestroManual).toHaveBeenCalledWith({
        identificacion: '111111111',
        numero_siniestro: 'SIN-555',
        origen: undefined,
        estado: undefined,
        fecha_aviso: undefined,
        fecha_siniestro: undefined,
        incapacidad_id: 'inc-a',
      });
    });

    expect(await screen.findByRole('button', { name: /volver al lote/i })).toBeInTheDocument();
  });

  it('shows the specific duplicate message on a 409 response', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.crearSiniestroManual).mockRejectedValue({
      response: { status: 409, data: { detail: "Ya existe un siniestro con numero_siniestro='SIN-999'" } },
    });
    renderPage();

    await user.type(screen.getByLabelText(/identificación/i), '123456789');
    await user.type(screen.getByLabelText(/número de siniestro/i), 'SIN-999');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    expect(await screen.findByText(/ya existe un siniestro con ese número/i)).toBeInTheDocument();
    expect(screen.getByText(/numero_siniestro='SIN-999'/i)).toBeInTheDocument();
  });

  it('shows the backend validation message on a 400 response', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.crearSiniestroManual).mockRejectedValue({
      response: {
        status: 400,
        data: { detail: "identificacion no coincide con la de la incapacidad_id indicada" },
      },
    });
    renderPage();

    await user.type(screen.getByLabelText(/identificación/i), '123456789');
    await user.type(screen.getByLabelText(/número de siniestro/i), 'SIN-999');
    await user.click(screen.getByRole('button', { name: /registrar siniestro/i }));

    expect(await screen.findByText(/datos inválidos/i)).toBeInTheDocument();
    expect(screen.getByText(/identificacion no coincide/i)).toBeInTheDocument();
  });
});
