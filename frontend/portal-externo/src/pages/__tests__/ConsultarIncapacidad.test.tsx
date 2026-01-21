/**
 * Tests para la página ConsultarIncapacidad.
 * 
 * Cobertura:
 * - Renderizado inicial y estructura
 * - Integración de componentes
 * - Estados: loading, error, empty, success
 * - Navegación y scroll automático
 * - Interacción con búsquedas
 * - Botones de retry y nueva búsqueda
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConsultarIncapacidad } from '../ConsultarIncapacidad';
import * as useConsultaIncapacidad from '@/hooks/useConsultaIncapacidad';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

// Mock de los hooks de consulta
vi.mock('@/hooks/useConsultaIncapacidad');

// Mock de los componentes hijos
vi.mock('@/components/consulta/BusquedaIncapacidad', () => ({
  BusquedaIncapacidad: ({ onBuscarPorNumero, onBuscarPorDocumento, disabled }: any) => (
    <div data-testid="busqueda-incapacidad">
      <button
        onClick={() => onBuscarPorNumero('INC-ARL-20260117-0001')}
        disabled={disabled}
        data-testid="btn-buscar-numero"
      >
        Buscar por número
      </button>
      <button
        onClick={() => onBuscarPorDocumento('CEDULA', '1234567890')}
        disabled={disabled}
        data-testid="btn-buscar-documento"
      >
        Buscar por documento
      </button>
    </div>
  ),
}));

vi.mock('@/components/consulta/DetalleIncapacidad', () => ({
  DetalleIncapacidad: ({ incapacidad }: any) => (
    <div data-testid="detalle-incapacidad">
      Detalle: {incapacidad.numero}
    </div>
  ),
}));

vi.mock('@/components/consulta/TimelineEstados', () => ({
  TimelineEstados: ({ historial }: any) => (
    <div data-testid="timeline-estados">
      Timeline: {historial.length} estados
    </div>
  ),
}));

vi.mock('@/components/consulta/DocumentosDescargables', () => ({
  DocumentosDescargables: ({ documentos, numeroIncapacidad }: any) => (
    <div data-testid="documentos-descargables">
      Documentos: {documentos.length} de {numeroIncapacidad}
    </div>
  ),
}));

// Mock de scroll
const mockScrollIntoView = vi.fn();
Element.prototype.scrollIntoView = mockScrollIntoView;

// Data de prueba
const mockIncapacidad: ConsultaIncapacidadResponse = {
  numero: 'INC-ARL-20260117-0001',
  tipo: 'ARL',
  subtipo: 'ACCIDENTE_TRABAJO',
  estado: 'APROBADA',
  fecha_inicio: '2026-01-15',
  fecha_fin: '2026-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'S06.0',
  diagnostico_descripcion: 'Conmoción cerebral',
  valor_total: 500000,
  solicitante: {
    tipo_documento: 'CEDULA',
    numero_documento: '1234567890',
    nombre_completo: 'Juan Pérez',
    telefono: '3001234567',
    email: 'juan@example.com',
  },
  historial_estados: [
    {
      estado: 'RADICADA',
      fecha_cambio: '2026-01-15T10:00:00Z',
      usuario_nombre: 'Sistema',
      observacion: null,
    },
    {
      estado: 'APROBADA',
      fecha_cambio: '2026-01-17T14:30:00Z',
      usuario_nombre: 'Auditor 1',
      observacion: 'Aprobada',
    },
  ],
  documentos: [
    {
      id: 'doc-1',
      tipo: 'INCAPACIDAD_MEDICA',
      nombre_archivo: 'incapacidad.pdf',
      tamanio: 250000,
      created_at: '2026-01-15T10:00:00Z',
    },
  ],
  created_at: '2026-01-15T10:00:00Z',
  updated_at: '2026-01-17T14:30:00Z',
};

describe('ConsultarIncapacidad', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
    mockScrollIntoView.mockClear();

    // Mock por defecto: sin búsqueda activa
    vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.mocked(useConsultaIncapacidad.useConsultarPorDocumento).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ConsultarIncapacidad />
      </QueryClientProvider>
    );
  };

  describe('Renderizado inicial y estructura', () => {
    it('debe renderizar la página completa', () => {
      renderComponent();

      // Header
      expect(screen.getByText('Consulta de Incapacidades')).toBeInTheDocument();
      expect(screen.getByText(/Consulta el estado de tu incapacidad/)).toBeInTheDocument();

      // Footer
      expect(screen.getByText(/Sistema de Gestión de Incapacidades/)).toBeInTheDocument();
    });

    it('debe renderizar el componente BusquedaIncapacidad siempre', () => {
      renderComponent();
      expect(screen.getByTestId('busqueda-incapacidad')).toBeInTheDocument();
    });

    it('debe mostrar mensaje inicial cuando no hay búsqueda', () => {
      renderComponent();

      expect(screen.getByText('Busca tu incapacidad')).toBeInTheDocument();
      expect(screen.getByText(/Ingresa el número de radicación/)).toBeInTheDocument();
    });

    it('debe mostrar instrucciones de búsqueda en estado inicial', () => {
      renderComponent();

      expect(screen.getByText(/Número de radicación:/)).toBeInTheDocument();
      expect(screen.getByText(/Documento:/)).toBeInTheDocument();
    });
  });

  describe('Estado de loading', () => {
    it('debe mostrar spinner mientras busca por número', async () => {
      // Primero renderizar sin loading
      const { rerender } = renderComponent();

      // Click activa búsqueda
      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Simular estado de loading después del click
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      // Re-renderizar con nuevo estado
      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      expect(screen.getByText('Buscando incapacidad...')).toBeInTheDocument();
      expect(screen.getByText(/Estamos consultando la información/)).toBeInTheDocument();
    });

    it('debe deshabilitar búsqueda mientras está loading', async () => {
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Activar loading
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      // BusquedaIncapacidad recibe disabled=true
      const btnBuscar = screen.getByTestId('btn-buscar-numero');
      expect(btnBuscar).toBeDisabled();
    });

    it('debe mostrar icono de loading animado', async () => {
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Activar loading
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      // Verificar que hay un loader (clase animate-spin)
      const loader = document.querySelector('.animate-spin');
      expect(loader).toBeInTheDocument();
    });
  });

  describe('Estado de error', () => {
    it('debe mostrar mensaje de error cuando falla la búsqueda', async () => {
      const { rerender } = renderComponent();
      const errorMessage = 'Incapacidad no encontrada';

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Simular error después del click
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error(errorMessage),
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      expect(screen.getByText('Error al consultar incapacidad')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('debe mostrar botón de reintentar en error', async () => {
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Error de red'),
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
    });

    it('debe llamar a refetch al hacer clic en reintentar', async () => {
      const mockRefetch = vi.fn();
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      
      // Activar búsqueda
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Estado de error
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Error'),
        refetch: mockRefetch,
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      // Click en reintentar
      const btnReintentar = screen.getByRole('button', { name: /Reintentar/i });
      await user.click(btnReintentar);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });

    it('debe mostrar botón de nueva búsqueda en error', async () => {
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Error'),
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      expect(screen.getByRole('button', { name: /Nueva búsqueda/i })).toBeInTheDocument();
    });

    it('debe limpiar resultados al hacer clic en nueva búsqueda desde error', async () => {
      const { rerender } = renderComponent();

      const user = userEvent.setup();
      
      // Activar búsqueda con error
      await user.click(screen.getByTestId('btn-buscar-numero'));

      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Error'),
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <ConsultarIncapacidad />
        </QueryClientProvider>
      );

      expect(screen.getByText('Error al consultar incapacidad')).toBeInTheDocument();

      // Click en nueva búsqueda
      const btnNuevaBusqueda = screen.getByRole('button', { name: /Nueva búsqueda/i });
      await user.click(btnNuevaBusqueda);

      // Debe volver a estado inicial
      await waitFor(() => {
        expect(screen.queryByText('Error al consultar incapacidad')).not.toBeInTheDocument();
        expect(screen.getByText('Busca tu incapacidad')).toBeInTheDocument();
      });
    });
  });

  describe('Integración de componentes', () => {
    beforeEach(() => {
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidad,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);
    });

    it('debe renderizar DetalleIncapacidad cuando hay datos', async () => {
      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(screen.getByTestId('detalle-incapacidad')).toBeInTheDocument();
        expect(screen.getByText(/Detalle: INC-ARL-20260117-0001/)).toBeInTheDocument();
      });
    });

    it('debe renderizar TimelineEstados con historial correcto', async () => {
      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(screen.getByTestId('timeline-estados')).toBeInTheDocument();
        expect(screen.getByText(/Timeline: 2 estados/)).toBeInTheDocument();
      });
    });

    it('debe renderizar DocumentosDescargables con documentos correctos', async () => {
      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(screen.getByTestId('documentos-descargables')).toBeInTheDocument();
        expect(screen.getByText(/Documentos: 1 de INC-ARL-20260117-0001/)).toBeInTheDocument();
      });
    });

    it('debe mostrar los 3 componentes de resultados en grid', async () => {
      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(screen.getByTestId('detalle-incapacidad')).toBeInTheDocument();
        expect(screen.getByTestId('timeline-estados')).toBeInTheDocument();
        expect(screen.getByTestId('documentos-descargables')).toBeInTheDocument();
      });
    });

    it('debe ocultar mensaje inicial cuando hay resultados', async () => {
      renderComponent();

      const user = userEvent.setup();
      
      // Antes de buscar
      expect(screen.getByText('Busca tu incapacidad')).toBeInTheDocument();

      // Después de buscar
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(screen.queryByText('Busca tu incapacidad')).not.toBeInTheDocument();
      });
    });
  });

  describe('Búsqueda por número', () => {
    it('debe activar consulta por número al buscar', async () => {
      const mockHook = vi.fn().mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockImplementation(mockHook);

      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Debe llamar al hook con enabled=true y el número
      await waitFor(() => {
        expect(mockHook).toHaveBeenCalledWith('INC-ARL-20260117-0001', true);
      });
    });
  });

  describe('Búsqueda por documento', () => {
    it('debe activar consulta por documento al buscar', async () => {
      const mockHook = vi.fn().mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      vi.mocked(useConsultaIncapacidad.useConsultarPorDocumento).mockImplementation(mockHook);

      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-documento'));

      // Debe llamar al hook con enabled=true, tipo y documento
      await waitFor(() => {
        expect(mockHook).toHaveBeenCalledWith('CEDULA', '1234567890', true);
      });
    });
  });

  describe('Scroll automático', () => {
    it('debe hacer scroll a resultados cuando se obtienen datos', async () => {
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidad,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      // Esperar a que se ejecute el useEffect con timeout
      await waitFor(() => {
        expect(mockScrollIntoView).toHaveBeenCalled();
      }, { timeout: 200 });
    });

    it('debe usar scroll suave (smooth)', async () => {
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidad,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        expect(mockScrollIntoView).toHaveBeenCalledWith({
          behavior: 'smooth',
          block: 'start',
        });
      }, { timeout: 200 });
    });
  });

  describe('Botón de nueva búsqueda', () => {
    it('debe mostrar botón de nueva búsqueda cuando hay resultados', async () => {
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidad,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      const user = userEvent.setup();
      await user.click(screen.getByTestId('btn-buscar-numero'));

      await waitFor(() => {
        const btnNuevaBusqueda = screen.getAllByRole('button', { name: /Nueva búsqueda/i });
        expect(btnNuevaBusqueda.length).toBeGreaterThan(0);
      });
    });

    it('debe limpiar resultados al hacer clic en nueva búsqueda', async () => {
      vi.mocked(useConsultaIncapacidad.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidad,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      const user = userEvent.setup();
      
      // Buscar
      await user.click(screen.getByTestId('btn-buscar-numero'));
      
      await waitFor(() => {
        expect(screen.getByTestId('detalle-incapacidad')).toBeInTheDocument();
      });

      // Nueva búsqueda
      const btnNuevaBusqueda = screen.getAllByRole('button', { name: /Nueva búsqueda/i })[0];
      await user.click(btnNuevaBusqueda);

      // Debe volver a estado inicial
      await waitFor(() => {
        expect(screen.queryByTestId('detalle-incapacidad')).not.toBeInTheDocument();
        expect(screen.getByText('Busca tu incapacidad')).toBeInTheDocument();
      });
    });
  });
});
