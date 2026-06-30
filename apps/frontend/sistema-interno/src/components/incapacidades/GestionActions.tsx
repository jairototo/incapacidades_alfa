import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Incapacidad } from '@/types/incapacidad';
import { useHasRole } from '@/store/authStore';
import { AuditorApprovalTemplateModal } from '@/components/incapacidades/AuditorApprovalTemplateModal';
import type { PlantillaAuditoriaCreate } from '@/services/plantillaAuditoria';

const gestionSchema = z.object({
  observacion: z.string().optional(),
});

type GestionFormData = z.infer<typeof gestionSchema>;

interface GestionActionsProps {
  incapacidad: Incapacidad;
  onAction: (data: { nuevoEstado: string; observacion?: string }) => void;
  isLoading?: boolean;
}

/**
 * Componente de acciones de auditoría para incapacidades
 * Permite aprobar, observar o rechazar incapacidades
 *
 * Para LIQUIDACION / LIQUIDACION_PARCIAL abre el AuditorApprovalTemplateModal
 * antes de confirmar. El botón solo se muestra a roles AUDITOR y ADMIN.
 */
export function GestionActions({ incapacidad, onAction, isLoading }: GestionActionsProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [pendingLiquidacion, setPendingLiquidacion] = useState<'LIQUIDACION' | 'LIQUIDACION_PARCIAL' | null>(null);

  const isAuditorOrAdmin = useHasRole(['AUDITOR', 'ADMIN']);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<GestionFormData>({
    resolver: zodResolver(gestionSchema),
  });

  const onSubmit = (data: GestionFormData) => {
    if (!selectedAction) return;

    // LIQUIDACION / LIQUIDACION_PARCIAL → open the template modal instead
    if (selectedAction === 'LIQUIDACION' || selectedAction === 'LIQUIDACION_PARCIAL') {
      setPendingLiquidacion(selectedAction as 'LIQUIDACION' | 'LIQUIDACION_PARCIAL');
      setTemplateModalOpen(true);
      return;
    }

    // Validar que haya observación si es requerida
    const needsObservation = selectedAction === 'GLOSADA' || selectedAction === 'PENDIENTE';
    if (needsObservation && !data.observacion?.trim()) {
      return;
    }

    onAction({
      nuevoEstado: selectedAction,
      observacion: data.observacion,
    });
  };

  const handleCancelAction = () => {
    setSelectedAction(null);
    reset();
  };

  /**
   * Called by AuditorApprovalTemplateModal on successful submit.
   * Fires the parent onAction with the pending liquidacion state.
   */
  const handleTemplateConfirm = (
    _plantilla: PlantillaAuditoriaCreate,
    observacion: string,
  ) => {
    if (!pendingLiquidacion) return;
    onAction({
      nuevoEstado: pendingLiquidacion,
      observacion: observacion || undefined,
    });
    setPendingLiquidacion(null);
    setSelectedAction(null);
    reset();
  };

  const handleTemplateCancel = () => {
    setPendingLiquidacion(null);
    setTemplateModalOpen(false);
    setSelectedAction(null);  // Fix 4: also clear the action panel so it collapses
  };

  const needsObservation = selectedAction === 'GLOSADA' || selectedAction === 'PENDIENTE';

  return (
    <>
      {/* Template modal — only mounted when needed */}
      {pendingLiquidacion && (
        <AuditorApprovalTemplateModal
          incapacidad={incapacidad}
          accion={pendingLiquidacion}
          open={templateModalOpen}
          onOpenChange={setTemplateModalOpen}
          onConfirm={handleTemplateConfirm}
          onCancel={handleTemplateCancel}
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Información del estado actual */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Estado actual: <strong>{incapacidad.estado}</strong>.
            Seleccione una acción para cambiar el estado de la incapacidad.
          </AlertDescription>
        </Alert>

        {/* Botones de acción */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Aprobar → LIQUIDACION (solo AUDITOR/ADMIN) */}
          {isAuditorOrAdmin && (
            <Button
              type="button"
              variant={selectedAction === 'LIQUIDACION' ? 'default' : 'outline'}
              className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
                selectedAction === 'LIQUIDACION' ? 'ring-2 ring-green-500 shadow-lg' : ''
              }`}
              onClick={() => setSelectedAction('LIQUIDACION')}
              disabled={isLoading}
            >
              <CheckCircle className="h-10 w-10 text-green-600" />
              <div className="text-center">
                <p className="font-semibold">Liquidar</p>
                <p className="text-xs text-slate-500 mt-1">
                  Pasar a liquidación completa
                </p>
              </div>
            </Button>
          )}

          {/* Liquidar Parcial → LIQUIDACION_PARCIAL (solo AUDITOR/ADMIN) */}
          {isAuditorOrAdmin && (
            <Button
              type="button"
              variant={selectedAction === 'LIQUIDACION_PARCIAL' ? 'default' : 'outline'}
              className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
                selectedAction === 'LIQUIDACION_PARCIAL' ? 'ring-2 ring-teal-500 shadow-lg' : ''
              }`}
              onClick={() => setSelectedAction('LIQUIDACION_PARCIAL')}
              disabled={isLoading}
            >
              <CheckCircle className="h-10 w-10 text-teal-600" />
              <div className="text-center">
                <p className="font-semibold">Liquidar Parcial</p>
                <p className="text-xs text-slate-500 mt-1">
                  Pasar a liquidación parcial
                </p>
              </div>
            </Button>
          )}

          {/* Poner en Pendiente */}
          <Button
            type="button"
            variant={selectedAction === 'PENDIENTE' ? 'default' : 'outline'}
            className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
              selectedAction === 'PENDIENTE' ? 'ring-2 ring-orange-500 shadow-lg' : ''
            }`}
            onClick={() => setSelectedAction('PENDIENTE')}
            disabled={isLoading}
          >
            <AlertCircle className="h-10 w-10 text-orange-600" />
            <div className="text-center">
              <p className="font-semibold">Poner en Pendiente</p>
              <p className="text-xs text-slate-500 mt-1">
                Solicitar información adicional
              </p>
            </div>
          </Button>

          {/* Glosar → GLOSADA */}
          <Button
            type="button"
            variant={selectedAction === 'GLOSADA' ? 'destructive' : 'outline'}
            className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
              selectedAction === 'GLOSADA' ? 'ring-2 ring-red-500 shadow-lg' : ''
            }`}
            onClick={() => setSelectedAction('GLOSADA')}
            disabled={isLoading}
          >
            <XCircle className="h-10 w-10 text-red-600" />
            <div className="text-center">
              <p className="font-semibold">Glosar</p>
              <p className="text-xs text-slate-500 mt-1">
                Marcar como glosada
              </p>
            </div>
          </Button>
        </div>

        {/* Formulario de observaciones */}
        {selectedAction && selectedAction !== 'LIQUIDACION' && selectedAction !== 'LIQUIDACION_PARCIAL' && (
          <div className="space-y-4 p-4 bg-slate-50 rounded-lg border-2 border-slate-200">
            <div className="space-y-2">
              <Label htmlFor="observacion" className="text-base">
                Observaciones {needsObservation && <span className="text-red-500">*</span>}
              </Label>
              <p className="text-sm text-slate-500">
                {selectedAction === 'PENDIENTE' && 'Requerido: Describa la información faltante o las correcciones necesarias'}
                {selectedAction === 'GLOSADA' && 'Requerido: Justifique las razones de la glosa'}
              </p>
              <Textarea
                id="observacion"
                {...register('observacion', {
                  required: needsObservation ? 'Este campo es obligatorio' : false,
                  minLength: needsObservation ? {
                    value: 10,
                    message: 'La observación debe tener al menos 10 caracteres'
                  } : undefined,
                })}
                placeholder="Describa las razones de su decisión..."
                rows={5}
                className="resize-none"
                disabled={isLoading}
              />
              {errors.observacion && (
                <p className="text-sm text-red-500">{errors.observacion.message}</p>
              )}
            </div>

            {/* Botones de confirmación */}
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancelAction}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className={
                  selectedAction === 'PENDIENTE' ? 'bg-orange-600 hover:bg-orange-700' :
                  'bg-red-600 hover:bg-red-700'
                }
              >
                {isLoading ? 'Procesando...' : `Confirmar ${selectedAction}`}
              </Button>
            </div>
          </div>
        )}

        {/* For LIQUIDACION / LIQUIDACION_PARCIAL, show a notice that the template modal will open */}
        {(selectedAction === 'LIQUIDACION' || selectedAction === 'LIQUIDACION_PARCIAL') && (
          <div className="space-y-4 p-4 bg-slate-50 rounded-lg border-2 border-slate-200">
            <p className="text-sm text-slate-600">
              Se abrirá el formulario de plantilla de auditoría para completar antes de confirmar la{' '}
              {selectedAction === 'LIQUIDACION' ? 'liquidación completa' : 'liquidación parcial'}.
            </p>
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancelAction}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                {isLoading ? 'Procesando...' : 'Continuar con plantilla'}
              </Button>
            </div>
          </div>
        )}

        {/* Información adicional */}
        {selectedAction && selectedAction !== 'LIQUIDACION' && selectedAction !== 'LIQUIDACION_PARCIAL' && (
          <Alert className="bg-blue-50 border-blue-200">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              {selectedAction === 'PENDIENTE' && 'Se notificará al solicitante para que complete la información.'}
              {selectedAction === 'GLOSADA' && 'Esta acción marca la incapacidad como glosada.'}
            </AlertDescription>
          </Alert>
        )}
      </form>
    </>
  );
}
