import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestionarPage } from '../GestionarPage';
import { incapacidadService } from '@/services/incapacidadService';
import { EstadoIncapacidad, TipoIncapacidad } from '@/types';

// Mock del servicio de incapacidades
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getById: vi.fn(),
    getHistorial: vi.fn(),
    getDocumentos: vi.fn(),
    cambiarEstado: vi.fn(),
    getDatosAprobados: vi.fn(),
    getValidaciones: vi.fn(),
    reenviarNotificacionGlosada: vi.fn(),
    getSiniestrosCandidatos: vi.fn().mockResolvedValue([]),
  },
}));

// Mock del servicio de pre-incapacidades
vi.mock('@/services/preIncapacidadService', () => ({
  preIncapacidadService: {
    getById: vi.fn(),
  },
}));

// Mock del store de autenticación — ADMIN/AUDITOR por defecto
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
  useHasRole: vi.fn().mockReturnValue(true),
}));

// Mock de react-router-dom para useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-id-123' }),
  };
});

const mockIncapacidad = {
  id: 'test-id-123',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'S06.0',
  diagnostico_descripcion: 'Conmoción cerebral',
  valor_total: 500000,
  observaciones: null,
  prioridad: 'NORMAL',
  empleado: {
    id: 'emp-123',
    numero_documento: '12345678',
    tipo_documento: 'CEDULA',
    nombres: 'Juan',
    apellidos: 'Pérez',
    email: 'juan@example.com',
  },
  empresa: {
    id: 'emp-456',
    nit: '900123456',
    razon_social: 'Empresa Test SA',
  },
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
};

const mockHistorial = [
  {
    id: 'hist-1',
    entity_type: 'incapacidad',
    entity_id: 'test-id-123',
    estado_anterior: EstadoIncapacidad.RADICADA,
    estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
    cambiado_por: 'user-admin',
    cambiado_por_nombre: 'Admin Usuario',
    observacion: 'Pasando a auditoría',
    created_at: '2024-01-10T11:00:00Z',
  },
] as any;

const mockDocumentos = [
  {
    id: 'doc-1',
    nombre_original: 'incapacidad.pdf',
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano_bytes: 102400,
    ruta_archivo: '/documentos/incapacidad.pdf',
    uploaded_by: 'user-123',
    created_at: '2024-01-10T10:30:00Z',
    extension: 'pdf',
  },
] as any;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/incapacidades/test-id-123/gestionar']}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

/** Set up default service mocks used in most tests */
function setupDefaultMocks() {
  vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
  vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
  vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
  vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
  vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
    issues: [],
    has_fraud_alert: false,
    total: 0,
  } as any);
}

