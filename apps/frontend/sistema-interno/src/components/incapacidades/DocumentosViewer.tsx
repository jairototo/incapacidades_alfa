import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Documento } from '@/types/incapacidad';
import { incapacidadService } from '@/services/incapacidadService';
import { formatDate } from '@/utils/formatters';
import {
  FileText,
  Download,
  Eye,
  FileIcon,
  Image as ImageIcon,
  AlertCircle,
} from 'lucide-react';

/**
 * Verificar si es imagen
 */
const isImage = (fileName: string | undefined) => {
  if (!fileName) return false;
  const ext = fileName.split('.').pop()?.toLowerCase();
  return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
};

/**
 * Verificar si es PDF
 */
const isPdf = (fileName: string | undefined) => {
  if (!fileName) return false;
  const ext = fileName.split('.').pop()?.toLowerCase();
  return ext === 'pdf';
};

/**
 * Verificar si se puede previsualizar
 */
const canPreview = (fileName: string | undefined) => {
  return isImage(fileName) || isPdf(fileName);
};

interface DocumentosViewerProps {
  documentos: Documento[];
}

interface DocumentoPreview {
  documentoId: string;
  url: string;
}

/**
 * Componente para visualizar y descargar documentos de una incapacidad
 * Soporta preview de PDFs e imágenes directamente en las tarjetas
 */
