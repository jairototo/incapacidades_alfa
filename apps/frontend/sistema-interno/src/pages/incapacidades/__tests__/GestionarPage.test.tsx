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
    cambiado_por: 'user-admin', // Agregado: requerido por HistorialTimeline
    cambiado_por_nombre: 'Admin Usuario',
    observacion: 'Pasando a auditoría',
    created_at: '2024-01-10T11:00:00Z',
  },
] as any;

const mockDocumentos = [
  {
    id: 'doc-1',
    nombre_original: 'incapacidad.pdf', // Cambiado de nombre_archivo
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano_bytes: 102400, // Cambiado de tamano
    ruta_archivo: '/documentos/incapacidad.pdf',
    uploaded_by: 'user-123', // Cambiado de uploaded_by_id
    created_at: '2024-01-10T10:30:00Z',
    extension: 'pdf', // Agregado
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

describe('GestionarPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar el componente con título y número de incapacidad', async () => {
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);

    render(<GestionarPage />, { wrapper: createWrapper() });

    // Esperar a que cargue el componente completo
    await waitFor(() => {
      const elementos = screen.getAllByText(/INC-2024-001/);
      expect(elementos.length).toBeGreaterThan(0);
    });
    
    // Verificar que se muestra el estado (puede aparecer múltiples veces)
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

    render(<GestionarPage />, { wrapper: createWrapper() });

    expect(screen.getByText(/Cargando/)).toBeInTheDocument();
  });

  it('debe mostrar error si falla la carga de incapacidad', async () => {
    vi.mocked(incapacidadService.getById).mockRejectedValue(new Error('Error de red'));
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([]);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);

    render(<GestionarPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // El componente muestra "Incapacidad no encontrada" como título de error
      expect(screen.getByText(/Incapacidad no encontrada/)).toBeInTheDocument();
    });
    
    // También muestra el mensaje de error secundario
    expect(screen.getByText(/No se pudo cargar la información/)).toBeInTheDocument();
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

    // Esperar a que carguen los datos (INC-2024-001 puede aparecer múltiples veces)
    await waitFor(() => {
      const numeroElements = screen.queryAllByText(/INC-2024-001/);
      expect(numeroElements.length).toBeGreaterThan(0);
    });

    // Por defecto debe mostrar "Datos Generales" - buscar un elemento específico de IncapacidadDetalle
    // Por ejemplo, el diagnóstico o el nombre del empleado
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument();

    // Click en pestaña "Documentos"
    const docsTab = screen.getByRole('tab', { name: /Documentos/i });
    await user.click(docsTab);

    // Verificar que el contenido cambió (debe aparecer el documento)
    await waitFor(() => {
      expect(screen.getByText('incapacidad.pdf')).toBeInTheDocument();
    });

    // Click en pestaña "Historial"
    const histTab = screen.getByRole('tab', { name: /Historial/i });
    await user.click(histTab);

    // Verificar que el contenido cambió (debe aparecer texto del resumen o badge "Más reciente")
    await waitFor(() => {
      expect(screen.getByText('Cambios totales')).toBeInTheDocument();
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
      const aprobarElements = screen.getAllByText(/Aprobar/);
      expect(aprobarElements.length).toBeGreaterThan(0);
      
      const observarElements = screen.getAllByText(/Observar/);
      expect(observarElements.length).toBeGreaterThan(0);
      
      const rechazarElements = screen.getAllByText(/Rechazar/);
      expect(rechazarElements.length).toBeGreaterThan(0);
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
      // INC-2024-001 puede aparecer múltiples veces, usar getAllByText para verificar carga
      const numeroElements = screen.queryAllByText(/INC-2024-001/);
      expect(numeroElements.length).toBeGreaterThan(0);
    });

    // No debe mostrar botones de acciones (estado PAGADA no es gestionable)
    expect(screen.queryByText(/Aprobar/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Observar/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Rechazar/)).not.toBeInTheDocument();
    
    // Debe mostrar mensaje de estado final
    expect(screen.getByText(/no se puede gestionar/)).toBeInTheDocument();
  });

  it('debe llamar a cambiarEstado y refrescar datos al aprobar', async () => {
    const user = userEvent.setup();
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad);
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue(mockHistorial);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue(mockDocumentos);
    vi.mocked(incapacidadService.cambiarEstado).mockResolvedValue({
      ...mockIncapacidad,
      estado: EstadoIncapacidad.LIQUIDACION,
    });

    render(<GestionarPage />, { wrapper: createWrapper() });

    // Esperar a que carguen los datos
    await waitFor(() => {
      const numeroElements = screen.queryAllByText(/INC-2024-001/);
      expect(numeroElements.length).toBeGreaterThan(0);
    });

    // Esperar a que aparezca el botón Aprobar
    await waitFor(() => {
      expect(screen.getByText(/Aprobar incapacidad para pago/)).toBeInTheDocument();
    });

    // Click en botón Aprobar
    const aprobarBtn = screen.getByText(/Aprobar incapacidad para pago/);
    await user.click(aprobarBtn);

    // Esperar y click en botón Confirmar del formulario
    const confirmarBtn = await screen.findByRole('button', { name: /Confirmar/i });
    await user.click(confirmarBtn);

    // Verificar que se llamó al servicio
    await waitFor(() => {
      expect(incapacidadService.cambiarEstado).toHaveBeenCalled();
    });
  });
});

