/**
 * Tests para el componente DocumentosDescargables.
 * 
 * Cobertura:
 * - Renderizado básico con documentos
 * - Renderizado sin documentos (vacío)
 * - Iconos y etiquetas por tipo de documento
 * - Información de documentos (nombre, tamaño, fecha)
 * - Botón de descarga y estados (normal, loading, error)
 * - Interacción con mutation de descarga
 * - Props className
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentosDescargables } from '../DocumentosDescargables';
import type { DocumentoPublico } from '@/types/consulta';
import * as hooks from '@/hooks/useConsultaIncapacidad';

// Mock del hook de descarga
vi.mock('@/hooks/useConsultaIncapacidad', () => ({
  useDescargarDocumento: vi.fn(),
}));

// Mock de window.open
global.window.open = vi.fn();

describe('DocumentosDescargables', () => {
  // ========== SETUP ==========

  const createQueryClient = () =>
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

  const renderWithClient = (ui: React.ReactElement) => {
    const queryClient = createQueryClient();
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  // ========== DATOS DE PRUEBA ==========

  const documentosCompletos: DocumentoPublico[] = [
    {
      id: 'doc-001',
      nombre_archivo: 'incapacidad_medica.pdf',
      tipo_documento: 'INCAPACIDAD_MEDICA',
      tamanio_kb: 250,
      fecha_upload: '2026-01-15T10:00:00Z',
    },
    {
      id: 'doc-002',
      nombre_archivo: 'cedula_frente.jpg',
      tipo_documento: 'CEDULA',
      tamanio_kb: 150,
      fecha_upload: '2026-01-15T10:05:00Z',
    },
    {
      id: 'doc-003',
      nombre_archivo: 'historia_clinica.pdf',
      tipo_documento: 'HISTORIA_CLINICA',
      tamanio_kb: 1024,
      fecha_upload: '2026-01-15T10:10:00Z',
    },
  ];

  const documentoSingle: DocumentoPublico[] = [
    {
      id: 'doc-001',
      nombre_archivo: 'incapacidad_medica.pdf',
      tipo_documento: 'INCAPACIDAD_MEDICA',
      tamanio_kb: 250,
      fecha_upload: '2026-01-15T10:00:00Z',
    },
  ];

  const documentosVacio: DocumentoPublico[] = [];

  const mockMutate = vi.fn();
  const defaultMockHook = {
    mutate: mockMutate,
    isPending: false,
    error: null,
    data: undefined,
    isError: false,
    isSuccess: false,
    reset: vi.fn(),
    mutateAsync: vi.fn(),
    variables: undefined,
    context: undefined,
    failureCount: 0,
    failureReason: null,
    isIdle: true,
    status: 'idle' as const,
    submittedAt: 0,
  };

  // ========== TESTS ==========

  describe('Renderizado básico', () => {
    it('debe renderizar el componente correctamente con documentos', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('Documentos Adjuntos')).toBeInTheDocument();
      expect(screen.getByText(/documentos disponibles para descarga/)).toBeInTheDocument();
    });

    it('debe mostrar el número correcto de documentos en el subtítulo', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText(/3 documentos disponibles/)).toBeInTheDocument();
    });

    it('debe mostrar "1 documento disponible" en singular', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText(/1 documento disponible/)).toBeInTheDocument();
    });

    it('debe aplicar className personalizada al contenedor', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
          className="custom-class"
        />
      );

      const card = container.querySelector('.custom-class');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Lista vacía', () => {
    it('debe mostrar mensaje cuando no hay documentos', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosVacio}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('No hay documentos adjuntos disponibles')).toBeInTheDocument();
    });

    it('debe mostrar icono de archivo en mensaje vacío', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentosVacio}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      // Verificar que hay iconos SVG
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });

    it('NO debe mostrar el footer informativo cuando está vacío', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosVacio}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.queryByText(/expiran en 15 minutos/)).not.toBeInTheDocument();
    });
  });

  describe('Información de documentos', () => {
    it('debe mostrar nombres de archivos', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('incapacidad_medica.pdf')).toBeInTheDocument();
      expect(screen.getByText('cedula_frente.jpg')).toBeInTheDocument();
      expect(screen.getByText('historia_clinica.pdf')).toBeInTheDocument();
    });

    it('debe mostrar etiquetas de tipo de documento', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('Incapacidad Médica')).toBeInTheDocument();
      expect(screen.getByText('Cédula de Identidad')).toBeInTheDocument();
      expect(screen.getByText('Historia Clínica')).toBeInTheDocument();
    });

    it('debe formatear y mostrar tamaños de archivo', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('250 KB')).toBeInTheDocument();
      expect(screen.getByText('150 KB')).toBeInTheDocument();
      expect(screen.getByText('1.0 MB')).toBeInTheDocument();
    });

    it('debe mostrar fechas de carga formateadas', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      // Verificar que existe texto con "Cargado el" (puede haber múltiples)
      const textosCargado = screen.queryAllByText(/Cargado el/);
      expect(textosCargado.length).toBeGreaterThan(0);
    });
  });

  describe('Iconos por tipo de documento', () => {
    it('debe renderizar iconos para cada documento', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      // Verificar que hay múltiples iconos (uno por documento + título + footer)
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(3);
    });

    it('debe aplicar colores de fondo a los iconos según el tipo', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      // Verificar que hay elementos con clases de color (bg-blue-50, bg-purple-50, etc.)
      const iconoAzul = container.querySelector('.bg-blue-50');
      expect(iconoAzul).toBeInTheDocument();
    });
  });

  describe('Botones de descarga', () => {
    it('debe mostrar botón de descarga para cada documento', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const botones = screen.getAllByRole('button', { name: /Descargar/ });
      expect(botones).toHaveLength(3);
    });

    it('debe llamar a mutate con los parámetros correctos al hacer click', async () => {
      const user = userEvent.setup();
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const boton = screen.getByRole('button', { name: /Descargar/ });
      await user.click(boton);

      expect(mockMutate).toHaveBeenCalledWith(
        {
          numero: 'INC-ARL-20260117-0001',
          documentoId: 'doc-001',
        },
        expect.any(Object)
      );
    });

    it('debe mostrar estado de loading mientras descarga', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue({
        ...defaultMockHook,
        isPending: true,
      });

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('Generando...')).toBeInTheDocument();
      const boton = screen.getByRole('button', { name: /Generando/ });
      expect(boton).toBeDisabled();
    });

    it('debe deshabilitar el botón mientras está en loading', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue({
        ...defaultMockHook,
        isPending: true,
      });

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const boton = screen.getByRole('button');
      expect(boton).toBeDisabled();
    });

    it('debe mostrar mensaje de error cuando falla la descarga', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue({
        ...defaultMockHook,
        error: new Error('Network error'),
        isError: true,
      });

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText('Error al generar descarga')).toBeInTheDocument();
    });

    it('debe abrir URL en nueva pestaña en onSuccess', async () => {
      const user = userEvent.setup();
      const mockMutateWithSuccess = vi.fn((params, options) => {
        // Simular éxito inmediato
        options?.onSuccess?.({
          url: 'https://ejemplo.com/archivo.pdf',
          nombre_archivo: 'archivo.pdf',
          expires_at: '2026-01-21T12:00:00Z',
        });
      });

      vi.mocked(hooks.useDescargarDocumento).mockReturnValue({
        ...defaultMockHook,
        mutate: mockMutateWithSuccess,
      });

      renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const boton = screen.getByRole('button', { name: /Descargar/ });
      await user.click(boton);

      expect(window.open).toHaveBeenCalledWith(
        'https://ejemplo.com/archivo.pdf',
        '_blank'
      );
    });
  });

  describe('Footer informativo', () => {
    it('debe mostrar el footer con información de expiración', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      expect(screen.getByText(/expiran en 15 minutos/)).toBeInTheDocument();
    });

    it('debe mostrar emoji de información en el footer', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const footerText = screen.getByText(/expiran en 15 minutos/);
      expect(footerText.textContent).toContain('ℹ️');
    });
  });

  describe('Tipos de documento completos', () => {
    const tiposDocumento = [
      { tipo: 'INCAPACIDAD_MEDICA', label: 'Incapacidad Médica' },
      { tipo: 'CEDULA', label: 'Cédula de Identidad' },
      { tipo: 'HISTORIA_CLINICA', label: 'Historia Clínica' },
      { tipo: 'SOPORTE_PAGO', label: 'Soporte de Pago' },
      { tipo: 'OTROS', label: 'Otros Documentos' },
    ] as const;

    tiposDocumento.forEach(({ tipo, label }) => {
      it(`debe renderizar correctamente documento tipo ${tipo}`, () => {
        vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

        const documentos: DocumentoPublico[] = [
          {
            id: 'doc-test',
            nombre_archivo: 'archivo_test.pdf',
            tipo_documento: tipo as any,
            tamanio_kb: 100,
            fecha_upload: '2026-01-15T10:00:00Z',
          },
        ];

        renderWithClient(
          <DocumentosDescargables
            documentos={documentos}
            numeroIncapacidad="INC-ARL-20260117-0001"
          />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });
  });

  describe('Estructura del componente', () => {
    it('debe renderizar la lista de documentos correctamente', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentosCompletos}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      // Verificar que hay 3 items de documento (divs con border rounded-lg)
      // Nota: incluye el Card contenedor, así que son 4 elementos total
      const items = container.querySelectorAll('.border.rounded-lg');
      expect(items.length).toBeGreaterThanOrEqual(3);
    });

    it('debe aplicar hover effect a los items', () => {
      vi.mocked(hooks.useDescargarDocumento).mockReturnValue(defaultMockHook);

      const { container } = renderWithClient(
        <DocumentosDescargables
          documentos={documentoSingle}
          numeroIncapacidad="INC-ARL-20260117-0001"
        />
      );

      const item = container.querySelector('.hover\\:bg-gray-50');
      expect(item).toBeInTheDocument();
    });
  });
});
