import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StateDescriptionPanel } from '../StateDescriptionPanel';
import type { ValidationIssue } from '@/types/incapacidad';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ALL_STATES = [
  'RADICADA',
  'EN_AUDITORIA',
  'PENDIENTE',
  'CREACION_SINIESTRO',
  'LIQUIDACION',
  'LIQUIDACION_PARCIAL',
  'GLOSADA',
  'PAGADA',
  'PAGADA_PARCIAL',
] as const;

function makeIssue(overrides: Partial<ValidationIssue> = {}): ValidationIssue {
  return {
    id: 'issue-1',
    pre_incapacidad_id: 'pre-1',
    incapacidad_id: 'inc-1',
    categoria: 'BUSINESS_RULE',
    severidad: 'WARNING',
    codigo: 'TEST_CODE',
    descripcion: 'Test description',
    campo_afectado: null,
    valor_encontrado: null,
    valor_esperado: null,
    fecha_deteccion: '2026-06-01T10:00:00Z',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// General rendering
// ---------------------------------------------------------------------------

describe('StateDescriptionPanel — general', () => {
  it('renders null for an unknown estado', () => {
    const { container } = render(
      <StateDescriptionPanel estado="ESTADO_DESCONOCIDO" />
    );
    expect(container.firstChild).toBeNull();
  });

  it.each(ALL_STATES)('renders panel for estado %s', (estado) => {
    render(<StateDescriptionPanel estado={estado} />);
    expect(screen.getByTestId('state-description-panel')).toBeInTheDocument();
  });

  it.each(ALL_STATES)('shows a non-empty descripcion for %s', (estado) => {
    render(<StateDescriptionPanel estado={estado} />);
    // Each state info has a descripcion; the panel renders it
    const panel = screen.getByTestId('state-description-panel');
    expect(panel.textContent?.length).toBeGreaterThan(10);
  });

  it('shows the "Para avanzar" heading when there are requisitos', () => {
    render(<StateDescriptionPanel estado="RADICADA" />);
    expect(screen.getByText(/para avanzar/i)).toBeInTheDocument();
  });

  it('has aria-label containing the estado name', () => {
    render(<StateDescriptionPanel estado="EN_AUDITORIA" />);
    const panel = screen.getByTestId('state-description-panel');
    expect(panel).toHaveAttribute('aria-label', expect.stringContaining('EN_AUDITORIA'));
  });
});

// ---------------------------------------------------------------------------
// Per-state descriptions
// ---------------------------------------------------------------------------

describe('StateDescriptionPanel — RADICADA', () => {
  it('shows the RADICADA description text', () => {
    render(<StateDescriptionPanel estado="RADICADA" />);
    expect(
      screen.getByText(/validación automática de campos y reglas de negocio/i)
    ).toBeInTheDocument();
  });

  it('lists the RADICADA requisitos', () => {
    render(<StateDescriptionPanel estado="RADICADA" />);
    expect(screen.getByText(/Documentación mínima presente/i)).toBeInTheDocument();
    expect(screen.getByText(/Diagnóstico CIE-10/i)).toBeInTheDocument();
    expect(screen.getByText(/Empleado activo/i)).toBeInTheDocument();
  });

  it('shows SLA hint for RADICADA', () => {
    render(<StateDescriptionPanel estado="RADICADA" />);
    expect(screen.getByTestId('sla-hint')).toBeInTheDocument();
    expect(screen.getByText(/2 días hábiles/i)).toBeInTheDocument();
  });

  it('does NOT render ValidacionesPanel when auditoriaResultados is undefined', () => {
    render(<StateDescriptionPanel estado="RADICADA" />);
    // When no auditoriaResultados are passed, there must be no inline issues block
    // (the border-t separator div only appears when issues are provided)
    expect(screen.queryByText(/ISSUE/)).toBeNull();
    // The ValidacionesPanel "Alertas y problemas" heading should not appear
    expect(screen.queryByText(/Alertas y problemas/i)).toBeNull();
  });

  it('renders inline ValidacionesPanel when auditoriaResultados has items', () => {
    const issues = [makeIssue({ codigo: 'ISSUE_001', descripcion: 'Falta documento principal' })];
    render(<StateDescriptionPanel estado="RADICADA" auditoriaResultados={issues} />);
    expect(screen.getByText('ISSUE_001')).toBeInTheDocument();
    expect(screen.getByText('Falta documento principal')).toBeInTheDocument();
  });

  it('does NOT render ValidacionesPanel when auditoriaResultados is empty array', () => {
    render(<StateDescriptionPanel estado="RADICADA" auditoriaResultados={[]} />);
    // Empty array → no inline validaciones rendered (condition: length > 0)
    expect(screen.queryByText(/ISSUE/)).toBeNull();
  });
});

describe('StateDescriptionPanel — EN_AUDITORIA', () => {
  it('shows the EN_AUDITORIA description text', () => {
    render(<StateDescriptionPanel estado="EN_AUDITORIA" />);
    expect(screen.getByText(/revisión por el auditor/i)).toBeInTheDocument();
  });

  it('lists the siniestro requisito', () => {
    render(<StateDescriptionPanel estado="EN_AUDITORIA" />);
    expect(screen.getByText(/Siniestro vinculado/i)).toBeInTheDocument();
  });

  it('shows SLA hint for EN_AUDITORIA', () => {
    render(<StateDescriptionPanel estado="EN_AUDITORIA" />);
    expect(screen.getByText(/5 días hábiles/i)).toBeInTheDocument();
  });
});

describe('StateDescriptionPanel — PENDIENTE', () => {
  it('shows the PENDIENTE description text', () => {
    render(<StateDescriptionPanel estado="PENDIENTE" />);
    expect(screen.getByText(/espera de información adicional/i)).toBeInTheDocument();
  });

  it('shows the 8-day warning for PENDIENTE', () => {
    render(<StateDescriptionPanel estado="PENDIENTE" />);
    expect(screen.getByTestId('pendiente-warning')).toBeInTheDocument();
    expect(screen.getByText(/8\+ días sin respuesta/i)).toBeInTheDocument();
  });

  it('does NOT show the 8-day warning for other states', () => {
    render(<StateDescriptionPanel estado="EN_AUDITORIA" />);
    expect(screen.queryByTestId('pendiente-warning')).toBeNull();
  });
});

describe('StateDescriptionPanel — CREACION_SINIESTRO', () => {
  it('shows the CREACION_SINIESTRO description text', () => {
    render(<StateDescriptionPanel estado="CREACION_SINIESTRO" />);
    expect(screen.getByText(/siniestro en el sistema externo/i)).toBeInTheDocument();
  });

  it('shows SLA hint for CREACION_SINIESTRO', () => {
    render(<StateDescriptionPanel estado="CREACION_SINIESTRO" />);
    expect(screen.getByText(/1 día hábil/i)).toBeInTheDocument();
  });
});

describe('StateDescriptionPanel — LIQUIDACION', () => {
  it('shows the LIQUIDACION description text', () => {
    render(<StateDescriptionPanel estado="LIQUIDACION" />);
    expect(screen.getByText(/calcular el valor y autorizar el pago/i)).toBeInTheDocument();
  });

  it('lists IBL requisito', () => {
    render(<StateDescriptionPanel estado="LIQUIDACION" />);
    expect(screen.getByText(/IBL calculado/i)).toBeInTheDocument();
  });

  it('shows SLA hint for LIQUIDACION', () => {
    render(<StateDescriptionPanel estado="LIQUIDACION" />);
    expect(screen.getByText(/3 días hábiles/i)).toBeInTheDocument();
  });
});

describe('StateDescriptionPanel — LIQUIDACION_PARCIAL', () => {
  it('shows the LIQUIDACION_PARCIAL description text', () => {
    render(<StateDescriptionPanel estado="LIQUIDACION_PARCIAL" />);
    expect(screen.getByText(/primer día no es pagable/i)).toBeInTheDocument();
  });

  it('mentions mismos requisitos que LIQUIDACION', () => {
    render(<StateDescriptionPanel estado="LIQUIDACION_PARCIAL" />);
    expect(screen.getByText(/Mismos requisitos que LIQUIDACION/i)).toBeInTheDocument();
  });
});

describe('StateDescriptionPanel — GLOSADA', () => {
  it('shows the GLOSADA description text', () => {
    render(<StateDescriptionPanel estado="GLOSADA" />);
    expect(screen.getByText(/fue glosada/i)).toBeInTheDocument();
  });

  it('shows terminal state requisito', () => {
    render(<StateDescriptionPanel estado="GLOSADA" />);
    expect(screen.getByText(/Estado terminal/i)).toBeInTheDocument();
  });

  it('does NOT show SLA hint for GLOSADA (terminal)', () => {
    render(<StateDescriptionPanel estado="GLOSADA" />);
    expect(screen.queryByTestId('sla-hint')).toBeNull();
  });
});

describe('StateDescriptionPanel — PAGADA', () => {
  it('shows the PAGADA description text', () => {
    render(<StateDescriptionPanel estado="PAGADA" />);
    expect(screen.getByText(/Pago completo completado/i)).toBeInTheDocument();
  });
});

describe('StateDescriptionPanel — PAGADA_PARCIAL', () => {
  it('shows the PAGADA_PARCIAL description text', () => {
    render(<StateDescriptionPanel estado="PAGADA_PARCIAL" />);
    expect(screen.getByText(/Pago parcial completado/i)).toBeInTheDocument();
  });
});
