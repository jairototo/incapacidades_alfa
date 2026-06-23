/**
 * TimelineEstados - Componente para mostrar el historial de cambios de estado.
 * 
 * Muestra una línea de tiempo vertical con todos los cambios de estado por los que
 * ha pasado una incapacidad, con iconos, fechas formateadas y observaciones.
 * 
 * @example
 * ```tsx
 * <TimelineEstados historial={incapacidad.historial_estados} />
 * ```
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { HistorialEstadoSimple, EstadoIncapacidad } from '@/types/consulta';
import { formatearFechaHora, formatearEstado } from '@/utils/formatters';
import {
  Clock,
  AlertTriangle,
  XCircle,
  CreditCard,
  DollarSign,
  FileText,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ========== TIPOS ==========

interface TimelineEstadosProps {
  /** Historial de estados de la incapacidad */
  historial: HistorialEstadoSimple[];
  
  /** Clase CSS adicional para el contenedor */
  className?: string;
}

// ========== MAPAS DE CONFIGURACIÓN ==========

/**
 * Mapa de colores de badge por estado.
 */
const ESTADO_COLORS: Record<EstadoIncapacidad, string> = {
  RADICADA: 'bg-blue-100 text-blue-800',
  EN_AUDITORIA: 'bg-yellow-100 text-yellow-800',
  PENDIENTE: 'bg-orange-100 text-orange-800',
  CREACION_SINIESTRO: 'bg-purple-100 text-purple-800',
  LIQUIDACION: 'bg-indigo-100 text-indigo-800',
  LIQUIDACION_PARCIAL: 'bg-indigo-100 text-indigo-800',
  GLOSADA: 'bg-red-100 text-red-800',
  PAGADA: 'bg-emerald-100 text-emerald-800',
  PAGADA_PARCIAL: 'bg-emerald-100 text-emerald-800',
};

/**
 * Mapa de iconos por estado.
 */
const ESTADO_ICONS: Record<EstadoIncapacidad, React.ElementType> = {
  RADICADA: FileText,
  EN_AUDITORIA: Clock,
  PENDIENTE: AlertTriangle,
  CREACION_SINIESTRO: FileText,
  LIQUIDACION: CreditCard,
  LIQUIDACION_PARCIAL: CreditCard,
  GLOSADA: XCircle,
  PAGADA: DollarSign,
  PAGADA_PARCIAL: DollarSign,
};

/**
 * Mapa de descripciones por estado.
 */
const ESTADO_DESCRIPTIONS: Record<EstadoIncapacidad, string> = {
  RADICADA: 'Incapacidad recibida y en cola para revisión',
  EN_AUDITORIA: 'En proceso de auditoría médica',
  PENDIENTE: 'Requiere correcciones o información adicional',
  CREACION_SINIESTRO: 'En creación de siniestro (ARL)',
  LIQUIDACION: 'En proceso de liquidación',
  LIQUIDACION_PARCIAL: 'En liquidación parcial',
  GLOSADA: 'Incapacidad glosada',
  PAGADA: 'Pago efectuado exitosamente',
  PAGADA_PARCIAL: 'Pagada parcialmente',
};

// ========== SUB-COMPONENTES ==========

/**
 * Componente para un item individual del timeline.
 */
interface TimelineItemProps {
  estado: HistorialEstadoSimple;
  isLast: boolean;
}

function TimelineItem({ estado, isLast }: TimelineItemProps) {
  const Icon = ESTADO_ICONS[estado.estado];
  const colorClass = ESTADO_COLORS[estado.estado];
  const description = ESTADO_DESCRIPTIONS[estado.estado];

  return (
    <div className="relative pb-8">
      {/* Línea vertical conectora */}
      {!isLast && (
        <div className="absolute left-5 top-5 -ml-px h-full w-0.5 bg-gray-200" />
      )}

      <div className="relative flex items-start space-x-3">
        {/* Icono circular */}
        <div className={cn(
          'relative flex h-10 w-10 items-center justify-center rounded-full',
          colorClass
        )}>
          <Icon className="h-5 w-5" />
        </div>

        {/* Contenido */}
        <div className="min-w-0 flex-1 space-y-2">
          {/* Header con badge y fecha */}
          <div className="flex items-center gap-3 flex-wrap">
            <Badge className={colorClass}>
              {formatearEstado(estado.estado)}
            </Badge>
            <span className="text-sm text-gray-500">
              {formatearFechaHora(estado.fecha_cambio)}
            </span>
          </div>

          {/* Descripción del estado */}
          <p className="text-sm text-gray-600">
            {description}
          </p>

          {/* Observaciones (solo para estado PENDIENTE) */}
          {estado.estado === 'PENDIENTE' && estado.observaciones && (
            <div className="mt-2 rounded-lg bg-orange-50 p-3 border border-orange-200">
              <p className="text-xs font-semibold text-orange-800 mb-1">
                Observaciones del auditor:
              </p>
              <p className="text-sm text-orange-900">
                {estado.observaciones}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ========== COMPONENTE PRINCIPAL ==========

/**
 * TimelineEstados - Muestra el historial de cambios de estado en formato timeline.
 */
export function TimelineEstados({ historial, className }: TimelineEstadosProps) {
  // Ordenar historial por fecha (más reciente primero)
  const historialOrdenado = [...historial].sort((a, b) => {
    return new Date(b.fecha_cambio).getTime() - new Date(a.fecha_cambio).getTime();
  });

  // Si no hay historial, mostrar mensaje
  if (historialOrdenado.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Historial de Estados
          </CardTitle>
          <CardDescription>
            Seguimiento cronológico de los cambios de estado
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-gray-500">
            <Clock className="h-12 w-12 mb-2 opacity-30" />
            <p className="text-sm">No hay historial de cambios disponible</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Historial de Estados
        </CardTitle>
        <CardDescription>
          Seguimiento cronológico de los cambios de estado ({historialOrdenado.length} {historialOrdenado.length === 1 ? 'evento' : 'eventos'})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flow-root">
          <ul className="-mb-8">
            {historialOrdenado.map((estado, index) => (
              <li key={`${estado.estado}-${estado.fecha_cambio}`}>
                <TimelineItem
                  estado={estado}
                  isLast={index === historialOrdenado.length - 1}
                />
              </li>
            ))}
          </ul>
        </div>

        {/* Footer informativo */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="flex items-center gap-1.5 text-xs text-gray-500">
            <Info className="h-3.5 w-3.5 shrink-0" />
            <span>Los estados se muestran en orden cronológico descendente (más reciente primero)</span>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
