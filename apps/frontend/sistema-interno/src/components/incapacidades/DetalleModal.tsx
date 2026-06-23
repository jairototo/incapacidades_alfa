import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { incapacidadService } from '@/services/incapacidadService';
import { formatDate, formatCurrency, formatFileSize } from '@/utils/formatters';
import type { Incapacidad, HistorialEstado, Documento } from '@/types/incapacidad';
import { EstadoIncapacidad } from '@/types/enums';

interface DetalleModalProps {
  open: boolean;
  onClose: () => void;
  incapacidadId: string | null;
}

/**
 * Modal de detalle de incapacidad con 3 tabs:
 * - Información: Datos completos de la incapacidad
 * - Timeline: Historial de estados
 * - Documentos: Lista de documentos con descarga
 */
export function DetalleModal({ open, onClose, incapacidadId }: DetalleModalProps) {
  // Fetch incapacidad
  const {
    data: incapacidad,
    isLoading: isLoadingIncap,
    error: errorIncap,
  } = useQuery<Incapacidad>({
    queryKey: ['incapacidad', incapacidadId],
    queryFn: () => incapacidadService.getById(incapacidadId!),
    enabled: !!incapacidadId && open,
  });

  // Fetch historial
  const {
    data: historial = [],
    isLoading: isLoadingHistorial,
  } = useQuery<HistorialEstado[]>({
    queryKey: ['incapacidad-historial', incapacidadId],
    queryFn: () => incapacidadService.getHistorial(incapacidadId!),
    enabled: !!incapacidadId && open,
  });

  // Fetch documentos
  const {
    data: documentos = [],
    isLoading: isLoadingDocs,
  } = useQuery<Documento[]>({
    queryKey: ['incapacidad-documentos', incapacidadId],
    queryFn: () => incapacidadService.getDocumentos(incapacidadId!),
    enabled: !!incapacidadId && open,
  });

  // Descargar documento
  const handleDownloadDocument = async (documentoId: string, nombreArchivo: string) => {
    try {
      const blob = await incapacidadService.descargarDocumento(documentoId);
      
      // Crear enlace de descarga temporal
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = nombreArchivo;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error descargando documento:', error);
      alert('Error al descargar el documento');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>
            {isLoadingIncap ? 'Cargando...' : `Incapacidad #${incapacidad?.numero || ''}`}
          </DialogTitle>
        </DialogHeader>

        {isLoadingIncap && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {errorIncap && (
          <div className="text-center py-12 text-destructive">
            Error al cargar la incapacidad
          </div>
        )}

        {incapacidad && (
          <Tabs defaultValue="informacion" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="informacion">Información</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="documentos">Documentos</TabsTrigger>
            </TabsList>

            {/* TAB 1: INFORMACIÓN */}
            <TabsContent value="informacion">
              <ScrollArea className="h-[500px] pr-4">
                <div className="space-y-6">
                  {/* Información General */}
                  <section>
                    <h3 className="text-lg font-semibold mb-3 border-b pb-2">
                      Información General
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Número</p>
                        <p className="font-medium">{incapacidad.numero}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Estado</p>
                        <Badge variant="default">{incapacidad.estado}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Tipo</p>
                        <Badge variant="secondary">{incapacidad.tipo}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Prioridad</p>
                        <Badge variant="outline">{incapacidad.prioridad}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Fecha Inicio</p>
                        <p className="font-medium">{formatDate(incapacidad.fecha_inicio)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Fecha Fin</p>
                        <p className="font-medium">{formatDate(incapacidad.fecha_fin)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Días Totales</p>
                        <p className="font-medium">{incapacidad.dias_totales} días</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Valor Total</p>
                        <p className="font-medium">{formatCurrency(incapacidad.valor_total)}</p>
                      </div>
                    </div>
                  </section>

                  {/* Diagnóstico */}
                  <section>
                    <h3 className="text-lg font-semibold mb-3 border-b pb-2">Diagnóstico</h3>
                    <div className="space-y-2">
                      <div>
                        <p className="text-sm text-muted-foreground">Código CIE-10</p>
                        <p className="font-medium">{incapacidad.diagnostico_cie10}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Descripción</p>
                        <p className="font-medium">{incapacidad.diagnostico_descripcion}</p>
                      </div>
                    </div>
                  </section>

                  {/* Empleado (solo si tipo ARL) */}
                  {incapacidad.empleado && (
                    <section>
                      <h3 className="text-lg font-semibold mb-3 border-b pb-2">Empleado</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Documento</p>
                          <p className="font-medium">
                            {incapacidad.empleado.tipo_documento} {incapacidad.empleado.numero_documento}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Nombres</p>
                          <p className="font-medium">
                            {incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}
                          </p>
                        </div>
                        {incapacidad.empleado.email && (
                          <div>
                            <p className="text-sm text-muted-foreground">Email</p>
                            <p className="font-medium">{incapacidad.empleado.email}</p>
                          </div>
                        )}
                        {incapacidad.empleado.telefono && (
                          <div>
                            <p className="text-sm text-muted-foreground">Teléfono</p>
                            <p className="font-medium">{incapacidad.empleado.telefono}</p>
                          </div>
                        )}
                        {incapacidad.empleado.cargo && (
                          <div>
                            <p className="text-sm text-muted-foreground">Cargo</p>
                            <p className="font-medium">{incapacidad.empleado.cargo}</p>
                          </div>
                        )}
                      </div>
                    </section>
                  )}

                  {/* Afiliado (solo si tipo SALUD) */}
                  {incapacidad.afiliado && (
                    <section>
                      <h3 className="text-lg font-semibold mb-3 border-b pb-2">Afiliado</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Documento</p>
                          <p className="font-medium">
                            {incapacidad.afiliado.tipo_documento} {incapacidad.afiliado.numero_documento}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Nombres</p>
                          <p className="font-medium">
                            {incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}
                          </p>
                        </div>
                        {incapacidad.afiliado.email && (
                          <div>
                            <p className="text-sm text-muted-foreground">Email</p>
                            <p className="font-medium">{incapacidad.afiliado.email}</p>
                          </div>
                        )}
                        {incapacidad.afiliado.telefono && (
                          <div>
                            <p className="text-sm text-muted-foreground">Teléfono</p>
                            <p className="font-medium">{incapacidad.afiliado.telefono}</p>
                          </div>
                        )}
                        {incapacidad.afiliado.fecha_nacimiento && (
                          <div>
                            <p className="text-sm text-muted-foreground">Fecha Nacimiento</p>
                            <p className="font-medium">
                              {formatDate(incapacidad.afiliado.fecha_nacimiento)}
                            </p>
                          </div>
                        )}
                      </div>
                    </section>
                  )}

                  {/* Empresa */}
                  {incapacidad.empresa && (
                    <section>
                      <h3 className="text-lg font-semibold mb-3 border-b pb-2">Empresa</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">NIT</p>
                          <p className="font-medium">{incapacidad.empresa.nit}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Razón Social</p>
                          <p className="font-medium">{incapacidad.empresa.razon_social}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Email</p>
                          <p className="font-medium">{incapacidad.empresa.email_contacto}</p>
                        </div>
                        {incapacidad.empresa.telefono && (
                          <div>
                            <p className="text-sm text-muted-foreground">Teléfono</p>
                            <p className="font-medium">{incapacidad.empresa.telefono}</p>
                          </div>
                        )}
                        {incapacidad.empresa.direccion && (
                          <div>
                            <p className="text-sm text-muted-foreground">Dirección</p>
                            <p className="font-medium">{incapacidad.empresa.direccion}</p>
                          </div>
                        )}
                        {incapacidad.empresa.ciudad && (
                          <div>
                            <p className="text-sm text-muted-foreground">Ciudad</p>
                            <p className="font-medium">{incapacidad.empresa.ciudad}</p>
                          </div>
                        )}
                      </div>
                    </section>
                  )}

                  {/* Orden de Pago */}
                  {incapacidad.orden_pago && (
                    <section>
                      <h3 className="text-lg font-semibold mb-3 border-b pb-2">Orden de Pago</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Número</p>
                          <p className="font-medium">{incapacidad.orden_pago.numero}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Estado</p>
                          <Badge variant="default">{incapacidad.orden_pago.estado}</Badge>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Fecha Generación</p>
                          <p className="font-medium">
                            {formatDate(incapacidad.orden_pago.fecha_generacion)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Valor</p>
                          <p className="font-medium">
                            {formatCurrency(incapacidad.orden_pago.valor_total)}
                          </p>
                        </div>
                        {incapacidad.orden_pago.fecha_aprobacion && (
                          <div>
                            <p className="text-sm text-muted-foreground">Fecha Aprobación</p>
                            <p className="font-medium">
                              {formatDate(incapacidad.orden_pago.fecha_aprobacion)}
                            </p>
                          </div>
                        )}
                        {incapacidad.orden_pago.fecha_pago && (
                          <div>
                            <p className="text-sm text-muted-foreground">Fecha Pago</p>
                            <p className="font-medium">
                              {formatDate(incapacidad.orden_pago.fecha_pago)}
                            </p>
                          </div>
                        )}
                      </div>
                    </section>
                  )}

                  {/* Observaciones */}
                  {incapacidad.observaciones && (
                    <section>
                      <h3 className="text-lg font-semibold mb-3 border-b pb-2">Observaciones</h3>
                      <p className="text-sm">{incapacidad.observaciones}</p>
                    </section>
                  )}

                  {/* Fechas de auditoría */}
                  <section>
                    <h3 className="text-lg font-semibold mb-3 border-b pb-2">Auditoría</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Creada</p>
                        <p className="font-medium">{formatDate(incapacidad.created_at)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Última actualización</p>
                        <p className="font-medium">{formatDate(incapacidad.updated_at)}</p>
                      </div>
                    </div>
                  </section>
                </div>
              </ScrollArea>
            </TabsContent>

            {/* TAB 2: TIMELINE */}
            <TabsContent value="timeline">
              <ScrollArea className="h-[500px] pr-4">
                {isLoadingHistorial && (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                )}

                {!isLoadingHistorial && historial.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No hay historial de estados
                  </div>
                )}

                {!isLoadingHistorial && historial.length > 0 && (
                  <div className="space-y-4">
                    {historial.map((item, index) => (
                      <div key={item.id} className="relative pl-8 pb-6">
                        {/* Línea conectora */}
                        {index < historial.length - 1 && (
                          <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-border" />
                        )}

                        {/* Icono de estado */}
                        <div className="absolute left-0 top-0 flex h-6 w-6 items-center justify-center rounded-full border-2 bg-background">
                          {getEstadoIcon(item.estado_nuevo as EstadoIncapacidad)}
                        </div>

                        {/* Contenido */}
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div>
                              <Badge variant="default" className="mb-1">
                                {item.estado_nuevo}
                              </Badge>
                              {item.estado_anterior && (
                                <p className="text-xs text-muted-foreground">
                                  Desde: {item.estado_anterior}
                                </p>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {formatDate(item.created_at)}
                            </p>
                          </div>

                          <div>
                            <p className="text-sm font-medium">{item.cambiado_por_nombre}</p>
                            {item.observacion && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {item.observacion}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            {/* TAB 3: DOCUMENTOS */}
            <TabsContent value="documentos">
              <ScrollArea className="h-[500px] pr-4">
                {isLoadingDocs && (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                )}

                {!isLoadingDocs && documentos.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No hay documentos adjuntos
                  </div>
                )}

                {!isLoadingDocs && documentos.length > 0 && (
                  <div className="space-y-3">
                    {documentos.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-medium">{doc.nombre_original}</p>
                          <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                            <span>{doc.tipo_documento}</span>
                            <span>•</span>
                            <span>{formatFileSize(doc.tamano_bytes)}</span>
                            <span>•</span>
                            <span>{formatDate(doc.created_at)}</span>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadDocument(doc.id, doc.nombre_original)}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Descargar
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * Obtiene el icono apropiado según el estado
 */
function getEstadoIcon(estado: EstadoIncapacidad) {
  switch (estado) {
    case EstadoIncapacidad.LIQUIDACION:
    case EstadoIncapacidad.PAGADA:
    case EstadoIncapacidad.PAGADA_PARCIAL:
      return <CheckCircle2 className="h-3 w-3 text-green-600" />;
    case EstadoIncapacidad.GLOSADA:
      return <XCircle className="h-3 w-3 text-red-600" />;
    case EstadoIncapacidad.PENDIENTE:
      return <AlertCircle className="h-3 w-3 text-yellow-600" />;
    case EstadoIncapacidad.RADICADA:
    case EstadoIncapacidad.EN_AUDITORIA:
    case EstadoIncapacidad.CREACION_SINIESTRO:
    case EstadoIncapacidad.LIQUIDACION_PARCIAL:
    default:
      return <Clock className="h-3 w-3 text-blue-600" />;
  }
}
