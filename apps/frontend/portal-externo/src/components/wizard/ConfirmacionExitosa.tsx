import { CheckCircle, FileText, Search, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ConfirmacionExitosaProps {
  numeroRadicacion: number;
  onConsultarEstado?: () => void;
  onRadicarOtra: () => void;
}

/**
 * Componente de confirmación exitosa después de radicar incapacidad
 * Muestra número de radicación y opciones de seguimiento
 */
export function ConfirmacionExitosa({
  numeroRadicacion,
  onConsultarEstado,
  onRadicarOtra,
}: ConfirmacionExitosaProps) {
  return (
    <div className="max-w-2xl mx-auto">
      {/* Icono de éxito */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-muted rounded-full mb-4">
          <CheckCircle className="h-12 w-12 text-primary" />
        </div>
        <h2 className="text-3xl font-bold text-foreground mb-2">
          ¡Incapacidad radicada exitosamente!
        </h2>
        <p className="text-muted-foreground">
          Su solicitud ha sido recibida y se encuentra en proceso de revisión
        </p>
      </div>

      {/* Número de radicación */}
      <div className="bg-muted border-2 border-primary/30 rounded-lg p-6 mb-8">
        <div className="text-center">
          <p className="text-sm font-medium text-muted-foreground mb-2">
            Número de radicación
          </p>
          <p className="text-3xl font-bold text-primary mb-2">
            {numeroRadicacion}
          </p>
          <p className="text-sm text-muted-foreground">
            Guarde este número para consultar el estado de su solicitud
          </p>
        </div>
      </div>

      {/* Timeline estimado */}
      <div className="bg-background border border-border rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Proceso estimado
        </h3>
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <span className="text-primary-foreground text-sm font-bold">✓</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">Radicada</p>
              <p className="text-sm text-muted-foreground">Hoy</p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                <span className="text-primary text-sm font-bold">2</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">En auditoría</p>
              <p className="text-sm text-muted-foreground">1-2 días hábiles</p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                <span className="text-muted-foreground text-sm font-bold">3</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">Aprobación</p>
              <p className="text-sm text-muted-foreground">3-5 días hábiles</p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                <span className="text-muted-foreground text-sm font-bold">4</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">Pago</p>
              <p className="text-sm text-muted-foreground">5-10 días hábiles</p>
            </div>
          </div>
        </div>
      </div>

      {/* Información adicional */}
      <div className="bg-accent/10 border border-accent/30 rounded-lg p-4 mb-8">
        <div className="flex gap-3">
          <FileText className="h-5 w-5 text-accent-foreground flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-foreground mb-1">
              Importante
            </p>
            <ul className="text-sm text-foreground/80 space-y-1 list-disc list-inside">
              <li>Conserve el número de radicación para hacer seguimiento</li>
              <li>Recibirá notificaciones por email sobre cambios de estado</li>
              <li>Puede consultar el estado en cualquier momento</li>
              <li>Si tiene observaciones, se le notificará para corregir</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        {onConsultarEstado && (
          <Button
            variant="outline"
            onClick={onConsultarEstado}
            className="flex items-center gap-2"
          >
            <Search className="h-4 w-4" />
            Consultar Estado
          </Button>
        )}
        <Button
          onClick={onRadicarOtra}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Radicar otra Incapacidad
        </Button>
      </div>

      {/* Nota sobre descarga de comprobante (Fase 2) */}
      <div className="text-center mt-8">
        <p className="text-sm text-muted-foreground">
          La opción de descargar comprobante PDF estará disponible próximamente
        </p>
      </div>
    </div>
  );
}
