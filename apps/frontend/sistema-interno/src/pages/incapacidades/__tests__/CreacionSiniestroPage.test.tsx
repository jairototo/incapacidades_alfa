import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { CreacionSiniestroPage } from '../CreacionSiniestroPage';
import { incapacidadService } from '@/services/incapacidadService';
import { useHasRole } from '@/store/authStore';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getById: vi.fn(),
    iniciarCreacionSiniestro: vi.fn(),
  },
}));

vi.mock('@/store/authStore', async () => {
  const actual = await vi.importActual('@/store/authStore');
  return {
    ...actual,
    useHasRole: vi.fn(),
  };
});

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockIncapacidadARL = {
  id: 'inc-arl-001',
  numero: 'INC-ARL-20260101-0001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
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
  },
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-01-01T10:00:00Z',
};

function renderPage(incapacidadId = 'inc-arl-001') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/incapacidades/${incapacidadId}/creacion-siniestro`]}>
        <Routes>
          <Route
            path="/incapacidades/:id/creacion-siniestro"
            element={<CreacionSiniestroPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CreacionSiniestroPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: user is ADMIN
    vi.mocked(useHasRole).mockReturnValue(true);
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidadARL as any);
  });

  it('shows unauthorized message for non-admin users', () => {
    vi.mocked(useHasRole).mockReturnValue(false);
    renderPage();
    expect(
      screen.getByText(/exclusiva para administradores/i)
    ).toBeInTheDocument();
  });

  it('renders incapacidad header with employee and company data', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('INC-ARL-20260101-0001')).toBeInTheDocument();
    });

    expect(screen.getByText(/Juan Pérez/)).toBeInTheDocument();
    expect(screen.getByText(/Empresa Test SAS/)).toBeInTheDocument();
  });

  it('renders form fields for numero_siniestro and observacion', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/número de siniestro externo/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/observación/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /vincular siniestro/i })).toBeInTheDocument();
  });

  it('shows validation errors when fields are empty on submit', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /vincular siniestro/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /vincular siniestro/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/el número de siniestro es obligatorio/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/la observación es obligatoria/i)
      ).toBeInTheDocument();
    });
  });

  it('calls iniciarCreacionSiniestro and shows success screen on valid submit', async () => {
    const user = userEvent.setup();

    vi.mocked(incapacidadService.iniciarCreacionSiniestro).mockResolvedValue({
      ...mockIncapacidadARL,
      estado: EstadoIncapacidad.CREACION_SINIESTRO,
    } as any);

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/número de siniestro externo/i)).toBeInTheDocument();
    });

    await user.type(
      screen.getByLabelText(/número de siniestro externo/i),
      'SINX-2026-001'
    );
    await user.type(
      screen.getByLabelText(/observación/i),
      'Vinculando siniestro externo del sistema RRHH'
    );
    await user.click(screen.getByRole('button', { name: /vincular siniestro/i }));

    await waitFor(() => {
      expect(incapacidadService.iniciarCreacionSiniestro).toHaveBeenCalledWith(
        'inc-arl-001',
        {
          numero_siniestro: 'SINX-2026-001',
          observacion: 'Vinculando siniestro externo del sistema RRHH',
        }
      );
    });

    await waitFor(() => {
      expect(
        screen.getByText(/siniestro en proceso de vinculación/i)
      ).toBeInTheDocument();
    });
  });
});
