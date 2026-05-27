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
 */
export function GestionActions({ incapacidad, onAction, isLoading }: GestionActionsProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  
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
    
    // Validar que haya observación si es requerida
    const needsObservation = selectedAction === 'RECHAZADA' || selectedAction === 'OBSERVADA';
    if (needsObservation && !data.observacion?.trim()) {
      return;
    }
    
    onAction({ 
      nuevoEstado: selectedAction, 
      observacion: data.observacion 
    });
  };

  const handleCancelAction = () => {
    setSelectedAction(null);
    reset();
  };

  const needsObservation = selectedAction === 'RECHAZADA' || selectedAction === 'OBSERVADA';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
        {/* Aprobar */}
        <Button
          type="button"
          variant={selectedAction === 'APROBADA' ? 'default' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'APROBADA' ? 'ring-2 ring-green-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('APROBADA')}
          disabled={isLoading}
        >
          <CheckCircle className="h-10 w-10 text-green-600" />
          <div className="text-center">
            <p className="font-semibold">Aprobar</p>
            <p className="text-xs text-slate-500 mt-1">
              Aprobar incapacidad para pago
            </p>
          </div>
        </Button>

        {/* Observar */}
        <Button
          type="button"
          variant={selectedAction === 'OBSERVADA' ? 'default' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'OBSERVADA' ? 'ring-2 ring-orange-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('OBSERVADA')}
          disabled={isLoading}
        >
          <AlertCircle className="h-10 w-10 text-orange-600" />
          <div className="text-center">
            <p className="font-semibold">Observar</p>
            <p className="text-xs text-slate-500 mt-1">
              Solicitar información adicional
            </p>
          </div>
        </Button>

        {/* Rechazar */}
        <Button
          type="button"
          variant={selectedAction === 'RECHAZADA' ? 'destructive' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'RECHAZADA' ? 'ring-2 ring-red-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('RECHAZADA')}
          disabled={isLoading}
        >
          <XCircle className="h-10 w-10 text-red-600" />
          <div className="text-center">
            <p className="font-semibold">Rechazar</p>
            <p className="text-xs text-slate-500 mt-1">
              Rechazar definitivamente
            </p>
          </div>
        </Button>
      </div>

      {/* Formulario de observaciones */}
      {selectedAction && (
        <div className="space-y-4 p-6 bg-slate-50 rounded-lg border-2 border-slate-200">
          <div className="space-y-2">
            <Label htmlFor="observacion" className="text-base">
              Observaciones {needsObservation && <span className="text-red-500">*</span>}
            </Label>
            <p className="text-sm text-slate-500">
              {selectedAction === 'APROBADA' && 'Opcional: Agregue comentarios adicionales sobre la aprobación'}
              {selectedAction === 'OBSERVADA' && 'Requerido: Describa la información faltante o las correcciones necesarias'}
              {selectedAction === 'RECHAZADA' && 'Requerido: Justifique las razones del rechazo'}
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
                selectedAction === 'APROBADA' ? 'bg-green-600 hover:bg-green-700' :
                selectedAction === 'OBSERVADA' ? 'bg-orange-600 hover:bg-orange-700' :
                'bg-red-600 hover:bg-red-700'
              }
            >
              {isLoading ? 'Procesando...' : `Confirmar ${selectedAction}`}
            </Button>
          </div>
        </div>
      )}

      {/* Información adicional */}
      {selectedAction && (
        <Alert className="bg-blue-50 border-blue-200">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            {selectedAction === 'APROBADA' && 'La incapacidad quedará lista para generar orden de pago.'}
            {selectedAction === 'OBSERVADA' && 'Se notificará al solicitante para que complete la información.'}
            {selectedAction === 'RECHAZADA' && 'Esta acción es definitiva y no se podrá revertir.'}
          </AlertDescription>
        </Alert>
      )}
    </form>
  );
}
