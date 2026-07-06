/**
 * CreacionSiniestroPage — Crear siniestro para incapacidad en estado CREACION_SINIESTRO.
 *
 * Solo ADMINISTRADOR. Layout idéntico a GestionarPage:
 *   - Sidebar de documentos (collapsible, 50 % del ancho)
 *   - Tabs: "Creación Siniestro" | "Validaciones" | "Historial"
 *
 * Flujo:
 *   1. AUDITOR envió la incapacidad a CREACION_SINIESTRO (desde GestionarPage).
 *   2. ADMIN rellena el formulario con los datos del siniestro.
 *   3. POST → siniestro creado en BD → estado pasa a EN_AUDITORIA en la misma tx.
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  AlertTriangle,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  FileText,
  History,
  Image,
  Link2,
  XCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { useHasRole } from '@/store/authStore';
import { incapacidadService } from '@/services/incapacidadService';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { ValidacionesPanel } from '@/components/incapacidades/ValidacionesPanel';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TIPOS_SINIESTRO = [
  { value: 'ACCIDENTE_TRABAJO', label: 'Accidente de Trabajo' },
  { value: 'ENFERMEDAD_LABORAL', label: 'Enfermedad Laboral' },
  { value: 'ACCIDENTE_TRAYECTO', label: 'Accidente de Trayecto' },
] as const;

// ---------------------------------------------------------------------------
// Zod schema (Zod v3 — sistema-interno)
// ---------------------------------------------------------------------------
const formSchema = z.object({
  numero_siniestro: z
    .string()
    .min(1, 'El número de siniestro es obligatorio')
    .max(50, 'Máximo 50 caracteres'),
  fecha_siniestro: z
    .string()
    .min(1, 'La fecha del siniestro es obligatoria')
    .refine((v) => !isNaN(Date.parse(v)), 'Fecha inválida')
    .refine((v) => new Date(v) <= new Date(), 'La fecha no puede ser futura'),
  tipo_siniestro: z.enum(['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'], {
    required_error: 'El tipo de siniestro es obligatorio',
  }),
  descripcion: z
    .string()
    .min(10, 'La descripción debe tener al menos 10 caracteres')
    .max(2000, 'Máximo 2000 caracteres'),
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

  const [activeTab, setActiveTab] = useState('siniestro');
  const [showDocumentsSidebar, setShowDocumentsSidebar] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      numero_siniestro: '',
      fecha_siniestro: '',
      tipo_siniestro: undefined,
      descripcion: '',
      observacion: '',
    },
  });

  // Data queries
  const { data: incapacidad, isLoading, error } = useQuery({
    queryKey: ['incapacidad', id],
    queryFn: () => incapacidadService.getById(id!),
    enabled: !!id,
  });

  const { data: historial } = useQuery({
    queryKey: ['incapacidad', id, 'historial'],
    queryFn: () => incapacidadService.getHistorial(id!),
    enabled: !!id,
  });

  const { data: documentos } = useQuery({
    queryKey: ['incapacidad', id, 'documentos'],
    queryFn: () => incapacidadService.getDocumentos(id!),
    enabled: !!id,
  });

  const { data: validaciones, isLoading: validacionesLoading } = useQuery({
    queryKey: ['incapacidad', id, 'validaciones'],
    queryFn: () => incapacidadService.getValidaciones(id!),
    enabled: !!id,
  });

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      incapacidadService.iniciarCreacionSiniestro(id!, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades-bandeja-siniestro'] });
      toast({
        title: 'Siniestro creado',
        description: 'La incapacidad ha vuelto a EN_AUDITORIA con el siniestro vinculado.',
      });
      setTimeout(() => navigate('/incapacidades/creacion-siniestro'), 1500);
    },
    onError: (err: any) => {
      const message =
        err?.response?.data?.detail ?? err?.message ?? 'Error al crear el siniestro';
      toast({ variant: 'destructive', title: 'Error', description: message });
    },
  });

  const onSubmit = (values: FormValues) => mutation.mutate(values);

  // Guards
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
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="text-slate-500">Cargando incapacidad...</p>
        </div>
      </div>
    );
  }

  if (error || !incapacidad) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md">
          <div className="text-center space-y-4">
            <XCircle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">Incapacidad no encontrada</h2>
            <Button onClick={() => navigate('/incapacidades/creacion-siniestro')}>
              Volver a la bandeja
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const empleado = incapacidad.empleado;
  const empresa = incapacidad.empresa;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/incapacidades/creacion-siniestro')}
            className="hover:bg-slate-100"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Volver
          </Button>
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-3">
              Creación de Siniestro
              <Badge variant="secondary">{incapacidad.estado}</Badge>
            </h1>
            <p className="text-slate-500 mt-1 font-mono">{incapacidad.numero}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="default">ARL</Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDocumentsSidebar(!showDocumentsSidebar)}
            className="flex items-center gap-2"
          >
            {showDocumentsSidebar ? (
              <>
                <ChevronLeft className="h-4 w-4" />
                Ocultar Documentos
              </>
            ) : (
              <>
                <ChevronRight className="h-4 w-4" />
                Mostrar Documentos ({documentos?.length || 0})
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Split-screen: Documentos | Tabs */}
      <div className="flex gap-4">
        {/* Documents sidebar */}
        {showDocumentsSidebar && (
          <div className="w-1/2 flex-shrink-0">
            <Card className="h-full sticky top-4">
              <div className="p-4 border-b flex items-center gap-2">
                <Image className="h-5 w-5 text-blue-600" />
                <h3 className="text-base font-semibold">Documentos Adjuntos</h3>
                <Badge variant="secondary">{documentos?.length || 0}</Badge>
              </div>
              <div className="p-4 overflow-y-auto max-h-[calc(100vh-200px)]">
                <DocumentosViewer documentos={documentos || []} />
              </div>
            </Card>
          </div>
        )}

        {/* Main tabs */}
        <div className={cn('flex-1', showDocumentsSidebar ? 'w-1/2' : 'w-full')}>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="siniestro" className="space-x-2">
                <Link2 className="h-4 w-4" />
                <span>Creación Siniestro</span>
              </TabsTrigger>
              <TabsTrigger value="validaciones" className="space-x-2">
                <FileText className="h-4 w-4" />
                <span>Validaciones</span>
              </TabsTrigger>
              <TabsTrigger value="historial" className="space-x-2">
                <History className="h-4 w-4" />
                <span>Historial ({historial?.length || 0})</span>
              </TabsTrigger>
            </TabsList>

            {/* Tab: Creación Siniestro */}
            <TabsContent value="siniestro" className="space-y-4">
              {/* Incapacidad read-only header */}
              <Card className="p-4 bg-slate-50 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Datos de la incapacidad
                </p>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                  {empleado && (
                    <>
                      <div>
                        <span className="text-slate-500">Empleado</span>
                        <p className="font-medium">
                          {empleado.nombres} {empleado.apellidos}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-500">Documento</span>
                        <p>{empleado.numero_documento}</p>
                      </div>
                    </>
                  )}
                  {empresa && (
                    <div className="col-span-2">
                      <span className="text-slate-500">Empresa</span>
                      <p className="font-medium">{empresa.razon_social}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-slate-500">Período</span>
                    <p>
                      {incapacidad.fecha_inicio} → {incapacidad.fecha_fin}{' '}
                      <span className="text-slate-400">({incapacidad.dias_totales} días)</span>
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Diagnóstico CIE-10</span>
                    <p className="font-mono">{incapacidad.diagnostico_cie10 ?? '—'}</p>
                  </div>
                </div>
              </Card>

              {/* Siniestro form */}
              <Card className="p-4">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  {/* Número de siniestro */}
                  <div className="space-y-1.5">
                    <label htmlFor="numero_siniestro" className="text-sm font-medium">
                      Número de siniestro <span className="text-destructive">*</span>
                    </label>
                    <input
                      id="numero_siniestro"
                      type="text"
                      placeholder="Ej. SIN-2026-00123"
                      className={cn(
                        'flex h-8 w-full rounded-md border bg-background px-2.5 py-1.5 text-sm font-mono',
                        'ring-offset-background placeholder:text-muted-foreground',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                        errors.numero_siniestro ? 'border-destructive' : 'border-input'
                      )}
                      {...register('numero_siniestro')}
                    />
                    {errors.numero_siniestro && (
                      <p className="text-xs text-destructive">{errors.numero_siniestro.message}</p>
                    )}
                  </div>

                  {/* Fecha siniestro */}
                  <div className="space-y-1.5">
                    <label htmlFor="fecha_siniestro" className="text-sm font-medium">
                      Fecha del siniestro <span className="text-destructive">*</span>
                    </label>
                    <input
                      id="fecha_siniestro"
                      type="date"
                      max={new Date().toISOString().split('T')[0]}
                      className={cn(
                        'flex h-8 w-full rounded-md border bg-background px-2.5 py-1.5 text-sm',
                        'ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                        errors.fecha_siniestro ? 'border-destructive' : 'border-input'
                      )}
                      {...register('fecha_siniestro')}
                    />
                    {errors.fecha_siniestro && (
                      <p className="text-xs text-destructive">{errors.fecha_siniestro.message}</p>
                    )}
                  </div>

                  {/* Tipo siniestro */}
                  <div className="space-y-1.5">
                    <label htmlFor="tipo_siniestro" className="text-sm font-medium">
                      Tipo de siniestro <span className="text-destructive">*</span>
                    </label>
                    <select
                      id="tipo_siniestro"
                      className={cn(
                        'flex h-8 w-full rounded-md border bg-background px-2.5 py-1 text-sm',
                        'ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                        errors.tipo_siniestro ? 'border-destructive' : 'border-input'
                      )}
                      {...register('tipo_siniestro')}
                    >
                      <option value="">Seleccionar tipo...</option>
                      {TIPOS_SINIESTRO.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                    {errors.tipo_siniestro && (
                      <p className="text-xs text-destructive">{errors.tipo_siniestro.message}</p>
                    )}
                  </div>

                  {/* Descripción del siniestro */}
                  <div className="space-y-1.5">
                    <label htmlFor="descripcion" className="text-sm font-medium">
                      Descripción del siniestro <span className="text-destructive">*</span>
                    </label>
                    <textarea
                      id="descripcion"
                      rows={4}
                      placeholder="Describa cómo ocurrió el accidente o evento (mínimo 10 caracteres)..."
                      className={cn(
                        'flex w-full rounded-md border bg-background px-2.5 py-1.5 text-sm',
                        'ring-offset-background placeholder:text-muted-foreground resize-none',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                        errors.descripcion ? 'border-destructive' : 'border-input'
                      )}
                      {...register('descripcion')}
                    />
                    {errors.descripcion && (
                      <p className="text-xs text-destructive">{errors.descripcion.message}</p>
                    )}
                  </div>

                  {/* Observación para historial */}
                  <div className="space-y-1.5">
                    <label htmlFor="observacion" className="text-sm font-medium">
                      Observación para el historial <span className="text-destructive">*</span>
                    </label>
                    <textarea
                      id="observacion"
                      rows={3}
                      placeholder="Observación que quedará registrada en el historial de estados..."
                      className={cn(
                        'flex w-full rounded-md border bg-background px-2.5 py-1.5 text-sm',
                        'ring-offset-background placeholder:text-muted-foreground resize-none',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                        errors.observacion ? 'border-destructive' : 'border-input'
                      )}
                      {...register('observacion')}
                    />
                    {errors.observacion && (
                      <p className="text-xs text-destructive">{errors.observacion.message}</p>
                    )}
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => navigate('/incapacidades/creacion-siniestro')}
                    >
                      Cancelar
                    </Button>
                    <Button type="submit" disabled={isSubmitting || mutation.isPending}>
                      <Link2 className="mr-2 h-4 w-4" />
                      {mutation.isPending
                        ? 'Creando siniestro...'
                        : 'Crear siniestro y reanudar auditoría'}
                    </Button>
                  </div>
                </form>
              </Card>
            </TabsContent>

            {/* Tab: Validaciones */}
            <TabsContent value="validaciones" className="space-y-4">
              <ValidacionesPanel
                issues={validaciones?.issues ?? []}
                isLoading={validacionesLoading}
              />
            </TabsContent>

            {/* Tab: Historial */}
            <TabsContent value="historial">
              <HistorialTimeline historial={historial || []} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
