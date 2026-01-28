import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ConsultaPage } from '../ConsultaPage';
import { incapacidadService } from '@/services/incapacidadService';
import { EstadoIncapacidad, TipoIncapacidad, Prioridad } from '@/types';
import type { Incapacidad } from '@/types';

// Mocks
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    list: vi.fn(),
    getById: vi.fn(),
    consultarPublica: vi.fn(),
    radicar: vi.fn(),
    auditar: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

/**
 * Mock data - 3 incapacidades de prueba
 */
const mockIncapacidades: Incapacidad[] = [
  {
    id: '1',
    numero: 'INC-ARL-20260123-0001',
    tipo: TipoIncapacidad.ARL,
    estado: EstadoIncapacidad.APROBADA,
    prioridad: Prioridad.NORMAL,
    fecha_inicio: '2026-01-10',
    fecha_fin: '2026-01-20',
    dias_totales: 10,
    valor_total: 1500000,
    diagnostico_cie10: 'S62.0',
    diagnostico_descripcion: 'Fractura de muñeca',
    empleado: {
      id: '1',
      tipo_documento: 'CEDULA',
      numero_documento: '1234567890',
      nombres: 'Juan',
      apellidos: 'Pérez',
      email: 'juan@example.com',
      telefono: '3001234567',
      cargo: 'Operario',
      empresa_id: '1',
    },
    empresa: {
      id: '1',
      nit: '900123456',
      razon_social: 'Empresa Test SA',
      email_contacto: 'contacto@empresa.com',
    },
    created_at: '2026-01-23T10:00:00Z',
    updated_at: '2026-01-23T10:00:00Z',
  },
  {
    id: '2',
    numero: 'INC-SALUD-20260123-0002',
    tipo: TipoIncapacidad.SALUD,
    estado: EstadoIncapacidad.EN_AUDITORIA,
    prioridad: Prioridad.ALTA,
    fecha_inicio: '2026-01-15',
    fecha_fin: '2026-01-25',
    dias_totales: 10,
    valor_total: 2400000,
    diagnostico_cie10: 'J11.1',
    diagnostico_descripcion: 'Gripe',
    afiliado: {
      id: '2',
      tipo_documento: 'CEDULA',
      numero_documento: '9876543210',
      nombres: 'María',
      apellidos: 'García',
      email: 'maria@example.com',
      telefono: '3009876543',
      fecha_nacimiento: '1985-05-15',
    },
    created_at: '2026-01-23T11:00:00Z',
    updated_at: '2026-01-23T11:00:00Z',
  },
  {
    id: '3',
    numero: 'INC-ARL-20260123-0003',
    tipo: TipoIncapacidad.ARL,
    estado: EstadoIncapacidad.RECHAZADA,
    prioridad: Prioridad.BAJA,
    fecha_inicio: '2026-01-05',
    fecha_fin: '2026-01-10',
    dias_totales: 5,
    valor_total: 750000,
    diagnostico_cie10: 'M54.5',
    diagnostico_descripcion: 'Lumbalgia',
    empleado: {
      id: '3',
      tipo_documento: 'CC',
      numero_documento: '5555555555',
      nombres: 'Pedro',
      apellidos: 'López',
      email: 'pedro@example.com',
      telefono: '3005555555',
      cargo: 'Supervisor',
      empresa_id: '2',
    },
    empresa: {
      id: '2',
      nit: '900654321',
      razon_social: 'Construcciones XYZ',
      email_contacto: 'info@construccionesxyz.com',
    },
    created_at: '2026-01-23T09:00:00Z',
    updated_at: '2026-01-23T09:00:00Z',
  },
];

/**
 * Helper para renderizar el componente con providers
 */
function renderConsultaPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConsultaPage />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('ConsultaPage', () => {
  beforeEach(() => {
    // Reset mocks antes de cada test
    vi.clearAllMocks();
    // Por defecto, list devuelve las 3 incapacidades
    (incapacidadService.list as ReturnType<typeof vi.fn>).mockResolvedValue(mockIncapacidades);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Grupo 1: Renderizado inicial
   */
  describe('Renderizado inicial', () => {
    it('debe renderizar el título y descripción de la página', async () => {
      renderConsultaPage();

      expect(screen.getByText('Consulta de Incapacidades')).toBeInTheDocument();
      expect(
        screen.getByText(/Busque incapacidades por número, documento, empresa o rango de fechas/i)
      ).toBeInTheDocument();
    });

    it('debe renderizar el componente de filtros', () => {
      renderConsultaPage();

      // Verificar que existen los labels de filtros
      expect(screen.getByText('Número de Radicación')).toBeInTheDocument();
      expect(screen.getByText('Tipo')).toBeInTheDocument();
      expect(screen.getByText('Estado')).toBeInTheDocument();
      expect(screen.getByText('Documento Empleado')).toBeInTheDocument();
      expect(screen.getByText('NIT Empresa')).toBeInTheDocument();
    });

    it('debe mostrar loading state mientras carga datos', async () => {
      // Mock que nunca se resuelve para mantener loading
      (incapacidadService.list as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(() => {}) // Promise que nunca se resuelve
      );

      renderConsultaPage();

      // Buscar por el spinner en lugar del texto "Cargando..."
      // El componente DataTable muestra un <Loader2 /> cuando isLoading=true
      const loadingElement = document.querySelector('.animate-spin');
      expect(loadingElement).toBeInTheDocument();
    });
  });

  /**
   * Grupo 2: Filtros de búsqueda
   */
  describe('Filtros de búsqueda', () => {
    it('debe filtrar por número de radicación', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Buscar input de número
      const numeroInput = screen.getByLabelText(/Número de Radicación/i);
      await user.type(numeroInput, 'INC-ARL-20260123-0001');

      // Hacer clic en buscar
      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que se llama al servicio con el filtro correcto (2da llamada)
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith(
          expect.objectContaining({
            numero: 'INC-ARL-20260123-0001',
            skip: 0,
            limit: 100,
          })
        );
      }, { timeout: 3000 });
    });

    it('debe filtrar por documento de empleado', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Buscar input de documento
      const documentoInput = screen.getByLabelText(/Documento Empleado/i);
      await user.type(documentoInput, '1234567890');

      // Hacer clic en buscar
      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que se llama al servicio con el filtro correcto
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith(
          expect.objectContaining({
            empleado_documento: '1234567890',
            skip: 0,
            limit: 100,
          })
        );
      }, { timeout: 3000 });
    });

    it('debe filtrar por NIT de empresa', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Buscar input de NIT
      const nitInput = screen.getByLabelText(/NIT Empresa/i);
      await user.type(nitInput, '900123456');

      // Hacer clic en buscar
      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que se llama al servicio con el filtro correcto
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith(
          expect.objectContaining({
            empresa_nit: '900123456',
            skip: 0,
            limit: 100,
          })
        );
      }, { timeout: 3000 });
    });

    it('debe filtrar por rango de fechas', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Buscar inputs de fecha
      const fechaInicioInput = screen.getByLabelText(/Fecha Inicio/i);
      const fechaFinInput = screen.getByLabelText(/Fecha Fin/i);

      await user.type(fechaInicioInput, '2026-01-01');
      await user.type(fechaFinInput, '2026-01-31');

      // Hacer clic en buscar
      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que se llama al servicio con el filtro correcto
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith(
          expect.objectContaining({
            fecha_inicio: '2026-01-01',
            fecha_fin: '2026-01-31',
            skip: 0,
            limit: 100,
          })
        );
      }, { timeout: 3000 });
    });

    it('debe limpiar los filtros cuando se hace clic en Limpiar', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Llenar algunos filtros
      const numeroInput = screen.getByLabelText(/Número de Radicación/i);
      await user.type(numeroInput, 'INC-ARL-20260123-0001');

      // Hacer clic en limpiar
      const limpiarBtn = screen.getByRole('button', { name: /Limpiar/i });
      await user.click(limpiarBtn);

      // Verificar que se llama al servicio solo con paginación
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith({
          skip: 0,
          limit: 100,
        });
      }, { timeout: 3000 });
    });
  });

  /**
   * Grupo 3: Tabla de resultados
   */
  describe('Tabla de resultados', () => {
    it('debe mostrar los datos de incapacidades en la tabla', async () => {
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      });

      // Verificar datos de la primera incapacidad
      expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
      expect(screen.getByText('Empresa Test SA')).toBeInTheDocument();

      // Verificar datos de la segunda incapacidad
      expect(screen.getByText('INC-SALUD-20260123-0002')).toBeInTheDocument();
      expect(screen.getByText('María García')).toBeInTheDocument();

      // Verificar datos de la tercera incapacidad
      expect(screen.getByText('INC-ARL-20260123-0003')).toBeInTheDocument();
      expect(screen.getByText('Pedro López')).toBeInTheDocument();
      expect(screen.getByText('Construcciones XYZ')).toBeInTheDocument();
    });

    it('debe mostrar el contador de resultados', async () => {
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText(/Resultados \(3\)/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar mensaje cuando no hay resultados', async () => {
      // Mock sin resultados
      incapacidadService.list.mockResolvedValue([]);

      renderConsultaPage();

      // Esperar a que cargue (sin datos)
      await waitFor(() => {
        expect(screen.getByText(/No se encontraron incapacidades/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar badges de estado correctamente', async () => {
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      });

      // Verificar que aparecen los estados (como badges)
      expect(screen.getByText('APROBADA')).toBeInTheDocument();
      expect(screen.getByText('EN AUDITORIA')).toBeInTheDocument(); // El espacio se reemplaza
      expect(screen.getByText('RECHAZADA')).toBeInTheDocument();
    });
  });

  /**
   * Grupo 4: Descarga CSV
   */
  describe('Descarga CSV', () => {
    it('debe mostrar botón de descarga cuando hay datos', async () => {
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      });

      // Verificar que existe el botón de descarga
      const descargarBtn = screen.getByRole('button', { name: /Descargar CSV/i });
      expect(descargarBtn).toBeInTheDocument();
    });

    it('NO debe mostrar botón de descarga cuando no hay datos', async () => {
      // Mock sin resultados
      incapacidadService.list.mockResolvedValue([]);

      renderConsultaPage();

      // Esperar a que cargue
      await waitFor(() => {
        expect(screen.getByText(/No se encontraron incapacidades/i)).toBeInTheDocument();
      });

      // Verificar que NO existe el botón de descarga
      const descargarBtn = screen.queryByRole('button', { name: /Descargar CSV/i });
      expect(descargarBtn).not.toBeInTheDocument();
    });
  });

  /**
   * Grupo 5: Navegación a detalle
   */
  describe('Navegación a detalle', () => {
    it('debe navegar al detalle al hacer clic en el botón Ver', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      });

      // Hacer clic en el primer botón Ver
      const verButtons = screen.getAllByRole('button', { name: /Ver/i });
      await user.click(verButtons[0]);

      // Verificar que se llamó a navigate con el ID correcto
      expect(mockNavigate).toHaveBeenCalledWith('/incapacidades/1');
    });

    it('debe tener un botón Ver por cada incapacidad en la tabla', async () => {
      renderConsultaPage();

      // Esperar a que carguen los datos
      await waitFor(() => {
        expect(screen.getByText('INC-ARL-20260123-0001')).toBeInTheDocument();
      });

      // Verificar que hay 3 botones Ver (uno por incapacidad)
      const verButtons = screen.getAllByRole('button', { name: /Ver/i });
      expect(verButtons).toHaveLength(3);
    });
  });

  /**
   * Grupo 6: Integración y casos complejos
   */
  describe('Integración y casos complejos', () => {
    it('debe combinar múltiples filtros y buscar', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que se renderice la página
      await screen.findByRole('button', { name: /Buscar/i });

      // Llenar múltiples filtros
      const numeroInput = screen.getByLabelText(/Número de Radicación/i);
      const documentoInput = screen.getByLabelText(/Documento Empleado/i);

      await user.type(numeroInput, 'INC-ARL-20260123-0001');
      await user.type(documentoInput, '1234567890');

      // Hacer clic en buscar
      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que se llamó al servicio con todos los filtros
      await waitFor(() => {
        expect(incapacidadService.list).toHaveBeenCalledWith(
          expect.objectContaining({
            numero: 'INC-ARL-20260123-0001',
            empleado_documento: '1234567890',
            skip: 0,
            limit: 100,
          })
        );
      }, { timeout: 3000 });
    });

    it('debe actualizar la tabla cuando cambian los filtros', async () => {
      const user = userEvent.setup();
      renderConsultaPage();

      // Esperar a que carguen los datos iniciales (3 incapacidades)
      await waitFor(() => {
        expect(screen.getByText(/Resultados \(3\)/i)).toBeInTheDocument();
      });

      // Limpiar y mockear solo 1 resultado
      vi.clearAllMocks();
      incapacidadService.list.mockResolvedValue([mockIncapacidades[0]]);

      // Aplicar filtro
      const numeroInput = screen.getByLabelText(/Número de Radicación/i);
      await user.type(numeroInput, 'INC-ARL-20260123-0001');

      const buscarBtn = screen.getByRole('button', { name: /Buscar/i });
      await user.click(buscarBtn);

      // Verificar que la tabla se actualiza con 1 resultado
      await waitFor(() => {
        expect(screen.getByText(/Resultados \(1\)/i)).toBeInTheDocument();
      });
    });
  });
});
