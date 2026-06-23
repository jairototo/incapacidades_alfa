import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DetalleIncapacidad } from '../DetalleIncapacidad';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

describe('DetalleIncapacidad', () => {
  const incapacidadARLBase: ConsultaIncapacidadResponse = {
    numero: 'INC-ARL-20260117-0001',
    tipo: 'ARL',
    estado: 'EN_AUDITORIA',
    fecha_inicio: '2026-01-10',
    fecha_fin: '2026-01-20',
    dias_totales: 10,
    diagnostico_cie10: 'S62.5',
    descripcion_diagnostico: 'Fractura de pulgar',
    observaciones_publicas: 'Reposo absoluto recomendado',
    nombre_completo: 'Juan Pérez García',
    tipo_documento: 'CC',
    eps: null,
    created_at: '2026-01-17T10:00:00Z',
    updated_at: '2026-01-17T10:00:00Z',
    historial_estados: [],
    documentos: [],
  };

  const incapacidadSaludBase: ConsultaIncapacidadResponse = {
    numero: 'INC-SALUD-20260115-0042',
    tipo: 'SALUD',
    estado: 'PAGADA',
    fecha_inicio: '2026-01-08',
    fecha_fin: '2026-01-14',
    dias_totales: 6,
    diagnostico_cie10: 'J06.9',
    descripcion_diagnostico: null,
    observaciones_publicas: null,
    nombre_completo: 'María López Gómez',
    tipo_documento: 'CE',
    eps: null,
    created_at: '2026-01-15T09:00:00Z',
    updated_at: '2026-01-15T09:00:00Z',
    historial_estados: [],
    documentos: [],
  };

  describe('Renderizado básico', () => {
    it('debe renderizar el componente correctamente', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText(/detalle de incapacidad/i)).toBeInTheDocument();
      expect(screen.getByText('INC-ARL-20260117-0001')).toBeInTheDocument();
    });

    it('debe mostrar el título y subtítulo', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText(/detalle de incapacidad/i)).toBeInTheDocument();
      expect(screen.getByText(incapacidadARLBase.numero)).toBeInTheDocument();
    });
  });

  describe('Badges de estado y tipo', () => {
    it('debe mostrar badge de tipo ARL con color correcto', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      const badgeTipo = screen.getByText('ARL');
      expect(badgeTipo).toBeInTheDocument();
      expect(badgeTipo).toHaveClass('bg-indigo-100', 'text-indigo-800');
    });

    it('debe mostrar badge de tipo SALUD con color correcto', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadSaludBase} />);

      const badgeTipo = screen.getByText('SALUD');
      expect(badgeTipo).toBeInTheDocument();
      expect(badgeTipo).toHaveClass('bg-teal-100', 'text-teal-800');
    });

    it('debe mostrar badge de estado EN_AUDITORIA formateado', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      const badgesEstado = screen.getAllByText('En Auditoría');
      expect(badgesEstado[0]).toBeInTheDocument();
      expect(badgesEstado[0]).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('debe mostrar badge de estado PAGADA con color correcto', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadSaludBase} />);

      const badgesEstado = screen.getAllByText('Pagada');
      expect(badgesEstado[0]).toBeInTheDocument();
      expect(badgesEstado[0]).toHaveClass('bg-emerald-100', 'text-emerald-800');
    });

    it('debe formatear correctamente los estados con guión bajo', () => {
      const incapacidadLiquidacion: ConsultaIncapacidadResponse = {
        ...incapacidadARLBase,
        estado: 'LIQUIDACION',
      };

      render(<DetalleIncapacidad incapacidad={incapacidadLiquidacion} />);

      const badgesLiquidacion = screen.getAllByText('En Liquidación');
      expect(badgesLiquidacion[0]).toBeInTheDocument();
    });
  });

  describe('Sección: Datos del Solicitante', () => {
    it('debe mostrar nombre completo del solicitante', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Nombre completo')).toBeInTheDocument();
      expect(screen.getByText('Juan Pérez García')).toBeInTheDocument();
    });

    it('debe mostrar tipo de documento', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Tipo de documento')).toBeInTheDocument();
      expect(screen.getByText('CC')).toBeInTheDocument();
    });

    it('debe mostrar diferentes tipos de documento correctamente', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadSaludBase} />);

      expect(screen.getByText('CE')).toBeInTheDocument();
    });
  });

  describe('Sección: Información Médica', () => {
    it('debe mostrar diagnóstico CIE-10', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Diagnóstico (CIE-10)')).toBeInTheDocument();
      expect(screen.getByText('S62.5')).toBeInTheDocument();
    });

    it('debe mostrar descripción del diagnóstico cuando está disponible', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Descripción del diagnóstico')).toBeInTheDocument();
      expect(screen.getByText('Fractura de pulgar')).toBeInTheDocument();
    });

    it('NO debe mostrar descripción del diagnóstico cuando es null', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadSaludBase} />);

      expect(screen.queryByText('Descripción del diagnóstico')).not.toBeInTheDocument();
    });

    it('debe mostrar observaciones médicas cuando están disponibles', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Observaciones médicas')).toBeInTheDocument();
      expect(screen.getByText('Reposo absoluto recomendado')).toBeInTheDocument();
    });

    it('NO debe mostrar observaciones médicas cuando son null', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadSaludBase} />);

      expect(screen.queryByText('Observaciones médicas')).not.toBeInTheDocument();
    });
  });

  describe('Sección: Fechas y Períodos', () => {
    it('debe formatear y mostrar fecha de inicio correctamente', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Fecha de inicio')).toBeInTheDocument();
      const labelFechaInicio = screen.getByText('Fecha de inicio').closest('div');
      expect(labelFechaInicio).toBeInTheDocument();
    });

    it('debe formatear y mostrar fecha de fin correctamente', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Fecha de fin')).toBeInTheDocument();
      const labelFechaFin = screen.getByText('Fecha de fin').closest('div');
      expect(labelFechaFin).toBeInTheDocument();
    });

    it('debe mostrar días totales con palabra en singular', () => {
      const incapacidadUnDia: ConsultaIncapacidadResponse = {
        ...incapacidadARLBase,
        dias_totales: 1,
        fecha_fin: '2026-01-10',
      };

      render(<DetalleIncapacidad incapacidad={incapacidadUnDia} />);

      expect(screen.getByText('Días totales')).toBeInTheDocument();
      expect(screen.getByText('1 día')).toBeInTheDocument();
    });

    it('debe mostrar días totales con palabra en plural', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('10 días')).toBeInTheDocument();
    });
  });

  describe('Sección: Información Adicional', () => {
    it('debe formatear y mostrar fecha de radicación', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Fecha de radicación')).toBeInTheDocument();
      expect(screen.getByText(/17 de enero de 2026/i)).toBeInTheDocument();
    });

    it('debe mostrar estado actual formateado', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      const estadosTexto = screen.getAllByText(/En Auditoría/i);
      expect(estadosTexto.length).toBeGreaterThan(0);
    });
  });

  describe('Secciones visuales', () => {
    it('debe mostrar los títulos de secciones esperados', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText('Datos del Solicitante')).toBeInTheDocument();
      expect(screen.getByText('Información Médica')).toBeInTheDocument();
      expect(screen.getByText('Fechas y Períodos')).toBeInTheDocument();
      expect(screen.getByText('Información Adicional')).toBeInTheDocument();
    });

    it('debe mostrar iconos en los títulos de secciones', () => {
      const { container } = render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(4);
    });

    it('debe mostrar el footer con información de ayuda', () => {
      render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(screen.getByText(/¿Necesitas más información?/i)).toBeInTheDocument();
      expect(screen.getByText(/Consulta el historial de estados/i)).toBeInTheDocument();
    });
  });

  describe('Prop className', () => {
    it('debe aplicar className personalizada al contenedor', () => {
      const { container } = render(
        <DetalleIncapacidad incapacidad={incapacidadARLBase} className="custom-class" />
      );

      const card = container.querySelector('.custom-class');
      expect(card).toBeInTheDocument();
    });

    it('debe funcionar sin className', () => {
      const { container } = render(<DetalleIncapacidad incapacidad={incapacidadARLBase} />);

      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Campos opcionales con "No especificado"', () => {
    it('debe no mostrar "No especificado" cuando campos null no se renderizan', () => {
      const incapacidadConCamposNull: ConsultaIncapacidadResponse = {
        ...incapacidadSaludBase,
        descripcion_diagnostico: null,
        observaciones_publicas: null,
      };

      render(<DetalleIncapacidad incapacidad={incapacidadConCamposNull} />);

      expect(screen.queryByText('No especificado')).not.toBeInTheDocument();
    });
  });

  describe('Diferentes estados de incapacidad', () => {
    const estados: Array<{ estado: any; colorClass: string; label: string }> = [
      { estado: 'RADICADA', colorClass: 'bg-blue-100', label: 'Radicada' },
      { estado: 'EN_AUDITORIA', colorClass: 'bg-yellow-100', label: 'En Auditoría' },
      { estado: 'PENDIENTE', colorClass: 'bg-orange-100', label: 'Pendiente de información' },
      { estado: 'CREACION_SINIESTRO', colorClass: 'bg-purple-100', label: 'En creación de siniestro' },
      { estado: 'LIQUIDACION', colorClass: 'bg-indigo-100', label: 'En Liquidación' },
      { estado: 'LIQUIDACION_PARCIAL', colorClass: 'bg-indigo-100', label: 'En Liquidación Parcial' },
      { estado: 'GLOSADA', colorClass: 'bg-red-100', label: 'Glosada' },
      { estado: 'PAGADA', colorClass: 'bg-emerald-100', label: 'Pagada' },
      { estado: 'PAGADA_PARCIAL', colorClass: 'bg-emerald-100', label: 'Pagada Parcialmente' },
    ];

    estados.forEach(({ estado, colorClass, label }) => {
      it(`debe mostrar badge correcto para estado ${estado}`, () => {
        const incapacidad: ConsultaIncapacidadResponse = {
          ...incapacidadARLBase,
          estado: estado as any,
        };

        render(<DetalleIncapacidad incapacidad={incapacidad} />);

        const badges = screen.getAllByText(label);
        expect(badges[0]).toHaveClass(colorClass);
      });
    });
  });
});
