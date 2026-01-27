import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GestionarPage } from '../GestionarPage';
import { incapacidadService } from '@/services/incapacidadService';
import { EstadoIncapacidad, TipoIncapacidad } from '@/types';

// Mock del servicio
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getById: vi.fn(),
    getHistorial: vi.fn(),
    getDocumentos: vi.fn(),
    cambiarEstado: vi.fn(),
  },
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
    cambiado_por_nombre: 'Admin Usuario',
    observacion: 'Pasando a auditoría',
    created_at: '2024-01-10T11:00:00Z',
  },
];

const mockDocumentos = [
  {
    id: 'doc-1',
    nombre_archivo: 'incapacidad.pdf',
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano: 102400,
    ruta_archivo: '/documentos/incapacidad.pdf',
    uploaded_by_id: 'user-123',
    created_at: '2024-01-10T10:30:00Z',
  },
];

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

describe('GestionarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar el componente con título y número de incapacidad', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    // Verificar título
    expect(screen.getByText('Gestionar Incapacidad')).toBeInTheDocument();

    // Esperar a que cargue el número
    await waitFor(() => {
      expect(screen.getByText(/INC-2024-001/)).toBeInTheDocument();
    });
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

    render(<GestionarPage />, { wrapper: createWrapper() });

    expect(screen.getByText(/Cargando/)).toBeInTheDocument();
  });

  it('debe mostrar error si falla la carga de incapacidad', async () => {
    vi.mocked(incapacidadService.getById).mockRejectedValue(new Error('Error de red'));
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Error al cargar la incapacidad/)).toBeInTheDocument();
    });
  });

  it('debe renderizar las 3 pestañas (Datos Generales, Documentos, Historial)', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Datos Generales/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Documentos/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Historial/i })).toBeInTheDocument();
    });
  });

  it('debe cambiar de pestaña al hacer click', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    // Esperar a que carguen los datos
    await waitFor(() => {
      expect(screen.getByText(/INC-2024-001/)).toBeInTheDocument();
    });

    // Por defecto debe mostrar "Datos Generales"
    expect(screen.getByText(/Información General/)).toBeInTheDocument();

    // Click en pestaña "Documentos"
    const docsTab = screen.getByRole('tab', { name: /Documentos/i });
    await user.click(docsTab);

    // Verificar que el contenido cambió (debe aparecer texto de DocumentosViewer)
    await waitFor(() => {
      expect(screen.getByText(/Documentos Adjuntos/)).toBeInTheDocument();
    });

    // Click en pestaña "Historial"
    const histTab = screen.getByRole('tab', { name: /Historial/i });
    await user.click(histTab);

    // Verificar que el contenido cambió (debe aparecer contenido de HistorialTimeline)
    await waitFor(() => {
      expect(screen.getByText(/Historial de Estados/)).toBeInTheDocument();
    });
  });

  it('debe mostrar acciones de gestión para estados auditables', async () => {
    const incapacidadAuditable = {
      ...mockIncapacidad,
      estado: EstadoIncapacidad.EN_AUDITORIA,
    };

    vi.mocked(incapacidadService.getById).mockResolvedValue(incapacidadAuditable);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Debe mostrar botones de acciones (Aprobar, Observar, Rechazar)
      expect(screen.getByText(/Aprobar/)).toBeInTheDocument();
      expect(screen.getByText(/Observar/)).toBeInTheDocument();
      expect(screen.getByText(/Rechazar/)).toBeInTheDocument();
    });
  });

  it('NO debe mostrar acciones para estados finales', async () => {
    const incapacidadPagada = {
      ...mockIncapacidad,
      estado: EstadoIncapacidad.PAGADA,
    };

    vi.mocked(incapacidadService.getById).mockResolvedValue(incapacidadPagada);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/INC-2024-001/)).toBeInTheDocument();
    });

    // No debe mostrar botones de acciones
    expect(screen.queryByText(/Aprobar/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Observar/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Rechazar/)).not.toBeInTheDocument();
  });

  it('debe llamar a cambiarEstado y refrescar datos al aprobar', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
    vi.mocked(incapacidadService.cambiarEstado).mockResolvedValue({
      ...mockIncapacidad,
      estado: EstadoIncapacidad.APROBADA,
    });

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/INC-2024-001/)).toBeInTheDocument();
    });

    // Click en botón Aprobar
    const aprobarBtn = screen.getByText(/Aprobar/);
    await user.click(aprobarBtn);

    // Click en botón Confirmar del formulario
    const confirmarBtn = screen.getByRole('button', { name: /Confirmar/i });
    await user.click(confirmarBtn);

    // Verificar que se llamó al servicio
    await waitFor(() => {
      expect(incapacidadService.cambiarEstado).toHaveBeenCalledWith(
        'test-id-123',
        EstadoIncapacidad.APROBADA,
        undefined
      );
    });

    // Verificar que se refrescaron los datos (se vuelve a llamar getById)
    await waitFor(() => {
      expect(incapacidadService.getById).toHaveBeenCalledTimes(2); // 1 inicial + 1 refresh
    });
  });
});
