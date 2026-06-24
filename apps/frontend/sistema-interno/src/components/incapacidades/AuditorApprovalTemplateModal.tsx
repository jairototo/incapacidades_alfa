/**
 * AuditorApprovalTemplateModal
 *
 * Modal que permite al auditor completar una plantilla de auditoría antes de
 * confirmar una acción de LIQUIDACION o LIQUIDACION_PARCIAL. Tras el submit
 * exitoso muestra el texto copiable para pegar en Arpis.
 *
 * Props:
 *   incapacidad  — objeto Incapacidad con datos para pre-rellenar el form
 *   accion       — 'LIQUIDACION' | 'LIQUIDACION_PARCIAL'
 *   open         — estado de visibilidad del dialog
 *   onOpenChange — callback para abrir/cerrar
 *   onConfirm    — llamado con (plantilla, observacion) cuando el submit es exitoso
 *   onCancel     — llamado cuando el usuario cancela
 */
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Copy, Check, ClipboardCheck, Loader2 } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

import type { Incapacidad } from '@/types/incapacidad';
import { plantillaAuditoriaService, type PlantillaAuditoriaCreate } from '@/services/plantillaAuditoria';

// ---------------------------------------------------------------------------
// Zod schema
// ---------------------------------------------------------------------------
const plantillaSchema = z.object({
  canal_recepcion: z.string().min(1, 'Seleccione el canal de recepción'),
  dias_autorizados: z
    .number({ invalid_type_error: 'Ingrese un número válido' })
    .int('Debe ser un número entero')
    .positive('Los días deben ser mayor a 0'),
  fecha_inicio_autorizada: z.string().min(1, 'Ingrese la fecha de inicio'),
  fecha_fin_autorizada: z.string().min(1, 'Ingrese la fecha de fin'),
  diagnostico_cie10: z.string().optional(),
  descripcion_cie10: z.string().optional(),
  nombre_medico: z.string().optional(),
  especialidad_medico: z.string().optional(),
  nombre_ips: z.string().optional(),
  observacion: z.string().optional(),
});

type PlantillaFormData = z.infer<typeof plantillaSchema>;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface AuditorApprovalTemplateModalProps {
  incapacidad: Incapacidad;
  accion: 'LIQUIDACION' | 'LIQUIDACION_PARCIAL';
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (plantilla: PlantillaAuditoriaCreate, observacion: string) => void;
  onCancel: () => void;
}

