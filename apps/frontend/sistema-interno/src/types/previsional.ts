/**
 * Tipos TypeScript espejo de los schemas Pydantic del módulo Previsionales
 * (backend: `app/schemas/previsionales/*.py`, Fases 2-4).
 *
 * Fuente de verdad: los archivos Pydantic listados en cada bloque de
 * comentario. No se adivinó ningún nombre de campo -- todos fueron leídos
 * directamente del backend.
 *
 * Nota sobre `PeriodoPrevisional`: el modelo SQLAlchemy existe
 * (`app/models/previsionales/periodo_previsional.py`) y se referencia en
 * `endpoints/previsionales/lotes.py` para construir el export ARPIS, pero
 * NO tiene un schema Pydantic de respuesta propio -- ningún endpoint de
 * Fase 4 lo expone directamente en su `response_model`. No se define un
 * tipo para él aquí porque inventar la forma de un shape que el backend no
 * expone sería adivinar; si una tarea futura (5.3 o posterior) necesita
 * mostrar periodos, debe agregarse cuando el backend exponga el schema.
 */

// ---------------------------------------------------------------------------
// Lotes e Incapacidades (app/schemas/previsionales/lote.py)
// ---------------------------------------------------------------------------

/** Espejo de `LotePrevisionalResponse`. */
export interface LotePrevisional {
  id: string;
  nombre_archivo: string;
  estado: string;
  fecha_cargue: string;
  cargado_por_id: string | null;
  total_filas: number;
  total_incapacidades: number;
  observaciones: string | null;
  created_at: string;
  updated_at: string;
}

/** Espejo de `IncapacidadPrevisionalResponse`. */
export interface IncapacidadPrevisional {
  id: string;
  lote_id: string;
  tipo_identificacion: string | null;
  identificacion: string | null;
  radicado: string | null;
  radicado_normalizado: string | null;
  tipo_ingreso: string | null;
  fecha_inicial: string | null;
  fecha_final: string | null;
  dia_181_alfa: string | null;
  dia_181_afp: string | null;
  dia_181_arpis: string | null;
  fecha_crie: string | null;
  fecha_radicacion_afp: string | null;
  fecha_radicacion_alfa: string | null;
  numero_siniestro: string | null;
  valor_afp: number | null;
  cie10: string | null;
  observacion: string | null;
  observacion_causal: string | null;
  aval: string | null;
  motivo_no_aval: string | null;
  estado: string;
  prorroga_de_id: string | null;
  incapacidad_origen_id: string | null;
  es_duplicado_interno: boolean;
  valor_auditado: number | null;
  diferencia_valor_afp: number | null;
  errores_carga: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/** Filtros opcionales de `GET /previsionales/lotes/{loteId}/incapacidades`. */
export interface FiltrosIncapacidadesLote {
  sin_siniestro?: boolean;
  repetidas?: boolean;
  errores?: boolean;
  dif_valor?: boolean;
}

// ---------------------------------------------------------------------------
// Auditoría (app/schemas/previsionales/auditoria.py)
// ---------------------------------------------------------------------------

/** Estados posibles de una señal AB-AT (`EstadoSenal` en `auditoria_rules.py`). */
export type EstadoSenalAuditoria = 'OK' | 'ALERTA' | 'PENDIENTE' | 'INFO';

/** Espejo de `SenalAuditoriaPrevisionalResponse`. */
export interface SenalAuditoriaPrevisional {
  id: string;
  incapacidad_previsional_id: string;
  codigo: string;
  nombre: string;
  estado: EstadoSenalAuditoria;
  valor: unknown;
  detalle: string | null;
  created_at: string;
  updated_at: string;
}

/** Body de `PATCH /previsionales/incapacidades/{id}` (`IncapacidadPrevisionalPatchRequest`). */
export interface PatchIncapacidadRequest {
  dia_181_alfa?: string | null;
}

/** Body de `POST /previsionales/incapacidades/{id}/aval` (`AvalRequest`). */
export interface AvalRequest {
  aval: 'SI' | 'NO';
  motivo?: string;
}

/** Body de `POST /previsionales/incapacidades/{id}/duplicar` (`DuplicarRequest`). */
export interface DuplicarRequest {
  fecha_inicial: string;
  fecha_final: string;
}

// ---------------------------------------------------------------------------
// Liquidación (app/schemas/previsionales/liquidacion.py)
// ---------------------------------------------------------------------------

/** Espejo de `LiquidarLoteResponse`. */
export interface LiquidarLoteResponse {
  liquidadas: number;
}

// ---------------------------------------------------------------------------
// Parámetros SMLMV (app/schemas/previsionales/parametros.py)
// ---------------------------------------------------------------------------

/** Espejo de `SmlmvParametrosResponse`. */
export interface SmlmvParametros {
  id: string;
  ano: number;
  valor: number;
  vigente_desde: string;
}

// ---------------------------------------------------------------------------
// Referencia (app/schemas/previsionales/referencia.py)
// ---------------------------------------------------------------------------

/** Los 3 tipos de hoja de referencia que acepta `POST /previsionales/referencia/importar`. */
export type TipoReferenciaPrevisional = 'siniestros' | 'solicitudes' | 'ite_historico';

/** Espejo de `ReferenciaImportarResponse`. */
export interface ReferenciaImportarResponse {
  tipo: string;
  importados: number;
}

// ---------------------------------------------------------------------------
// Siniestros (app/schemas/previsionales/siniestros.py)
// ---------------------------------------------------------------------------

/** Body de `POST /previsionales/siniestros` (`SiniestroPrevisionalCreateRequest`). */
export interface SiniestroManualRequest {
  identificacion?: string;
  numero_siniestro: string;
  origen?: string;
  estado?: string;
  fecha_aviso?: string;
  fecha_siniestro?: string;
  incapacidad_id?: string;
}

/** Espejo de `SiniestroPrevisionalResponse`. */
export interface SiniestroPrevisional {
  id: string;
  identificacion: string;
  numero_siniestro: string;
  origen: string | null;
  estado: string | null;
  fecha_aviso: string | null;
  fecha_siniestro: string | null;
  created_at: string;
  updated_at: string;
}
