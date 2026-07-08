import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQueryClient, useMutation } from '@tanstack/react-query';
import { CheckCircle, XCircle, AlertCircle, Copy, Check } from 'lucide-react';

import type { Incapacidad } from '@/types/incapacidad';
import { incapacidadService } from '@/services/incapacidadService';
import api from '@/lib/api';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Zod schema
// ---------------------------------------------------------------------------

const today = new Date().toISOString().split('T')[0];

const approvalSchema = z.object({
  fecha_inicio_aprobada: z.string().min(1, 'Requerido').refine(v => v <= today, {
    message: 'No puede ser posterior a hoy',
  }),
  fecha_fin_aprobada: z.string().min(1, 'Requerido').refine(v => v <= today, {
    message: 'No puede ser posterior a hoy',
  }),
  cie10_aprobado: z.string().regex(/^[A-Z]\d{2}[0-9X]$/, 'Formato inválido (ej: M545, A09X)').optional().or(z.literal('')),
  descripcion_cie10: z.string().optional(),
  canal_recepcion: z.string().min(1, 'Requerido'),
  nombre_ips: z.string().optional(),
  nombre_medico: z.string().optional(),
  especialidad_medico: z.string().optional(),
  observacion: z.string().min(10, 'Mínimo 10 caracteres'),
}).refine(d => !d.fecha_inicio_aprobada || !d.fecha_fin_aprobada || d.fecha_fin_aprobada >= d.fecha_inicio_aprobada, {
  message: 'La fecha fin no puede ser anterior a la fecha inicio',
  path: ['fecha_fin_aprobada'],
});

const simpleSchema = z.object({
  observacion: z.string().min(10, 'Mínimo 10 caracteres'),
});

type ApprovalFormData = z.infer<typeof approvalSchema>;
type SimpleFormData = z.infer<typeof simpleSchema>;

// ---------------------------------------------------------------------------
// CIE-10 autocomplete
// ---------------------------------------------------------------------------

interface Cie10Item { codigo: string; descripcion: string }

function useCie10Search(query: string) {
  const [results, setResults] = useState<Cie10Item[]>([]);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (query.length < 2) { setResults([]); return; }
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const { data } = await api.get<Cie10Item[]>('/catalogos/cie10', { params: { q: query, limit: 8 } });
        setResults(data);
      } catch { setResults([]); }
      finally { setLoading(false); }
    }, 300);
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
  }, [query]);

  return { results, loading };
}

