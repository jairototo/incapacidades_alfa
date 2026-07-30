/**
 * Diccionario de etiquetas para las 19 señales de auditoría previsional
 * (reglas AB-AT). Clon del patrón de `reglasAuditoriaLabels.ts`.
 *
 * `nombre` viene literal del registro `REGLAS_PREVISIONALES` del backend
 * (`app/services/previsionales/auditoria_rules.py`, línea ~347). Las
 * `descripcion` son un resumen en español de la semántica real de cada
 * `regla_xx_*` (mismo archivo) -- no son una traducción del `nombre`, sino
 * lo que la regla efectivamente calcula/verifica.
 */
export interface SenalPrevisionalLabel {
  nombre: string;
  descripcion: string;
}

export const SENALES_PREVISIONALES_LABELS: Record<string, SenalPrevisionalLabel> = {
  AB: {
    nombre: 'Dia 181 (auditado)',
    descripcion: 'Texto de observación con el día 181 confirmado por el auditor (dia_181_alfa).',
  },
  AC: {
    nombre: 'Aval',
    descripcion: 'Decisión humana de aval de la incapacidad; nunca se autocalcula.',
  },
  AD: {
    nombre: 'Filas repetidas en el lote',
    descripcion: 'Detecta si más de una fila del lote comparte la misma identificación y fecha inicial.',
  },
  AE: {
    nombre: 'Dia 181 (AFP)',
    descripcion: 'Día 181 según la solicitud ya radicada en ARPIS (fuente AFP).',
  },
  AF: {
    nombre: 'Dia 540 (limite)',
    descripcion: 'Día 181 (AFP) más 359 días: el límite de la ventana de pago.',
  },
  AG: {
    nombre: 'Fecha CRIE',
    descripcion: 'Fecha del concepto de rehabilitación (CRIE), tomada de la solicitud ARPIS.',
  },
  AH: {
    nombre: 'FI',
    descripcion: 'Clave tipada {identificación, fecha inicial} de la fila, nunca texto concatenado.',
  },
  AI: {
    nombre: 'FF',
    descripcion: 'Clave tipada {identificación, fecha final} de la fila, nunca texto concatenado.',
  },
  AJ: {
    nombre: 'CI',
    descripcion: 'Cruce contra el libro externo [1]DATOS; permanece PENDIENTE porque ese libro nunca fue entregado.',
  },
  AK: {
    nombre: 'CF',
    descripcion: 'Cruce contra el libro externo [1]DATOS; permanece PENDIENTE porque ese libro nunca fue entregado.',
  },
  AL: {
    nombre: 'Coincidencia dia 181 (Arpis vs AFP)',
    descripcion: 'Compara el día 181 registrado en ARPIS contra el reportado por la AFP en la fila.',
  },
  AM: {
    nombre: 'Siniestro',
    descripcion: 'Número de siniestro cruzado por identificación; PENDIENTE con candidatos si hay más de uno.',
  },
  AN: {
    nombre: 'Origen del siniestro',
    descripcion: 'Origen del siniestro seleccionado para el afiliado (misma selección que la regla AM).',
  },
  AO: {
    nombre: 'Estado del siniestro',
    descripcion: 'Estado del siniestro seleccionado para el afiliado (misma selección que la regla AM).',
  },
  AP: {
    nombre: 'Fechas del siniestro',
    descripcion: 'Fecha de aviso y fecha del siniestro seleccionado, reportadas tal cual sin bloquear por orden.',
  },
  AQ: {
    nombre: 'Texto pago ITE',
    descripcion: 'Texto de comentario de pago generado a partir de la fecha inicial y final de la fila.',
  },
  AR: {
    nombre: 'Siniestro + valor AFP',
    descripcion: 'Concatenación del número de siniestro reportado por la AFP con el valor AFP de la fila.',
  },
  AS: {
    nombre: 'Sipren',
    descripcion: 'Campo informativo que diligencia Sipren posteriormente; este motor no lo calcula.',
  },
  AT: {
    nombre: 'Posible doble pago',
    descripcion: 'Verifica si la identificación y fecha inicial ya existen en el histórico de ITE pagado.',
  },
};
