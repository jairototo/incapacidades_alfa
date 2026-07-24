/**
 * LiquidacionPage — Página de liquidación de incapacidades.
 *
 * Accesible únicamente para incapacidades en estado LIQUIDACION o LIQUIDACION_PARCIAL.
 * Roles requeridos: AUDITOR o ADMIN (gateado también a nivel de router).
 *
 * Layout: split-screen replicando GestionarPage.
 *   - Sidebar izquierdo colapsable: documentos adjuntos
 *   - Columna derecha: Tabs "Liquidación" e "Historial"
 */
import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  ArrowLeft,
  Calculator,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  FileText,
  History,
  Image,
  RotateCcw,
  XCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

import { IncapacidadContextStrip } from '@/components/incapacidades/IncapacidadContextStrip';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';

import { incapacidadService } from '@/services/incapacidadService';
import { plantillaAuditoriaService } from '@/services/plantillaAuditoria';
import {
  liquidacionService,
  mapLiquidacionToBreakdown,
  MetodoPagoLiquidacion,
  METODO_PAGO_LABELS,
  type LiquidacionGuardar,
  type BreakdownResponse,
} from '@/services/liquidacion';
import { formatCurrency, formatDate } from '@/utils/formatters';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ALLOWED_STATES = ['LIQUIDACION', 'LIQUIDACION_PARCIAL'];

const BREAKDOWN_ROWS: {
  label: string;
  key: keyof BreakdownResponse;
}[] = [
  { label: 'Días y valor incapacidad temporal', key: 'incapacidad_temporal' },
  {
    label: 'Días y valor aporte patronal pensión',
    key: 'aporte_patronal_pension',
  },
  {
    label: 'Días y valor aporte trabajador pensión',
    key: 'aporte_trabajador_pension',
  },
  {
    label: 'Días y valor aporte adicional trabajador pensión',
    key: 'aporte_adicional_trabajador_pension',
  },
  {
    label: 'Días y valor aporte patronal salud',
    key: 'aporte_patronal_salud',
  },
  {
    label: 'Días y valor aporte trabajador salud',
    key: 'aporte_trabajador_salud',
  },
];

// ---------------------------------------------------------------------------
// Zod schemas (Zod v3 — sistema-interno uses v3.25.76)
// ---------------------------------------------------------------------------

const liquidacionFormSchema = z.object({
  ibl: z
    .string()
    .min(1, 'El IBL es obligatorio')
    .refine(
      (val) => !isNaN(Number(val)) && Number(val) > 0,
      'El IBL debe ser un número mayor a 0'
    ),
  metodo_pago: z
    .string()
    .optional()
    .transform((val) => (val === '' ? undefined : val)),
  notas_liquidador: z.string().max(1000, 'Máximo 1000 caracteres').optional(),
});

const devolucionSchema = z.object({
  observacion: z
    .string()
    .min(1, 'La observación es obligatoria')
    .max(1000, 'Máximo 1000 caracteres'),
});

type LiquidacionFormValues = z.infer<typeof liquidacionFormSchema>;
type DevolucionFormValues = z.infer<typeof devolucionSchema>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatBreakdownValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'Pendiente de configuración';
  return formatCurrency(value);
}

