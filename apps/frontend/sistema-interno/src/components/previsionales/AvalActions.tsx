/**
 * AvalActions — Botones de decisión humana de aval (Task 4.2,
 * `POST /previsionales/incapacidades/{id}/aval`). "Avalar" dispara el
 * request directo; "No avalar" abre un modal que exige `motivo` (regla AC:
 * "el aval jamás se autocalcula" -- el backend rechaza `aval='NO'` sin
 * `motivo` con 400 ANTES de tocar la BD). El campo se valida con zod en el
 * cliente para dar feedback inmediato en vez de esperar el 400 del server.
 *
 * Presentacional + su propio estado de diálogo/formulario -- las mutations
 * reales (useMutation, invalidación de caché) las controla el padre
 * (`AuditoriaPrevisionalPage`) vía las props `onAvalar`/`onNoAvalar`. El
 * diálogo se cierra de forma optimista al enviar "No avalar": si la
 * mutation falla, el padre muestra el error en la página (fuera del
 * diálogo) -- ver `avalError` en `AuditoriaPrevisionalPage.tsx`.
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CheckCircle2, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const motivoSchema = z.object({
  motivo: z.string().trim().min(1, 'El motivo es obligatorio para no avalar.'),
});
type MotivoForm = z.infer<typeof motivoSchema>;

interface AvalActionsProps {
  aval: string | null;
  motivoNoAval: string | null;
  isSubmitting: boolean;
  onAvalar: () => void;
  onNoAvalar: (motivo: string) => void;
}

export function AvalActions({
  aval,
  motivoNoAval,
  isSubmitting,
  onAvalar,
  onNoAvalar,
}: AvalActionsProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MotivoForm>({
    resolver: zodResolver(motivoSchema),
    defaultValues: { motivo: '' },
  });

  const handleOpenChange = (open: boolean) => {
    setDialogOpen(open);
    if (!open) reset();
  };

  const submitNoAval = (values: MotivoForm) => {
    onNoAvalar(values.motivo.trim());
    setDialogOpen(false);
    reset();
  };

  if (aval === 'SI') {
    return (
      <Badge className="bg-green-100 text-green-800 hover:bg-green-100" data-testid="aval-badge-si">
        AVALADO
      </Badge>
    );
  }

  if (aval === 'NO') {
    return (
      <div className="space-y-1" data-testid="aval-badge-no">
        <Badge className="bg-red-100 text-red-800 hover:bg-red-100">NO AVALADO</Badge>
        {motivoNoAval && <p className="text-xs text-slate-600">Motivo: {motivoNoAval}</p>}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button size="sm" onClick={onAvalar} disabled={isSubmitting} data-testid="btn-avalar">
        <CheckCircle2 className="mr-1.5 h-4 w-4" />
        Avalar
      </Button>
      <Button
        type="button"
        size="sm"
        variant="outline"
        disabled={isSubmitting}
        onClick={() => setDialogOpen(true)}
        data-testid="btn-no-avalar"
      >
        <XCircle className="mr-1.5 h-4 w-4" />
        No avalar
      </Button>

      <Dialog open={dialogOpen} onOpenChange={handleOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>No avalar incapacidad</DialogTitle>
            <DialogDescription>
              Indica el motivo por el que esta incapacidad no se avala. Este campo es
              obligatorio.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit(submitNoAval)} className="space-y-3" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="motivo-no-aval">Motivo</Label>
              <Textarea
                id="motivo-no-aval"
                rows={4}
                disabled={isSubmitting}
                {...register('motivo')}
              />
              {errors.motivo && <p className="text-xs text-destructive">{errors.motivo.message}</p>}
            </div>
            <DialogFooter>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Guardando...' : 'Confirmar no aval'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
