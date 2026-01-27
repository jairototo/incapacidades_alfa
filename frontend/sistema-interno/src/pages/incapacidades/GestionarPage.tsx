import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, History, CheckCircle, XCircle, AlertCircle, Image } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';

import { IncapacidadDetalle } from '@/components/incapacidades/IncapacidadDetalle';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { GestionActions } from '@/components/incapacidades/GestionActions';

import { incapacidadService } from '@/services/incapacidadService';

/**
 * Página de Gestión de Incapacidad
 * 
 * Permite visualizar y gestionar una incapacidad específica a través de:
 * - Tab "Datos Generales": Información completa de la incapacidad
 * - Tab "Documentos": Visualización y descarga de documentos adjuntos
 * - Tab "Historial": Timeline de cambios de estado
 * 
 * Incluye acciones de auditoría (Aprobar, Observar, Rechazar) para
 * incapacidades en estados: RADICADA, EN_AUDITORIA, OBSERVADA
 */
export function GestionarPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('detalle');

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

  // Mutation: Cambiar estado
  const cambiarEstadoMutation = useMutation({
    mutationFn: ({ nuevoEstado, observacion }: { nuevoEstado: string; observacion?: string }) =>
      incapacidadService.cambiarEstado(id!, nuevoEstado, observacion),
    onSuccess: (data) => {
      // Invalidar queries relacionadas
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id, 'historial'] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
      
      toast({
        title: '✅ Estado actualizado',
        description: `La incapacidad ahora está en estado: ${data.estado}`,
      });
      
      // Redirigir a pendientes después de un breve delay
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
            <h2 className="text-2xl font-bold text-slate-900">Incapacidad no encontrada</h2>
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
  const canManage = ['RADICADA', 'EN_AUDITORIA', 'OBSERVADA'].includes(incapacidad.estado);

  return (
    <div className="space-y-6">
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
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
              Gestión de Incapacidad
              <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>
                {incapacidad.estado}
              </Badge>
            </h1>
            <p className="text-slate-500 mt-1 font-mono text-lg">{incapacidad.numero}</p>
          </div>
        </div>

        {/* Indicador de tipo */}
        <div>
          <Badge variant={incapacidad.tipo === 'ARL' ? 'default' : 'secondary'} className="text-base px-4 py-2">
            {incapacidad.tipo}
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-auto">
          <TabsTrigger value="detalle" className="space-x-2">
            <FileText className="h-4 w-4" />
            <span>Datos Generales</span>
          </TabsTrigger>
          <TabsTrigger value="documentos" className="space-x-2">
            <Image className="h-4 w-4" />
            <span>Documentos ({documentos?.length || 0})</span>
          </TabsTrigger>
          <TabsTrigger value="historial" className="space-x-2">
            <History className="h-4 w-4" />
            <span>Historial ({historial?.length || 0})</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab: Datos Generales */}
        <TabsContent value="detalle" className="space-y-6">
          <IncapacidadDetalle incapacidad={incapacidad} />
          
          {/* Acciones de Gestión */}
          {canManage && (
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-6">
                <CheckCircle className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-semibold">Acciones de Auditoría</h3>
              </div>
              <GestionActions
                incapacidad={incapacidad}
                onAction={cambiarEstadoMutation.mutate}
                isLoading={cambiarEstadoMutation.isPending}
              />
            </Card>
          )}

          {/* Mensaje si no se puede gestionar */}
          {!canManage && (
            <Card className="p-6 bg-slate-50">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-slate-500 mt-0.5" />
                <div>
                  <p className="font-medium text-slate-700">
                    Esta incapacidad no se puede gestionar en su estado actual
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    Las acciones de auditoría solo están disponibles para incapacidades en estado 
                    RADICADA, EN_AUDITORIA u OBSERVADA.
                  </p>
                </div>
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Tab: Documentos */}
        <TabsContent value="documentos">
          <DocumentosViewer documentos={documentos || []} />
        </TabsContent>

        {/* Tab: Historial */}
        <TabsContent value="historial">
          <HistorialTimeline historial={historial || []} />
        </TabsContent>
      </Tabs>
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
    case 'OBSERVADA':
      return 'outline';
    case 'APROBADA':
      return 'default';
    case 'RECHAZADA':
      return 'destructive';
    case 'EN_PAGO':
    case 'PAGADA':
      return 'default';
    default:
      return 'secondary';
  }
}
