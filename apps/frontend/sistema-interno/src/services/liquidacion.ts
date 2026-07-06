/**
 * Servicio de liquidación de incapacidades.
 *
 * Endpoints:
 *   GET  /api/v1/incapacidades/{id}/liquidacion           — recuperar liquidación
 *   POST /api/v1/incapacidades/{id}/liquidacion           — crear/actualizar liquidación
 *   GET  /api/v1/incapacidades/{id}/liquidacion/calcular-breakdown  — calcular desglose (preview)
 *   POST /api/v1/incapacidades/{id}/liquidacion/devolver  — devolver a EN_AUDITORIA
 *   POST /api/v1/incapacidades/{id}/liquidacion/completar — pasar a PAGADA/PAGADA_PARCIAL
 */
import api from '@/lib/api';

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export const MetodoPagoLiquidacion = {
  CHEQUE: 'CHEQUE',
  OXIRRE: 'OXIRRE',
} as const;

export type MetodoPagoLiquidacion =
  (typeof MetodoPagoLiquidacion)[keyof typeof MetodoPagoLiquidacion];

export const METODO_PAGO_LABELS: Record<MetodoPagoLiquidacion, string> = {
  CHEQUE: 'Cheque',
  OXIRRE: 'Oxirre (transferencia electrónica)',
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LiquidacionResponse {
  id: string;
  incapacidad_id: string;
  ibl: number | null;
  periodo_ibl_inicio: string | null;
  periodo_ibl_fin: string | null;
  dias_autorizados: number;
  fecha_inicio_autorizada: string;
  fecha_fin_autorizada: string;
  valor_incapacidad_temporal: number | null;
  valor_aporte_patronal_pension: number | null;
  valor_aporte_trabajador_pension: number | null;
  valor_aporte_adicional_trabajador_pension: number | null;
  valor_aporte_patronal_salud: number | null;
  valor_aporte_trabajador_salud: number | null;
  valor_total: number | null;
  metodo_pago: MetodoPagoLiquidacion | null;
  notas_liquidador: string | null;
  liquidador_id: string | null;
}

export interface LiquidacionGuardar {
  ibl?: number | null;
  periodo_ibl_inicio?: string | null;
  periodo_ibl_fin?: string | null;
  dias_autorizados: number;
  fecha_inicio_autorizada: string;
  fecha_fin_autorizada: string;
  valor_incapacidad_temporal?: number | null;
  valor_aporte_patronal_pension?: number | null;
  valor_aporte_trabajador_pension?: number | null;
  valor_aporte_adicional_trabajador_pension?: number | null;
  valor_aporte_patronal_salud?: number | null;
  valor_aporte_trabajador_salud?: number | null;
  valor_total?: number | null;
  metodo_pago?: MetodoPagoLiquidacion | null;
  notas_liquidador?: string | null;
}

export interface BreakdownResponse {
  ibl: number | null;
  dias: number;
  incapacidad_temporal: number | null;
  aporte_patronal_pension: number | null;
  aporte_trabajador_pension: number | null;
  aporte_adicional_trabajador_pension: number | null;
  aporte_patronal_salud: number | null;
  aporte_trabajador_salud: number | null;
  valor_total: number | null;
  nota: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Maps a saved LiquidacionResponse to a BreakdownResponse for display.
 *
 * Returns null when the liquidación has no calculated breakdown
 * (valor_total is null — i.e. a draft without breakdown).
 *
 * Uses Number() for defensive conversion: handles both runtime numbers and
 * strings, and preserves null as null (not 0).
 */
export function mapLiquidacionToBreakdown(
  liq: LiquidacionResponse
): BreakdownResponse | null {
  if (liq.valor_total == null) return null;

  const toNum = (v: number | null): number | null =>
    v != null ? Number(v) : null;

  return {
    ibl: liq.ibl != null ? Number(liq.ibl) : null,
    dias: liq.dias_autorizados,
    incapacidad_temporal: toNum(liq.valor_incapacidad_temporal),
    aporte_patronal_pension: toNum(liq.valor_aporte_patronal_pension),
    aporte_trabajador_pension: toNum(liq.valor_aporte_trabajador_pension),
    aporte_adicional_trabajador_pension: toNum(
      liq.valor_aporte_adicional_trabajador_pension
    ),
    aporte_patronal_salud: toNum(liq.valor_aporte_patronal_salud),
    aporte_trabajador_salud: toNum(liq.valor_aporte_trabajador_salud),
    valor_total: Number(liq.valor_total),
    nota: 'Desglose de la liquidación guardada',
  };
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const liquidacionService = {
  /**
   * Obtener liquidación existente de una incapacidad.
   * GET /api/v1/incapacidades/{id}/liquidacion
   */
  async getLiquidacion(incapacidadId: string): Promise<LiquidacionResponse> {
    const { data } = await api.get<LiquidacionResponse>(
      `/incapacidades/${incapacidadId}/liquidacion`
    );
    return data;
  },

  /**
   * Crear o actualizar la liquidación de una incapacidad.
   * POST /api/v1/incapacidades/{id}/liquidacion
   * IBL es required para guardar (validado en UI).
   */
  async guardarLiquidacion(
    incapacidadId: string,
    payload: LiquidacionGuardar
  ): Promise<LiquidacionResponse> {
    const { data } = await api.post<LiquidacionResponse>(
      `/incapacidades/${incapacidadId}/liquidacion`,
      payload
    );
    return data;
  },

  /**
   * Calcular desglose sin guardar (preview).
   * GET /api/v1/incapacidades/{id}/liquidacion/calcular-breakdown?ibl=...&dias=...
   */
  async calcularBreakdown(
    incapacidadId: string,
    ibl: number | null,
    dias: number
  ): Promise<BreakdownResponse> {
    const params: Record<string, unknown> = { dias };
    if (ibl !== null && ibl !== undefined) {
      params['ibl'] = ibl;
    }
    const { data } = await api.get<BreakdownResponse>(
      `/incapacidades/${incapacidadId}/liquidacion/calcular-breakdown`,
      { params }
    );
    return data;
  },

  /**
   * Devolver incapacidad a EN_AUDITORIA.
   * POST /api/v1/incapacidades/{id}/liquidacion/devolver
   * Body: { observacion: string }
   */
  async devolverAuditoria(
    incapacidadId: string,
    observacion: string
  ): Promise<void> {
    await api.post(
      `/incapacidades/${incapacidadId}/liquidacion/devolver`,
      { observacion }
    );
  },

  /**
   * Completar liquidación → PAGADA / PAGADA_PARCIAL.
   * POST /api/v1/incapacidades/{id}/liquidacion/completar
   */
  async completarLiquidacion(incapacidadId: string): Promise<void> {
    await api.post(`/incapacidades/${incapacidadId}/liquidacion/completar`);
  },
};