const CANALES_RECEPCION = ['Portal', 'Imaginex', 'Onbase'] as const;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function AuditorApprovalTemplateModal({
  incapacidad,
  accion,
  open,
  onOpenChange,
  onConfirm,
  onCancel,
}: AuditorApprovalTemplateModalProps) {
  const { toast } = useToast();

  // State for the generated texto-copiable after successful submit
  const [textoCopiable, setTextoCopiable] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Computed linea_autorizacion preview (mirrors backend logic)
  const [lineaAutorizacion, setLineaAutorizacion] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<PlantillaFormData>({
    resolver: zodResolver(plantillaSchema),
    defaultValues: {
      canal_recepcion: '',
      dias_autorizados: incapacidad.dias_totales,
      fecha_inicio_autorizada: incapacidad.fecha_inicio,
      fecha_fin_autorizada: incapacidad.fecha_fin,
      diagnostico_cie10: incapacidad.diagnostico_cie10 ?? '',
      descripcion_cie10: incapacidad.diagnostico_descripcion ?? '',
      nombre_medico: '',
      especialidad_medico: '',
      nombre_ips: '',
      observacion: '',
    },
  });

  const watchedDias = watch('dias_autorizados');
  const watchedInicio = watch('fecha_inicio_autorizada');
  const watchedFin = watch('fecha_fin_autorizada');

  // Update linea_autorizacion preview whenever relevant fields change
  useEffect(() => {
    if (watchedDias && watchedInicio && watchedFin) {
      setLineaAutorizacion(
        `Se autoriza pago por ${watchedDias} días desde ${watchedInicio} hasta ${watchedFin}`,
      );
    } else {
      setLineaAutorizacion('');
    }
  }, [watchedDias, watchedInicio, watchedFin]);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setTextoCopiable(null);
      setIsCopied(false);
      setIsSubmitting(false);
      reset({
        canal_recepcion: '',
        dias_autorizados: incapacidad.dias_totales,
        fecha_inicio_autorizada: incapacidad.fecha_inicio,
        fecha_fin_autorizada: incapacidad.fecha_fin,
        diagnostico_cie10: incapacidad.diagnostico_cie10 ?? '',
        descripcion_cie10: incapacidad.diagnostico_descripcion ?? '',
        nombre_medico: '',
        especialidad_medico: '',
        nombre_ips: '',
        observacion: '',
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const onSubmit = async (formData: PlantillaFormData) => {
    setIsSubmitting(true);
    try {
      const plantilla: PlantillaAuditoriaCreate = {
        canal_recepcion: formData.canal_recepcion,
        dias_autorizados: formData.dias_autorizados,
        fecha_inicio_autorizada: formData.fecha_inicio_autorizada,
        fecha_fin_autorizada: formData.fecha_fin_autorizada,
        diagnostico_cie10: formData.diagnostico_cie10 || undefined,
        descripcion_cie10: formData.descripcion_cie10 || undefined,
        nombre_medico: formData.nombre_medico || undefined,
        especialidad_medico: formData.especialidad_medico || undefined,
        nombre_ips: formData.nombre_ips || undefined,
      };

      // POST the template
      await plantillaAuditoriaService.createOrUpdate(incapacidad.id, plantilla);

      // GET the formatted texto copiable
      const texto = await plantillaAuditoriaService.getTextoCopiable(incapacidad.id);
      setTextoCopiable(texto);

      // Notify parent so it can proceed with the state change
      onConfirm(plantilla, formData.observacion ?? '');
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al guardar la plantilla de auditoría';
      toast({ title: 'Error', description: detail, variant: 'destructive' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyToClipboard = async () => {
    if (!textoCopiable) return;
    try {
      await navigator.clipboard.writeText(textoCopiable);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      toast({ title: 'Error al copiar', description: 'No se pudo copiar al portapapeles', variant: 'destructive' });
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
    onCancel();
  };

  const handleDone = () => {
    onOpenChange(false);
  };

  const tituloAccion = accion === 'LIQUIDACION' ? 'Liquidación Completa' : 'Liquidación Parcial';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClipboardCheck className="h-5 w-5 text-green-600" />
            Plantilla de Auditoría — {tituloAccion}
          </DialogTitle>
          <DialogDescription>
            Complete los datos de la plantilla para la incapacidad{' '}
            <strong>{incapacidad.numero}</strong>. El texto generado se usará para pegar en
            Arpis.
          </DialogDescription>
        </DialogHeader>

        {/* ---------------------------------------------------------------- */}
        {/* Phase 1: Form                                                     */}
        {/* ---------------------------------------------------------------- */}
        {!textoCopiable && (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Canal de recepción */}
            <div className="space-y-2">
              <Label htmlFor="canal_recepcion">
                Canal de recepción <span className="text-red-500">*</span>
              </Label>
              <Select
                onValueChange={(val) => setValue('canal_recepcion', val, { shouldValidate: true })}
              >
                <SelectTrigger id="canal_recepcion" className={errors.canal_recepcion ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Seleccione el canal..." />
                </SelectTrigger>
                <SelectContent>
                  {CANALES_RECEPCION.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.canal_recepcion && (
                <p className="text-sm text-red-600">{errors.canal_recepcion.message}</p>
              )}
            </div>

            {/* Diagnóstico CIE-10 + descripción */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="diagnostico_cie10">Código CIE-10</Label>
                <Input
                  id="diagnostico_cie10"
                  {...register('diagnostico_cie10')}
                  placeholder="Ej. M545"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="descripcion_cie10">Descripción diagnóstico</Label>
                <Input
                  id="descripcion_cie10"
                  {...register('descripcion_cie10')}
                  placeholder="Ej. Lumbago"
                />
              </div>
            </div>

            {/* Médico */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nombre_medico">Médico tratante</Label>
                <Input
                  id="nombre_medico"
                  {...register('nombre_medico')}
                  placeholder="Nombre del médico"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="especialidad_medico">Especialidad</Label>
                <Input
                  id="especialidad_medico"
                  {...register('especialidad_medico')}
                  placeholder="Ej. Ortopedia"
                />
              </div>
            </div>

            {/* IPS */}
            <div className="space-y-2">
              <Label htmlFor="nombre_ips">IPS prestadora</Label>
              <Input
                id="nombre_ips"
                {...register('nombre_ips')}
                placeholder="Nombre de la IPS"
              />
            </div>

            {/* Fechas y días */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fecha_inicio_autorizada">
                  Fecha inicio <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="fecha_inicio_autorizada"
                  type="date"
                  {...register('fecha_inicio_autorizada')}
                  className={errors.fecha_inicio_autorizada ? 'border-red-500' : ''}
                />
                {errors.fecha_inicio_autorizada && (
                  <p className="text-sm text-red-600">{errors.fecha_inicio_autorizada.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="fecha_fin_autorizada">
                  Fecha fin <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="fecha_fin_autorizada"
                  type="date"
                  {...register('fecha_fin_autorizada')}
                  className={errors.fecha_fin_autorizada ? 'border-red-500' : ''}
                />
                {errors.fecha_fin_autorizada && (
                  <p className="text-sm text-red-600">{errors.fecha_fin_autorizada.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="dias_autorizados">
                  Días autorizados <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="dias_autorizados"
                  type="number"
                  min={1}
                  {...register('dias_autorizados', { valueAsNumber: true })}
                  className={errors.dias_autorizados ? 'border-red-500' : ''}
                />
                {errors.dias_autorizados && (
                  <p className="text-sm text-red-600">{errors.dias_autorizados.message}</p>
                )}
              </div>
            </div>

            {/* Línea de autorización preview (read-only) */}
            {lineaAutorizacion && (
              <Alert className="bg-blue-50 border-blue-200">
                <AlertDescription className="text-blue-800 font-mono text-sm">
                  <span className="font-semibold block mb-1">Vista previa línea de autorización:</span>
                  {lineaAutorizacion}
                </AlertDescription>
              </Alert>
            )}

            {/* Observación (opcional) */}
            <div className="space-y-2">
              <Label htmlFor="observacion">
                Observación adicional{' '}
                <span className="text-slate-400 text-xs font-normal">(opcional)</span>
              </Label>
              <Textarea
                id="observacion"
                {...register('observacion')}
                rows={3}
                placeholder="Comentarios adicionales sobre la aprobación..."
                className="resize-none"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700"
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSubmitting ? 'Generando...' : 'Generar plantilla y confirmar'}
              </Button>
            </DialogFooter>
          </form>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Phase 2: Show generated texto copiable                           */}
        {/* ---------------------------------------------------------------- */}
        {textoCopiable && (
          <div className="space-y-4">
            <Alert className="bg-green-50 border-green-200">
              <AlertDescription className="text-green-800">
                Plantilla generada correctamente. Copie el texto y péguelo en Arpis.
              </AlertDescription>
            </Alert>

            <div className="space-y-2">
              <Label>Texto copiable para Arpis</Label>
              <div className="relative">
                <Textarea
                  readOnly
                  value={textoCopiable}
                  rows={8}
                  className="font-mono text-sm resize-none bg-slate-50"
                  aria-label="Texto copiable"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="absolute top-2 right-2"
                  onClick={handleCopyToClipboard}
                  aria-label="Copiar texto"
                >
                  {isCopied ? (
                    <>
                      <Check className="h-4 w-4 mr-1 text-green-600" />
                      Copiado
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      Copiar
                    </>
                  )}
                </Button>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" onClick={handleDone} className="bg-green-600 hover:bg-green-700">
                Listo — cerrar
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
