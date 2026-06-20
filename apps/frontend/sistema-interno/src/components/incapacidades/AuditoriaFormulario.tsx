import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQueryClient, useMutation } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Calendar, CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';

import type { Incapacidad, IncapacidadAuditarRequest } from '@/types/incapacidad';
import { incapacidadService } from '@/services/incapacidadService';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

// ============================================================
// SCHEMAS DE VALIDACIÓN
// ============================================================

const cie10Regex = /^[A-Z]\d{3}(\.\d{1,2})?$/;

const auditoriaFormSchema = z.object({
  observaciones: z.string().min(10, 'Mínimo 10 caracteres'),
  fecha_inicio_aprobada: z.string().optional(),
  fecha_fin_aprobada: z.string().optional(),
  dias_aprobados: z.number().int().positive().optional(),
  cie10_aprobado: z
    .string()
    .regex(cie10Regex, 'Formato CIE-10 inválido (ej: A091, J062.9)')
    .toUpperCase()
    .optional(),
  diagnostico_aprobado: z.string().min(3, 'Mínimo 3 caracteres').optional(),
});

type AuditoriaFormData = z.infer<typeof auditoriaFormSchema>;

// ============================================================
// INTERFACES
// ============================================================

interface AuditoriaFormularioProps {
  incapacidad: Incapacidad;
  onSuccess?: (incapacidadActualizada: Incapacidad) => void;
}

// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