export function DocumentosViewer({ documentos }: DocumentosViewerProps) {
  const [loadingDocId, setLoadingDocId] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Documento | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(new Map());
  const [loadingPreviewIds, setLoadingPreviewIds] = useState<Set<string>>(new Set());

  // Cargar URLs de preview para TODAS las imágenes y PDFs
  useEffect(() => {
    const loadPreviews = async () => {
      for (const documento of documentos) {
        if ((isImage(documento.nombre_original) || isPdf(documento.nombre_original)) && 
            !previewUrls.has(documento.id)) {
          setLoadingPreviewIds(prev => new Set(prev).add(documento.id));
          
          try {
            // Usar el nuevo endpoint /view que sirve el archivo directamente
            // El API lo va a servir con los headers CORS correctos
            const baseURL = import.meta.env.VITE_API_URL || '/api/v1';
            const viewUrl = `${baseURL}/documentos/${documento.id}/view`;
            setPreviewUrls(prev => new Map(prev).set(documento.id, viewUrl));
          } catch (error) {
            console.error(`Error al cargar preview para ${documento.id}:`, error);
          } finally {
            setLoadingPreviewIds(prev => {
              const newSet = new Set(prev);
              newSet.delete(documento.id);
              return newSet;
            });
          }
        }
      }
    };

    loadPreviews();
  }, [documentos]);

  const getFileIcon = (fileName: string | undefined) => {
    if (!fileName) {
      return <FileIcon className="h-8 w-8 text-slate-500" />;
    }
    
    const ext = fileName.split('.').pop()?.toLowerCase();
    
    if (ext === 'pdf') {
      return <FileText className="h-8 w-8 text-red-500" />;
    }
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) {
      return <ImageIcon className="h-8 w-8 text-blue-500" />;
    }
    
    return <FileIcon className="h-8 w-8 text-slate-500" />;
  };

  const handleDownload = async (documento: Documento) => {
    try {
      setLoadingDocId(documento.id);
      
      // Obtener URL de descarga firmada
      const url = await incapacidadService.getDownloadUrl(documento.id);
      
      // Abrir URL en nueva pestaña
      window.open(url, '_blank');
    } catch (error) {
      console.error('Error al descargar documento:', error);
      alert('No se pudo descargar el documento');
    } finally {
      setLoadingDocId(null);
    }
  };

  const handlePreview = async (documento: Documento) => {
    try {
      setLoadingDocId(documento.id);
      
      // Obtener URL de descarga
      const url = await incapacidadService.getDownloadUrl(documento.id);
      
      setSelectedDoc(documento);
      setPreviewUrl(url);
    } catch (error) {
      console.error('Error al previsualizar documento:', error);
      alert('No se pudo previsualizar el documento');
    } finally {
      setLoadingDocId(null);
    }
  };

  if (documentos.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No hay documentos adjuntos a esta incapacidad.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Lista de Documentos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documentos.map((documento) => {
          const isImg = isImage(documento.nombre_original);
          const isPdf2 = isPdf(documento.nombre_original);
          const hasPreview = isImg || isPdf2;
          const previewUrl = previewUrls.get(documento.id);
          const isLoadingPreview = loadingPreviewIds.has(documento.id);
          
          return (
            <Card key={documento.id} className="hover:shadow-lg transition-shadow overflow-hidden flex flex-col">
              {/* Preview - Imágenes y PDFs */}
              {hasPreview && (
                <>
                  {previewUrl ? (
                    <div 
                      className="w-full h-48 bg-slate-100 flex items-center justify-center overflow-hidden border-b border-slate-200 cursor-pointer hover:bg-slate-200 transition-colors"
                      onClick={() => {
                        setSelectedDoc(documento);
                        setPreviewUrl(previewUrl);
                      }}
                    >
                      {isImg ? (
                        <img
                          src={previewUrl}
                          alt={documento.nombre_original || 'Documento'}
                          className="max-w-full max-h-full object-contain"
                        />
                      ) : isPdf2 ? (
                        <div className="text-center">
                          <FileText className="h-16 w-16 text-red-500 mx-auto mb-2" />
                          <p className="text-sm font-medium text-slate-700">PDF Preview</p>
                        </div>
                      ) : null}
                    </div>
                  ) : isLoadingPreview ? (
                    <div className="w-full h-48 bg-slate-100 flex items-center justify-center border-b border-slate-200">
                      <div className="text-center">
                        {isImg ? (
                          <ImageIcon className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                        ) : (
                          <FileText className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                        )}
                        <p className="text-xs text-slate-500">Cargando...</p>
                      </div>
                    </div>
                  ) : null}
                </>
              )}
              
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getFileIcon(documento.nombre_original)}
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-sm font-medium truncate">
                        {documento.nombre_original || 'Sin nombre'}
                      </CardTitle>
                      <Badge variant="secondary" className="mt-1">
                        {documento.tipo_documento}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 flex-1 flex flex-col justify-between">
                <div className="text-xs text-slate-500">
                  <p>Subido: {formatDate(documento.created_at)}</p>
                </div>

                <div className="flex gap-2">
                  {canPreview(documento.nombre_original) && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => {
                        const url = previewUrls.get(documento.id);
                        if (url) {
                          setSelectedDoc(documento);
                          setPreviewUrl(url);
                        } else {
                          handlePreview(documento);
                        }
                      }}
                      disabled={loadingDocId === documento.id || isLoadingPreview}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      Ver
                    </Button>
                  )}
                  
                  <Button
                    variant="default"
                    size="sm"
                    className={canPreview(documento.nombre_original) ? 'flex-1' : 'w-full'}
                    onClick={() => handleDownload(documento)}
                    disabled={loadingDocId === documento.id}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    {loadingDocId === documento.id ? 'Descargando...' : 'Descargar'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Preview Modal */}
      {selectedDoc && previewUrl && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => {
            setSelectedDoc(null);
            setPreviewUrl(null);
          }}
        >
          <div
            className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <div className="flex items-center gap-3">
                {getFileIcon(selectedDoc.nombre_original)}
                <div>
                  <h3 className="font-semibold">{selectedDoc.nombre_original || 'Sin nombre'}</h3>
                  <p className="text-sm text-slate-500">{selectedDoc.tipo_documento}</p>
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDownload(selectedDoc)}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Descargar
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedDoc(null);
                    setPreviewUrl(null);
                  }}
                >
                  Cerrar
                </Button>
              </div>
            </div>

            {/* Preview Content */}
            <div className="p-4 overflow-auto max-h-[calc(90vh-80px)]">
              {selectedDoc.nombre_original?.toLowerCase().endsWith('.pdf') ? (
                <iframe
                  src={previewUrl}
                  className="w-full h-[800px] border-0"
                  title="Vista previa PDF"
                />
              ) : (
                <img
                  src={previewUrl}
                  alt={selectedDoc.nombre_original || 'Documento'}
                  className="max-w-full h-auto mx-auto"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
