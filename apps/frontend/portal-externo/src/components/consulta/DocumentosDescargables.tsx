/**
 * DocumentosDescargables - Componente para mostrar y descargar documentos públicos.
 * 
 * Muestra una lista de documentos asociados a la incapacidad con botones de descarga,
 * iconos por tipo de documento, indicadores de tamaño y fechas de carga.
 * 
 * @example
 * ```tsx
 * <DocumentosDescargables 
 *   documentos={incapacidad.documentos_publicos}
 *   numeroIncapacidad={incapacidad.numero}
 * />
 * ```
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { DocumentoPublico, TipoDocumentoArchivo } from '@/types/consulta';
import { useDescargarDocumento } from '@/hooks/useConsultaIncapacidad';
import { formatearTamanioArchivo, formatearFechaCorta } from '@/utils/formatters';
import {
  FileText,
  Download,
  AlertCircle,
  Loader2,
  File,
  Image,
  FileCheck,
  CreditCard,
  Folder,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ========== TIPOS ==========

interface DocumentosDescargablesProps {
  /** Lista de documentos públicos */
  documentos: DocumentoPublico[];
  
  /** Número de incapacidad (requerido para la descarga) */
  numeroIncapacidad: string;
  
  /** Clase CSS adicional para el contenedor */
  className?: string;
}

// ========== MAPAS DE CONFIGURACIÓN ==========

/**
 * Mapa de iconos por tipo de documento.
 */
const TIPO_DOCUMENTO_ICONS: Record<TipoDocumentoArchivo, React.ElementType> = {
  INCAPACIDAD_MEDICA: FileCheck,
  CEDULA: CreditCard,
  HISTORIA_CLINICA: FileText,
  SOPORTE_PAGO: File,
  OTROS: Folder,
};

/**
 * Mapa de etiquetas amigables por tipo de documento.
 */
const TIPO_DOCUMENTO_LABELS: Record<TipoDocumentoArchivo, string> = {
  INCAPACIDAD_MEDICA: 'Incapacidad Médica',
  CEDULA: 'Cédula de Identidad',
  HISTORIA_CLINICA: 'Historia Clínica',
  SOPORTE_PAGO: 'Soporte de Pago',
  OTROS: 'Otros Documentos',
};

/**
 * Mapa de colores por tipo de documento.
 */
const TIPO_DOCUMENTO_COLORS: Record<TipoDocumentoArchivo, string> = {
  INCAPACIDAD_MEDICA: 'text-blue-600 bg-blue-50',
  CEDULA: 'text-purple-600 bg-purple-50',
  HISTORIA_CLINICA: 'text-green-600 bg-green-50',
  SOPORTE_PAGO: 'text-orange-600 bg-orange-50',
  OTROS: 'text-gray-600 bg-gray-50',
};

// ========== SUB-COMPONENTES ==========

/**
 * Componente para un item individual de documento.
 */
interface DocumentoItemProps {
  documento: DocumentoPublico;
  numeroIncapacidad: string;
}

function DocumentoItem({ documento, numeroIncapacidad }: DocumentoItemProps) {
  const { mutate: descargar, isPending, error } = useDescargarDocumento();

  const Icon = TIPO_DOCUMENTO_ICONS[documento.tipo_documento];
  const label = TIPO_DOCUMENTO_LABELS[documento.tipo_documento];
  const colorClass = TIPO_DOCUMENTO_COLORS[documento.tipo_documento];

  const handleDescargar = () => {
    descargar(
      { numero: numeroIncapacidad, documentoId: documento.id },
      {
        onSuccess: (data) => {
          // Abrir URL presignada en nueva pestaña
          window.open(data.url, '_blank');
        },
      }
    );
  };

  return (
    <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
      {/* Icono y detalles */}
      <div className="flex items-start gap-3 flex-1 min-w-0">
        {/* Icono del tipo de documento */}
        <div className={cn('p-2 rounded-lg', colorClass)}>
          <Icon className="h-5 w-5" />
        </div>

        {/* Información del documento */}
        <div className="flex-1 min-w-0 space-y-1">
          {/* Nombre del archivo */}
          <p className="text-sm font-semibold text-gray-900 truncate">
            {documento.nombre_archivo}
          </p>

          {/* Tipo de documento */}
          <p className="text-xs text-gray-500">
            {label}
          </p>

          {/* Metadata (tamaño y fecha) */}
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>{formatearTamanioArchivo(documento.tamanio_kb)}</span>
            <span>•</span>
            <span>Cargado el {formatearFechaCorta(documento.fecha_upload)}</span>
          </div>

          {/* Error de descarga */}
          {error && (
            <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
              <AlertCircle className="h-3 w-3" />
              <span>Error al generar descarga</span>
            </div>
          )}
        </div>
      </div>

      {/* Botón de descarga */}
      <Button
        onClick={handleDescargar}
        disabled={isPending}
        variant="outline"
        size="sm"
        className="ml-4 shrink-0"
      >
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Generando...
          </>
        ) : (
          <>
            <Download className="h-4 w-4 mr-2" />
            Descargar
          </>
        )}
      </Button>
    </div>
  );
}

// ========== COMPONENTE PRINCIPAL ==========

/**
 * DocumentosDescargables - Muestra lista de documentos con opción de descarga.
 */
export function DocumentosDescargables({
  documentos,
  numeroIncapacidad,
  className,
}: DocumentosDescargablesProps) {
  // Si no hay documentos, mostrar mensaje
  if (documentos.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Documentos Adjuntos
          </CardTitle>
          <CardDescription>
            Archivos disponibles para consulta y descarga
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <File className="h-12 w-12 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No hay documentos adjuntos disponibles</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Documentos Adjuntos
        </CardTitle>
        <CardDescription>
          {documentos.length} {documentos.length === 1 ? 'documento disponible' : 'documentos disponibles'} para descarga
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {documentos.map((documento) => (
            <DocumentoItem
              key={documento.id}
              documento={documento}
              numeroIncapacidad={numeroIncapacidad}
            />
          ))}
        </div>

        {/* Footer informativo */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            ℹ️ Los documentos se descargan en una nueva pestaña. Las URLs de descarga expiran en 15 minutos.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
