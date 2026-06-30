import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, History, CheckCircle, XCircle, AlertCircle, Image, ChevronLeft, ChevronRight, AlertTriangle, Send } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { GestionActions } from '@/components/incapacidades/GestionActions';
import { AuditoriaFormulario } from '@/components/incapacidades/AuditoriaFormulario';
import { IncapacidadContextStrip } from '@/components/incapacidades/IncapacidadContextStrip';
import { ValidacionesPanel } from '@/components/incapacidades/ValidacionesPanel';
import { StateDescriptionPanel } from '@/components/incapacidades/StateDescriptionPanel';
import { SiniestroPanel } from '@/components/incapacidades/SiniestroPanel';

import { incapacidadService } from '@/services/incapacidadService';
import { preIncapacidadService } from '@/services/preIncapacidadService';
import { useHasRole } from '@/store/authStore';
import { cn } from '@/lib/utils';

/**
 * Página de Gestión de Incapacidad (MEJORADA - Auditoría Avanzada)
 * 
 * Permite visualizar y gestionar una incapacidad específica con:
 * - Sidebar de documentos (collapsible, 50% ancho)
 * - Tabs: "Auditoría" (con aprobación parcial), "Detalle Completo", "Historial"
 * - Formulario de auditoría con soporte para modificación de fechas, CIE-10, diagnóstico
 * 
 * Soporta aprobación parcial cuando días aprobados < días solicitados
 */
