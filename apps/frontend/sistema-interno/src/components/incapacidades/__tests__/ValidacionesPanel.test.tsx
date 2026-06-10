import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ValidacionesPanel } from '../ValidacionesPanel';
import type { ValidationIssue } from '@/types/incapacidad';

const makeIssue = (overrides: Partial<ValidationIssue>): ValidationIssue => ({
  id: 'issue-1',
  pre_incapacidad_id: 'pre-1',
  incapacidad_id: 'inc-1',
  categoria: 'INTEGRATION_CHECK',
  severidad: 'WARNING',
  codigo: 'EMPLEADO_NOT_FOUND',
  descripcion: 'Empleado no encontrado en BD',
  campo_afectado: null,
  valor_encontrado: null,
  valor_esperado: null,
  fecha_deteccion: '2026-06-10T10:00:00Z',
  ...overrides,
});

describe('ValidacionesPanel', () => {
  it('muestra los issues con su código y descripción', () => {
    render(<ValidacionesPanel issues={[makeIssue({})]} isLoading={false} />);
    expect(screen.getByText('EMPLEADO_NOT_FOUND')).toBeInTheDocument();
    expect(screen.getByText('Empleado no encontrado en BD')).toBeInTheDocument();
  });

  it('muestra categorías sin problemas en verde cuando no hay issues', () => {
    render(<ValidacionesPanel issues={[]} isLoading={false} />);
    expect(screen.getByText(/FIELD_VALIDATION/i)).toBeInTheDocument();
    expect(screen.getByText(/BUSINESS_RULE/i)).toBeInTheDocument();
    expect(screen.getByText(/FRAUD_ALERT/i)).toBeInTheDocument();
    expect(screen.getByText(/INTEGRATION_CHECK/i)).toBeInTheDocument();
  });

  it('los issues ERROR aparecen antes que los WARNING', () => {
    const issues = [
      makeIssue({ id: '1', severidad: 'WARNING', codigo: 'WARN_CODE', descripcion: 'Warning issue' }),
      makeIssue({ id: '2', severidad: 'ERROR', codigo: 'ERR_CODE', descripcion: 'Error issue' }),
    ];
    render(<ValidacionesPanel issues={issues} isLoading={false} />);
    const items = screen.getAllByRole('listitem');
    const errIdx = items.findIndex(el => el.textContent?.includes('ERR_CODE'));
    const warnIdx = items.findIndex(el => el.textContent?.includes('WARN_CODE'));
    expect(errIdx).toBeLessThan(warnIdx);
  });

  it('cuando isLoading es true muestra estado de carga', () => {
    render(<ValidacionesPanel issues={[]} isLoading={true} />);
    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it('categorías con issues no aparecen en la sección verde', () => {
    const issues = [makeIssue({ categoria: 'FRAUD_ALERT' })];
    render(<ValidacionesPanel issues={issues} isLoading={false} />);
    const greenItems = screen.queryAllByText(/sin problemas/i);
    const fraudAlertGreen = greenItems.find(el =>
      el.closest('li')?.textContent?.includes('FRAUD_ALERT')
    );
    expect(fraudAlertGreen).toBeUndefined();
  });
});
