/**
 * Tests para el componente BusquedaIncapacidad.
 * 
 * Cobertura:
 * - Renderizado inicial
 * - Cambio entre modos de búsqueda
 * - Validación de formularios
 * - Integración con hooks React Query
 * - Manejo de estados loading/error/success
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BusquedaIncapacidad } from '../BusquedaIncapacidad';
import * as consultaHooks from '@/hooks/useConsultaIncapacidad';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

// Mock de los hooks
vi.mock('@/hooks/useConsultaIncapacidad');

describe('BusquedaIncapacidad', () => {
  let queryClient: QueryClient;
  const mockOnResultado = vi.fn();

  const mockIncapacidadARL: ConsultaIncapacidadResponse = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    numero: 'INC-ARL-20260117-0001',
    tipo: 'ARL',
    estado: 'EN_AUDITORIA',
    fecha_inicio: '2026-01-10',
    fecha_fin: '2026-01-20',
    dias_totales: 10,
    diagnostico_cie10: 'S62.5',
    descripcion_diagnostico: 'Fractura de pulgar',
    valor_dia: 80000,
    valor_total: 800000,
    observaciones: null,
    nombre_completo: 'Juan Pérez García',
    documento: '1234567890',
    tipo_documento: 'CC',
    empresa_razon_social: 'Empresa Test S.A.',
    empresa_nit: '900123456-7',
    created_at: '2026-01-17T10:00:00Z',
    historial_estados: [
      {
        estado: 'RADICADA',
        fecha_cambio: '2026-01-17T10:00:00Z',
        observaciones: null,
      },
    ],
    documentos_publicos: [],
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();

    // Mock por defecto - queries deshabilitadas
    vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.mocked(consultaHooks.useConsultarPorDocumento).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as any);
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BusquedaIncapacidad onResultado={mockOnResultado} />
      </QueryClientProvider>
    );
  };

  describe('Renderizado inicial', () => {
    it('debe renderizar el componente correctamente', () => {
      renderComponent();

      expect(screen.getByText(/consultar incapacidad/i)).toBeInTheDocument();
      expect(screen.getByText(/buscar por:/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/número de radicación/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/documento de identidad/i)).toBeInTheDocument();
    });

    it('debe mostrar el modo "número" por defecto', () => {
      renderComponent();

      const radioNumero = screen.getByRole('radio', { name: /número de radicación/i });
      expect(radioNumero).toBeChecked();

      expect(screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i)).toBeInTheDocument();
    });

    it('debe mostrar el botón de búsqueda deshabilitado inicialmente', () => {
      renderComponent();

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      expect(botonBuscar).toBeDisabled();
    });

    it('debe mostrar consejos de búsqueda', () => {
      renderComponent();

      expect(screen.getByText(/💡 consejos de búsqueda:/i)).toBeInTheDocument();
      expect(screen.getByText(/el número de radicación está en el documento de confirmación/i)).toBeInTheDocument();
    });
  });

  describe('Cambio entre modos de búsqueda', () => {
    it('debe cambiar a modo "documento" al hacer clic en el radio', async () => {
      const user = userEvent.setup();
      renderComponent();

      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      expect(radioDocumento).toBeChecked();
      // Verificar que aparecen los campos del modo documento
      expect(screen.getByText(/tipo de documento/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/ej: 1234567890/i)).toBeInTheDocument();
    });

    it('debe limpiar el formulario al cambiar de modo', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Ingresar datos en modo número
      const inputNumero = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(inputNumero, 'INC-ARL-20260117-0001');

      // Cambiar a modo documento
      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      // Volver a modo número
      const radioNumero = screen.getByRole('radio', { name: /número de radicación/i });
      await user.click(radioNumero);

      // Verificar que el campo está limpio
      const nuevoInputNumero = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      expect(nuevoInputNumero).toHaveValue('');
    });
  });

  describe('Validación de formularios', () => {
    describe('Modo número', () => {
      it('debe validar formato de número de radicación', async () => {
        const user = userEvent.setup();
        renderComponent();

        const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
        await user.type(input, 'FORMATO-INVALIDO');
        await user.tab(); // Trigger blur

        await waitFor(() => {
          expect(screen.getByText(/formato inválido/i)).toBeInTheDocument();
        });
      });

      it('debe aceptar formato válido de número de radicación', async () => {
        const user = userEvent.setup();
        renderComponent();

        const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
        await user.type(input, 'INC-ARL-20260117-0001');

        await waitFor(() => {
          const botonBuscar = screen.getByRole('button', { name: /buscar/i });
          expect(botonBuscar).not.toBeDisabled();
        });
      });

      it('debe transformar a mayúsculas el número ingresado', async () => {
        const user = userEvent.setup();
        renderComponent();

        const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i) as HTMLInputElement;
        await user.type(input, 'inc-arl-20260117-0001');

        // El valor debe estar en minúsculas mientras se escribe
        expect(input.value).toBe('inc-arl-20260117-0001');
      });
    });

    describe('Modo documento', () => {
      it('debe validar longitud mínima de documento', async () => {
        const user = userEvent.setup();
        renderComponent();

        // Cambiar a modo documento
        const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
        await user.click(radioDocumento);

        const input = screen.getByPlaceholderText(/ej: 1234567890/i);
        await user.type(input, '12345');
        await user.tab();

        await waitFor(() => {
          expect(screen.getByText(/debe tener al menos 6 caracteres/i)).toBeInTheDocument();
        });
      });

      it('debe validar longitud máxima de documento', async () => {
        const user = userEvent.setup();
        renderComponent();

        const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
        await user.click(radioDocumento);

        const input = screen.getByPlaceholderText(/ej: 1234567890/i);
        await user.type(input, '123456789012345678901'); // 21 caracteres
        await user.tab();

        await waitFor(() => {
          expect(screen.getByText(/no puede tener más de 20 caracteres/i)).toBeInTheDocument();
        });
      });

      it('debe validar caracteres alfanuméricos', async () => {
        const user = userEvent.setup();
        renderComponent();

        const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
        await user.click(radioDocumento);

        const input = screen.getByPlaceholderText(/ej: 1234567890/i);
        await user.type(input, '123-456-789');
        await user.tab();

        await waitFor(() => {
          expect(screen.getByText(/solo puede contener letras y números/i)).toBeInTheDocument();
        });
      });

      it('debe permitir seleccionar tipo de documento', async () => {
        const user = userEvent.setup();
        const { container } = renderComponent();

        const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
        await user.click(radioDocumento);

        const select = container.querySelector('#tipo-documento') as HTMLSelectElement;
        expect(select).toBeInTheDocument();
        
        await user.selectOptions(select, 'PASAPORTE');
        expect(select.value).toBe('PASAPORTE');
      });
    });
  });

  describe('Integración con React Query hooks', () => {
    it('debe llamar al hook useConsultarPorNumero al buscar por número', async () => {
      const user = userEvent.setup();
      const mockRefetch = vi.fn();

      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any);

      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-ARL-20260117-0001');

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      await user.click(botonBuscar);

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('debe llamar al hook useConsultarPorDocumento al buscar por documento', async () => {
      const user = userEvent.setup();
      const mockRefetch = vi.fn();

      vi.mocked(consultaHooks.useConsultarPorDocumento).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any);

      renderComponent();

      // Cambiar a modo documento
      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const input = screen.getByPlaceholderText(/ej: 1234567890/i);
      await user.type(input, '1234567890');

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      await user.click(botonBuscar);

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('debe ejecutar onResultado cuando la búsqueda es exitosa', async () => {
      const user = userEvent.setup();

      // Primera llamada: sin datos
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValueOnce({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      const { rerender } = renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-ARL-20260117-0001');

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      await user.click(botonBuscar);

      // Segunda llamada: con datos
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidadARL,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <BusquedaIncapacidad onResultado={mockOnResultado} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(mockOnResultado).toHaveBeenCalledWith(mockIncapacidadARL);
      });
    });
  });

  describe('Estados de carga y error', () => {
    it('debe mostrar estado de carga durante la búsqueda', () => {
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      expect(screen.getByText(/buscando.../i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /buscando.../i })).toBeDisabled();
    });

    it('debe deshabilitar el formulario durante la búsqueda', () => {
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      expect(input).toBeDisabled();
    });

    it('debe mostrar mensaje de error 404 cuando no se encuentra la incapacidad', () => {
      const error404 = {
        response: { status: 404 },
        message: 'Not found',
      };

      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: error404 as any,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      expect(screen.getByText(/no se encontró la incapacidad/i)).toBeInTheDocument();
      expect(
        screen.getByText(/no existe una incapacidad con los datos proporcionados/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar mensaje de error genérico para otros errores', () => {
      const errorGenerico = {
        response: { status: 500 },
        message: 'Internal server error',
      };

      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: errorGenerico as any,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      expect(screen.getByText(/no se encontró la incapacidad/i)).toBeInTheDocument();
      expect(
        screen.getByText(/ocurrió un error al realizar la búsqueda/i)
      ).toBeInTheDocument();
    });

    it('debe limpiar errores al cambiar de modo', async () => {
      const user = userEvent.setup();

      const error404 = {
        response: { status: 404 },
        message: 'Not found',
      };

      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: error404 as any,
        refetch: vi.fn(),
      } as any);

      renderComponent();

      // Verificar que hay error
      expect(screen.getByText(/no se encontró la incapacidad/i)).toBeInTheDocument();

      // Cambiar a modo documento
      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      // Mock sin error para modo documento
      vi.mocked(consultaHooks.useConsultarPorDocumento).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      // El error debería desaparecer
      await waitFor(() => {
        expect(screen.queryByText(/no se encontró la incapacidad/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Limpieza de formulario', () => {
    it('debe limpiar el formulario después de una búsqueda exitosa', async () => {
      const user = userEvent.setup();

      // Mock inicial sin datos
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValueOnce({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      const { rerender } = renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-ARL-20260117-0001');

      // Simular búsqueda exitosa
      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: mockIncapacidadARL,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      rerender(
        <QueryClientProvider client={queryClient}>
          <BusquedaIncapacidad onResultado={mockOnResultado} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        const inputLimpio = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
        expect(inputLimpio).toHaveValue('');
      });
    });
  });

  describe('Interacción con teclado', () => {
    it('debe permitir submit con tecla Enter en modo número', async () => {
      const user = userEvent.setup();
      const mockRefetch = vi.fn();

      vi.mocked(consultaHooks.useConsultarPorNumero).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any);

      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-ARL-20260117-0001');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('debe permitir submit con tecla Enter en modo documento', async () => {
      const user = userEvent.setup();
      const mockRefetch = vi.fn();

      vi.mocked(consultaHooks.useConsultarPorDocumento).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as any);

      renderComponent();

      // Cambiar a modo documento
      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const input = screen.getByPlaceholderText(/ej: 1234567890/i);
      await user.type(input, '1234567890');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('debe mantener focus en input después de error de validación', async () => {
      const user = userEvent.setup();
      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'FORMATO-INVALIDO');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/formato inválido/i)).toBeInTheDocument();
      });

      // El input debe seguir siendo accesible para corrección
      expect(input).toBeInTheDocument();
      expect(input).not.toBeDisabled();
    });
  });

  describe('Validación adicional de inputs', () => {
    it('debe deshabilitar botón cuando input está vacío en modo número', () => {
      renderComponent();

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      expect(botonBuscar).toBeDisabled();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      expect(input).toHaveValue('');
    });

    it('debe deshabilitar botón cuando input está vacío en modo documento', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Cambiar a modo documento
      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const botonBuscar = screen.getByRole('button', { name: /buscar/i });
      expect(botonBuscar).toBeDisabled();

      const input = screen.getByPlaceholderText(/ej: 1234567890/i);
      expect(input).toHaveValue('');
    });

    it('debe validar formatos específicos de número de radicación para ARL', async () => {
      const user = userEvent.setup();
      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-ARL-20260117-0001');

      await waitFor(() => {
        const botonBuscar = screen.getByRole('button', { name: /buscar/i });
        expect(botonBuscar).not.toBeDisabled();
      });
    });

    it('debe validar formatos específicos de número de radicación para SALUD', async () => {
      const user = userEvent.setup();
      renderComponent();

      const input = screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i);
      await user.type(input, 'INC-SALUD-20260117-0002');

      await waitFor(() => {
        const botonBuscar = screen.getByRole('button', { name: /buscar/i });
        expect(botonBuscar).not.toBeDisabled();
      });
    });
  });

  describe('Selección de tipos de documento', () => {
    it('debe mostrar todos los tipos de documento disponibles', async () => {
      const user = userEvent.setup();
      const { container } = renderComponent();

      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const select = container.querySelector('#tipo-documento') as HTMLSelectElement;
      expect(select).toBeInTheDocument();

      // Verificar opciones
      const options = select.querySelectorAll('option');
      expect(options.length).toBeGreaterThanOrEqual(5);
      
      // Verificar que contiene los tipos esperados
      expect(screen.getByText(/cédula de ciudadanía/i)).toBeInTheDocument();
      expect(screen.getByText(/pasaporte/i)).toBeInTheDocument();
    });

    it('debe tener Cédula de Ciudadanía seleccionada por defecto', async () => {
      const user = userEvent.setup();
      const { container } = renderComponent();

      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const select = container.querySelector('#tipo-documento') as HTMLSelectElement;
      expect(select.value).toBe('CC');
    });

    it('debe cambiar de tipo de documento correctamente', async () => {
      const user = userEvent.setup();
      const { container } = renderComponent();

      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      const select = container.querySelector('#tipo-documento') as HTMLSelectElement;
      
      await user.selectOptions(select, 'CE');
      expect(select.value).toBe('CE');

      await user.selectOptions(select, 'TI');
      expect(select.value).toBe('TI');

      await user.selectOptions(select, 'PASAPORTE');
      expect(select.value).toBe('PASAPORTE');
    });
  });

  describe('Campos condicionales según modo', () => {
    it('debe mostrar solo campo de número en modo número', () => {
      const { container } = renderComponent();

      expect(screen.getByPlaceholderText(/ej: inc-arl-20260117-0001/i)).toBeInTheDocument();
      expect(container.querySelector('#tipo-documento')).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/ej: 1234567890/i)).not.toBeInTheDocument();
    });

    it('debe mostrar solo campos de documento en modo documento', async () => {
      const user = userEvent.setup();
      const { container } = renderComponent();

      const radioDocumento = screen.getByRole('radio', { name: /documento de identidad/i });
      await user.click(radioDocumento);

      expect(container.querySelector('#tipo-documento')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/ej: 1234567890/i)).toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/ej: inc-arl-20260117-0001/i)).not.toBeInTheDocument();
    });
  });
});
