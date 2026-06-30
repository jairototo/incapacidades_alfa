/**
 * Tests for AuditoriaFormulario
 *
 * Covers:
 *  - SINIESTRO_REQUERIDO backend error surfaces as destructive toast
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditoriaFormulario } from '../AuditoriaFormulario';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';
import { incapacidadService } from '@/services/incapacidadService';

// ---------------------------------------------------------------------------
// Capture mockToast BEFORE vi.mock hoisting via vi.hoisted
// ---------------------------------------------------------------------------
const mockToast = vi.hoisted(() => vi.fn());

// Mock use-toast so we can assert on the toast call
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

// Mock incapacidadService — only the methods used by this component
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    auditar: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Shared mock incapacidad
// The component uses incapacidad.diagnostico (not diagnostico_descripcion),
// so we cast as any and include both to avoid runtime errors.
// ---------------------------------------------------------------------------
const mockIncapacidad = {
  id: 'inc-test-001',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL',
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'M545',
  diagnostico_descripcion: 'Lumbago',
  diagnostico: 'Lumbago',
  valor_total: 500000,
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
} as any;

// ---------------------------------------------------------------------------
// QueryClientProvider wrapper
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('AuditoriaFormulario', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra toast de error destructivo con el detail de SINIESTRO_REQUERIDO cuando auditar falla', async () => {
    const SINIESTRO_MSG =
      'Esta incapacidad no tiene un siniestro asociado. Debe crear o vincular el siniestro antes de continuar.';

    vi.mocked(incapacidadService.auditar).mockRejectedValue({
      response: { data: { detail: SINIESTRO_MSG } },
    });

    const user = userEvent.setup();
    render(<AuditoriaFormulario incapacidad={mockIncapacidad} />, {
      wrapper: createWrapper(),
    });

    // 1. Select "Aprobar para Pago" action
    const aprobarBtn = screen.getByRole('button', { name: /Aprobar para Pago/i });
    await user.click(aprobarBtn);

    // 2. Fill observaciones (minimum 10 characters required)
    const observacionesTextarea = screen.getByLabelText(/Observaciones/i);
    await user.type(observacionesTextarea, 'Observación de auditoría completa.');

    // 3. Submit the form
    const submitBtn = screen.getByRole('button', { name: /Confirmar Auditoría/i });
    await user.click(submitBtn);

    // 4. Assert the error toast was shown with the SINIESTRO_REQUERIDO detail
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: '❌ Error en auditoría',
        description: SINIESTRO_MSG,
        variant: 'destructive',
      });
    });
  });
});
