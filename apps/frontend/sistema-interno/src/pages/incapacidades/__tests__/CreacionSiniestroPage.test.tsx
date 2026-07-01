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
    getHistorial: vi.fn(),
    getDocumentos: vi.fn(),
    getValidaciones: vi.fn(),
    iniciarCreacionSiniestro: vi.fn(),
  },
}));

vi.mock('@/store/authStore', async () => {
  const actual = await vi.importActual('@/store/authStore');
  return { ...actual, useHasRole: vi.fn() };
});

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockIncapacidad = {
  id: 'inc-arl-001',
  numero: 'INC-ARL-20260101-0001',
  tipo: TipoIncapacidad.ARL,
  estado: 'CREACION_SINIESTRO' as EstadoIncapacidad,
  fecha_inicio: '2026-01-01',
  fecha_fin: '2026-01-10',
  dias_totales: 10,
  diagnostico_cie10: 'M545',
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

function renderPage(id = 'inc-arl-001') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/incapacidades/${id}/creacion-siniestro`]}>
        <Routes>
          <Route
            path="/incapacidades/:id/creacion-siniestro"
            element={<CreacionSiniestroPage />}
          />
          <Route path="/incapacidades/creacion-siniestro" element={<div>Bandeja</div>} />
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
    vi.mocked(useHasRole).mockReturnValue(true);
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad as any);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);
    vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({ issues: [], has_fraud_alert: false });
  });

  it('shows unauthorized message for non-admin users', () => {
    vi.mocked(useHasRole).mockReturnValue(false);
    renderPage();
    expect(screen.getByText(/exclusiva para administradores/i)).toBeInTheDocument();
  });

  it('renders incapacidad header with employee and company data', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('INC-ARL-20260101-0001')).toBeInTheDocument();
    });
    expect(screen.getByText(/Juan Pérez/)).toBeInTheDocument();
    expect(screen.getByText(/Empresa Test SAS/)).toBeInTheDocument();
  });

  it('renders siniestro form fields', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByLabelText(/fecha del siniestro/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/tipo de siniestro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/descripción del siniestro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/observación para el historial/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /crear siniestro/i })).toBeInTheDocument();
  });

  it('shows validation errors when fields are empty on submit', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear siniestro/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /crear siniestro/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/la fecha del siniestro es obligatoria/i)
      ).toBeInTheDocument();
    });
  });

  it('calls iniciarCreacionSiniestro with correct fields on valid submit', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.iniciarCreacionSiniestro).mockResolvedValue({
      ...mockIncapacidad,
      estado: 'EN_AUDITORIA' as EstadoIncapacidad,
    } as any);

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/fecha del siniestro/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/fecha del siniestro/i), '2026-01-01');
    await user.selectOptions(
      screen.getByLabelText(/tipo de siniestro/i),
      'ACCIDENTE_TRABAJO'
    );
    await user.type(
      screen.getByLabelText(/descripción del siniestro/i),
      'Accidente de trabajo durante jornada laboral'
    );
    await user.type(
      screen.getByLabelText(/observación para el historial/i),
      'Siniestro creado manualmente por el administrador'
    );

    await user.click(screen.getByRole('button', { name: /crear siniestro/i }));

    await waitFor(() => {
      expect(incapacidadService.iniciarCreacionSiniestro).toHaveBeenCalledWith(
        'inc-arl-001',
        expect.objectContaining({
          tipo_siniestro: 'ACCIDENTE_TRABAJO',
          descripcion: 'Accidente de trabajo durante jornada laboral',
          observacion: 'Siniestro creado manualmente por el administrador',
        })
      );
    });
  });
});
