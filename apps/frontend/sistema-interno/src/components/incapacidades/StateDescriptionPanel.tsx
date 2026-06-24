import {
  FileCheck,
  Search,
  Clock,
  Link,
  AlertTriangle,
  Ban,
  CreditCard,
  CheckCircle,
  CheckCircle2,
} from 'lucide-react';
import type { EstadoIncapacidad } from '@/types/enums';
import type { ValidationIssue } from '@/types/incapacidad';
import { ValidacionesPanel } from './ValidacionesPanel';

interface StateInfo {
  descripcion: string;
  requisitos: string[];
  icon: React.ReactNode;
  /** Optional SLA hint shown below requisitos */
  sla?: string;
  colorClass: string;
}

const STATE_INFO: Record<string, StateInfo> = {
  RADICADA: {
    icon: <FileCheck className="h-4 w-4" />,
    colorClass: 'border-slate-200 bg-slate-50 text-slate-700',
    descripcion:
      'Incapacidad registrada. El sistema ejecutó la validación automática de campos y reglas de negocio.',
    requisitos: [
      'Documentación mínima presente (incapacidad médica)',
      'Empleado activo vinculado a la empresa',
      'Diagnóstico CIE-10 válido en el catálogo',
      'Tipo de enfermedad registrado (Accidente de Trabajo / Enfermedad Laboral / Accidente de Trayecto)',
    ],
    sla: 'SLA: 2 días hábiles para pasar a EN_AUDITORIA',
  },
  EN_AUDITORIA: {
    icon: <Search className="h-4 w-4" />,
    colorClass: 'border-blue-200 bg-blue-50 text-blue-800',
    descripcion:
      'En proceso de revisión por el auditor. Las reglas de negocio ya se evaluaron automáticamente.',
    requisitos: [
      'Siniestro vinculado (obligatorio antes de aprobar o glosar)',
      'Si fecha_inicio == fecha_siniestro: usar aprobación parcial',
      'Revisar resultados de reglas en la pestaña de Auditoría',
    ],
    sla: 'SLA: 5 días hábiles para completar la auditoría',
  },
  PENDIENTE: {
    icon: <Clock className="h-4 w-4" />,
    colorClass: 'border-orange-200 bg-orange-50 text-orange-800',
    descripcion:
      'En espera de información adicional solicitada por el auditor. Motivo registrado en el historial.',
    requisitos: [
      'La empresa tiene hasta la fecha indicada para responder',
      'Después de 8 días sin respuesta se genera una alerta',
      'El auditor puede devolver a EN_AUDITORIA o glosar directamente',
    ],
  },
  CREACION_SINIESTRO: {
    icon: <Link className="h-4 w-4" />,
    colorClass: 'border-violet-200 bg-violet-50 text-violet-800',
    descripcion:
      'En espera de la creación del siniestro en el sistema externo. El siniestro debe ser vinculado antes de continuar.',
    requisitos: [
      'Número de siniestro asignado por el sistema externo',
      'Siniestro vinculado a la incapacidad antes de avanzar',
    ],
    sla: 'SLA: 1 día hábil para vincular el siniestro',
  },
  LIQUIDACION: {
    icon: <CreditCard className="h-4 w-4" />,
    colorClass: 'border-green-200 bg-green-50 text-green-800',
    descripcion:
      'Aprobada por el auditor. El liquidador debe calcular el valor y autorizar el pago a la empresa.',
    requisitos: [
      'IBL calculado (promedio IBC 6 meses previos a la incapacidad)',
      'Desglose de liquidación diligenciado',
      'Método de pago seleccionado (Cheque / Oxirre)',
      'Completar para pasar a PAGADA, o devolver a auditoría si hay un error',
    ],
    sla: 'SLA: 3 días hábiles para completar la liquidación',
  },
  LIQUIDACION_PARCIAL: {
    icon: <CreditCard className="h-4 w-4" />,
    colorClass: 'border-teal-200 bg-teal-50 text-teal-800',
    descripcion:
      'Aprobada parcialmente. El primer día no es pagable (coincide con el siniestro) o el auditor ajustó los días.',
    requisitos: [
      'Mismos requisitos que LIQUIDACION',
      'El rango de días pagados está especificado en la plantilla de auditoría',
    ],
    sla: 'SLA: 3 días hábiles para completar la liquidación',
  },
  GLOSADA: {
    icon: <Ban className="h-4 w-4" />,
    colorClass: 'border-red-200 bg-red-50 text-red-800',
    descripcion:
      'Caso cerrado — la incapacidad fue glosada. Se notificó a la empresa por correo electrónico.',
    requisitos: [
      'Notificación PDF generada y adjunta al expediente',
      'Estado terminal — no admite más transiciones',
    ],
  },
  PAGADA: {
    icon: <CheckCircle className="h-4 w-4" />,
    colorClass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    descripcion: 'Pago completo completado.',
    requisitos: ['Estado terminal'],
  },
  PAGADA_PARCIAL: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    colorClass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    descripcion: 'Pago parcial completado.',
    requisitos: ['Estado terminal'],
  },
};

interface StateDescriptionPanelProps {
  estado: EstadoIncapacidad | string;
  /** Pass auditoria validation issues to show inline when estado === RADICADA */
  auditoriaResultados?: ValidationIssue[];
}

export function StateDescriptionPanel({
  estado,
  auditoriaResultados,
}: StateDescriptionPanelProps) {
  const info = STATE_INFO[estado];
  if (!info) return null;

  return (
    <div
      className={`rounded-lg border p-4 text-sm space-y-3 ${info.colorClass}`}
      data-testid="state-description-panel"
      aria-label={`Descripción del estado ${estado}`}
    >
      {/* Header: icon + descripción */}
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex-shrink-0" aria-hidden="true">
          {info.icon}
        </span>
        <p className="leading-snug">{info.descripcion}</p>
      </div>

      {/* Requisitos */}
      {info.requisitos.length > 0 && (
        <div>
          <p className="font-semibold text-xs uppercase tracking-wide opacity-70 mb-1">
            Para avanzar / tener en cuenta
          </p>
          <ul className="space-y-1 list-disc list-inside" role="list">
            {info.requisitos.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* SLA */}
      {info.sla && (
        <p
          className="text-xs font-medium opacity-80 border-t border-current/20 pt-2"
          data-testid="sla-hint"
        >
          {info.sla}
        </p>
      )}

      {/* Validaciones inline (solo RADICADA cuando se proveen resultados) */}
      {estado === 'RADICADA' && auditoriaResultados && auditoriaResultados.length > 0 && (
        <div className="border-t border-slate-200 pt-3">
          <ValidacionesPanel issues={auditoriaResultados} isLoading={false} />
        </div>
      )}

      {/* Alerta PENDIENTE > 8 días */}
      {estado === 'PENDIENTE' && (
        <p
          className="text-orange-700 font-medium flex items-center gap-1"
          data-testid="pendiente-warning"
        >
          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
          Si han pasado 8+ días sin respuesta, puede glosar directamente o devolver a auditoría.
        </p>
      )}
    </div>
  );
}
