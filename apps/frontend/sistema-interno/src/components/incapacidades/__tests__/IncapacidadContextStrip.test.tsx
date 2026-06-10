import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IncapacidadContextStrip } from '../IncapacidadContextStrip';

const baseIncapacidad = {
  id: 'inc-1',
  numero: 'INC-001',
  tipo: 'ARL',
  estado: 'EN_AUDITORIA',
  prioridad: 'NORMAL',
  fecha_inicio: '2026-06-01',
  fecha_fin: '2026-06-07',
  dias_totales: 7,
  diagnostico_cie10: 'M54.5',
  diagnostico_descripcion: 'Lumbalgia',
  valor_total: 350000,
  created_at: '2026-06-01T10:00:00Z',
  updated_at: '2026-06-01T10:00:00Z',
  empleado: {
    id: 'emp-1',
    tipo_documento: 'CC',
    numero_documento: '12345678',
    nombres: 'Pedro',
    apellidos: 'Promo',
    empresa_id: 'emp-co-1',
  },
  empresa: {
    id: 'co-1',
    nit: '901000999',
    razon_social: 'Empresa Test SAS',
    email_contacto: 'test@empresa.com',
  },
};

describe('IncapacidadContextStrip', () => {
  it('muestra el nombre y documento del empleado', () => {
    render(
      <IncapacidadContextStrip
        incapacidad={baseIncapacidad as any}
        hasFraudAlert={false}
      />
    );
    expect(screen.getByText(/Pedro Promo/)).toBeInTheDocument();
    expect(screen.getByText(/12345678/)).toBeInTheDocument();
  });

  it('muestra CIE-10 y días', () => {
    render(
      <IncapacidadContextStrip
        incapacidad={baseIncapacidad as any}
        hasFraudAlert={false}
      />
    );
    expect(screen.getByText(/M54\.5/)).toBeInTheDocument();
    expect(screen.getByText(/7 días/)).toBeInTheDocument();
  });

  it('muestra badge Sin ficha cuando no hay empleado en BD', () => {
    const sinEmpleado = { ...baseIncapacidad, empleado: undefined };
    render(
      <IncapacidadContextStrip
        incapacidad={sinEmpleado as any}
        hasFraudAlert={false}
        empleadoFallback={{ nombres: 'Luis Fallback', numero_documento: '99887766' }}
      />
    );
    expect(screen.getByText(/Luis Fallback/)).toBeInTheDocument();
    expect(screen.getByText('Sin ficha')).toBeInTheDocument();
  });

  it('aplica clase roja cuando hasFraudAlert es true', () => {
    const { container } = render(
      <IncapacidadContextStrip
        incapacidad={{ ...baseIncapacidad, empleado: undefined } as any}
        hasFraudAlert={true}
        empleadoFallback={{ nombres: 'Luis', numero_documento: '99887766' }}
      />
    );
    const empleadoSection = container.querySelector('[data-testid="empleado-section"]');
    expect(empleadoSection?.className).toMatch(/red/);
  });
});
