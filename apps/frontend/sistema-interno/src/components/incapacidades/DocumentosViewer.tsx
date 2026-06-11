import { useState, useEffect, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Documento } from '@/types/incapacidad';
import { incapacidadService } from '@/services/incapacidadService';
import { formatDate } from '@/utils/formatters';
import api from '@/lib/api';
import {
  FileText,
  Download,
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

interface DocumentosViewerProps {
  documentos: Documento[];
  /** URL path prefix for the view endpoint. Defaults to 'documentos'. Override to 'pre-incapacidades/documentos' for PreDocumento records. */
  viewUrlPrefix?: string;
  /** Custom download function. Defaults to incapacidadService.getDownloadUrl. */
  downloadFn?: (id: string) => Promise<string>;
}

/**
 * Componente para visualizar documentos con tabs horizontales e inline viewer
 * Auto-carga el primer documento al montar el componente
 */
export function DocumentosViewer({ documentos, viewUrlPrefix = 'documentos', downloadFn }: DocumentosViewerProps) {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(new Map());
  const [loadingPreviewIds, setLoadingPreviewIds] = useState<Set<string>>(new Set());
  const [downloadingDocId, setDownloadingDocId] = useState<string | null>(null);

  // Track object URLs so we can revoke them on unmount
  const objectUrlsRef = useRef<Map<string, string>>(new Map());

  // Auto-select first document on mount
  useEffect(() => {
    if (documentos.length > 0 && !selectedDocId) {
      setSelectedDocId(documentos[0].id);
    }
  }, [documentos, selectedDocId]);

  // Revoke all object URLs when component unmounts to free memory
  useEffect(() => {
    const objectUrls = objectUrlsRef.current;
    return () => {
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  // Load preview URLs for all documents via authenticated fetch
  useEffect(() => {
    const loadPreviews = async () => {
      for (const documento of documentos) {
        if ((isImage(documento.nombre_original) || isPdf(documento.nombre_original)) &&
            !previewUrls.has(documento.id)) {
          setLoadingPreviewIds(prev => new Set(prev).add(documento.id));

          try {
            const res = await api.get(`/${viewUrlPrefix}/${documento.id}/view`, {
              responseType: 'blob',
            });
            const objectUrl = URL.createObjectURL(res.data as Blob);
            objectUrlsRef.current.set(documento.id, objectUrl);
            setPreviewUrls(prev => new Map(prev).set(documento.id, objectUrl));
          } catch (error) {
            console.error(`Error loading preview for ${documento.id}:`, error);
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
  }, [documentos, previewUrls, viewUrlPrefix]);

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
      setDownloadingDocId(documento.id);
      const resolveFn = downloadFn ?? incapacidadService.getDownloadUrl.bind(incapacidadService);
      const url = await resolveFn(documento.id);

      // If the resolved URL is a relative /api/v1/storage/files/... path (filesystem
      // backend), we must fetch it via the authenticated axios instance and serve the
      // blob through a temporary object URL — a direct window.open would not carry
      // the Authorization header and would get a 401.
      if (url.startsWith('/api/') || url.startsWith('/storage/')) {
        const res = await api.get(url, { responseType: 'blob' });
        const objectUrl = URL.createObjectURL(res.data as Blob);
        const anchor = document.createElement('a');
        anchor.href = objectUrl;
        anchor.download = documento.nombre_original || 'documento';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(objectUrl);
      } else {
        // MinIO presigned URL — already carries auth via query params; open directly
        window.open(url, '_blank');
      }
    } catch (error) {
      console.error('Error downloading document:', error);
      alert('Could not download document');
    } finally {
      setDownloadingDocId(null);
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
      <div>

        <Tabs value={selectedDocId || ''} onValueChange={setSelectedDocId} className="w-full">
          {/* Horizontal Tab List */}
          <div className="overflow-x-auto border-b border-slate-200 mb-6">
            <TabsList className="flex gap-2 bg-transparent h-auto p-0 justify-start">
              {documentos.map((documento) => {
                const isImg = isImage(documento.nombre_original);
                const isPdf2 = isPdf(documento.nombre_original);

                return (
                  <TabsTrigger
                    key={documento.id}
                    value={documento.id}
                    className="flex items-center gap-2 px-3 py-2 border-b-2 border-transparent rounded-none data-[state=active]:border-blue-600 data-[state=active]:bg-transparent"
                  >
                    {isImg ? (
                      <ImageIcon className="h-4 w-4 text-blue-500" />
                    ) : isPdf2 ? (
                      <FileText className="h-4 w-4 text-red-500" />
                    ) : (
                      <FileIcon className="h-4 w-4 text-slate-500" />
                    )}
                    <span className="truncate max-w-[200px] text-sm">
                      {documento.nombre_original || 'Sin nombre'}
                    </span>
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </div>

          {/* Inline Document Viewer */}
          {documentos.map((documento) => {
            const isImg = isImage(documento.nombre_original);
            const isPdf2 = isPdf(documento.nombre_original);
            const hasPreview = isImg || isPdf2;
            const previewUrl = previewUrls.get(documento.id);
            const isLoadingPreview = loadingPreviewIds.has(documento.id);

            return (
              <TabsContent key={documento.id} value={documento.id} className="space-y-4">
                {/* Document Info Header */}
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center gap-3">
                    {getFileIcon(documento.nombre_original)}
                    <div>
                      <p className="font-semibold text-sm">{documento.nombre_original || 'Sin nombre'}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {documento.tipo_documento}
                        </Badge>
                        <span className="text-xs text-slate-500">
                          Subido: {formatDate(documento.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => handleDownload(documento)}
                    disabled={downloadingDocId === documento.id}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    {downloadingDocId === documento.id ? 'Descargando...' : 'Descargar'}
                  </Button>
                </div>

                {/* Preview Viewer */}
                {hasPreview && (
                  <div className="rounded-lg border border-slate-200 overflow-hidden bg-white">
                    {previewUrl ? (
                      <div className="p-4">
                        {isPdf2 ? (
                          <iframe
                            src={previewUrl}
                            className="w-full h-[600px] border-0 rounded"
                            title={`Vista previa de ${documento.nombre_original}`}
                          />
                        ) : (
                          <img
                            src={previewUrl}
                            alt={documento.nombre_original || 'Documento'}
                            className="max-w-full h-auto mx-auto max-h-[600px]"
                          />
                        )}
                      </div>
                    ) : isLoadingPreview ? (
                      <div className="w-full h-[300px] flex items-center justify-center">
                        <div className="text-center">
                          {isImg ? (
                            <ImageIcon className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                          ) : (
                            <FileText className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                          )}
                          <p className="text-sm text-slate-500">Cargando vista previa...</p>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}

                {!hasPreview && (
                  <div className="p-4 rounded-lg border border-slate-200 bg-slate-50 text-center">
                    <FileIcon className="h-12 w-12 text-slate-400 mx-auto mb-2" />
                    <p className="text-sm text-slate-500">Este tipo de archivo no puede ser visualizado</p>
                  </div>
                )}
              </TabsContent>
            );
          })}
        </Tabs>
      </div>
    </div>
  );
}
