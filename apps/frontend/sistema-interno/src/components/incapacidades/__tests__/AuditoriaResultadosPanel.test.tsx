import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditoriaResultadosPanel } from '../AuditoriaResultadosPanel';
import type { AuditoriaResultado } from '@/types/incapacidad';
import { REGLAS_AUDITORIA_LABELS } from '../reglasAuditoriaLabels';

const makeResultado = (overrides: Partial<AuditoriaResultado>): AuditoriaResultado => ({
  id: `id-${Math.random()}`,
  incapacidad_id: 'inc-1',
  regla: 'REGLA_TEST',
  categoria: 'GENERAL',
  aprobado: true,
  severidad: 'INFO',
  detalle: null,
  ...overrides,
});

describe('AuditoriaResultadosPanel', () => {
  it('shows Spanish nombre for known rules instead of raw key', () => {
    const resultados = [
      makeResultado({ regla: 'DIAS_TOTALES_MISMATCH', aprobado: true }),
      makeResultado({ id: 'id-2', regla: 'SINIESTRO_REQUERIDO', aprobado: false, detalle: 'Siniestro no vinculado' }),
      makeResultado({ id: 'id-3', regla: 'EMPTY_NOMBRE_MEDICO', aprobado: true }),
    ];
    render(<AuditoriaResultadosPanel resultados={resultados} isLoading={false} />);

    expect(screen.getByText(REGLAS_AUDITORIA_LABELS.DIAS_TOTALES_MISMATCH.nombre)).toBeInTheDocument();
    expect(screen.getByText(REGLAS_AUDITORIA_LABELS.SINIESTRO_REQUERIDO.nombre)).toBeInTheDocument();
    expect(screen.getByText(REGLAS_AUDITORIA_LABELS.EMPTY_NOMBRE_MEDICO.nombre)).toBeInTheDocument();
    expect(screen.queryByText('DIAS_TOTALES_MISMATCH')).not.toBeInTheDocument();
    expect(screen.queryByText('SINIESTRO_REQUERIDO')).not.toBeInTheDocument();
  });

  it('shows label descripcion for passing rules, not generic "Regla cumplida"', () => {
    render(
      <AuditoriaResultadosPanel
        resultados={[makeResultado({ regla: 'DURATION_EXCEEDS_LIMIT', aprobado: true, detalle: 'Regla cumplida' })]}
        isLoading={false}
      />
    );
    expect(screen.getByText(REGLAS_AUDITORIA_LABELS.DURATION_EXCEEDS_LIMIT.descripcion)).toBeInTheDocument();
    expect(screen.queryByText('Regla cumplida')).not.toBeInTheDocument();
  });

  it('shows backend detalle for failing rules, not the descripcion', () => {
    const failDetalle = 'Días totales (5) no coincide con el rango (37)';
    render(
      <AuditoriaResultadosPanel
        resultados={[makeResultado({ regla: 'DIAS_TOTALES_MISMATCH', aprobado: false, detalle: failDetalle })]}
        isLoading={false}
      />
    );
    expect(screen.getByText(failDetalle)).toBeInTheDocument();
    expect(screen.queryByText(REGLAS_AUDITORIA_LABELS.DIAS_TOTALES_MISMATCH.descripcion)).not.toBeInTheDocument();
  });

  it('falls back to raw key for unmapped rules', () => {
    render(
      <AuditoriaResultadosPanel
        resultados={[makeResultado({ regla: 'REGLA_DESCONOCIDA', aprobado: true })]}
        isLoading={false}
      />
    );
    expect(screen.getByText('REGLA_DESCONOCIDA')).toBeInTheDocument();
  });

  it('failed results appear before passed results', () => {
    const resultados = [
      makeResultado({ id: 'id-1', regla: 'REGLA_OK', aprobado: true }),
      makeResultado({ id: 'id-2', regla: 'REGLA_FAIL', aprobado: false }),
    ];
    render(<AuditoriaResultadosPanel resultados={resultados} isLoading={false} />);

    const items = screen.getAllByRole('listitem');
    const failIdx = items.findIndex((el) => el.textContent?.includes('REGLA_FAIL'));
    const okIdx = items.findIndex((el) => el.textContent?.includes('REGLA_OK'));
    expect(failIdx).toBeLessThan(okIdx);
  });

  it('<details> is open by default', () => {
    render(
      <AuditoriaResultadosPanel
        resultados={[makeResultado({})]}
        isLoading={false}
      />
    );
    const details = document.querySelector('details');
    expect(details).toBeInTheDocument();
    expect(details).toHaveAttribute('open');
  });

  it('clicking summary toggles the open attribute on <details>', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <AuditoriaResultadosPanel
        resultados={[makeResultado({})]}
        isLoading={false}
      />
    );

    const details = container.querySelector('details');
    expect(details).toHaveAttribute('open');

    const summary = container.querySelector('summary')!;
    await user.click(summary);
    expect(details).not.toHaveAttribute('open');
  });

  it('summary shows correct counts', () => {
    const resultados = [
      makeResultado({ id: 'id-1', aprobado: true }),
      makeResultado({ id: 'id-2', aprobado: true }),
      makeResultado({ id: 'id-3', aprobado: false }),
    ];
    render(<AuditoriaResultadosPanel resultados={resultados} isLoading={false} />);

    const summary = document.querySelector('summary');
    expect(summary?.textContent).toContain('3 total');
    expect(summary?.textContent).toContain('2 aprobadas');
    expect(summary?.textContent).toContain('1 fallidas');
  });

  it('shows loading state when isLoading is true', () => {
    render(<AuditoriaResultadosPanel resultados={[]} isLoading={true} />);
    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it('shows pass and fail icons', () => {
    const resultados = [
      makeResultado({ id: 'id-1', regla: 'REGLA_OK', aprobado: true }),
      makeResultado({ id: 'id-2', regla: 'REGLA_FAIL', aprobado: false }),
    ];
    render(<AuditoriaResultadosPanel resultados={resultados} isLoading={false} />);

    // Check for aria-label on icon spans
    expect(screen.getByLabelText('aprobado')).toBeInTheDocument();
    expect(screen.getByLabelText('fallido')).toBeInTheDocument();
  });

  it('shows detail text when present', () => {
    const resultados = [
      makeResultado({ regla: 'REGLA_DETALLE', detalle: 'El campo días_totales excede el límite' }),
    ];
    render(<AuditoriaResultadosPanel resultados={resultados} isLoading={false} />);
    expect(screen.getByText('El campo días_totales excede el límite')).toBeInTheDocument();
  });
});
