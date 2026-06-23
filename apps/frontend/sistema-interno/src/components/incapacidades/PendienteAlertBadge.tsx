/**
 * PendienteAlertBadge
 *
 * Displays a warning badge when an incapacidad has been in PENDIENTE state
 * for 8 or more days without a response from the person responsible.
 *
 * Usage:
 *   <PendienteAlertBadge diasEnPendiente={inc.dias_en_estado_actual} />
 *
 * Returns null (renders nothing) when diasEnPendiente < PENDIENTE_ALERT_DAYS.
 */

const PENDIENTE_ALERT_DAYS = 8;

interface Props {
  /** Number of days the incapacidad has been in PENDIENTE state. */
  diasEnPendiente: number;
}

export function PendienteAlertBadge({ diasEnPendiente }: Props) {
  if (diasEnPendiente < PENDIENTE_ALERT_DAYS) return null;

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
      role="status"
      aria-label={`Alerta: ${diasEnPendiente} días sin respuesta`}
    >
      ⚠ {diasEnPendiente} días sin respuesta
    </span>
  );
}
