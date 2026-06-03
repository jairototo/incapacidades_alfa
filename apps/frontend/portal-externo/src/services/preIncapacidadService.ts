import apiClient from './api';

export interface PreIncapacidadPayload {
  solicitante: {
    correo: string;
    nombres: string;
    apellidos?: string;
    telefono?: string;
  };
  empresa?: {
    nit?: string;
    nombre?: string;
  };
  empleado: {
    tipo_documento: string;
    numero_documento: string;
    nombres: string;
    apellidos?: string;
    email?: string;
    telefono?: string;
  };
  incapacidad: {
    tipo_enfermedad: string;
    fecha_inicio: string; // ISO date string YYYY-MM-DD
    fecha_fin: string;
    dias_totales: number;
    diagnostico_cie10: string;
    descripcion_diagnostico?: string;
    nombre_medico: string;
    registro_medico: string;
    ips?: string;
    observaciones?: string;
  };
}

export interface PreIncapacidadResponse {
  id: string;
  numero_radicacion: number;
  estado: string;
  mensaje: string;
}

export interface PreDocumentoResponse {
  id: string;
  tipo_documento: string;
  nombre_original: string;
  tamanio_bytes: number;
  estado_subida: string;
  created_at: string;
}

/**
 * Crea una pre-incapacidad en el backend (portal externo).
 * No requiere autenticación.
 */
export async function crearPreIncapacidad(
  payload: PreIncapacidadPayload
): Promise<PreIncapacidadResponse> {
  const response = await apiClient.post<PreIncapacidadResponse>(
    '/pre-incapacidades/radicar',
    payload
  );
  return response.data;
}

/**
 * Sube un documento asociado a una pre-incapacidad.
 * Retorna el registro creado independientemente de si el storage tuvo éxito.
 */
export async function subirPreDocumento(
  preIncapacidadId: string,
  file: File,
  tipoDocumento: 'INCAPACIDAD_MEDICA' | 'HISTORIA_CLINICA' | 'SOPORTE_ADICIONAL'
): Promise<PreDocumentoResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo_documento', tipoDocumento);

  const response = await apiClient.post<PreDocumentoResponse>(
    `/pre-incapacidades/${preIncapacidadId}/documentos`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
}

export interface UploadDocumentosResult {
  file: File;
  tipo: 'INCAPACIDAD_MEDICA' | 'HISTORIA_CLINICA' | 'SOPORTE_ADICIONAL';
  success: boolean;
  result?: PreDocumentoResponse;
  error?: string;
}

/**
 * Sube múltiples documentos de forma secuencial.
 * No lanza excepción — cada resultado indica éxito/fallo individualmente.
 * Garantiza que todos los intentos quedan registrados en BD.
 */
export async function subirTodosLosDocumentos(
  preIncapacidadId: string,
  documentos: {
    file: File;
    tipo: 'INCAPACIDAD_MEDICA' | 'HISTORIA_CLINICA' | 'SOPORTE_ADICIONAL';
  }[]
): Promise<UploadDocumentosResult[]> {
  const resultados: UploadDocumentosResult[] = [];

  for (const doc of documentos) {
    let intentos = 0;
    const maxIntentos = 3;

    while (intentos < maxIntentos) {
      try {
        const result = await subirPreDocumento(preIncapacidadId, doc.file, doc.tipo);
        resultados.push({ ...doc, success: true, result });
        break;
      } catch (error: any) {
        intentos++;
        if (intentos === maxIntentos) {
          resultados.push({
            ...doc,
            success: false,
            error: error?.response?.data?.detail || error?.message || 'Error desconocido',
          });
        }
        // Esperar brevemente antes de reintentar
        if (intentos < maxIntentos) {
          await new Promise((resolve) => setTimeout(resolve, 500 * intentos));
        }
      }
    }
  }

  return resultados;
}

/**
 * Formatea la fecha de un objeto Date al formato ISO YYYY-MM-DD sin zona horaria.
 */
export function formatDateForApi(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
