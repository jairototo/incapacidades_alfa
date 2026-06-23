import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { HistorialEstado } from '@/types/incapacidad';
import { formatDate } from '@/utils/formatters';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  FileText,
  DollarSign,
  AlertTriangle,
  Circle,
} from 'lucide-react';

interface HistorialTimelineProps {
  historial: HistorialEstado[];
}

/**
 * Componente Timeline para mostrar el historial de estados de una incapacidad
 * Muestra cambios de estado, usuario responsable y observaciones
 */
export function HistorialTimeline({ historial }: HistorialTimelineProps) {
  if (historial.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No hay historial de cambios para esta incapacidad.
        </AlertDescription>
      </Alert>
    );
  }

  // Ordenar por fecha descendente (más reciente primero)
  const sortedHistorial = [...historial].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-4">
      {/* Timeline */}
      <div className="relative">
        {/* Línea vertical */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

        {sortedHistorial.map((item, index) => (
          <div key={item.id} className="relative flex gap-4 pb-8">
            {/* Ícono */}
            <div className="relative z-10 flex-shrink-0">
              <div
                className={`
                  w-12 h-12 rounded-full flex items-center justify-center
                  ${getEstadoBackground(item.estado_nuevo)}
                `}
              >
                {getEstadoIcon(item.estado_nuevo)}
              </div>
            </div>

            {/* Contenido */}
            <Card className="flex-1">
              <CardContent className="pt-6">
                <div className="space-y-3">
                  {/* Header del cambio */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant={getEstadoBadgeVariant(item.estado_nuevo)}>
                          {STATE_LABELS[item.estado_nuevo] || item.estado_nuevo}
                        </Badge>

                        {index === 0 && (
                          <Badge variant="outline" className="text-xs">
                            Más reciente
                          </Badge>
                        )}
                      </div>

                      <p className="text-sm text-slate-500">
                        {formatDate(item.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Cambio de estado */}
                  {item.estado_anterior && (
                    <div className="flex items-center gap-2 text-sm">
                      <Badge variant="outline" className="text-xs">
                        {STATE_LABELS[item.estado_anterior] || item.estado_anterior}
                      </Badge>
                      <span className="text-slate-400">→</span>
                      <Badge variant={getEstadoBadgeVariant(item.estado_nuevo)} className="text-xs">
                        {STATE_LABELS[item.estado_nuevo] || item.estado_nuevo}
                      </Badge>
                    </div>
                  )}

                  {/* Usuario */}
                  {item.cambiado_por && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <span className="font-medium">
                        {item.cambiado_por_nombre || item.cambiado_por}
                      </span>
                    </div>
                  )}

                  {/* Observación */}
                  {item.observacion && (
                    <div className="pt-2 border-t border-slate-100">
                      <p className="text-sm font-medium text-slate-700 mb-1">Observaciones:</p>
                      <p className="text-sm text-slate-600 italic bg-slate-50 p-3 rounded-md">
                        {item.observacion}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>

      {/* Resumen */}
      <Card className="bg-slate-50">
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-slate-900">{historial.length}</p>
              <p className="text-sm text-slate-500">Cambios totales</p>
            </div>
            
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {historial.filter((h) => h.cambiado_por).length}
              </p>
              <p className="text-sm text-slate-500">Con responsable</p>
            </div>
            
            <div>
              <p className="text-2xl font-bold text-orange-600">
                {historial.filter((h) => h.observacion).length}
              </p>
              <p className="text-sm text-slate-500">Con observaciones</p>
            </div>
            
            <div>
              <p className="text-2xl font-bold text-green-600">
                {calculateDaysInProcess(historial)}
              </p>
              <p className="text-sm text-slate-500">Días en proceso</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// State labels for display
const STATE_LABELS: Record<string, string> = {
  RADICADA: 'Radicada',
  EN_AUDITORIA: 'En Auditoría',
  PENDIENTE: 'Pendiente',
  CREACION_SINIESTRO: 'Creación de Siniestro',
  LIQUIDACION: 'En Liquidación',
  LIQUIDACION_PARCIAL: 'En Liquidación Parcial',
  GLOSADA: 'Glosada',
  PAGADA: 'Pagada',
  PAGADA_PARCIAL: 'Pagada Parcialmente',
};

// Helper functions
function getEstadoIcon(estado: string) {
  switch (estado) {
    case 'RADICADA':
      return <FileText className="h-6 w-6 text-white" />;
    case 'EN_AUDITORIA':
      return <Clock className="h-6 w-6 text-white" />;
    case 'PENDIENTE':
      return <AlertTriangle className="h-6 w-6 text-white" />;
    case 'CREACION_SINIESTRO':
      return <FileText className="h-6 w-6 text-white" />;
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
      return <DollarSign className="h-6 w-6 text-white" />;
    case 'GLOSADA':
      return <XCircle className="h-6 w-6 text-white" />;
    case 'PAGADA':
    case 'PAGADA_PARCIAL':
      return <CheckCircle className="h-6 w-6 text-white" />;
    default:
      return <Circle className="h-6 w-6 text-white" />;
  }
}

function getEstadoBackground(estado: string): string {
  switch (estado) {
    case 'RADICADA':
      return 'bg-blue-500';
    case 'EN_AUDITORIA':
      return 'bg-yellow-500';
    case 'PENDIENTE':
      return 'bg-orange-500';
    case 'CREACION_SINIESTRO':
      return 'bg-cyan-500';
    case 'LIQUIDACION':
      return 'bg-purple-500';
    case 'LIQUIDACION_PARCIAL':
      return 'bg-indigo-500';
    case 'GLOSADA':
      return 'bg-red-500';
    case 'PAGADA':
      return 'bg-green-500';
    case 'PAGADA_PARCIAL':
      return 'bg-teal-500';
    default:
      return 'bg-slate-400';
  }
}

function getEstadoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'RADICADA':
      return 'secondary';
    case 'EN_AUDITORIA':
      return 'default';
    case 'PENDIENTE':
      return 'outline';
    case 'CREACION_SINIESTRO':
      return 'secondary';
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
      return 'default';
    case 'GLOSADA':
      return 'destructive';
    case 'PAGADA':
    case 'PAGADA_PARCIAL':
      return 'default';
    default:
      return 'secondary';
  }
}

function calculateDaysInProcess(historial: HistorialEstado[]): number {
  if (historial.length === 0) return 0;
  
  const sorted = [...historial].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  
  const firstDate = new Date(sorted[0].created_at);
  const lastDate = new Date(sorted[sorted.length - 1].created_at);
  
  const diffTime = Math.abs(lastDate.getTime() - firstDate.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  return diffDays;
}
