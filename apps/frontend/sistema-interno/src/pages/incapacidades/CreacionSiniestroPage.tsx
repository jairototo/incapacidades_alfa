/**
 * CreacionSiniestroPage — Vinculación de siniestro externo (solo ADMIN)
 *
 * Permite a un administrador ingresar el número de siniestro externo para una
 * incapacidad ARL que se encuentra en estado EN_AUDITORIA sin siniestro vinculado.
 *
 * Flujo:
 *  1. Muestra encabezado de solo lectura con datos del empleado, empresa y fechas.
 *  2. Formulario: número de siniestro externo + observación (ambos requeridos).
 *  3. POST → EN_AUDITORIA (Celery encola la vinculación automática).
 *  4. Mensaje de éxito y botón para volver al listado.
 */
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertTriangle, ArrowLeft, CheckCircle, Link2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useHasRole } from '@/store/authStore';
import { incapacidadService } from '@/services/incapacidadService';
import { TipoIncapacidad } from '@/types';

// ---------------------------------------------------------------------------
// Zod schema (Zod v3 — sistema-interno uses v3.25.76)
// ---------------------------------------------------------------------------
const formSchema = z.object({
  numero_siniestro: z
    .string()
    .min(1, 'El número de siniestro es obligatorio')
    .max(50, 'Máximo 50 caracteres'),
  observacion: z
    .string()
    .min(1, 'La observación es obligatoria')
    .max(500, 'Máximo 500 caracteres'),
});

type FormValues = z.infer<typeof formSchema>;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function CreacionSiniestroPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const isAdmin = useHasRole('ADMIN');

  const [submitted, setSubmitted] = useState(false);

  // React Hook Form + Zod
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      numero_siniestro: '',
      observacion: '',
    },
  });

  // Fetch incapacidad
  const { data: incapacidad, isLoading, error } = useQuery({
    queryKey: ['incapacidad', id],
    queryFn: () => incapacidadService.getById(id!),
    enabled: !!id,
  });

  // Mutation
  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      incapacidadService.iniciarCreacionSiniestro(id!, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      setSubmitted(true);
      toast({
        title: 'Siniestro en proceso de vinculación',
        description:
          'La incapacidad volverá a EN_AUDITORIA automáticamente una vez que el siniestro sea vinculado.',
      });
    },
    onError: (err: any) => {
      const message =
        err?.response?.data?.detail ??
        err?.message ??
        'Ocurrió un error al vincular el siniestro';
      toast({
        variant: 'destructive',
        title: 'Error al vincular siniestro',
        description: message,
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    mutation.mutate(values);
  };

  // ------------------------------------------------------------------
  // Guards
  // ------------------------------------------------------------------
  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertTriangle className="h-12 w-12 text-destructive" />
        <p className="text-lg font-medium text-muted-foreground">
          Esta página es exclusiva para administradores.
        </p>
        <Button variant="outline" onClick={() => navigate(-1)}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver
        </Button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Cargando incapacidad...
      </div>
    );
  }

  if (error || !incapacidad) {
    return (
      <div className="p-8 text-center text-destructive">
        No se pudo cargar la incapacidad.{' '}
        <button className="underline" onClick={() => navigate(-1)}>
          Volver
        </button>
      </div>
    );
  }

  // ------------------------------------------------------------------
  // Success screen
  // ------------------------------------------------------------------
  if (submitted) {
    return (
      <div className="max-w-xl mx-auto mt-16 flex flex-col items-center gap-4 text-center px-4">
        <CheckCircle className="h-16 w-16 text-green-500" />
        <h2 className="text-lg font-bold">Siniestro en proceso de vinculación</h2>
        <p className="text-muted-foreground">
          La incapacidad <span className="font-mono font-medium">{incapacidad.numero}</span> ha
          sido cambiada a estado{' '}
          <Badge variant="outline">CREACION_SINIESTRO</Badge> y volverá a{' '}
          <Badge variant="outline">EN_AUDITORIA</Badge> automáticamente una vez que el
          siniestro sea vinculado desde el sistema externo.
        </p>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate('/incapacidades/pendientes')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Ir a pendientes
          </Button>
          <Button onClick={() => navigate(`/incapacidades/${id}`)}>
            Ver incapacidad
          </Button>
        </div>
      </div>
    );
  }

  const empleado = incapacidad.empleado;
  const empresa = incapacidad.empresa;

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-4">
      {/* Back button */}
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Volver
      </Button>

      {/* Page title */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Link2 className="h-6 w-6 text-primary" />
          <h1 className="text-lg font-bold">Vincular siniestro externo</h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Ingresa el número de siniestro del sistema externo (RRHH/ARL) para vincularlo
          a esta incapacidad ARL.
        </p>
      </div>

      {/* Incapacidad header — read-only */}
      {incapacidad.tipo === TipoIncapacidad.ARL && (
        <Card className="p-5 space-y-3 bg-muted/40">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Datos de la incapacidad
          </h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <div>
              <span className="text-muted-foreground">Número</span>
              <p className="font-mono font-medium">{incapacidad.numero}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Estado</span>
              <p>
                <Badge variant="outline">{incapacidad.estado}</Badge>
              </p>
            </div>
            {empleado && (
              <>
                <div>
                  <span className="text-muted-foreground">Empleado</span>
                  <p className="font-medium">
                    {empleado.nombres} {empleado.apellidos}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Documento</span>
                  <p>{empleado.numero_documento}</p>
                </div>
              </>
            )}
            {empresa && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Empresa</span>
                <p className="font-medium">{empresa.razon_social}</p>
              </div>
            )}
            <div>
              <span className="text-muted-foreground">Período</span>
              <p>
                {incapacidad.fecha_inicio} → {incapacidad.fecha_fin} (
                {incapacidad.dias_totales} días)
              </p>
            </div>
            <div>
              <span className="text-muted-foreground">Diagnóstico</span>
              <p>{incapacidad.diagnostico_cie10}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Vinculación form */}
      <Card className="p-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Número de siniestro */}
          <div className="space-y-1.5">
            <label
              htmlFor="numero_siniestro"
              className="text-sm font-medium leading-none"
            >
              Número de siniestro externo{' '}
              <span className="text-destructive">*</span>
            </label>
            <input
              id="numero_siniestro"
              type="text"
              placeholder="Ej: SINX-2026-001"
              className={[
                'flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm',
                'ring-offset-background placeholder:text-muted-foreground',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                errors.numero_siniestro ? 'border-destructive' : 'border-input',
              ].join(' ')}
              {...register('numero_siniestro')}
            />
            {errors.numero_siniestro && (
              <p className="text-xs text-destructive">
                {errors.numero_siniestro.message}
              </p>
            )}
          </div>

          {/* Observación */}
          <div className="space-y-1.5">
            <label
              htmlFor="observacion"
              className="text-sm font-medium leading-none"
            >
              Observación <span className="text-destructive">*</span>
            </label>
            <textarea
              id="observacion"
              rows={4}
              placeholder="Describe por qué se está vinculando este siniestro externo..."
              className={[
                'flex w-full rounded-md border bg-background px-3 py-2 text-sm',
                'ring-offset-background placeholder:text-muted-foreground',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                'resize-none',
                errors.observacion ? 'border-destructive' : 'border-input',
              ].join(' ')}
              {...register('observacion')}
            />
            {errors.observacion && (
              <p className="text-xs text-destructive">
                {errors.observacion.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || mutation.isPending}
            >
              <Link2 className="mr-2 h-4 w-4" />
              {mutation.isPending ? 'Vinculando...' : 'Vincular siniestro'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
