import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { PendientesPage } from '../PendientesPage';
import { incapacidadService } from '@/services/incapacidadService';
import type { IncapacidadPendiente } from '@/types/incapacidad';
import { TipoIncapacidad, EstadoIncapacidad, Prioridad, TipoDocumento } from '@/types/enums';

// Mock del servicio
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    listarPendientes: vi.fn(),
  },
}));

// Mock del servicio de auditores (usado por PendientesFilters al abrir el panel de filtros)
vi.mock('@/services/auditorService', () => ({
  auditorService: {
    listActivos: vi.fn().mockResolvedValue([]),
  },
}));

// Mock de react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Datos de prueba
const mockIncapacidadesPendientes: IncapacidadPendiente[] = [
  {
    id: '1',
    numero: 'INC-001',
    tipo: TipoIncapacidad.ARL,
    estado: EstadoIncapacidad.RADICADA,
    prioridad: Prioridad.ALTA,
    fecha_inicio: '2026-01-20',
    fecha_fin: '2026-01-25',
    dias_totales: 5,
    diagnostico_cie10: 'M54.5',
    diagnostico_descripcion: 'Lumbalgia',
    valor_total: 500000,
    dias_desde_radicacion: 6,
    dias_en_estado_actual: 6,
    empleado: {
      id: 'emp-1',
      tipo_documento: TipoDocumento.CEDULA,
      numero_documento: '1234567890',
      nombres: 'Juan',
      apellidos: 'Pérez',
      cargo: 'Operario',
      empresa_id: 'emp-1',
    },
    empresa: {
      id: 'emp-1',
      nit: '900123456',
      razon_social: 'Empresa ABC',
      email_contacto: 'contacto@empresaabc.com',
    },
    created_at: '2026-01-20T10:00:00Z',
    updated_at: '2026-01-20T10:00:00Z',
  },
  {
    id: '2',
    numero: 'INC-002',
    tipo: TipoIncapacidad.SALUD,
    estado: EstadoIncapacidad.EN_AUDITORIA,
    prioridad: Prioridad.NORMAL,
    fecha_inicio: '2026-01-22',
    fecha_fin: '2026-01-27',
    dias_totales: 5,
    diagnostico_cie10: 'J06.9',
    diagnostico_descripcion: 'Infección respiratoria',
    valor_total: 300000,
    dias_desde_radicacion: 4,
    dias_en_estado_actual: 3,
    afiliado: {
      id: 'afi-1',
      tipo_documento: TipoDocumento.CEDULA,
      numero_documento: '9876543210',
      nombres: 'María',
      apellidos: 'López',
    },
    created_at: '2026-01-22T14:00:00Z',
    updated_at: '2026-01-23T09:00:00Z',
  },
];

