/**
 * SenalesPrevisionalesPanel — Panel colapsable con las 19 señales de
 * auditoría AB-AT (Task 3.3) de una incapacidad previsional. Clon
 * ESTRUCTURAL de `AuditoriaResultadosPanel.tsx`
 * (`src/components/incapacidades/`): mismo patrón `<details>` con resumen
 * de conteos y lista de badges. La forma de los datos es distinta -- 4
 * estados (`OK|ALERTA|PENDIENTE|INFO`) en vez de un `aprobado: boolean` --
 * así que el mapeo de colores se adapta en vez de reutilizarse literal.
 *
 * Punto crítico de UX (ver brief de Task 5.5): `PENDIENTE` debe ser
 * visualmente DISTINTO de `OK`, no un tono más claro del mismo color.
 * AJ/AK quedan PENDIENTE de forma permanente (el libro externo [1]DATOS
 * nunca fue entregado) y AM-AP quedan PENDIENTE con una lista de
 * candidatos cuando el cruce de siniestro/solicitud es ambiguo -- si
 * PENDIENTE se viera parecido a OK, esas señales se volverían invisibles
 * para el auditor. Mapeo elegido: OK=verde, ALERTA=rojo, PENDIENTE=morado
 * (nunca verde), INFO=gris. El morado ya se usa en esta app para "requiere
 * atención administrativa" (ver el badge "Repetida" en
 * `RadicacionLotePage.tsx`), así que reutilizarlo aquí es consistente con
 * el resto de la UI, no una elección aislada.
 */
import type { SenalAuditoriaPrevisional } from '@/types/previsional';
import { SENALES_PREVISIONALES_LABELS } from './senalesPrevisionalesLabels';

interface SenalesPrevisionalesPanelProps {
  senales: SenalAuditoriaPrevisional[];
  isLoading: boolean;
}

/** Orden de aparición: lo que requiere atención primero, lo verificado al final. */
const ESTADO_ORDEN: Record<string, number> = {
  ALERTA: 0,
  PENDIENTE: 1,
  INFO: 2,
  OK: 3,
};

const ESTADO_BADGE: Record<string, string> = {
  OK: 'bg-green-100 text-green-700 border-green-200',
  ALERTA: 'bg-red-100 text-red-700 border-red-200',
  PENDIENTE: 'bg-purple-100 text-purple-800 border-purple-300',
  INFO: 'bg-slate-100 text-slate-600 border-slate-200',
};

const ESTADO_ICONO: Record<string, string> = {
  OK: '✅',
  ALERTA: '❌',
  PENDIENTE: '🕒',
  INFO: 'ℹ️',
};

export function SenalesPrevisionalesPanel({ senales, isLoading }: SenalesPrevisionalesPanelProps) {
  if (isLoading) {
    return (
      <div className="py-4 text-center text-sm text-slate-500" data-testid="senales-loading">
        Cargando señales de auditoría…
      </div>
    );
  }

  // Lote nunca auditado (`auditar_lote` todavía no corrió para él): un
  // panel vacío sin explicación se lee como un error o un bug, no como "no
  // hay nada que mostrar todavía". Mensaje explícito en vez de reusar el
  // fallback genérico de lista vacía.
  if (senales.length === 0) {
    return (
      <div
        className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600"
        data-testid="senales-vacio"
      >
        Este lote aún no ha sido auditado — no hay señales AB-AT persistidas para esta
        incapacidad todavía. Ejecuta la auditoría del lote para generarlas.
      </div>
    );
  }

  const sorted = [...senales].sort((a, b) => {
    const diff = (ESTADO_ORDEN[a.estado] ?? 4) - (ESTADO_ORDEN[b.estado] ?? 4);
    if (diff !== 0) return diff;
    return a.codigo.localeCompare(b.codigo);
  });

  const total = sorted.length;
  const conteo = {
    OK: sorted.filter((s) => s.estado === 'OK').length,
    ALERTA: sorted.filter((s) => s.estado === 'ALERTA').length,
    PENDIENTE: sorted.filter((s) => s.estado === 'PENDIENTE').length,
    INFO: sorted.filter((s) => s.estado === 'INFO').length,
  };

  return (
    <details data-testid="senales-previsionales-details" open>
      <summary
        className="cursor-pointer select-none text-sm font-semibold text-blue-800 py-1"
        data-testid="senales-previsionales-summary"
      >
        Señales AB-AT ({total} total — {conteo.OK} OK, {conteo.ALERTA} en alerta,{' '}
        {conteo.PENDIENTE} pendientes, {conteo.INFO} informativas)
      </summary>

      <ul className="mt-2 space-y-1.5" role="list" data-testid="senales-previsionales-list">
        {sorted.map((s) => {
          const badgeCls = ESTADO_BADGE[s.estado] ?? 'bg-slate-100 text-slate-600 border-slate-200';
          const label = SENALES_PREVISIONALES_LABELS[s.codigo];

          return (
            <li
              key={s.id}
              className="flex items-start gap-2 rounded border px-3 py-2 text-sm bg-white"
              data-testid={`senal-item-${s.codigo}`}
            >
              <span className="flex-shrink-0 mt-0.5" aria-label={s.estado}>
                {ESTADO_ICONO[s.estado] ?? 'ℹ️'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-xs" data-testid={`nombre-senal-${s.codigo}`}>
                    {s.codigo} — {label?.nombre ?? s.nombre}
                  </span>
                  <span
                    className={`border rounded px-1.5 py-0.5 text-xs leading-none font-medium ${badgeCls}`}
                    data-testid={`estado-badge-${s.codigo}`}
                  >
                    {s.estado}
                  </span>
                </div>
                <p className="mt-0.5 text-slate-600 leading-snug" data-testid={`descripcion-senal-${s.codigo}`}>
                  {s.detalle ?? label?.descripcion ?? ''}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </details>
  );
}
