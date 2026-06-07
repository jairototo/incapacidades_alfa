import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CornerDownLeft, Loader2, Mail } from 'lucide-react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { preIncapacidadService } from '@/services/preIncapacidadService';

const schema = z.object({
  motivo: z.string().min(20, 'El motivo debe tener al menos 20 caracteres').max(2000),
});
type FormData = z.infer<typeof schema>;

interface Props {
  preIncapacidadId: string;
  numeroRadicacion: number;
  solicitanteCorreo: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function DevolucionModal({
  preIncapacidadId,
  numeroRadicacion,
  solicitanteCorreo,
  open,
  onOpenChange,
  onSuccess,
}: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      preIncapacidadService.devolver(preIncapacidadId, { motivo: data.motivo }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidades-bandeja'] });
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', preIncapacidadId] });
      toast({
        title: 'Pre-incapacidad devuelta',
        description: result.email_enviado
          ? `Carta de devolución enviada a ${solicitanteCorreo}`
          : 'Estado actualizado. El email no pudo enviarse.',
      });
      reset();
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: unknown) => {
      const msg =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            'No se pudo procesar la devolución';
      toast({
        title: 'Error al devolver',
        description: msg,
        variant: 'destructive',
      });
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CornerDownLeft className="h-5 w-5 text-orange-500" />
            Devolver radicación N° {numeroRadicacion}
          </DialogTitle>
          <DialogDescription>
            Se enviará una carta formal por email a{' '}
            <strong>{solicitanteCorreo}</strong> explicando el motivo de la devolución.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <Alert>
            <Mail className="h-4 w-4" />
            <AlertDescription>
              El estado cambiará a <strong>DEVUELTA</strong> y se enviará una carta
              empresarial formal al solicitante.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="motivo">
              Motivo de devolución <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="motivo"
              rows={6}
              placeholder="Describa detalladamente qué información requiere corrección y cómo el solicitante debe proceder..."
              {...register('motivo')}
              className={errors.motivo ? 'border-red-500' : ''}
            />
            {errors.motivo && (
              <p className="text-sm text-red-600">{errors.motivo.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                onOpenChange(false);
                reset();
              }}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="destructive" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Devolver y enviar email
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