function getEstadoBadgeVariant(
  estado: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
      return 'default';
    case 'PAGADA':
    case 'PAGADA_PARCIAL':
      return 'secondary';
    case 'EN_AUDITORIA':
      return 'outline';
    default:
      return 'secondary';
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LiquidacionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [breakdown, setBreakdown] = useState<BreakdownResponse | null>(null);
  const [isBreakdownLoading, setIsBreakdownLoading] = useState(false);
  const [showDevolucionDialog, setShowDevolucionDialog] = useState(false);
  const [showDocumentsSidebar, setShowDocumentsSidebar] = useState(true);
  const [activeTab, setActiveTab] = useState('liquidacion');

  // ---------------------------------------------------------------------------
  // Queries
  // ---------------------------------------------------------------------------

  const {
    data: incapacidad,
    isLoading: incapacidadLoading,
    error: incapacidadError,
  } = useQuery({
    queryKey: ['incapacidad', id],
    queryFn: () => incapacidadService.getById(id!),
    enabled: !!id,
  });

  const { data: historial } = useQuery({
    queryKey: ['incapacidad', id, 'historial'],
    queryFn: () => incapacidadService.getHistorial(id!),
    enabled: !!id,
  });

  const { data: liquidacionExistente } = useQuery({
    queryKey: ['incapacidad', id, 'liquidacion'],
    queryFn: () => liquidacionService.getLiquidacion(id!),
    enabled:
      !!id &&
      !!incapacidad &&
      ALLOWED_STATES.includes(incapacidad.estado),
    retry: false,
  });

  const { data: plantilla } = useQuery({
    queryKey: ['incapacidad', id, 'plantilla-auditoria'],
    queryFn: () => plantillaAuditoriaService.getByIncapacidad(id!),
    enabled: !!id && !!incapacidad && ALLOWED_STATES.includes(incapacidad.estado),
    retry: false,
  });

  const { data: documentos } = useQuery({
    queryKey: ['incapacidad', id, 'documentos'],
    queryFn: () => incapacidadService.getDocumentos(id!),
    enabled: !!id,
  });

  // Breakdown displayed in the table: user's recalculation takes priority;
  // falls back to the saved values when the user hasn't pressed "Calcular".
  const displayedBreakdown = useMemo(
    () => breakdown ?? (liquidacionExistente ? mapLiquidacionToBreakdown(liquidacionExistente) : null),
    [breakdown, liquidacionExistente]
  );

  // ---------------------------------------------------------------------------
  // Forms
  // ---------------------------------------------------------------------------

  const {
    register,
    handleSubmit,
    getValues,
    trigger,
    reset: resetForm,
    formState: { errors, isSubmitting },
  } = useForm<LiquidacionFormValues>({
    resolver: zodResolver(liquidacionFormSchema),
    defaultValues: {
      ibl: '',
      metodo_pago: undefined,
      notas_liquidador: '',
    },
  });

  useEffect(() => {
    if (liquidacionExistente) {
      resetForm({
        ibl: liquidacionExistente.ibl != null ? String(liquidacionExistente.ibl) : '',
        metodo_pago: liquidacionExistente.metodo_pago ?? undefined,
        notas_liquidador: liquidacionExistente.notas_liquidador ?? '',
      });
    }
  }, [liquidacionExistente, resetForm]);

  const {
    register: devolucionRegister,
    handleSubmit: handleDevolucionSubmit,
    reset: resetDevolucion,
    formState: { errors: devolucionErrors, isSubmitting: devolucionSubmitting },
  } = useForm<DevolucionFormValues>({
    resolver: zodResolver(devolucionSchema),
    defaultValues: { observacion: '' },
  });

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const guardarMutation = useMutation({
    mutationFn: (payload: LiquidacionGuardar) =>
      liquidacionService.guardarLiquidacion(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id, 'liquidacion'] });
      toast({ title: 'Liquidación guardada correctamente' });
    },
    onError: (err: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al guardar',
        description:
          err?.response?.data?.detail ?? err?.message ?? 'Error desconocido',
      });
    },
  });

  const completarMutation = useMutation({
    mutationFn: () => liquidacionService.completarLiquidacion(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      toast({
        title: 'Liquidación completada',
        description: 'La incapacidad pasó a estado EN_PAGO y queda lista para generar la orden de pago.',
      });
      setTimeout(() => navigate('/incapacidades/pendientes'), 1500);
    },
    onError: (err: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al completar',
        description:
          err?.response?.data?.detail ?? err?.message ?? 'Error desconocido',
      });
    },
  });

  const devolverMutation = useMutation({
    mutationFn: (observacion: string) =>
      liquidacionService.devolverAuditoria(id!, observacion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      setShowDevolucionDialog(false);
      resetDevolucion();
      toast({
        title: 'Incapacidad devuelta a auditoría',
        description: 'El auditor recibirá la incapacidad nuevamente.',
      });
      setTimeout(() => navigate('/incapacidades/pendientes'), 1500);
    },
    onError: (err: any) => {
      toast({
        variant: 'destructive',
        title: 'Error al devolver',
        description:
          err?.response?.data?.detail ?? err?.message ?? 'Error desconocido',
      });
    },
  });

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleCalcularBreakdown = async () => {
    const iblValid = await trigger('ibl');
    if (!iblValid) return;

    const iblStr = getValues('ibl');
    const iblNum = iblStr ? Number(iblStr) : null;
    const dias = incapacidad?.dias_totales ?? 0;
    if (!dias) {
      toast({
        variant: 'destructive',
        title: 'No se puede calcular',
        description: 'La incapacidad no tiene días totales definidos.',
      });
      return;
    }
    setIsBreakdownLoading(true);
    try {
      const result = await liquidacionService.calcularBreakdown(
        id!,
        iblNum,
        dias
      );
      setBreakdown(result);
    } catch (err: any) {
      toast({
        variant: 'destructive',
        title: 'Error al calcular desglose',
        description:
          err?.response?.data?.detail ?? err?.message ?? 'Error desconocido',
      });
    } finally {
      setIsBreakdownLoading(false);
    }
  };

  const onSave = (values: z.infer<typeof liquidacionFormSchema>) => {
    if (!incapacidad) return;
    const payload: LiquidacionGuardar = {
      ibl: Number(values.ibl),
      dias_autorizados: incapacidad.dias_totales,
      fecha_inicio_autorizada: incapacidad.fecha_inicio,
      fecha_fin_autorizada: incapacidad.fecha_fin,
      metodo_pago: values.metodo_pago
        ? (values.metodo_pago as MetodoPagoLiquidacion)
        : null,
      notas_liquidador: values.notas_liquidador || null,
    };
    guardarMutation.mutate(payload);
  };

  const onCompletar = () => {
    completarMutation.mutate();
  };

  const onDevolver = (values: DevolucionFormValues) => {
    devolverMutation.mutate(values.observacion);
  };

  // ---------------------------------------------------------------------------
  // Loading / Error states
  // ---------------------------------------------------------------------------

  if (incapacidadLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="text-slate-500">Cargando incapacidad...</p>
        </div>
      </div>
    );
  }

  if (incapacidadError || !incapacidad) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md">
          <div className="text-center space-y-4">
            <XCircle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">
              Incapacidad no encontrada
            </h2>
            <p className="text-slate-500">
              No se pudo cargar la información de la incapacidad solicitada.
            </p>
            <Button onClick={() => navigate('/incapacidades/pendientes')}>
              Volver a Pendientes
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!ALLOWED_STATES.includes(incapacidad.estado)) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md">
          <div className="text-center space-y-4">
            <XCircle className="h-16 w-16 text-amber-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">
              Estado no válido para liquidación
            </h2>
            <p className="text-slate-500">
              La página de liquidación solo está disponible para incapacidades
              en estado{' '}
              <strong>LIQUIDACION</strong> o <strong>LIQUIDACION_PARCIAL</strong>.
            </p>
            <p className="text-sm text-slate-600">
              Estado actual:{' '}
              <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>
                {incapacidad.estado}
              </Badge>
            </p>
            <Button onClick={() => navigate(-1)}>Volver</Button>
          </div>
        </Card>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/incapacidades/pendientes')}
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Volver
          </Button>
          <div>
            <h1 className="text-lg font-bold text-slate-900 flex items-center gap-3">
              Liquidación de Incapacidad
              <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>
                {incapacidad.estado}
              </Badge>
            </h1>
            <p className="text-slate-500 mt-0.5 font-mono">{incapacidad.numero}</p>
          </div>
        </div>

        {/* Tipo + Toggle documentos */}
        <div className="flex items-center gap-3">
          <Badge
            variant={incapacidad.tipo === 'ARL' ? 'default' : 'secondary'}
            className="text-sm px-3 py-1"
          >
            {incapacidad.tipo}
          </Badge>
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

      {/* Contexto de la incapacidad (solo lectura) */}
      <IncapacidadContextStrip
        incapacidad={incapacidad}
        hasFraudAlert={false}
      />

      {/* Split-screen: Documentos | Área de trabajo */}
      <div className="flex flex-col lg:flex-row gap-4">

        {/* Sidebar izquierdo — Documentos (colapsable) */}
        {showDocumentsSidebar && (
          <div className="w-full lg:w-1/2 flex-shrink-0">
            <Card className="h-full sticky top-4" data-testid="documentos-section">
              <div className="p-4 border-b flex items-center gap-2">
                <Image className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold">Documentos Adjuntos</h3>
                <Badge variant="secondary">{documentos?.length || 0}</Badge>
              </div>
              <div className="p-4 overflow-y-auto max-h-[calc(100vh-200px)]">
                {documentos && documentos.length === 0 ? (
                  <div
                    className="flex items-center gap-2 text-slate-500"
                    data-testid="documentos-empty"
                  >
                    <FileText className="h-4 w-4" />
                    <span className="text-sm">
                      No hay documentos adjuntos para esta incapacidad.
                    </span>
                  </div>
                ) : (
                  <DocumentosViewer documentos={documentos || []} />
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Columna derecha — Área de trabajo */}
        <div className={cn('flex-1', showDocumentsSidebar ? 'lg:w-1/2' : 'w-full')}>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="liquidacion" className="space-x-2">
                <Calculator className="h-4 w-4" />
                <span>Liquidación</span>
              </TabsTrigger>
              <TabsTrigger value="historial" className="space-x-2">
                <History className="h-4 w-4" />
                <span>Historial ({historial?.length || 0})</span>
              </TabsTrigger>
            </TabsList>

            {/* Tab: Liquidación */}
            <TabsContent value="liquidacion" className="space-y-4">

              {/* a. Período autorizado */}
              <Card className="p-4 bg-slate-50 border-slate-200">
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
                  Período autorizado
                </h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Fecha inicio</span>
                    <p className="font-medium">{formatDate(incapacidad.fecha_inicio)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Fecha fin</span>
                    <p className="font-medium">{formatDate(incapacidad.fecha_fin)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Días autorizados</span>
                    <p className="font-bold text-blue-700">{incapacidad.dias_totales}</p>
                  </div>
                </div>
              </Card>

              {/* b. Plantilla de Auditoría (condicional) */}
              {plantilla && (
                <Card className="p-4" data-testid="plantilla-auditoria-card">
                  <div className="flex items-center gap-2 mb-4">
                    <ClipboardCheck className="h-5 w-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-slate-800">
                      Plantilla de Auditoría
                    </h2>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {plantilla.linea_autorizacion && (
                      <div className="col-span-2">
                        <span className="text-slate-500">Línea de autorización</span>
                        <p className="font-medium text-blue-800">
                          {plantilla.linea_autorizacion}
                        </p>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-500">Canal de recepción</span>
                      <p className="font-medium">{plantilla.canal_recepcion}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Días autorizados</span>
                      <p className="font-medium">{plantilla.dias_autorizados}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Fecha inicio autorizada</span>
                      <p className="font-medium">
                        {formatDate(plantilla.fecha_inicio_autorizada)}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500">Fecha fin autorizada</span>
                      <p className="font-medium">
                        {formatDate(plantilla.fecha_fin_autorizada)}
                      </p>
                    </div>
                    {plantilla.diagnostico_cie10 && (
                      <div>
                        <span className="text-slate-500">CIE-10</span>
                        <p className="font-medium">{plantilla.diagnostico_cie10}</p>
                      </div>
                    )}
                    {plantilla.descripcion_cie10 && (
                      <div>
                        <span className="text-slate-500">Diagnóstico</span>
                        <p className="font-medium">{plantilla.descripcion_cie10}</p>
                      </div>
                    )}
                    {plantilla.nombre_medico && (
                      <div>
                        <span className="text-slate-500">Médico tratante</span>
                        <p className="font-medium">{plantilla.nombre_medico}</p>
                      </div>
                    )}
                    {plantilla.nombre_ips && (
                      <div>
                        <span className="text-slate-500">IPS prestadora</span>
                        <p className="font-medium">{plantilla.nombre_ips}</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}

              {/* c. Formulario de liquidación */}
              <form onSubmit={handleSubmit(onSave)} className="space-y-4">

                {/* IBL + Calcular desglose */}
                <Card className="p-4 space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h2 className="text-lg font-semibold text-slate-800">
                      Ingreso Base de Liquidación (IBL)
                    </h2>
                    <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                      Integración Imaginex pendiente — ingreso manual
                    </span>
                  </div>
                  <div className="flex gap-3 items-start">
                    <div className="flex-1 space-y-1.5">
                      <label
                        htmlFor="ibl"
                        className="text-sm font-medium leading-none"
                      >
                        IBL (Ingreso Base de Liquidación){' '}
                        <span className="text-destructive">*</span>
                      </label>
                      <input
                        id="ibl"
                        type="text"
                        inputMode="decimal"
                        placeholder="Ej: 2500000.00"
                        data-testid="ibl-input"
                        className={[
                          'flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm',
                          'ring-offset-background placeholder:text-muted-foreground',
                          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                          errors.ibl ? 'border-destructive' : 'border-input',
                        ].join(' ')}
                        {...register('ibl')}
                      />
                      {errors.ibl && (
                        <p className="text-xs text-destructive">{errors.ibl.message}</p>
                      )}
                    </div>
                    <div className="pt-4">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleCalcularBreakdown}
                        disabled={isBreakdownLoading}
                        data-testid="calcular-breakdown-btn"
                      >
                        <Calculator className="mr-2 h-4 w-4" />
                        {isBreakdownLoading ? 'Calculando...' : 'Calcular desglose'}
                      </Button>
                    </div>
                  </div>
                </Card>

                {/* Tabla de desglose */}
                <Card className="p-4">
                  <h2 className="text-lg font-semibold text-slate-800 mb-4">
                    Desglose de liquidación
                  </h2>
                  {displayedBreakdown && (
                    <p className="text-xs text-slate-500 mb-3 italic">{displayedBreakdown.nota}</p>
                  )}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" data-testid="breakdown-table">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-2 px-3 font-medium text-slate-600">
                            Concepto
                          </th>
                          <th className="text-right py-2 px-3 font-medium text-slate-600">
                            Valor
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {BREAKDOWN_ROWS.map((row) => (
                          <tr
                            key={row.key}
                            className="border-b border-slate-100 last:border-0"
                          >
                            <td className="py-2 px-3 text-slate-700">{row.label}</td>
                            <td className="py-2 px-3 text-right font-mono text-slate-700">
                              {displayedBreakdown
                                ? formatBreakdownValue(
                                    displayedBreakdown[row.key] as number | null
                                  )
                                : 'Pendiente de configuración'}
                            </td>
                          </tr>
                        ))}
                        <tr className="bg-slate-50 font-semibold">
                          <td className="py-2 px-3 text-slate-800">Total</td>
                          <td className="py-2 px-3 text-right font-mono text-slate-800">
                            {displayedBreakdown
                              ? formatBreakdownValue(displayedBreakdown.valor_total)
                              : 'Pendiente de configuración'}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </Card>

                {/* Método de pago */}
                <Card className="p-4 space-y-4">
                  <h2 className="text-lg font-semibold text-slate-800">
                    Método de pago
                  </h2>
                  <div className="space-y-1.5">
                    <label
                      htmlFor="metodo_pago"
                      className="text-sm font-medium leading-none"
                    >
                      Método de pago
                      <span className="text-xs text-slate-500 ml-2">
                        (Opcional — pendiente lista de entidades C2)
                      </span>
                    </label>
                    <select
                      id="metodo_pago"
                      className={[
                        'flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm',
                        'ring-offset-background',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                        errors.metodo_pago ? 'border-destructive' : 'border-input',
                      ].join(' ')}
                      {...register('metodo_pago')}
                    >
                      <option value="">Seleccionar...</option>
                      {Object.entries(MetodoPagoLiquidacion).map(([key, value]) => (
                        <option key={key} value={value}>
                          {METODO_PAGO_LABELS[value as MetodoPagoLiquidacion]}
                        </option>
                      ))}
                    </select>
                  </div>
                </Card>

                {/* Notas del liquidador */}
                <Card className="p-4 space-y-4">
                  <h2 className="text-lg font-semibold text-slate-800">
                    Notas del liquidador
                  </h2>
                  <div className="space-y-1.5">
                    <label
                      htmlFor="notas_liquidador"
                      className="text-sm font-medium leading-none"
                    >
                      Notas{' '}
                      <span className="text-xs text-slate-500">(Opcional)</span>
                    </label>
                    <textarea
                      id="notas_liquidador"
                      rows={3}
                      placeholder="Observaciones libres sobre la liquidación..."
                      className={[
                        'flex w-full rounded-md border bg-background px-3 py-2 text-sm',
                        'ring-offset-background placeholder:text-muted-foreground',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                        'resize-none',
                        errors.notas_liquidador ? 'border-destructive' : 'border-input',
                      ].join(' ')}
                      {...register('notas_liquidador')}
                    />
                    {errors.notas_liquidador && (
                      <p className="text-xs text-destructive">
                        {errors.notas_liquidador.message}
                      </p>
                    )}
                  </div>
                </Card>

                {/* Botones de acción */}
                <Card className="p-4">
                  <div className="flex flex-col sm:flex-row gap-3 justify-between">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setShowDevolucionDialog(true)}
                      className="text-amber-700 border-amber-300 hover:bg-amber-50"
                      data-testid="devolver-auditoria-btn"
                    >
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Devolver a auditoría
                    </Button>
                    <div className="flex gap-3">
                      <Button
                        type="submit"
                        variant="outline"
                        disabled={isSubmitting || guardarMutation.isPending}
                        data-testid="guardar-borrador-btn"
                      >
                        {guardarMutation.isPending ? 'Guardando...' : 'Guardar borrador'}
                      </Button>
                      <Button
                        type="button"
                        onClick={onCompletar}
                        disabled={completarMutation.isPending}
                        data-testid="completar-liquidacion-btn"
                      >
                        <CheckCircle className="mr-2 h-4 w-4" />
                        {completarMutation.isPending
                          ? 'Completando...'
                          : 'Completar liquidación'}
                      </Button>
                    </div>
                  </div>
                </Card>
              </form>
            </TabsContent>

            {/* Tab: Historial */}
            <TabsContent value="historial">
              <Card className="p-4">
                <HistorialTimeline historial={historial || []} />
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Dialog: Devolver a auditoría */}
      <Dialog open={showDevolucionDialog} onOpenChange={setShowDevolucionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Devolver a auditoría</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleDevolucionSubmit(onDevolver)} className="space-y-4">
            <p className="text-sm text-slate-600">
              La incapacidad <strong>{incapacidad.numero}</strong> será devuelta
              al estado <strong>EN_AUDITORIA</strong>. El auditor recibirá la
              incapacidad nuevamente para revisión.
            </p>
            <div className="space-y-1.5">
              <label
                htmlFor="observacion-devolucion"
                className="text-sm font-medium leading-none"
              >
                Observación <span className="text-destructive">*</span>
              </label>
              <textarea
                id="observacion-devolucion"
                rows={4}
                placeholder="Describe el motivo de la devolución..."
                className={[
                  'flex w-full rounded-md border bg-background px-3 py-2 text-sm',
                  'ring-offset-background placeholder:text-muted-foreground',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'resize-none',
                  devolucionErrors.observacion
                    ? 'border-destructive'
                    : 'border-input',
                ].join(' ')}
                {...devolucionRegister('observacion')}
              />
              {devolucionErrors.observacion && (
                <p className="text-xs text-destructive" data-testid="devolucion-error">
                  {devolucionErrors.observacion.message}
                </p>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowDevolucionDialog(false);
                  resetDevolucion();
                }}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={devolucionSubmitting || devolverMutation.isPending}
                data-testid="confirmar-devolucion-btn"
              >
                {devolverMutation.isPending
                  ? 'Devolviendo...'
                  : 'Confirmar devolución'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
