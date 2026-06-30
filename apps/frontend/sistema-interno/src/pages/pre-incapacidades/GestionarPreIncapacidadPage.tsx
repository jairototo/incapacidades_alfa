import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  AlertCircle,
  Edit3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  CornerDownLeft,
  UserX,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

import { ValidationInconsistenciasList } from '@/components/pre-incapacidades/ValidationInconsistenciasList';
import { DevolucionModal } from '@/components/pre-incapacidades/DevolucionModal';
import { ResolverEntidadesPanel } from '@/components/pre-incapacidades/ResolverEntidadesPanel';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';

import { preIncapacidadService } from '@/services/preIncapacidadService';
import type { PreIncapacidadUpdate, PreDocumento } from '@/types/preIncapacidad';
import type { Documento } from '@/types/incapacidad';
import { formatDate } from '@/utils/formatters';

function toDocumento(d: PreDocumento): Documento {
  return {
    id: d.id,
    tipo_documento: d.tipo_documento,
    nombre_original: d.nombre_original,
    extension: d.nombre_original.split('.').pop() ?? '',
    tamano_bytes: 0,
    mime_type: '',
    uploaded_by: '',
    created_at: d.created_at,
  };
}

function estadoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'PENDIENTE': return 'default';
    case 'RECHAZADA': return 'destructive';
    case 'ERROR': return 'outline';
    case 'DEVUELTA': return 'secondary';
    case 'PROCESADA': return 'default';
    default: return 'outline';
  }
}

export function GestionarPreIncapacidadPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [showDocs, setShowDocs] = useState(true);
  const [activeTab, setActiveTab] = useState('inconsistencias');
  const [showDevolucion, setShowDevolucion] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editFields, setEditFields] = useState<PreIncapacidadUpdate>({});

  const { data: preInc, isLoading, error } = useQuery({
    queryKey: ['pre-incapacidad', id],
    queryFn: () => preIncapacidadService.getById(id!),
    enabled: !!id,
  });

  const { data: incapacidad } = useQuery({
    queryKey: ['pre-incapacidad-incapacidad', id, preInc?.incapacidad_id],
    queryFn: () => preIncapacidadService.getIncapacidad(id!),
    enabled: !!id && !!preInc?.incapacidad_id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: PreIncapacidadUpdate) =>
      preIncapacidadService.actualizar(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', id] });
      setEditMode(false);
      setEditFields({});
      toast({ title: 'Datos actualizados' });
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al guardar';
      toast({ title: 'Error al guardar', description: msg, variant: 'destructive' });
    },
  });

  const promoverMutation = useMutation({
    mutationFn: () => preIncapacidadService.promover(id!),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidades-bandeja'] });
      if (result.success) {
        toast({ title: 'Incapacidad creada', description: result.message });
        setTimeout(() => navigate('/pre-incapacidades/bandeja'), 1500);
      } else {
        toast({
          title: `Validación fallida — ${result.errors} error(es)`,
          description: result.message,
          variant: 'destructive',
        });
        setActiveTab('inconsistencias');
      }
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error al promover';
      toast({ title: 'Error al promover', description: msg, variant: 'destructive' });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !preInc) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md text-center space-y-4">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold">Pre-incapacidad no encontrada</h2>
          <Button onClick={() => navigate('/pre-incapacidades/bandeja')}>Volver a Bandeja</Button>
        </Card>
      </div>
    );
  }

  const errorCount = preInc.validation_inconsistencias.filter((i) => i.severidad === 'ERROR').length;
  const canPromote = !['PROCESADA', 'DEVUELTA'].includes(preInc.estado);
  const canDevolver = !['PROCESADA', 'DEVUELTA'].includes(preInc.estado);
  const empleadoNoEncontrado = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPLEADO_NOT_FOUND'
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/pre-incapacidades/bandeja')}>
            <ArrowLeft className="h-5 w-5 mr-2" />
            Bandeja
          </Button>
          <div>
            <h1 className="text-lg font-bold text-slate-900 flex items-center gap-3">
              Pre-Incapacidad
              <Badge variant={estadoBadgeVariant(preInc.estado)}>{preInc.estado}</Badge>
              {errorCount > 0 && (
                <Badge variant="destructive" className="gap-1">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {errorCount} error{errorCount > 1 ? 'es' : ''}
                </Badge>
              )}
            </h1>
            <p className="text-slate-500 font-mono">N° {preInc.numero_radicacion}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDocs(!showDocs)}
          >
            {showDocs ? (
              <><ChevronLeft className="h-4 w-4 mr-1" /> Ocultar docs</>
            ) : (
              <><ChevronRight className="h-4 w-4 mr-1" /> Documentos ({preInc.documentos.length})</>
            )}
          </Button>

          {canDevolver && (
            <Button
              variant="outline"
              className="border-orange-400 text-orange-700 hover:bg-orange-50"
              onClick={() => setShowDevolucion(true)}
            >
              <CornerDownLeft className="h-4 w-4 mr-2" />
              Devolver
            </Button>
          )}
          {canPromote && (
            <Button
              onClick={() => promoverMutation.mutate()}
              disabled={promoverMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {promoverMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Promover a Incapacidad
            </Button>
          )}
        </div>
      </div>

      {/* Incapacidad vinculada (shown after unified job completes) */}
      {preInc.incapacidad_id && (
        <Card className="p-4 border-blue-200 bg-blue-50 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-blue-900 text-sm font-semibold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Incapacidad N°{preInc.numero_radicacion} creada en el sistema
            </p>
            {incapacidad && (
              <Badge variant={incapacidad.estado === 'EN_AUDITORIA' ? 'default' : 'secondary'}>
                {incapacidad.estado}
              </Badge>
            )}
          </div>
          {empleadoNoEncontrado && (
            <div className="flex items-start gap-2 rounded bg-yellow-50 border border-yellow-200 p-3 text-yellow-800 text-xs">
              <UserX className="h-4 w-4 mt-0.5 shrink-0" />
              <span>
                <strong>Empleado no encontrado en BD.</strong> La incapacidad fue creada pero
                requiere resolución manual antes de poder procesar el pago.
              </span>
            </div>
          )}
        </Card>
      )}

      {/* Split-screen */}
      <div className="flex gap-4">
        {/* Document sidebar */}
        {showDocs && (
          <div className="w-1/2 flex-shrink-0">
            <Card className="sticky top-4 overflow-y-auto max-h-[calc(100vh-180px)]">
              <div className="p-4">
                <DocumentosViewer
                  documentos={preInc.documentos.map(toDocumento)}
                  viewUrlPrefix="pre-incapacidades/documentos"
                />
              </div>
            </Card>
          </div>
        )}

        {/* Main panel */}
        <div className={cn('flex-1', showDocs ? 'w-1/2' : 'w-full')}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="inconsistencias" className="gap-2">
                <AlertCircle className="h-4 w-4" />
                Inconsistencias{errorCount > 0 && ` (${errorCount})`}
              </TabsTrigger>
              <TabsTrigger value="datos" className="gap-2">
                <Edit3 className="h-4 w-4" />
                Datos
              </TabsTrigger>
            </TabsList>

            {/* Tab: Inconsistencias */}
            <TabsContent value="inconsistencias" className="space-y-4 mt-4">
              <ValidationInconsistenciasList issues={preInc.validation_inconsistencias} />

              <ResolverEntidadesPanel
                preInc={preInc}
                onEmpresaSelected={(nit, nombre) =>
                  updateMutation.mutate({ empresa_nit: nit, empresa_nombre: nombre })
                }
                onEmpleadoSelected={(tipoDoc, numero, nombres) =>
                  updateMutation.mutate({
                    empleado_tipo_documento: tipoDoc,
                    empleado_numero_documento: numero,
                    empleado_nombres: nombres,
                  })
                }
              />

              {errorCount === 0 && canPromote && (
                <Card className="p-4 bg-green-50 border-green-200 flex items-center justify-between">
                  <p className="text-green-800 text-sm font-medium">
                    Sin errores — listo para promover a incapacidad completa.
                  </p>
                  <Button
                    size="sm"
                    onClick={() => promoverMutation.mutate()}
                    disabled={promoverMutation.isPending}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {promoverMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Promover ahora'
                    )}
                  </Button>
                </Card>
              )}
            </TabsContent>

            {/* Tab: Datos */}
            <TabsContent value="datos" className="space-y-4 mt-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">Corrija los campos necesarios antes de volver a promover.</p>
                {!editMode ? (
                  <Button size="sm" variant="outline" onClick={() => setEditMode(true)}>
                    <Edit3 className="h-4 w-4 mr-1" /> Editar
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => { setEditMode(false); setEditFields({}); }}>
                      Cancelar
                    </Button>
                    <Button
                      size="sm"
                      disabled={updateMutation.isPending}
                      onClick={() => updateMutation.mutate(editFields)}
                    >
                      {updateMutation.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                      Guardar
                    </Button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Empresa */}
                <div className="col-span-2 space-y-2 border-b pb-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Empresa</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs">NIT</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empresa_nit ?? ''}
                          onChange={(e) => setEditFields((p) => ({ ...p, empresa_nit: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empresa_nit ?? '—'}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Nombre</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empresa_nombre ?? ''}
                          onChange={(e) => setEditFields((p) => ({ ...p, empresa_nombre: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empresa_nombre ?? '—'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Empleado */}
                <div className="col-span-2 space-y-2 border-b pb-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Empleado</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <Label className="text-xs">Tipo Doc.</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_tipo_documento}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_tipo_documento: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_tipo_documento}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Número Doc.</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_numero_documento}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_numero_documento: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_numero_documento}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Nombres</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_nombres}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_nombres: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_nombres} {preInc.empleado_apellidos ?? ''}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Incapacidad data (read-only summary) */}
                <div className="col-span-2 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Incapacidad</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label className="text-xs">Fecha inicio</Label><p className="text-sm mt-1">{formatDate(preInc.fecha_inicio)}</p></div>
                    <div><Label className="text-xs">Fecha fin</Label><p className="text-sm mt-1">{formatDate(preInc.fecha_fin)}</p></div>
                    <div><Label className="text-xs">Días totales</Label><p className="text-sm mt-1">{preInc.dias_totales}</p></div>
                    <div><Label className="text-xs">CIE-10</Label><p className="text-sm mt-1 font-mono">{preInc.diagnostico_cie10}</p></div>
                    <div><Label className="text-xs">Médico</Label><p className="text-sm mt-1">{preInc.nombre_medico}</p></div>
                    <div><Label className="text-xs">Reg. médico</Label><p className="text-sm mt-1">{preInc.registro_medico}</p></div>
                  </div>
                </div>

                {/* System notes */}
                {(preInc.error_procesamiento || preInc.motivo_devolucion) && (
                  <div className="col-span-2 space-y-2 border-t pt-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Notas del sistema</p>
                    {preInc.error_procesamiento && (
                      <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
                        <strong>Error de procesamiento:</strong> {preInc.error_procesamiento}
                      </div>
                    )}
                    {preInc.motivo_devolucion && (
                      <div className="bg-orange-50 border border-orange-200 rounded p-3 text-sm text-orange-700">
                        <strong>Motivo de devolución:</strong> {preInc.motivo_devolucion}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Devolution modal */}
      <DevolucionModal
        preIncapacidadId={preInc.id}
        numeroRadicacion={preInc.numero_radicacion}
        solicitanteCorreo={preInc.solicitante_correo}
        open={showDevolucion}
        onOpenChange={setShowDevolucion}
        onSuccess={() => navigate('/pre-incapacidades/bandeja')}
      />
    </div>
  );
}
