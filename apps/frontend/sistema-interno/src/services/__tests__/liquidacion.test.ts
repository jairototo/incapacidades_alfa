import { describe, it, expect } from 'vitest';
import { mapLiquidacionToBreakdown, type LiquidacionResponse } from '../liquidacion';

// ---------------------------------------------------------------------------
// Fixture helpers
// ---------------------------------------------------------------------------

function makeBase(): LiquidacionResponse {
  return {
    id: 'liq-001',
    incapacidad_id: 'inc-001',
    ibl: 3500000,
    periodo_ibl_inicio: null,
    periodo_ibl_fin: null,
    dias_autorizados: 10,
    fecha_inicio_autorizada: '2026-01-01',
    fecha_fin_autorizada: '2026-01-10',
    valor_incapacidad_temporal: 35000000,
    valor_aporte_patronal_pension: 4200000,
    valor_aporte_trabajador_pension: 1400000,
    valor_aporte_adicional_trabajador_pension: null,
    valor_aporte_patronal_salud: 2975000,
    valor_aporte_trabajador_salud: 1400000,
    valor_total: 44975000,
    metodo_pago: null,
    notas_liquidador: null,
    liquidador_id: null,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('mapLiquidacionToBreakdown', () => {
  it('returns null when valor_total is null (draft without breakdown)', () => {
    const liq = { ...makeBase(), valor_total: null };
    expect(mapLiquidacionToBreakdown(liq)).toBeNull();
  });

  it('maps all valor_* fields to their unprefixed counterparts', () => {
    const result = mapLiquidacionToBreakdown(makeBase());

    expect(result).not.toBeNull();
    expect(result!.incapacidad_temporal).toBe(35000000);
    expect(result!.aporte_patronal_pension).toBe(4200000);
    expect(result!.aporte_trabajador_pension).toBe(1400000);
    expect(result!.aporte_patronal_salud).toBe(2975000);
    expect(result!.aporte_trabajador_salud).toBe(1400000);
    expect(result!.valor_total).toBe(44975000);
  });

  it('preserves null as null — does NOT coerce to 0', () => {
    const result = mapLiquidacionToBreakdown(makeBase());
    expect(result!.aporte_adicional_trabajador_pension).toBeNull();
  });

  it('maps 0 (numeric zero) as 0 — not null', () => {
    const liq = { ...makeBase(), valor_aporte_patronal_pension: 0 };
    const result = mapLiquidacionToBreakdown(liq);
    expect(result!.aporte_patronal_pension).toBe(0);
  });

  it('sets dias from dias_autorizados', () => {
    const result = mapLiquidacionToBreakdown(makeBase());
    expect(result!.dias).toBe(10);
  });

  it('sets ibl from liq.ibl', () => {
    const result = mapLiquidacionToBreakdown(makeBase());
    expect(result!.ibl).toBe(3500000);
  });

  it('sets ibl to null when liq.ibl is null', () => {
    const liq = { ...makeBase(), ibl: null };
    const result = mapLiquidacionToBreakdown(liq);
    expect(result!.ibl).toBeNull();
  });

  it('includes a nota string', () => {
    const result = mapLiquidacionToBreakdown(makeBase());
    expect(typeof result!.nota).toBe('string');
    expect(result!.nota.length).toBeGreaterThan(0);
  });
});