export function GestionarPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState('auditoria');
  const [showDocumentsSidebar, setShowDocumentsSidebar] = useState(true);
  const [showReenviarDialog, setShowReenviarDialog] = useState(false);

  const isAdminOrAuditor = useHasRole(['ADMIN', 'AUDITOR']);

  // Query: Obtener incapacidad
  const {
    data: incapacidad,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['incapacidad', id],
    queryFn: () => incapacidadService.getById(id!),
    enabled: !!id,
  });

  // Query: Obtener historial
  const { data: historial } = useQuery({
    queryKey: ['incapacidad', id, 'historial'],
    queryFn: () => incapacidadService.getHistorial(id!),
    enabled: !!id,
  });

  // Query: Obtener documentos
  const { data: documentos } = useQuery({
    queryKey: ['incapacidad', id, 'documentos'],
    queryFn: () => incapacidadService.getDocumentos(id!),
    enabled: !!id,
  });

  // Query: Obtener datos aprobados (si existen)
  const { data: datosAprobados } = useQuery({
    queryKey: ['incapacidad', id, 'datos-aprobados'],
    queryFn: () => incapacidadService.getDatosAprobados(id!),
    enabled: !!id,
  });

  const { data: validaciones, isLoading: validacionesLoading } = useQuery({
    queryKey: ['incapacidad', id, 'validaciones'],
    queryFn: () => incapacidadService.getValidaciones(id!),
    enabled: !!id,
  });

  const { data: auditoriaResultados, isLoading: auditoriaResultadosLoading } = useQuery({
    queryKey: ['incapacidad', id, 'auditoria-resultados'],
    queryFn: () => incapacidadService.getAuditoriaResultados(id!),
    enabled: !!id && incapacidad?.estado === 'EN_AUDITORIA',
  });

  const hasFraudAlert = validaciones?.has_fraud_alert ?? false;

  // Query: Pre-incapacidad para fallback de empleado (solo cuando empleado no está en BD)
  const needsEmpleadoFallback = !!incapacidad && !incapacidad.empleado && !!incapacidad.pre_incapacidad_id;
  const { data: preIncapacidadData } = useQuery({
    queryKey: ['pre-incapacidad', incapacidad?.pre_incapacidad_id],
    queryFn: () => preIncapacidadService.getById(incapacidad!.pre_incapacidad_id),
    enabled: needsEmpleadoFallback,
  });
  const empleadoFallback = needsEmpleadoFallback && preIncapacidadData
    ? { nombres: preIncapacidadData.empleado_nombres, numero_documento: preIncapacidadData.empleado_numero_documento }
    : null;

  // Mutation: Cambiar estado (deprecado - usar AuditoriaFormulario)
  const cambiarEstadoMutation = useMutation({
    mutationFn: ({ nuevoEstado, observacion }: { nuevoEstado: string; observacion?: string }) =>
      incapacidadService.cambiarEstado(id!, nuevoEstado, observacion),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id, 'historial'] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
      
      toast({
        title: '✅ Estado actualizado',
        description: `La incapacidad ahora está en estado: ${data.estado}`,
      });
      
      setTimeout(() => {
        navigate('/incapacidades/pendientes');
      }, 1500);
    },
    onError: (error: any) => {
      toast({
        title: '❌ Error',
        description: error.response?.data?.detail || 'No se pudo actualizar el estado',
        variant: 'destructive',
      });
    },
  });

  // Mutation: Reenviar notificación de glosa
  const reenviarNotificacionMutation = useMutation({
    mutationFn: () => incapacidadService.reenviarNotificacionGlosada(id!),
    onSuccess: () => {
      setShowReenviarDialog(false);
      toast({
        title: 'Notificación reenviada',
        description: 'La notificación de glosa fue reenviada al solicitante.',
      });
    },
    onError: (error: any) => {
      setShowReenviarDialog(false);
      toast({
        title: 'Error al reenviar',
        description: error.response?.data?.detail || 'No se pudo reenviar la notificación',
        variant: 'destructive',
      });
    },
  });

  // Handler éxito de auditoría
  const handleAuditoriaSuccess = () => {
    // Redirigir después de brief delay
    setTimeout(() => {
      navigate('/incapacidades/pendientes');
    }, 2000);
  };

  // Loading state
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

  // Error state
  if (error || !incapacidad) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md">
          <div className="text-center space-y-4">
            <XCircle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-lg font-bold text-slate-900">Incapacidad no encontrada</h2>
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

  // Determinar si se pueden aplicar acciones de gestión
  const canManage = ['RADICADA', 'EN_AUDITORIA', 'PENDIENTE'].includes(incapacidad.estado);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/incapacidades/pendientes')}
            className="hover:bg-slate-100"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Volver
          </Button>
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-3">
              Gestión de Incapacidad
              <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>
                {incapacidad.estado}
              </Badge>
            </h1>
            <p className="text-slate-500 mt-1 font-mono text-lg">{incapacidad.numero}</p>
          </div>
        </div>

        {/* Indicador de tipo + Toggle documentos */}
        <div className="flex items-center gap-3">
          <Badge variant={incapacidad.tipo === 'ARL' ? 'default' : 'secondary'} className="text-base px-4 py-2">
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

      {/* Panel de descripción del estado actual */}
      <StateDescriptionPanel
        estado={incapacidad.estado}
        auditoriaResultados={
          incapacidad.estado === 'RADICADA' ? (validaciones?.issues ?? undefined) : undefined
        }
        auditoriaResultadosList={
          incapacidad.estado === 'EN_AUDITORIA' ? (auditoriaResultados ?? undefined) : undefined
        }
        auditoriaResultadosListLoading={auditoriaResultadosLoading}
      />

      {/* Layout principal: Split-screen (Documentos | Tabs) */}
      <div className="flex gap-4">
        {/* Sidebar de documentos (collapsible) */}
        {showDocumentsSidebar && (
          <div className="w-1/2 flex-shrink-0">
            <Card className="h-full sticky top-4">
              <div className="p-4 border-b flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Image className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold">Documentos Adjuntos</h3>
                  <Badge variant="secondary">{documentos?.length || 0}</Badge>
                </div>
              </div>
              <div className="p-4 overflow-y-auto max-h-[calc(100vh-200px)]">
                <DocumentosViewer documentos={documentos || []} />
              </div>
            </Card>
          </div>
        )}

        {/* Panel principal de tabs */}
        <div className={cn('flex-1', showDocumentsSidebar ? 'w-1/2' : 'w-full')}>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="auditoria" className="space-x-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Auditoría</span>
              </TabsTrigger>
              <TabsTrigger value="detalle" className="space-x-2">
                <FileText className="h-4 w-4" />
                <span>Validaciones</span>
              </TabsTrigger>
              <TabsTrigger value="historial" className="space-x-2">
                <History className="h-4 w-4" />
                <span>Historial ({historial?.length || 0})</span>
              </TabsTrigger>
            </TabsList>

            {/* Tab: Auditoría (NUEVO) */}
            <TabsContent value="auditoria" className="space-y-4">
              {incapacidad && (
                <IncapacidadContextStrip
                  incapacidad={incapacidad}
                  hasFraudAlert={hasFraudAlert}
                  empleadoFallback={empleadoFallback}
                />
              )}
              {canManage ? (
                <>
                  {/* Panel de siniestro (solo ARL) */}
                  {incapacidad.tipo === 'ARL' && (
                    <SiniestroPanel
                      incapacidad={incapacidad}
                      onVinculated={() => {
                        queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
                      }}
                    />
                  )}

                  {/* Datos aprobados previos (si existen) */}
                  {datosAprobados && (
                    <Card className="p-4 bg-yellow-50 border-yellow-400">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        <div className="flex-1">
                          <h3 className="font-semibold text-yellow-900">
                            Aprobación Parcial Existente
                          </h3>
                          <p className="text-sm text-yellow-700 mt-1">
                            Esta incapacidad ya tiene datos aprobados modificados del {' '}
                            {new Date(datosAprobados.fecha_auditoria).toLocaleDateString('es-CO')}
                          </p>
                          <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
                            <div>
                              <span className="text-yellow-800 font-medium">Fechas aprobadas:</span>{' '}
                              {new Date(datosAprobados.fecha_inicio_aprobada).toLocaleDateString('es-CO')} - {' '}
                              {new Date(datosAprobados.fecha_fin_aprobada).toLocaleDateString('es-CO')}
                            </div>
                            <div>
                              <span className="text-yellow-800 font-medium">Días aprobados:</span>{' '}
                              {datosAprobados.dias_aprobados} días
                            </div>
                            <div>
                              <span className="text-yellow-800 font-medium">CIE-10:</span>{' '}
                              {datosAprobados.cie10_aprobado}
                            </div>
                            <div className="col-span-2">
                              <span className="text-yellow-800 font-medium">Diagnóstico:</span>{' '}
                              {datosAprobados.diagnostico_aprobado}
                            </div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  )}

                  {/* Formulario de auditoría mejorado */}
                  <AuditoriaFormulario
                    incapacidad={incapacidad}
                    onSuccess={handleAuditoriaSuccess}
                  />
                </>
              ) : (
                <>
                  <Card className="p-4 bg-slate-50">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="h-5 w-5 text-slate-500 mt-0.5" />
                      <div className="flex-1">
                        <p className="font-medium text-slate-700">
                          Esta incapacidad no se puede auditar en su estado actual
                        </p>
                        <p className="text-sm text-slate-500 mt-1">
                          Las acciones de auditoría solo están disponibles para incapacidades en estado{' '}
                          <strong>RADICADA</strong>, <strong>EN_AUDITORIA</strong> o <strong>PENDIENTE</strong>.
                        </p>
                        <p className="text-sm text-slate-600 mt-3">
                          Estado actual: <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>{incapacidad.estado}</Badge>
                        </p>
                      </div>
                    </div>
                  </Card>

                  {/* Botón reenviar notificación de glosa — solo visible en estado GLOSADA para ADMIN/AUDITOR */}
                  {incapacidad.estado === 'GLOSADA' && isAdminOrAuditor && (
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        onClick={() => setShowReenviarDialog(true)}
                        disabled={reenviarNotificacionMutation.isPending}
                        className="flex items-center gap-2"
                      >
                        <Send className="h-4 w-4" />
                        {reenviarNotificacionMutation.isPending
                          ? 'Reenviando...'
                          : 'Reenviar notificación de glosa'}
                      </Button>
                    </div>
                  )}

                  {/* Diálogo de confirmación para reenviar notificación */}
                  <Dialog open={showReenviarDialog} onOpenChange={setShowReenviarDialog}>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Reenviar notificación de glosa</DialogTitle>
                        <DialogDescription>
                          Se enviará nuevamente la notificación de glosa al solicitante. ¿Desea continuar?
                        </DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <Button
                          variant="outline"
                          onClick={() => setShowReenviarDialog(false)}
                          disabled={reenviarNotificacionMutation.isPending}
                        >
                          Cancelar
                        </Button>
                        <Button
                          onClick={() => reenviarNotificacionMutation.mutate()}
                          disabled={reenviarNotificacionMutation.isPending}
                        >
                          {reenviarNotificacionMutation.isPending ? 'Reenviando...' : 'Confirmar'}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </>
              )}
            </TabsContent>

            {/* Tab: Validaciones */}
            <TabsContent value="detalle" className="space-y-4">
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

// Helper function para badge de estado
function getEstadoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'RADICADA':
      return 'secondary';
    case 'EN_AUDITORIA':
      return 'default';
    case 'PENDIENTE':
      return 'outline';
    case 'CREACION_SINIESTRO':
      return 'secondary';
    case 'LIQUIDACION':
      return 'default';
    case 'LIQUIDACION_PARCIAL':
      return 'default';
    case 'GLOSADA':
      return 'destructive';
    case 'PAGADA':
      return 'default';
    case 'PAGADA_PARCIAL':
      return 'default';
    default:
      return 'secondary';
  }
}