async function fetchCie10Descripcion(codigo: string): Promise<string | null> {
  try {
    const { data } = await api.get<Cie10Item>(`/catalogos/cie10/${codigo}`);
    return data.descripcion;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Success panel
// ---------------------------------------------------------------------------

function SuccessPanel({ estado, textoCopiable }: { estado: string; textoCopiable: string }) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(textoCopiable);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [textoCopiable]);

  return (
    <Card className="border-green-300 bg-green-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-green-800">
          <CheckCircle className="h-5 w-5" />
          Incapacidad procesada exitosamente
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-green-700">Nuevo estado:</span>
          <Badge variant="default" className="bg-green-600">
            {estado}
          </Badge>
        </div>

        <div className="space-y-2">
          <Label className="text-green-800">Texto copiable (para Arpis)</Label>
          <div className="relative">
            <pre className="rounded-md bg-white border border-green-200 p-3 text-xs font-mono whitespace-pre-wrap text-slate-800 max-h-48 overflow-y-auto">
              {textoCopiable}
            </pre>
            <Button
              size="sm"
              variant="outline"
              className="absolute top-2 right-2 h-7 px-2"
              onClick={handleCopy}
            >
              {copied ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
              <span className="ml-1 text-xs">{copied ? 'Copiado' : 'Copiar'}</span>
            </Button>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button onClick={() => navigate('/incapacidades/pendientes')}>
            Volver a pendientes
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Approval form (for both "Aprobar" and "Liquidación Parcial")
// ---------------------------------------------------------------------------

interface ApprovalFormProps {
  incapacidad: Incapacidad;
  onSubmit: (data: ApprovalFormData) => void;
  onCancel: () => void;
  isLoading: boolean;
  backendErrors: { codigo: string; descripcion: string }[];
}

function ApprovalForm({ incapacidad, onSubmit, onCancel, isLoading, backendErrors }: ApprovalFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ApprovalFormData>({
    resolver: zodResolver(approvalSchema),
    defaultValues: {
      fecha_inicio_aprobada: incapacidad.fecha_inicio,
      fecha_fin_aprobada: incapacidad.fecha_fin,
      cie10_aprobado: incapacidad.diagnostico_cie10 ?? '',
      descripcion_cie10: '',
      canal_recepcion: 'Portal IT',
      nombre_ips: incapacidad.ips ?? '',
      nombre_medico: incapacidad.nombre_medico ?? '',
      observacion: '',
    },
  });

  const [cie10Query, setCie10Query] = useState(incapacidad.diagnostico_cie10 ?? '');
  const [showCie10Dropdown, setShowCie10Dropdown] = useState(false);
  const { results: cie10Results } = useCie10Search(cie10Query);

  // Resolver la descripción del código CIE-10 original consultando el catálogo
  useEffect(() => {
    const codigoOriginal = incapacidad.diagnostico_cie10;
    if (!codigoOriginal) return;
    let cancelled = false;
    fetchCie10Descripcion(codigoOriginal).then(descripcion => {
      if (!cancelled && descripcion) setValue('descripcion_cie10', descripcion);
    });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fechaInicio = watch('fecha_inicio_aprobada');
  const fechaFin = watch('fecha_fin_aprobada');

  const diasAprobados = (() => {
    if (!fechaInicio || !fechaFin || fechaFin < fechaInicio) return null;
    const d1 = new Date(fechaInicio);
    const d2 = new Date(fechaFin);
    return Math.floor((d2.getTime() - d1.getTime()) / 86400000) + 1;
  })();

  const handleCie10Select = (item: Cie10Item) => {
    setValue('cie10_aprobado', item.codigo);
    setValue('descripcion_cie10', item.descripcion);
    setCie10Query(item.codigo);
    setShowCie10Dropdown(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Fechas aprobadas */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor="fecha_inicio_aprobada">Fecha inicio aprobada <span className="text-red-500">*</span></Label>
          <Input id="fecha_inicio_aprobada" type="date" max={today} {...register('fecha_inicio_aprobada')} />
          {errors.fecha_inicio_aprobada && <p className="text-xs text-red-500">{errors.fecha_inicio_aprobada.message}</p>}
        </div>
        <div className="space-y-1">
          <Label htmlFor="fecha_fin_aprobada">Fecha fin aprobada <span className="text-red-500">*</span></Label>
          <Input id="fecha_fin_aprobada" type="date" max={today} {...register('fecha_fin_aprobada')} />
          {errors.fecha_fin_aprobada && <p className="text-xs text-red-500">{errors.fecha_fin_aprobada.message}</p>}
        </div>
      </div>

      {/* Días aprobados (read-only) */}
      <div className="space-y-1">
        <Label>Días aprobados</Label>
        <Input
          type="number"
          value={diasAprobados ?? ''}
          readOnly
          className="bg-slate-50 cursor-not-allowed"
          placeholder="Se calcula automáticamente"
        />
        {diasAprobados !== null && diasAprobados < incapacidad.dias_totales && (
          <p className="text-xs text-amber-600">
            {diasAprobados} días aprobados vs {incapacidad.dias_totales} solicitados → se generará liquidación parcial
          </p>
        )}
      </div>

      {/* CIE-10 autocomplete */}
      <div className="space-y-1 relative">
        <Label htmlFor="cie10_search">CIE-10</Label>
        <Input
          id="cie10_search"
          value={cie10Query}
          onChange={e => { setCie10Query(e.target.value); setShowCie10Dropdown(true); setValue('cie10_aprobado', e.target.value.toUpperCase()); }}
          onFocus={() => setShowCie10Dropdown(true)}
          onBlur={() => setTimeout(() => setShowCie10Dropdown(false), 150)}
          placeholder="Buscar código CIE-10..."
          className="uppercase"
          autoComplete="off"
        />
        <input type="hidden" {...register('cie10_aprobado')} />
        {errors.cie10_aprobado && <p className="text-xs text-red-500">{errors.cie10_aprobado.message}</p>}
        {showCie10Dropdown && cie10Results.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
            {cie10Results.map(item => (
              <button
                key={item.codigo}
                type="button"
                className="w-full text-left px-3 py-2 text-sm hover:bg-slate-100 flex items-baseline gap-2"
                onMouseDown={() => handleCie10Select(item)}
              >
                <span className="font-mono font-semibold text-blue-700 shrink-0">{item.codigo}</span>
                <span className="text-slate-600 truncate">{item.descripcion}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Descripción CIE-10 (read-only from catalog) */}
      <div className="space-y-1">
        <Label htmlFor="descripcion_cie10_display">Descripción diagnóstico</Label>
        <Input
          id="descripcion_cie10_display"
          value={watch('descripcion_cie10') ?? ''}
          readOnly
          className="bg-slate-50 cursor-not-allowed text-slate-600"
          placeholder="Se completa al seleccionar CIE-10"
        />
        <input type="hidden" {...register('descripcion_cie10')} />
      </div>

      {/* Canal de recepción */}
      <div className="space-y-1">
        <Label htmlFor="canal_recepcion">Canal de recepción <span className="text-red-500">*</span></Label>
        <Input id="canal_recepcion" {...register('canal_recepcion')} placeholder="Ej: Portal, Correo, Presencial" />
        {errors.canal_recepcion && <p className="text-xs text-red-500">{errors.canal_recepcion.message}</p>}
      </div>

      {/* Nombre IPS */}
      <div className="space-y-1">
        <Label htmlFor="nombre_ips">Nombre IPS</Label>
        <Input id="nombre_ips" {...register('nombre_ips')} placeholder="Institución prestadora de salud" />
      </div>

      {/* Nombre médico / especialidad */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label htmlFor="nombre_medico">Nombre médico</Label>
          <Input id="nombre_medico" {...register('nombre_medico')} placeholder="Dr. Apellido Nombre" />
        </div>
        <div className="space-y-1">
          <Label htmlFor="especialidad_medico">Especialidad</Label>
          <Input id="especialidad_medico" {...register('especialidad_medico')} placeholder="Medicina general, etc." />
        </div>
      </div>

      {/* Observación */}
      <div className="space-y-1">
        <Label htmlFor="observacion">Observación <span className="text-red-500">*</span></Label>
        <Textarea
          id="observacion"
          {...register('observacion')}
          rows={4}
          placeholder="Justificación de la decisión (mínimo 10 caracteres)"
        />
        {errors.observacion && <p className="text-xs text-red-500">{errors.observacion.message}</p>}
      </div>

      {/* Backend validation errors */}
      {backendErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <p className="font-medium mb-1">Reglas de auditoría fallidas:</p>
            <ul className="list-disc list-inside space-y-0.5 text-sm">
              {backendErrors.map(r => (
                <li key={r.codigo}><span className="font-mono">{r.codigo}</span> — {r.descripcion}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end gap-3 pt-2 border-t border-slate-200">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading} className="bg-green-600 hover:bg-green-700">
          {isLoading ? 'Procesando...' : 'Confirmar aprobación'}
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Simple form (PENDIENTE / GLOSAR)
// ---------------------------------------------------------------------------

interface SimpleFormProps {
  accion: 'PENDIENTE' | 'GLOSAR';
  onSubmit: (observacion: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}

function SimpleActionForm({ accion, onSubmit, onCancel, isLoading }: SimpleFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SimpleFormData>({ resolver: zodResolver(simpleSchema) });

  const isGlosar = accion === 'GLOSAR';

  return (
    <form onSubmit={handleSubmit(d => onSubmit(d.observacion))} className="space-y-4">
      <div className="space-y-1">
        <Label htmlFor="observacion-simple">
          {isGlosar ? 'Justificación de la glosa' : 'Información requerida'}{' '}
          <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="observacion-simple"
          {...register('observacion')}
          rows={5}
          placeholder={
            isGlosar
              ? 'Describa las razones de la glosa (mínimo 10 caracteres)'
              : 'Describa la información faltante o las correcciones necesarias (mínimo 10 caracteres)'
          }
        />
        {errors.observacion && <p className="text-xs text-red-500">{errors.observacion.message}</p>}
      </div>
      <div className="flex justify-end gap-3 pt-2 border-t border-slate-200">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button
          type="submit"
          disabled={isLoading}
          className={isGlosar ? 'bg-red-600 hover:bg-red-700' : 'bg-orange-600 hover:bg-orange-700'}
        >
          {isLoading ? 'Procesando...' : isGlosar ? 'Confirmar glosa' : 'Confirmar pendiente'}
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

type PanelAction = 'APROBAR' | 'LIQUIDACION_PARCIAL' | 'PENDIENTE' | 'GLOSAR';

interface AuditoriaPanelProps {
  incapacidad: Incapacidad;
}

export function AuditoriaPanel({ incapacidad }: AuditoriaPanelProps) {
  const queryClient = useQueryClient();
  const [selectedAction, setSelectedAction] = useState<PanelAction | null>(null);
  const [successData, setSuccessData] = useState<{ estado: string; textoCopiable: string } | null>(null);
  const [backendErrors, setBackendErrors] = useState<{ codigo: string; descripcion: string }[]>([]);

  // ARL without siniestro → only allow GLOSAR
  const isArlSinSiniestro = incapacidad.tipo === 'ARL' && !incapacidad.numero_siniestro;

  const invalidateQueries = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['incapacidad', incapacidad.id] });
    queryClient.invalidateQueries({ queryKey: ['incapacidad', incapacidad.id, 'historial'] });
    queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
  }, [queryClient, incapacidad.id]);

  // Mutation: aprobar en auditoría (LIQUIDACION / LIQUIDACION_PARCIAL)
  const aprobarMutation = useMutation({
    mutationFn: (data: ApprovalFormData) =>
      incapacidadService.aprobarEnAuditoria(incapacidad.id, {
        fecha_inicio_aprobada: data.fecha_inicio_aprobada,
        fecha_fin_aprobada: data.fecha_fin_aprobada,
        cie10_aprobado: data.cie10_aprobado || undefined,
        descripcion_cie10: data.descripcion_cie10 || undefined,
        canal_recepcion: data.canal_recepcion,
        nombre_ips: data.nombre_ips || undefined,
        nombre_medico: data.nombre_medico || undefined,
        especialidad_medico: data.especialidad_medico || undefined,
        observacion: data.observacion,
      }),
    onSuccess: result => {
      invalidateQueries();
      setBackendErrors([]);
      setSelectedAction(null);
      setSuccessData({ estado: result.estado, textoCopiable: result.texto_copiable });
    },
    onError: (error: any) => {
      const reglas = error.response?.data?.details?.reglas_fallidas ?? [];
      setBackendErrors(reglas);
    },
  });

  // Mutation: glosar
  const glosarMutation = useMutation({
    mutationFn: (observacion: string) => incapacidadService.glosar(incapacidad.id, observacion),
    onSuccess: result => {
      invalidateQueries();
      setSelectedAction(null);
      setSuccessData({ estado: result.estado, textoCopiable: `Incapacidad glosada. Estado: ${result.estado}` });
    },
  });

  // Mutation: pendiente
  const pendienteMutation = useMutation({
    mutationFn: (observacion: string) => incapacidadService.ponerPendiente(incapacidad.id, observacion),
    onSuccess: result => {
      invalidateQueries();
      setSelectedAction(null);
      setSuccessData({ estado: result.estado, textoCopiable: `Incapacidad en pendiente. Estado: ${result.estado}` });
    },
  });

  const isLoading = aprobarMutation.isPending || glosarMutation.isPending || pendienteMutation.isPending;

  // Show success panel after any successful action
  if (successData) {
    return <SuccessPanel estado={successData.estado} textoCopiable={successData.textoCopiable} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertCircle className="h-5 w-5 text-blue-600" />
          Acciones de auditoría
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* ARL warning if no siniestro */}
        {isArlSinSiniestro && (
          <Alert className="bg-amber-50 border-amber-300">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Esta incapacidad ARL no tiene siniestro vinculado. Solo es posible glosarla.
            </AlertDescription>
          </Alert>
        )}

        {/* Action buttons */}
        {!selectedAction && (
          <div className={cn('grid gap-3', isArlSinSiniestro ? 'grid-cols-1 max-w-xs' : 'grid-cols-2 md:grid-cols-4')}>
            {!isArlSinSiniestro && (
              <>
                <button
                  type="button"
                  onClick={() => { setBackendErrors([]); setSelectedAction('APROBAR'); }}
                  className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-green-200 bg-green-50 p-4 text-green-800 hover:bg-green-100 hover:border-green-400 transition-colors"
                >
                  <CheckCircle className="h-8 w-8 text-green-600" />
                  <div className="text-center">
                    <p className="font-semibold text-sm">Aprobar para pago</p>
                    <p className="text-xs text-green-600 mt-0.5">Periodo completo aprobado</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => { setBackendErrors([]); setSelectedAction('LIQUIDACION_PARCIAL'); }}
                  className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-teal-200 bg-teal-50 p-4 text-teal-800 hover:bg-teal-100 hover:border-teal-400 transition-colors"
                >
                  <CheckCircle className="h-8 w-8 text-teal-600" />
                  <div className="text-center">
                    <p className="font-semibold text-sm">Liquidación Parcial</p>
                    <p className="text-xs text-teal-600 mt-0.5">Periodo parcialmente aprobado</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => { setBackendErrors([]); setSelectedAction('PENDIENTE'); }}
                  className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-orange-200 bg-orange-50 p-4 text-orange-800 hover:bg-orange-100 hover:border-orange-400 transition-colors"
                >
                  <AlertCircle className="h-8 w-8 text-orange-500" />
                  <div className="text-center">
                    <p className="font-semibold text-sm">Pendiente</p>
                    <p className="text-xs text-orange-600 mt-0.5">Solicitar información adicional</p>
                  </div>
                </button>
              </>
            )}

            <button
              type="button"
              onClick={() => { setBackendErrors([]); setSelectedAction('GLOSAR'); }}
              className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-red-200 bg-red-50 p-4 text-red-800 hover:bg-red-100 hover:border-red-400 transition-colors"
            >
              <XCircle className="h-8 w-8 text-red-600" />
              <div className="text-center">
                <p className="font-semibold text-sm">Glosar</p>
                <p className="text-xs text-red-600 mt-0.5">Rechazar incapacidad</p>
              </div>
            </button>
          </div>
        )}

        {/* Selected action: header */}
        {selectedAction && (
          <div className={cn(
            'text-sm font-semibold px-3 py-2 rounded-md',
            selectedAction === 'APROBAR' && 'bg-green-100 text-green-800',
            selectedAction === 'LIQUIDACION_PARCIAL' && 'bg-teal-100 text-teal-800',
            selectedAction === 'PENDIENTE' && 'bg-orange-100 text-orange-800',
            selectedAction === 'GLOSAR' && 'bg-red-100 text-red-800',
          )}>
            {selectedAction === 'APROBAR' && 'Aprobar para pago — complete el formulario de aprobación'}
            {selectedAction === 'LIQUIDACION_PARCIAL' && 'Liquidación Parcial — ajuste las fechas aprobadas'}
            {selectedAction === 'PENDIENTE' && 'Pendiente — indique qué información se requiere'}
            {selectedAction === 'GLOSAR' && 'Glosar — justifique las razones de la glosa'}
          </div>
        )}

        {/* Approval form (APROBAR and LIQUIDACION_PARCIAL use same form) */}
        {(selectedAction === 'APROBAR' || selectedAction === 'LIQUIDACION_PARCIAL') && (
          <ApprovalForm
            incapacidad={incapacidad}
            onSubmit={data => aprobarMutation.mutate(data)}
            onCancel={() => { setSelectedAction(null); setBackendErrors([]); }}
            isLoading={isLoading}
            backendErrors={backendErrors}
          />
        )}

        {/* Simple form for PENDIENTE */}
        {selectedAction === 'PENDIENTE' && (
          <SimpleActionForm
            accion="PENDIENTE"
            onSubmit={obs => pendienteMutation.mutate(obs)}
            onCancel={() => setSelectedAction(null)}
            isLoading={isLoading}
          />
        )}

        {/* Simple form for GLOSAR */}
        {selectedAction === 'GLOSAR' && (
          <SimpleActionForm
            accion="GLOSAR"
            onSubmit={obs => glosarMutation.mutate(obs)}
            onCancel={() => setSelectedAction(null)}
            isLoading={isLoading}
          />
        )}
      </CardContent>
    </Card>
  );
}