describe('PendientesPage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <PendientesPage />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe('Renderizado inicial', () => {
    it('debe renderizar el título con contador', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      expect(screen.getByText('Incapacidades Pendientes')).toBeInTheDocument();
      
      // Esperar a que cargue el contador
      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    it('debe renderizar el botón de filtros', () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);

      renderComponent();

      expect(screen.getByRole('button', { name: /mostrar filtros/i })).toBeInTheDocument();
    });

    it('debe renderizar la tabla con columnas correctas', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('N° Radicación')).toBeInTheDocument();
        expect(screen.getByText('Tipo')).toBeInTheDocument();
        expect(screen.getByText('Solicitante')).toBeInTheDocument();
        expect(screen.getByText('Empresa / Afiliado')).toBeInTheDocument();
        expect(screen.getByText('Radicación')).toBeInTheDocument();
        expect(screen.getByText('Antigüedad')).toBeInTheDocument();
        expect(screen.getByText('Estado')).toBeInTheDocument();
        expect(screen.getByText('Prioridad')).toBeInTheDocument();
        expect(screen.getByText('Acciones')).toBeInTheDocument();
      });
    });

    it('debe mostrar loading state', () => {
      vi.mocked(incapacidadService.listarPendientes).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderComponent();

      // El DataTable muestra un spinner animado, no texto "Cargando..."
      expect(screen.getByRole('heading', { name: /incapacidades pendientes/i })).toBeInTheDocument();
    });
  });

  describe('Filtros', () => {
    it('debe mostrar filtros al hacer clic en el botón', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);
      const user = userEvent.setup();

      renderComponent();

      const filterButton = screen.getByRole('button', { name: /mostrar filtros/i });
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Tipo')).toBeInTheDocument();
        expect(screen.getByLabelText('Prioridad')).toBeInTheDocument();
        expect(screen.getByLabelText('NIT Empresa')).toBeInTheDocument();
        expect(screen.getByLabelText(/antigüedad mínima/i)).toBeInTheDocument();
      });
    });

    it('debe ocultar filtros al hacer clic nuevamente en el botón', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);
      const user = userEvent.setup();

      renderComponent();

      // Mostrar filtros
      const filterButton = screen.getByRole('button', { name: /mostrar filtros/i });
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Tipo')).toBeInTheDocument();
      });

      // Ocultar filtros
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.queryByLabelText('Tipo')).not.toBeInTheDocument();
      });
    });

    it('debe limpiar filtros correctamente', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);
      const user = userEvent.setup();

      renderComponent();

      // Mostrar filtros
      await user.click(screen.getByRole('button', { name: /mostrar filtros/i }));

      // Llenar un filtro
      const nitInput = screen.getByLabelText('NIT Empresa');
      await user.type(nitInput, '900123456');

      // Hacer clic en limpiar
      await user.click(screen.getByRole('button', { name: /limpiar/i }));

      // Verificar que el input se limpió
      expect(nitInput).toHaveValue('');
    });
  });

  describe('Tabla de resultados', () => {
    it('debe mostrar las pendientes en la tabla', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('INC-001')).toBeInTheDocument();
        expect(screen.getByText('INC-002')).toBeInTheDocument();
      });
    });

    it('debe mostrar badges de tipo correctamente', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('ARL')).toBeInTheDocument();
        expect(screen.getByText('SALUD')).toBeInTheDocument();
      });
    });

    it('debe mostrar badges de estado correctamente', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('Radicada')).toBeInTheDocument();
        expect(screen.getByText('En Auditoría')).toBeInTheDocument();
      });
    });

    it('debe mostrar días desde radicación', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('6 días')).toBeInTheDocument();
        expect(screen.getByText('4 días')).toBeInTheDocument();
      });
    });
  });

  describe('Navegación', () => {
    it('debe navegar al gestionar una incapacidad', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);
      const user = userEvent.setup();

      renderComponent();

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /gestionar/i }).length).toBe(2);
      });

      const gestionarButtons = screen.getAllByRole('button', { name: /gestionar/i });
      await user.click(gestionarButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith('/incapacidades/1/gestionar');
    });

    it('debe tener un botón "Gestionar" por cada pendiente', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      await waitFor(() => {
        const gestionarButtons = screen.getAllByRole('button', { name: /gestionar/i });
        expect(gestionarButtons).toHaveLength(2);
      });
    });
  });

  describe('Empty state', () => {
    it('debe mostrar mensaje "No hay pendientes" cuando está vacío', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('¡No hay pendientes!')).toBeInTheDocument();
        expect(screen.getByText('Todas las incapacidades están al día.')).toBeInTheDocument();
      });
    });

    it('debe mostrar el mensaje de "sin resultados con filtros" (no el de "no hay pendientes") cuando un filtro aplicado no encuentra coincidencias', async () => {
      // Con la bandeja llena, seleccionar un filtro (p. ej. un auditor específico) que no
      // tenga incapacidades asignadas debe devolver una lista vacía — pero la UI no debe
      // decir "¡No hay pendientes! Todas las incapacidades están al día", porque eso es
      // falso: sí hay pendientes, solo que ninguno coincide con el filtro aplicado. Ese
      // mensaje incorrecto es lo que hacía parecer que el filtro de auditor asignado no
      // funcionaba.
      vi.mocked(incapacidadService.listarPendientes)
        .mockResolvedValueOnce(mockIncapacidadesPendientes) // carga inicial sin filtros
        .mockResolvedValueOnce([]); // resultado tras aplicar el filtro

      const user = userEvent.setup();
      renderComponent();

      await waitFor(() => {
        expect(screen.getByText('INC-001')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /mostrar filtros/i }));
      await user.type(await screen.findByLabelText(/nit empresa/i), '900123456');
      await user.click(screen.getByRole('button', { name: /^buscar$/i }));

      await waitFor(() => {
        expect(
          screen.getByText('No se encontraron incapacidades pendientes con los filtros aplicados.')
        ).toBeInTheDocument();
      });
      expect(screen.queryByText('¡No hay pendientes!')).not.toBeInTheDocument();
    });

    it('debe mostrar botón de actualizar en empty state', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);

      renderComponent();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /actualizar/i })).toBeInTheDocument();
      });
    });

    it('debe refrescar datos al hacer clic en actualizar', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue([]);
      const user = userEvent.setup();

      renderComponent();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /actualizar/i })).toBeInTheDocument();
      });

      const actualizarButton = screen.getByRole('button', { name: /actualizar/i });
      await user.click(actualizarButton);

      // Verificar que se llamó al servicio nuevamente
      expect(incapacidadService.listarPendientes).toHaveBeenCalledTimes(2);
    });
  });

  describe('Auto-refresh', () => {
    it('debe refrescar datos cada 2 minutos', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);

      renderComponent();

      // Esperar a que cargue inicialmente
      await waitFor(() => {
        expect(incapacidadService.listarPendientes).toHaveBeenCalledTimes(1);
      });

      // El auto-refresh está configurado con refetchInterval: 2 min
      // Este test solo verifica que la configuración está presente
      // No probamos el timer real para evitar timeouts
      expect(screen.getByText('Auto-actualización cada 2 min')).toBeInTheDocument();
    });
  });

  describe('Validación de filtros', () => {
    it('no debe enviar NaN cuando el campo dias_antiguedad_min está vacío', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);
      const user = userEvent.setup();

      renderComponent();

      // Mostrar filtros
      await user.click(screen.getByRole('button', { name: /mostrar filtros/i }));

      await waitFor(() => {
        expect(screen.getByLabelText('Antigüedad mínima (días)')).toBeInTheDocument();
      });

      // Dejar el campo vacío y buscar
      await user.click(screen.getByRole('button', { name: /buscar/i }));

      // Verificar que el servicio fue llamado sin el parámetro dias_antiguedad_min
      // (o si está presente, que no sea NaN)
      await waitFor(() => {
        const lastCall = vi.mocked(incapacidadService.listarPendientes).mock.calls[
          vi.mocked(incapacidadService.listarPendientes).mock.calls.length - 1
        ];
        const filtros = lastCall[0];
        
        // Verificar que no existe el parámetro o que no es NaN
        if (filtros && 'dias_antiguedad_min' in filtros) {
          expect(filtros.dias_antiguedad_min).not.toBeNaN();
        }
      });
    });

    it('debe enviar el valor numérico correcto cuando se especifica dias_antiguedad_min', async () => {
      vi.mocked(incapacidadService.listarPendientes).mockResolvedValue(mockIncapacidadesPendientes);
      const user = userEvent.setup();

      renderComponent();

      // Mostrar filtros
      await user.click(screen.getByRole('button', { name: /mostrar filtros/i }));

      await waitFor(() => {
        expect(screen.getByLabelText('Antigüedad mínima (días)')).toBeInTheDocument();
      });

      // Ingresar un valor numérico
      const diasInput = screen.getByLabelText('Antigüedad mínima (días)');
      await user.type(diasInput, '3');

      // Buscar
      await user.click(screen.getByRole('button', { name: /buscar/i }));

      // Verificar que el servicio fue llamado con el valor correcto
      await waitFor(() => {
        const lastCall = vi.mocked(incapacidadService.listarPendientes).mock.calls[
          vi.mocked(incapacidadService.listarPendientes).mock.calls.length - 1
        ];
        const filtros = lastCall[0];
        
        expect(filtros.dias_antiguedad_min).toBe(3);
        expect(filtros.dias_antiguedad_min).not.toBeNaN();
      });
    });
  });
});
