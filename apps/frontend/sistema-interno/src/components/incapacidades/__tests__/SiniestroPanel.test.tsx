/**
 * Tests for SiniestroPanel
 *
 * Covers:
 * 1. When siniestro_id is set: renders read-only siniestro card with numero, fecha, tipo.
 * 2. When siniestro_id is null and candidates exist: renders radio list + "Vincular" button.
 * 3. When siniestro_id is null and no candidates: renders "No se encontraron siniestros candidatos."
 * 4. When tipo is SALUD: renders nothing.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SiniestroPanel } from '../SiniestroPanel';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';
import type { Incapacidad, SiniestroBasic } from '@/types/incapacidad';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getSiniestrosCandidatos: vi.fn(),
    vincularSiniestro: vi.fn(),
    iniciarCreacionSiniestro: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const mockSiniestroVinculado: SiniestroBasic = {
  id: 'sin-123',
  numero_siniestro: 'SIN-2026-001',
  fecha_siniestro: '2026-01-05',
  tipo_siniestro: 'ACCIDENTE_TRABAJO',
  descripcion: 'Caída en escalera durante jornada laboral',
  gravedad: 'LEVE',
  estado: 'ACTIVO',
};

const mockIncapacidadARL: Incapacidad = {
  id: 'inc-abc',
  numero: 'INC-ARL-2026-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL' as any,
  fecha_inicio: '2026-01-10',
  fecha_fin: '2026-01-20',
  dias_totales: 10,
  diagnostico_cie10: 'S00.0',
  diagnostico_descripcion: '',
  valor_total: 0,
  created_at: '2026-01-10T00:00:00Z',
  updated_at: '2026-01-10T00:00:00Z',
};

const mockCandidato: SiniestroBasic = {
  id: 'sin-cand-1',
  numero_siniestro: 'SIN-2026-CAND',
  fecha_siniestro: '2026-01-03',
  tipo_siniestro: 'ACCIDENTE_TRABAJO',
  descripcion: 'Accidente en área de producción',
  gravedad: 'MODERADA',
  estado: 'ACTIVO',
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SiniestroPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. renders read-only siniestro card when siniestro_id is set', async () => {
    const incapacidad: Incapacidad = {
      ...mockIncapacidadARL,
      siniestro_id: 'sin-123',
      numero_siniestro: 'SIN-2026-001',
      siniestro: mockSiniestroVinculado,
    };

    render(<SiniestroPanel incapacidad={incapacidad} />, { wrapper: createWrapper() });

    expect(screen.getByTestId('siniestro-vinculado')).toBeInTheDocument();
    expect(screen.getByText('SIN-2026-001')).toBeInTheDocument();
    expect(screen.getByText('ACCIDENTE_TRABAJO')).toBeInTheDocument();
    // Fecha formateada: al menos un elemento con texto de fecha debe existir
    expect(screen.getAllByText(/2026/).length).toBeGreaterThan(0);
  });

  it('2. renders radio list and Vincular button when siniestro_id is null and candidates exist', async () => {
    const { incapacidadService } = await import('@/services/incapacidadService');
    (incapacidadService.getSiniestrosCandidatos as ReturnType<typeof vi.fn>).mockResolvedValue([
      mockCandidato,
    ]);

    const incapacidad: Incapacidad = {
      ...mockIncapacidadARL,
      siniestro_id: null,
      siniestro: null,
    };

    render(<SiniestroPanel incapacidad={incapacidad} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('siniestro-candidatos')).toBeInTheDocument();
    });

    expect(screen.getByText('SIN-2026-CAND')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Vincular este siniestro/i })).toBeInTheDocument();
    expect(screen.getByTestId(`radio-siniestro-${mockCandidato.id}`)).toBeInTheDocument();
  });

  it('3. renders empty state message when siniestro_id is null and no candidates', async () => {
    const { incapacidadService } = await import('@/services/incapacidadService');
    (incapacidadService.getSiniestrosCandidatos as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const incapacidad: Incapacidad = {
      ...mockIncapacidadARL,
      siniestro_id: null,
      siniestro: null,
    };

    render(<SiniestroPanel incapacidad={incapacidad} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('siniestro-empty')).toBeInTheDocument();
    });

    expect(screen.getByText(/No se encontraron siniestros candidatos/i)).toBeInTheDocument();
  });

  it('4. renders nothing when tipo is SALUD', () => {
    const incapacidadSalud: Incapacidad = {
      ...mockIncapacidadARL,
      tipo: TipoIncapacidad.SALUD,
    };

    const { container } = render(
      <SiniestroPanel incapacidad={incapacidadSalud} />,
      { wrapper: createWrapper() }
    );

    expect(container.firstChild).toBeNull();
  });

  it('5. renders "Ninguno corresponde / Crear siniestro" button when no candidates', async () => {
    const { incapacidadService } = await import('@/services/incapacidadService');
    (incapacidadService.getSiniestrosCandidatos as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    const incapacidad: Incapacidad = {
      ...mockIncapacidadARL,
      siniestro_id: null,
      siniestro: null,
    };

    render(<SiniestroPanel incapacidad={incapacidad} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('siniestro-empty')).toBeInTheDocument();
    });

    expect(
      screen.getByRole('button', { name: /Ninguno corresponde \/ Crear siniestro/i })
    ).toBeInTheDocument();
  });

  it('6. clicking "Ninguno corresponde" button calls iniciarCreacionSiniestro', async () => {
    const { incapacidadService } = await import('@/services/incapacidadService');
    (incapacidadService.getSiniestrosCandidatos as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (incapacidadService.iniciarCreacionSiniestro as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockIncapacidadARL,
      estado: 'CREACION_SINIESTRO',
    });

    const incapacidad: Incapacidad = {
      ...mockIncapacidadARL,
      siniestro_id: null,
      siniestro: null,
    };

    render(<SiniestroPanel incapacidad={incapacidad} />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('siniestro-empty')).toBeInTheDocument();
    });

    const btn = screen.getByRole('button', {
      name: /Ninguno corresponde \/ Crear siniestro/i,
    });
    btn.click();

    await waitFor(() => {
      expect(incapacidadService.iniciarCreacionSiniestro).toHaveBeenCalledWith(
        mockIncapacidadARL.id,
        expect.objectContaining({ numero_siniestro: 'PENDIENTE' })
      );
    });
  });
});
