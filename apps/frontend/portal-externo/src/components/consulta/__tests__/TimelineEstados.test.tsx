/**
 * Tests para el componente TimelineEstados.
 *
 * Cobertura:
 * - Renderizado básico con historial
 * - Renderizado sin historial (vacío)
 * - Ordenamiento cronológico (más reciente primero)
 * - Iconos y badges por estado
 * - Formato de fechas
 * - Observaciones en estado PENDIENTE
 * - Descripciones de estados
 * - Líneas conectoras del timeline
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TimelineEstados } from '../TimelineEstados';
import type { HistorialEstadoSimple } from '@/types/consulta';

describe('TimelineEstados', () => {
  // ========== DATOS DE PRUEBA ==========

  const historialCompleto: HistorialEstadoSimple[] = [
    {
      estado: 'RADICADA',
      fecha_cambio: '2026-01-15T09:00:00Z',
      observaciones: null,
    },
    {
      estado: 'EN_AUDITORIA',
      fecha_cambio: '2026-01-16T10:30:00Z',
      observaciones: null,
    },
    {
      estado: 'PENDIENTE',
      fecha_cambio: '2026-01-17T14:45:00Z',
      observaciones: 'Falta firma del médico tratante en la incapacidad',
    },
    {
      estado: 'LIQUIDACION',
      fecha_cambio: '2026-01-18T11:20:00Z',
      observaciones: null,
    },
    {
      estado: 'PAGADA',
      fecha_cambio: '2026-01-19T16:00:00Z',
      observaciones: null,
    },
  ];

  const historialConUnSoloEstado: HistorialEstadoSimple[] = [
    {
      estado: 'RADICADA',
      fecha_cambio: '2026-01-15T09:00:00Z',
      observaciones: null,
    },
  ];

  const historialVacio: HistorialEstadoSimple[] = [];

  // ========== TESTS ==========

  describe('Renderizado básico', () => {
    it('debe renderizar el componente correctamente con historial', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText('Historial de Estados')).toBeInTheDocument();
      expect(screen.getByText(/Seguimiento cronológico/)).toBeInTheDocument();
    });

    it('debe mostrar el número correcto de eventos en el subtítulo', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText(/5 eventos/)).toBeInTheDocument();
    });

    it('debe mostrar "1 evento" en singular cuando hay un solo estado', () => {
      render(<TimelineEstados historial={historialConUnSoloEstado} />);

      expect(screen.getByText(/1 evento/)).toBeInTheDocument();
    });

    it('debe aplicar className personalizada al contenedor', () => {
      const { container } = render(
        <TimelineEstados historial={historialCompleto} className="custom-class" />
      );

      const card = container.querySelector('.custom-class');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Historial vacío', () => {
    it('debe mostrar mensaje cuando no hay historial', () => {
      render(<TimelineEstados historial={historialVacio} />);

      expect(screen.getByText('No hay historial de cambios disponible')).toBeInTheDocument();
    });

    it('debe mostrar icono de reloj en mensaje vacío', () => {
      const { container } = render(<TimelineEstados historial={historialVacio} />);

      // Verificar que hay múltiples iconos de Clock (título + mensaje vacío)
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });

    it('NO debe mostrar el footer informativo cuando está vacío', () => {
      render(<TimelineEstados historial={historialVacio} />);

      expect(screen.queryByText(/orden cronológico descendente/)).not.toBeInTheDocument();
    });
  });

  describe('Badges de estados', () => {
    it('debe mostrar todos los badges de estados del historial', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText('Radicada')).toBeInTheDocument();
      expect(screen.getByText('En Auditoría')).toBeInTheDocument();
      expect(screen.getByText('Pendiente de información')).toBeInTheDocument();
      expect(screen.getByText('En Liquidación')).toBeInTheDocument();
      expect(screen.getByText('Pagada')).toBeInTheDocument();
    });

    it('debe formatear correctamente los estados con guión bajo', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      // Los estados se muestran con sus etiquetas formateadas
      expect(screen.getByText('En Auditoría')).toBeInTheDocument();
      expect(screen.getByText('En Liquidación')).toBeInTheDocument();
    });

    it('debe aplicar colores correctos a los badges', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      const badgeLiquidacion = screen.getByText('En Liquidación');
      expect(badgeLiquidacion).toHaveClass('bg-indigo-100', 'text-indigo-800');
    });
  });

  describe('Fechas formateadas', () => {
    it('debe mostrar las fechas formateadas en el timeline', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      // Verificar que existen elementos con fechas (buscar por partes del texto)
      const fechaElements = screen.getAllByText((_content, element) => {
        return element?.textContent?.includes('2026') || false;
      });

      expect(fechaElements.length).toBeGreaterThan(0);
    });

    it('debe formatear fechas con hora en formato largo', () => {
      render(<TimelineEstados historial={historialConUnSoloEstado} />);

      // Verificar que existe un elemento con la fecha (usar getAllByText porque puede aparecer en múltiples lugares)
      const textosFecha = screen.getAllByText((_content, element) => {
        return element?.textContent?.includes('enero') &&
               element?.textContent?.includes('2026') || false;
      });

      expect(textosFecha.length).toBeGreaterThan(0);
    });
  });

  describe('Descripciones de estados', () => {
    it('debe mostrar la descripción de cada estado', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText(/Incapacidad recibida y en cola para revisión/)).toBeInTheDocument();
      expect(screen.getByText(/En proceso de auditoría médica/)).toBeInTheDocument();
      expect(screen.getByText(/Requiere correcciones o información adicional/)).toBeInTheDocument();
      expect(screen.getByText(/En proceso de liquidación/)).toBeInTheDocument();
      expect(screen.getByText(/Pago efectuado exitosamente/)).toBeInTheDocument();
    });

    it('debe mostrar descripción correcta para estado GLOSADA', () => {
      const historialGlosada: HistorialEstadoSimple[] = [
        {
          estado: 'GLOSADA',
          fecha_cambio: '2026-01-20T10:00:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialGlosada} />);

      expect(screen.getByText('Incapacidad glosada')).toBeInTheDocument();
    });

    it('debe mostrar descripción correcta para estado PAGADA', () => {
      const historialPagada: HistorialEstadoSimple[] = [
        {
          estado: 'PAGADA',
          fecha_cambio: '2026-01-20T15:00:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialPagada} />);

      expect(screen.getByText('Pago efectuado exitosamente')).toBeInTheDocument();
    });

    it('debe mostrar descripción correcta para estado PAGADA_PARCIAL', () => {
      const historialPagadaParcial: HistorialEstadoSimple[] = [
        {
          estado: 'PAGADA_PARCIAL',
          fecha_cambio: '2026-01-20T12:00:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialPagadaParcial} />);

      expect(screen.getByText('Pagada parcialmente')).toBeInTheDocument();
    });
  });

  describe('Observaciones en estado PENDIENTE', () => {
    it('debe mostrar observaciones cuando el estado es PENDIENTE', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText('Observaciones del auditor:')).toBeInTheDocument();
      expect(screen.getByText(/Falta firma del médico tratante/)).toBeInTheDocument();
    });

    it('debe aplicar estilos de alerta a las observaciones', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      const observacionesDiv = container.querySelector('.bg-orange-50');
      expect(observacionesDiv).toBeInTheDocument();
      expect(observacionesDiv).toHaveClass('border-orange-200');
    });

    it('NO debe mostrar observaciones para otros estados', () => {
      const historialSinObservaciones: HistorialEstadoSimple[] = [
        {
          estado: 'PAGADA',
          fecha_cambio: '2026-01-18T11:20:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialSinObservaciones} />);

      expect(screen.queryByText('Observaciones del auditor:')).not.toBeInTheDocument();
    });

    it('debe manejar estado PENDIENTE sin observaciones (null)', () => {
      const historialPendienteSinTexto: HistorialEstadoSimple[] = [
        {
          estado: 'PENDIENTE',
          fecha_cambio: '2026-01-17T14:45:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialPendienteSinTexto} />);

      // No debe mostrar el cuadro de observaciones si es null
      expect(screen.queryByText('Observaciones del auditor:')).not.toBeInTheDocument();
    });
  });

  describe('Ordenamiento cronológico', () => {
    it('debe ordenar el historial de más reciente a más antiguo', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      // El primer badge debe ser "Pagada" (el más reciente: 2026-01-19)
      const badges = screen.getAllByRole('status');
      expect(badges[0]).toHaveTextContent('Pagada');
    });

    it('debe mantener el orden correcto incluso si se pasa desordenado', () => {
      const historialDesordenado: HistorialEstadoSimple[] = [
        {
          estado: 'LIQUIDACION',
          fecha_cambio: '2026-01-18T11:20:00Z',
          observaciones: null,
        },
        {
          estado: 'RADICADA',
          fecha_cambio: '2026-01-15T09:00:00Z',
          observaciones: null,
        },
        {
          estado: 'EN_AUDITORIA',
          fecha_cambio: '2026-01-16T10:30:00Z',
          observaciones: null,
        },
      ];

      render(<TimelineEstados historial={historialDesordenado} />);

      const badges = screen.getAllByRole('status');
      // Debe estar ordenado: LIQUIDACION (más reciente) primero
      expect(badges[0]).toHaveTextContent('En Liquidación');
      expect(badges[1]).toHaveTextContent('En Auditoría');
      expect(badges[2]).toHaveTextContent('Radicada');
    });
  });

  describe('Iconos del timeline', () => {
    it('debe renderizar iconos para cada estado', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      // Cada item del timeline tiene un icono circular
      const iconos = container.querySelectorAll('.rounded-full');
      expect(iconos.length).toBe(5); // 5 estados en historialCompleto
    });

    it('debe aplicar colores de fondo a los iconos circulares', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      // Verificar que hay iconos con clases de color (historialCompleto tiene PAGADA que es emerald)
      const iconoEmerald = container.querySelector('.bg-emerald-100');
      expect(iconoEmerald).toBeInTheDocument();
    });
  });

  describe('Footer informativo', () => {
    it('debe mostrar el footer con información del ordenamiento', () => {
      render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText(/orden cronológico descendente/)).toBeInTheDocument();
      expect(screen.getByText(/más reciente primero/)).toBeInTheDocument();
    });

    it('debe mostrar el ícono de información (outline) en el footer', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      expect(screen.getByText(/orden cronológico descendente/)).toBeInTheDocument();
      expect(container.querySelector('.lucide-info')).toBeTruthy();
    });
  });

  describe('Estructura del timeline', () => {
    it('debe renderizar la estructura de lista correctamente', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      const lista = container.querySelector('ul');
      expect(lista).toBeInTheDocument();
      
      const items = container.querySelectorAll('li');
      expect(items.length).toBe(5); // 5 estados
    });

    it('debe NO mostrar línea conectora en el último item', () => {
      const { container } = render(<TimelineEstados historial={historialConUnSoloEstado} />);

      // Con un solo item, no debe haber línea conectora
      const lineasConectoras = container.querySelectorAll('.bg-gray-200');
      expect(lineasConectoras.length).toBe(0);
    });

    it('debe mostrar líneas conectoras entre items (excepto el último)', () => {
      const { container } = render(<TimelineEstados historial={historialCompleto} />);

      // Con 5 items, debe haber 4 líneas conectoras (todos excepto el último)
      const lineasConectoras = container.querySelectorAll('.bg-gray-200');
      expect(lineasConectoras.length).toBe(4);
    });
  });

  describe('Estados completos (uno por uno)', () => {
    const estadosPrueba = [
      { estado: 'RADICADA', colorClass: 'bg-blue-100 text-blue-800', label: 'Radicada' },
      { estado: 'EN_AUDITORIA', colorClass: 'bg-yellow-100 text-yellow-800', label: 'En Auditoría' },
      { estado: 'PENDIENTE', colorClass: 'bg-orange-100 text-orange-800', label: 'Pendiente de información' },
      { estado: 'CREACION_SINIESTRO', colorClass: 'bg-purple-100 text-purple-800', label: 'En creación de siniestro' },
      { estado: 'LIQUIDACION', colorClass: 'bg-indigo-100 text-indigo-800', label: 'En Liquidación' },
      { estado: 'LIQUIDACION_PARCIAL', colorClass: 'bg-indigo-100 text-indigo-800', label: 'En Liquidación Parcial' },
      { estado: 'GLOSADA', colorClass: 'bg-red-100 text-red-800', label: 'Glosada' },
      { estado: 'PAGADA', colorClass: 'bg-emerald-100 text-emerald-800', label: 'Pagada' },
      { estado: 'PAGADA_PARCIAL', colorClass: 'bg-emerald-100 text-emerald-800', label: 'Pagada Parcialmente' },
    ] as const;

    estadosPrueba.forEach(({ estado, colorClass, label }) => {
      it(`debe renderizar correctamente estado ${estado}`, () => {
        const historial: HistorialEstadoSimple[] = [
          {
            estado: estado as any,
            fecha_cambio: '2026-01-20T10:00:00Z',
            observaciones: null,
          },
        ];

        render(<TimelineEstados historial={historial} />);

        const badge = screen.getByText(label);
        expect(badge).toHaveClass(colorClass);
      });
    });
  });
});
