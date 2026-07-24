import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { LiquidacionPage } from '../LiquidacionPage';
import { incapacidadService } from '@/services/incapacidadService';
import { liquidacionService } from '@/services/liquidacion';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getById: vi.fn(),
    getHistorial: vi.fn(),
  },
}));

vi.mock('@/services/liquidacion', async (importOriginal) => {
  const actual = await importOriginal() as typeof import('@/services/liquidacion');
  return {
    ...actual, // preserves mapLiquidacionToBreakdown and other pure helpers
    liquidacionService: {
      getLiquidacion: vi.fn(),
      guardarLiquidacion: vi.fn(),
      calcularBreakdown: vi.fn(),
      devolverAuditoria: vi.fn(),
      completarLiquidacion: vi.fn(),
    },
  };
});

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mockIncapacidadLiquidacion = {
  id: 'inc-liq-001',
  numero: 'INC-LIQ-20260101-0001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.LIQUIDACION,
  fecha_inicio: '2026-01-01',
  fecha_fin: '2026-01-10',
  dias_totales: 10,
  diagnostico_cie10: 'M545',
  diagnostico_descripcion: 'Lumbago no especificado',
  valor_total: 1000000,
  prioridad: 'NORMAL',
  empleado: {
    id: 'emp-001',
    nombres: 'Juan',
    apellidos: 'Pérez',
    numero_documento: '1234567890',
    tipo_documento: 'CC',
    empresa_id: 'empresa-001',
  },
  empresa: {
    id: 'empresa-001',
    nit: '900123456',
    razon_social: 'Empresa Test SAS',
    email_contacto: 'test@test.com',
  },
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-01T10:00:00Z',
};

const mockLiquidacionExistente = {
  id: 'liq-001',
  incapacidad_id: 'inc-liq-001',
  ibl: 2500000,
  periodo_ibl_inicio: null,
  periodo_ibl_fin: null,
  dias_autorizados: 10,
  fecha_inicio_autorizada: '2026-01-01',
  fecha_fin_autorizada: '2026-01-10',
  valor_incapacidad_temporal: null,
  valor_aporte_patronal_pension: null,
  valor_aporte_trabajador_pension: null,
  valor_aporte_adicional_trabajador_pension: null,
  valor_aporte_patronal_salud: null,
  valor_aporte_trabajador_salud: null,
  valor_total: null,
  metodo_pago: null,
  notas_liquidador: null,
  liquidador_id: null,
};

const mockLiquidacionConDesglose = {
  id: 'liq-002',
  incapacidad_id: 'inc-liq-001',
  ibl: 3500000,
  periodo_ibl_inicio: null,
  periodo_ibl_fin: null,
  dias_autorizados: 10,
  fecha_inicio_autorizada: '2026-01-01',
  fecha_fin_autorizada: '2026-01-10',
  valor_incapacidad_temporal: 35000000,
  valor_aporte_patronal_pension: 4200000,
  valor_aporte_trabajador_pension: 1400000,
  valor_aporte_adicional_trabajador_pension: null,
  valor_aporte_patronal_salud: 2975000,
  valor_aporte_trabajador_salud: 1400000,
  valor_total: 44975000,
  metodo_pago: null,
  notas_liquidador: null,
  liquidador_id: null,
};

const mockBreakdownResponse = {
  ibl: 2500000,
  dias: 10,
  incapacidad_temporal: null,
  aporte_patronal_pension: null,
  aporte_trabajador_pension: null,
  aporte_adicional_trabajador_pension: null,
  aporte_patronal_salud: null,
  aporte_trabajador_salud: null,
  valor_total: null,
  nota: 'Fórmulas pendientes de confirmación con el cliente (C1).',
};

// ---------------------------------------------------------------------------
// Render helper
// ---------------------------------------------------------------------------