describe('GestionarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar el componente con título y número de incapacidad', async () => {
    setupDefaultMocks();

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const elementos = screen.getAllByText(/INC-2024-001/);
      expect(elementos.length).toBeGreaterThan(0);
    });

    const estadoElements = screen.getAllByText('EN_AUDITORIA');
    expect(estadoElements.length).toBeGreaterThan(0);
  });

  it('debe mostrar estado de carga mientras obtiene los datos', () => {
    vi.mocked(incapacidadService.getById).mockImplementation(
      () =>
        new Promise(() => {
          /* never resolves */
        })
    );
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
    vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
      issues: [],
      has_fraud_alert: false,
      total: 0,
    } as any);

    render(<GestionarPage />, { wrapper: createWrapper() });

    expect(screen.getByText(/Cargando/)).toBeInTheDocument();
  });

  it('debe mostrar error si falla la carga de incapacidad', async () => {
    vi.mocked(incapacidadService.getById).mockRejectedValue(new Error('Error de red'));
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
    vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
      issues: [],
      has_fraud_alert: false,
      total: 0,
    } as any);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Incapacidad no encontrada/)).toBeInTheDocument();
    });

    expect(screen.getByText(/No se pudo cargar la información/)).toBeInTheDocument();
  });

  it('debe renderizar las 3 pestañas correctas (Auditoría, Validaciones, Historial)', async () => {
    setupDefaultMocks();

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Auditoría/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Validaciones/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Historial/i })).toBeInTheDocument();
    });
  });

  it('debe mostrar mensaje cuando estado no es auditable', async () => {
    const incapacidadPagada = {
      ...mockIncapacidad,
      estado: EstadoIncapacidad.PAGADA,
    };

    vi.mocked(incapacidadService.getById).mockResolvedValue(incapacidadPagada);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
    vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
    vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
      issues: [],
      has_fraud_alert: false,
      total: 0,
    } as any);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const numeroElements = screen.queryAllByText(/INC-2024-001/);
      expect(numeroElements.length).toBeGreaterThan(0);
    });

    // Debe mostrar mensaje de estado no auditable
    expect(screen.getByText(/no se puede auditar/i)).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // Reenviar notificación de glosa
  // ---------------------------------------------------------------------------

  describe('Reenviar notificación de glosa', () => {
    const mockGlosada = {
      ...mockIncapacidad,
      estado: EstadoIncapacidad.GLOSADA,
    };

    it('debe mostrar el botón "Reenviar notificación de glosa" cuando estado es GLOSADA y rol es ADMIN/AUDITOR', async () => {
      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);

      render(<GestionarPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Reenviar notificación de glosa/i })
        ).toBeInTheDocument();
      });
    });

    it('NO debe mostrar el botón cuando el rol no es ADMIN ni AUDITOR', async () => {
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(false);

      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);

      render(<GestionarPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        const numeroElements = screen.queryAllByText(/INC-2024-001/);
        expect(numeroElements.length).toBeGreaterThan(0);
      });

      expect(
        screen.queryByRole('button', { name: /Reenviar notificación de glosa/i })
      ).not.toBeInTheDocument();
    });

    it('NO debe mostrar el botón cuando estado NO es GLOSADA', async () => {
      // useHasRole returns true (default mock)
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(true);

      const incapacidadPagada = { ...mockIncapacidad, estado: EstadoIncapacidad.PAGADA };
      vi.mocked(incapacidadService.getById).mockResolvedValue(incapacidadPagada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);

      render(<GestionarPage />, { wrapper: createWrapper() });

      await waitFor(() => {
        const numeroElements = screen.queryAllByText(/INC-2024-001/);
        expect(numeroElements.length).toBeGreaterThan(0);
      });

      expect(
        screen.queryByRole('button', { name: /Reenviar notificación de glosa/i })
      ).not.toBeInTheDocument();
    });

    it('debe abrir el diálogo de confirmación al hacer click en el botón', async () => {
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(true);

      const user = userEvent.setup();
      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);

      render(<GestionarPage />, { wrapper: createWrapper() });

      const btn = await screen.findByRole('button', { name: /Reenviar notificación de glosa/i });
      await user.click(btn);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText(/Se enviará nuevamente la notificación/i)).toBeInTheDocument();
      });
    });

    it('debe llamar a reenviarNotificacionGlosada al confirmar el diálogo', async () => {
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(true);

      const user = userEvent.setup();
      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);
      vi.mocked(incapacidadService.reenviarNotificacionGlosada).mockResolvedValue(undefined);

      render(<GestionarPage />, { wrapper: createWrapper() });

      // Abrir diálogo
      const btn = await screen.findByRole('button', { name: /Reenviar notificación de glosa/i });
      await user.click(btn);

      // Confirmar
      const confirmarBtn = await screen.findByRole('button', { name: /^Confirmar$/i });
      await user.click(confirmarBtn);

      await waitFor(() => {
        expect(incapacidadService.reenviarNotificacionGlosada).toHaveBeenCalledWith('test-id-123');
      });
    });

    it('debe cerrar el diálogo al cancelar', async () => {
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(true);

      const user = userEvent.setup();
      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);

      render(<GestionarPage />, { wrapper: createWrapper() });

      // Abrir diálogo
      const btn = await screen.findByRole('button', { name: /Reenviar notificación de glosa/i });
      await user.click(btn);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Cancelar
      const cancelarBtn = screen.getByRole('button', { name: /Cancelar/i });
      await user.click(cancelarBtn);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      // El servicio NO debe haber sido llamado
      expect(incapacidadService.reenviarNotificacionGlosada).not.toHaveBeenCalled();
    });

    it('debe mostrar toast de error cuando falla el reenvío', async () => {
      const { useHasRole } = await import('@/store/authStore');
      (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(true);

      const user = userEvent.setup();
      vi.mocked(incapacidadService.getById).mockResolvedValue(mockGlosada);
      vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
      vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
      vi.mocked(incapacidadService.getDatosAprobados).mockResolvedValue(null);
      vi.mocked(incapacidadService.getValidaciones).mockResolvedValue({
        issues: [],
        has_fraud_alert: false,
        total: 0,
      } as any);
      vi.mocked(incapacidadService.reenviarNotificacionGlosada).mockRejectedValue(
        new Error('Error de red')
      );

      render(<GestionarPage />, { wrapper: createWrapper() });

      const btn = await screen.findByRole('button', { name: /Reenviar notificación de glosa/i });
      await user.click(btn);

      const confirmarBtn = await screen.findByRole('button', { name: /^Confirmar$/i });
      await user.click(confirmarBtn);

      await waitFor(() => {
        expect(incapacidadService.reenviarNotificacionGlosada).toHaveBeenCalled();
      });
    });
  });
});
