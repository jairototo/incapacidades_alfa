import { useMutation } from '@tanstack/react-query';
import api from './api';
import type { DocumentoResponse, TipoDocumentoArchivo } from '@/types/api';

/**
 * Servicio para gestión de documentos
 */

export interface UploadDocumentoParams {
  incapacidadId: string;
  archivo: File;
  tipoDocumento: TipoDocumentoArchivo;
}

/**
 * Subir un documento asociado a una incapacidad
 */
export async function uploadDocumento({
  incapacidadId,
  archivo,
  tipoDocumento,
}: UploadDocumentoParams): Promise<DocumentoResponse> {
  // Crear FormData para enviar archivo binario
  const formData = new FormData();
  formData.append('file', archivo);
  formData.append('tipo_documento', tipoDocumento);
  formData.append('incapacidad_id', incapacidadId);

  const response = await api.post<DocumentoResponse>(
    `/documentos/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}

/**
 * Hook para subir documento con React Query
 */
export function useUploadDocumento() {
  return useMutation({
    mutationFn: uploadDocumento,
    onSuccess: (data, variables) => {
      if (import.meta.env.DEV) {
        console.log('[useUploadDocumento] Documento subido exitosamente:', {
          id: data.id,
          nombre: data.nombre_archivo,
          tipo: variables.tipoDocumento,
          incapacidad_id: variables.incapacidadId,
        });
      }
    },
    onError: (error: any, variables) => {
      if (import.meta.env.DEV) {
        console.error('[useUploadDocumento] Error al subir documento:', {
          archivo: variables.archivo.name,
          error: error.message,
          response: error.response?.data,
        });
      }
    },
  });
}

/**
 * Subir múltiples documentos de forma secuencial
 * Retorna array con resultados (success/error) de cada upload
 */
export async function uploadMultipleDocumentos(
  incapacidadId: string,
  archivos: Array<{ file: File; tipo: TipoDocumentoArchivo }>
): Promise<Array<{ success: boolean; data?: DocumentoResponse; error?: string }>> {
  const results = [];

  for (const { file, tipo } of archivos) {
    try {
      const data = await uploadDocumento({
        incapacidadId,
        archivo: file,
        tipoDocumento: tipo,
      });
      results.push({ success: true, data });
    } catch (error: any) {
      results.push({
        success: false,
        error: error.response?.data?.error?.message || error.message,
      });
    }
  }

  return results;
}