function renderPage(incapacidadId = 'inc-liq-001') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        initialEntries={[`/incapacidades/${incapacidadId}/liquidacion`]}
      >
        <Routes>
          <Route
            path="/incapacidades/:id/liquidacion"
            element={<LiquidacionPage />}
          />
          <Route
            path="/incapacidades/pendientes"
            element={<div>Pendientes page</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('LiquidacionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(liquidacionService.getLiquidacion).mockRejectedValue({ response: { status: 404 } });
  });

  // --- Loading state ---
  it('shows loading state while fetching incapacidad', () => {
    vi.mocked(incapacidadService.getById).mockImplementation(
      () => new Promise(() => { /* never resolves */ })
    );
    renderPage();
    expect(screen.getByText(/Cargando incapacidad/i)).toBeInTheDocument();
  });

  // --- Error state ---
  it('shows error state when incapacidad cannot be loaded', async () => {
    vi.mocked(incapacidadService.getById).mockRejectedValue(
      new Error('Network error')
    );
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Incapacidad no encontrada/i)).toBeInTheDocument();
    });
  });

  // --- Wrong state guard ---
  it('shows estado inválido message when incapacidad is not in LIQUIDACION state', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue({
      ...mockIncapacidadLiquidacion,
      estado: EstadoIncapacidad.EN_AUDITORIA,
    } as any);
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/Estado no válido para liquidación/i)
      ).toBeInTheDocument();
    });
  });

  // --- Page renders for LIQUIDACION state ---
  it('renders page with incapacidad context for LIQUIDACION state', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText('INC-LIQ-20260101-0001')
      ).toBeInTheDocument();
    });

    // Context strip
    expect(screen.getByText(/Juan Pérez/)).toBeInTheDocument();
    expect(screen.getByText(/Empresa Test SAS/)).toBeInTheDocument();
    expect(screen.getByText('M545')).toBeInTheDocument();
  });

  // --- Page renders for LIQUIDACION_PARCIAL state ---
  it('renders page for LIQUIDACION_PARCIAL state', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue({
      ...mockIncapacidadLiquidacion,
      estado: EstadoIncapacidad.LIQUIDACION_PARCIAL,
    } as any);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('LIQUIDACION_PARCIAL')).toBeInTheDocument();
    });
  });

  // --- IBL field is required ---
  it('shows IBL required error when trying to save without IBL value', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('ibl-input')).toBeInTheDocument();
    });

    // Submit without filling IBL
    const saveBtn = screen.getByRole('button', { name: /Guardar borrador/i });
    await user.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText(/El IBL es obligatorio/i)).toBeInTheDocument();
    });
  });

  // --- Breakdown table renders ---
  it('renders breakdown table with "Pendiente de configuración" rows', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('breakdown-table')).toBeInTheDocument();
    });

    // All 6 rows should show "Pendiente de configuración" before calculation
    const pendingCells = screen.getAllByText('Pendiente de configuración');
    // 6 rows + Total = 7 cells
    expect(pendingCells.length).toBeGreaterThanOrEqual(6);
  });

  // --- Calcular breakdown button ---
  it('calls calcularBreakdown when "Calcular desglose" is clicked', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.calcularBreakdown).mockResolvedValue(
      mockBreakdownResponse
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('ibl-input')).toBeInTheDocument();
    });

    // Enter IBL value via fireEvent for reliable value-setting
    fireEvent.change(screen.getByTestId('ibl-input'), {
      target: { value: '2500000' },
    });

    // Click calcular
    await user.click(screen.getByTestId('calcular-breakdown-btn'));

    await waitFor(() => {
      expect(liquidacionService.calcularBreakdown).toHaveBeenCalledWith(
        'inc-liq-001',
        2500000,
        10
      );
    });

    // The nota from backend should appear
    await waitFor(() => {
      expect(
        screen.getByText(/Fórmulas pendientes de confirmación/i)
      ).toBeInTheDocument();
    });
  });

  // --- Save liquidacion ---
  it('calls guardarLiquidacion with correct payload on save', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.guardarLiquidacion).mockResolvedValue(
      mockLiquidacionExistente
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('ibl-input')).toBeInTheDocument();
    });

    // Use fireEvent.change for reliable value setting in jsdom
    fireEvent.change(screen.getByTestId('ibl-input'), {
      target: { value: '2500000' },
    });

    await user.click(screen.getByTestId('guardar-borrador-btn'));

    await waitFor(() => {
      expect(liquidacionService.guardarLiquidacion).toHaveBeenCalledWith(
        'inc-liq-001',
        expect.objectContaining({
          ibl: 2500000,
          dias_autorizados: 10,
          fecha_inicio_autorizada: '2026-01-01',
          fecha_fin_autorizada: '2026-01-10',
        })
      );
    });
  });

  // --- Completar liquidacion ---
  it('calls completarLiquidacion when "Completar liquidación" is clicked', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.completarLiquidacion).mockResolvedValue(
      undefined
    );
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByTestId('completar-liquidacion-btn')
      ).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('completar-liquidacion-btn'));

    await waitFor(() => {
      expect(liquidacionService.completarLiquidacion).toHaveBeenCalledWith(
        'inc-liq-001'
      );
    });
  });

  // --- Devolver dialog opens ---
  it('opens devolucion dialog when "Devolver a auditoría" button is clicked', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByTestId('devolver-auditoria-btn')
      ).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('devolver-auditoria-btn'));

    await waitFor(() => {
      // Dialog title should appear
      expect(
        screen.getAllByText(/Devolver a auditoría/i).length
      ).toBeGreaterThan(1); // button + dialog title
      // Observacion textarea should be present (find by placeholder)
      expect(
        screen.getByPlaceholderText(/Describe el motivo de la devolución/i)
      ).toBeInTheDocument();
    });
  });

  // --- Devolver dialog: observacion required ---
  it('shows observacion required error in devolucion dialog when empty', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('devolver-auditoria-btn')).toBeInTheDocument();
    });

    // Open dialog
    await user.click(screen.getByTestId('devolver-auditoria-btn'));

    await waitFor(() => {
      expect(
        screen.getByTestId('confirmar-devolucion-btn')
      ).toBeInTheDocument();
    });

    // Submit without filling observacion
    await user.click(screen.getByTestId('confirmar-devolucion-btn'));

    await waitFor(() => {
      expect(
        screen.getByTestId('devolucion-error')
      ).toBeInTheDocument();
      expect(
        screen.getByText(/La observación es obligatoria/i)
      ).toBeInTheDocument();
    });
  });

  // --- Devolver calls service with observacion ---
  it('calls devolverAuditoria with observacion when dialog submitted', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.devolverAuditoria).mockResolvedValue(undefined);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('devolver-auditoria-btn')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('devolver-auditoria-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('confirmar-devolucion-btn')).toBeInTheDocument();
    });

    // Find the observacion textarea by its placeholder
    const textarea = screen.getByPlaceholderText(
      /Describe el motivo de la devolución/i
    );
    await user.type(textarea, 'Error en los días aprobados');

    await user.click(screen.getByTestId('confirmar-devolucion-btn'));

    await waitFor(() => {
      expect(liquidacionService.devolverAuditoria).toHaveBeenCalledWith(
        'inc-liq-001',
        'Error en los días aprobados'
      );
    });
  });

  // --- Hydration: breakdown populated from saved liquidacion ---
  it('shows saved breakdown values on mount without clicking "Calcular desglose"', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.getLiquidacion).mockResolvedValue(
      mockLiquidacionConDesglose
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('breakdown-table')).toBeInTheDocument();
    });

    // With a saved breakdown, fewer than 7 cells should say "Pendiente"
    // (only the null adicional_trabajador field renders as "Pendiente")
    await waitFor(() => {
      const pendingCells = screen.queryAllByText('Pendiente de configuración');
      expect(pendingCells.length).toBeLessThan(7);
    });

    // nota from the mapped breakdown should appear
    expect(
      screen.getByText(/Desglose de la liquidación guardada/i)
    ).toBeInTheDocument();
  });

  // --- Hydration: borrador sin cálculo (valor_total null) keeps "Pendiente" ---
  it('still shows "Pendiente de configuración" for all rows when saved liquidacion has no breakdown', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.getLiquidacion).mockResolvedValue(
      mockLiquidacionExistente // valor_total: null
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('breakdown-table')).toBeInTheDocument();
    });

    await waitFor(() => {
      const pendingCells = screen.queryAllByText('Pendiente de configuración');
      expect(pendingCells.length).toBeGreaterThanOrEqual(6);
    });
  });

  // --- User recalculation takes priority over saved values ---
  it('shows recalculated breakdown (from "Calcular desglose") over saved values', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.getLiquidacion).mockResolvedValue(
      mockLiquidacionConDesglose
    );
    const freshBreakdown = {
      ...mockBreakdownResponse,
      nota: 'Desglose recién calculado',
    };
    vi.mocked(liquidacionService.calcularBreakdown).mockResolvedValue(
      freshBreakdown
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('ibl-input')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('ibl-input'), {
      target: { value: '2500000' },
    });
    await user.click(screen.getByTestId('calcular-breakdown-btn'));

    await waitFor(() => {
      expect(
        screen.getByText(/Desglose recién calculado/i)
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByText(/Desglose de la liquidación guardada/i)
    ).not.toBeInTheDocument();
  });

  // --- Método de pago dropdown ---
  it('renders metodo_pago select with CHEQUE and OXIRRE options', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByRole('combobox', { name: /Método de pago/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByText('Cheque')).toBeInTheDocument();
    expect(screen.getByText('Oxirre (transferencia electrónica)')).toBeInTheDocument();
  });

  // --- Sucursal dropdown ---
  it('renders sucursal select with its four options', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByRole('combobox', { name: /Sucursal giradora/i })
      ).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox', { name: /Sucursal giradora/i });
    expect(select).toBeInTheDocument();
    expect(screen.getByText('Cali')).toBeInTheDocument();
    expect(screen.getByText('Medellín')).toBeInTheDocument();
    expect(screen.getByText('Cartagena')).toBeInTheDocument();
    expect(screen.getByText('Bogotá')).toBeInTheDocument();
  });

  // --- Save liquidacion includes sucursal ---
  it('calls guardarLiquidacion with sucursal in the payload when selected', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(
      mockIncapacidadLiquidacion as any
    );
    vi.mocked(liquidacionService.guardarLiquidacion).mockResolvedValue(
      mockLiquidacionExistente
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('ibl-input')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('ibl-input'), {
      target: { value: '2500000' },
    });

    const sucursalSelect = screen.getByRole('combobox', {
      name: /Sucursal giradora/i,
    });
    await user.selectOptions(sucursalSelect, 'Cali');

    await user.click(screen.getByTestId('guardar-borrador-btn'));

    await waitFor(() => {
      expect(liquidacionService.guardarLiquidacion).toHaveBeenCalledWith(
        'inc-liq-001',
        expect.objectContaining({
          sucursal: 'Cali',
        })
      );
    });
  });
});