export function AuditoriaFormulario({ incapacidad, onSuccess }: AuditoriaFormularioProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Estados locales
  const [selectedAction, setSelectedAction] = useState<
    'APROBAR_PARA_PAGO' | 'APROBAR_PARA_PAGO_PARCIAL' | 'SOLICITAR_INFORMACION' | 'RECHAZAR' | null
  >(null);

  const [diasCalculados, setDiasCalculados] = useState<number | null>(null);
  const [esAprobacionParcial, setEsAprobacionParcial] = useState(false);

  // React Hook Form
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<AuditoriaFormData>({
    resolver: zodResolver(auditoriaFormSchema),
    defaultValues: {
      observaciones: '',
      fecha_inicio_aprobada: '',
      fecha_fin_aprobada: '',
      dias_aprobados: undefined,
      cie10_aprobado: incapacidad.diagnostico_cie10,
      diagnostico_aprobado: incapacidad.diagnostico,
    },
  });

  // Watch form fields
  const fechaInicioAprobada = watch('fecha_inicio_aprobada');
  const fechaFinAprobada = watch('fecha_fin_aprobada');
  const diasAprobados = watch('dias_aprobados');

  // Cálculo automático de días cuando cambian las fechas
  useEffect(() => {
    if (fechaInicioAprobada && fechaFinAprobada) {
      const fechaInicio = new Date(fechaInicioAprobada);
      const fechaFin = new Date(fechaFinAprobada);
      const diffTime = Math.abs(fechaFin.getTime() - fechaInicio.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 para incluir ambos días
      setDiasCalculados(diffDays);
      setValue('dias_aprobados', diffDays);
    } else {
      setDiasCalculados(null);
    }
  }, [fechaInicioAprobada, fechaFinAprobada, setValue]);

  // Detectar aprobación parcial
  useEffect(() => {
    if (diasAprobados && diasAprobados < incapacidad.dias_totales) {
      setEsAprobacionParcial(true);
    } else {
      setEsAprobacionParcial(false);
    }
  }, [diasAprobados, incapacidad.dias_totales]);

  // Mutation para auditar
  const auditarMutation = useMutation({
    mutationFn: async (data: IncapacidadAuditarRequest) => {
      if (!selectedAction) throw new Error('Debe seleccionar una acción');
      return incapacidadService.auditar(incapacidad.id, data);
    },
    onSuccess: (incapacidadActualizada) => {
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades', incapacidad.id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidadesPendientes'] });
      
      toast({
        title: '✅ Incapacidad auditada exitosamente',
        description: `Estado: ${incapacidadActualizada.estado}`,
      });
      
      reset();
      setSelectedAction(null);
      onSuccess?.(incapacidadActualizada);
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || 'Error al auditar';
      toast({
        title: '❌ Error en auditoría',
        description: errorMsg,
        variant: 'destructive',
      });
    },
  });

  // Handler submit
  const onSubmit = (formData: AuditoriaFormData) => {
    if (!selectedAction) {
      toast({
        title: '❌ Debe seleccionar una acción',
        variant: 'destructive',
      });
      return;
    }

    // Construir payload según la acción
    const payload: IncapacidadAuditarRequest = {
      accion: selectedAction,
      observaciones: formData.observaciones,
    };

    // Si es aprobación parcial, incluir campos modificados
    if (selectedAction === 'APROBAR_PARA_PAGO_PARCIAL') {
      if (!formData.fecha_inicio_aprobada || !formData.fecha_fin_aprobada) {
        toast({
          title: '❌ Se requieren fechas aprobadas para aprobación parcial',
          variant: 'destructive',
        });
        return;
      }

      payload.fecha_inicio_aprobada = formData.fecha_inicio_aprobada;
      payload.fecha_fin_aprobada = formData.fecha_fin_aprobada;
      payload.dias_aprobados = formData.dias_aprobados;
      payload.cie10_aprobado = formData.cie10_aprobado;
      payload.diagnostico_aprobado = formData.diagnostico_aprobado;
    }

    auditarMutation.mutate(payload);
  };

  // Handler cambio de acción
  const handleActionChange = (action: typeof selectedAction) => {
    setSelectedAction(action);

    // Pre-cargar fechas para aprobación parcial
    if (action === 'APROBAR_PARA_PAGO_PARCIAL') {
      setValue('fecha_inicio_aprobada', incapacidad.fecha_inicio);
      setValue('fecha_fin_aprobada', incapacidad.fecha_fin);
      setValue('cie10_aprobado', incapacidad.diagnostico_cie10);
      setValue('diagnostico_aprobado', incapacidad.diagnostico);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-blue-600" />
          Auditoría de Incapacidad
        </CardTitle>
        <CardDescription>
          Revise los datos y decida la acción a tomar. Puede aprobar parcialmente si los días
          aprobados son menores a los solicitados.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Datos originales de la incapacidad */}
          <div className="rounded-lg bg-slate-50 p-4 space-y-2">
            <h3 className="font-semibold text-sm text-slate-700">Datos Solicitados</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-600">Fecha inicio:</span>{' '}
                <span className="font-medium">
                  {format(new Date(incapacidad.fecha_inicio), 'dd/MM/yyyy', { locale: es })}
                </span>
              </div>
              <div>
                <span className="text-slate-600">Fecha fin:</span>{' '}
                <span className="font-medium">
                  {format(new Date(incapacidad.fecha_fin), 'dd/MM/yyyy', { locale: es })}
                </span>
              </div>
              <div>
                <span className="text-slate-600">Días totales:</span>{' '}
                <span className="font-medium">{incapacidad.dias_totales} días</span>
              </div>
              <div>
                <span className="text-slate-600">CIE-10:</span>{' '}
                <span className="font-medium">{incapacidad.diagnostico_cie10}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-600">Diagnóstico:</span>{' '}
                <span className="font-medium">{incapacidad.diagnostico}</span>
              </div>
            </div>
          </div>

          {/* Botones de acción */}
          <div className="space-y-2">
            <Label>Acción a Realizar</Label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                type="button"
                variant={selectedAction === 'APROBAR_PARA_PAGO' ? 'default' : 'outline'}
                className={cn(
                  'h-auto flex-col py-3',
                  selectedAction === 'APROBAR_PARA_PAGO' && 'bg-green-600 hover:bg-green-700'
                )}
                onClick={() => handleActionChange('APROBAR_PARA_PAGO')}
              >
                <CheckCircle className="h-5 w-5 mb-1" />
                <span className="text-xs">Aprobar para Pago</span>
              </Button>

              <Button
                type="button"
                variant={selectedAction === 'APROBAR_PARA_PAGO_PARCIAL' ? 'default' : 'outline'}
                className={cn(
                  'h-auto flex-col py-3',
                  selectedAction === 'APROBAR_PARA_PAGO_PARCIAL' &&
                    'bg-yellow-600 hover:bg-yellow-700'
                )}
                onClick={() => handleActionChange('APROBAR_PARA_PAGO_PARCIAL')}
              >
                <CheckCircle className="h-5 w-5 mb-1" />
                <span className="text-xs">Aprobar Parcialmente</span>
              </Button>

              <Button
                type="button"
                variant={selectedAction === 'SOLICITAR_INFORMACION' ? 'default' : 'outline'}
                className={cn(
                  'h-auto flex-col py-3',
                  selectedAction === 'SOLICITAR_INFORMACION' && 'bg-blue-600 hover:bg-blue-700'
                )}
                onClick={() => handleActionChange('SOLICITAR_INFORMACION')}
              >
                <Info className="h-5 w-5 mb-1" />
                <span className="text-xs">Solicitar Información</span>
              </Button>

              <Button
                type="button"
                variant={selectedAction === 'RECHAZAR' ? 'default' : 'outline'}
                className={cn(
                  'h-auto flex-col py-3',
                  selectedAction === 'RECHAZAR' && 'bg-red-600 hover:bg-red-700'
                )}
                onClick={() => handleActionChange('RECHAZAR')}
              >
                <XCircle className="h-5 w-5 mb-1" />
                <span className="text-xs">Rechazar</span>
              </Button>
            </div>
          </div>

          {/* Campos de aprobación parcial */}
          {selectedAction === 'APROBAR_PARA_PAGO_PARCIAL' && (
            <div className="space-y-4 border-l-4 border-yellow-400 pl-4">
              <h3 className="font-semibold text-sm text-yellow-800">
                Datos Aprobados (Modificables)
              </h3>

              {/* Fechas aprobadas */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fecha_inicio_aprobada">Fecha Inicio Aprobada</Label>
                  <Input
                    id="fecha_inicio_aprobada"
                    type="date"
                    {...register('fecha_inicio_aprobada')}
                  />
                  {errors.fecha_inicio_aprobada && (
                    <p className="text-sm text-red-600">{errors.fecha_inicio_aprobada.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="fecha_fin_aprobada">Fecha Fin Aprobada</Label>
                  <Input
                    id="fecha_fin_aprobada"
                    type="date"
                    {...register('fecha_fin_aprobada')}
                  />
                  {errors.fecha_fin_aprobada && (
                    <p className="text-sm text-red-600">{errors.fecha_fin_aprobada.message}</p>
                  )}
                </div>
              </div>

              {/* Días aprobados (calculado automáticamente) */}
              <div className="space-y-2">
                <Label htmlFor="dias_aprobados">Días Aprobados</Label>
                <Input
                  id="dias_aprobados"
                  type="number"
                  value={diasCalculados || ''}
                  readOnly
                  className="bg-slate-50"
                />
                {esAprobacionParcial && (
                  <Alert variant="default" className="bg-yellow-50 border-yellow-400">
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-800">
                      Días aprobados ({diasAprobados}) {'<'} Días solicitados (
                      {incapacidad.dias_totales}) - Se generará aprobación parcial
                    </AlertDescription>
                  </Alert>
                )}
                {errors.dias_aprobados && (
                  <p className="text-sm text-red-600">{errors.dias_aprobados.message}</p>
                )}
              </div>

              {/* CIE-10 aprobado */}
              <div className="space-y-2">
                <Label htmlFor="cie10_aprobado">CIE-10 Aprobado</Label>
                <Input
                  id="cie10_aprobado"
                  {...register('cie10_aprobado')}
                  placeholder="Ej: A09"
                  className="uppercase"
                />
                {errors.cie10_aprobado && (
                  <p className="text-sm text-red-600">{errors.cie10_aprobado.message}</p>
                )}
              </div>

              {/* Diagnóstico aprobado */}
              <div className="space-y-2">
                <Label htmlFor="diagnostico_aprobado">Diagnóstico Aprobado</Label>
                <Textarea
                  id="diagnostico_aprobado"
                  {...register('diagnostico_aprobado')}
                  placeholder="Diagnóstico corregido o confirmado"
                  rows={2}
                />
                {errors.diagnostico_aprobado && (
                  <p className="text-sm text-red-600">{errors.diagnostico_aprobado.message}</p>
                )}
              </div>
            </div>
          )}

          {/* Observaciones (siempre visible) */}
          <div className="space-y-2">
            <Label htmlFor="observaciones">
              Observaciones <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="observaciones"
              {...register('observaciones')}
              placeholder="Describa la decisión tomada y las razones (mínimo 10 caracteres)"
              rows={4}
            />
            {errors.observaciones && (
              <p className="text-sm text-red-600">{errors.observaciones.message}</p>
            )}
          </div>

          {/* Botón de envío */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset();
                setSelectedAction(null);
              }}
              disabled={isSubmitting}
            >
              Limpiar
            </Button>
            <Button type="submit" disabled={!selectedAction || isSubmitting}>
              {isSubmitting ? 'Procesando...' : 'Confirmar Auditoría'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
