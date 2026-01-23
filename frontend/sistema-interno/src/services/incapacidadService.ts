import api from '@/lib/api';
import type {
  Incapacidad,
  IncapacidadFiltros,
  HistorialEstado,
  Documento,
} from '@/types/incapacidad';

/**
 * Servicio de incapacidades basado en OpenAPI specification
 * Endpoints: /api/v1/incapacidades/*
 */
export const incapacidadService = {
  /**
   * Listar incapacidades con filtros y paginación
   * GET /api/v1/incapacidades/
   * Query params: skip, limit
   */
  async list(filtros: IncapacidadFiltros = {}): Promise<Incapacidad[]> {
    const { data } = await api.get<Incapacidad[]>('/incapacidades', {
      params: {
        skip: filtros.skip || 0,
        limit: filtros.limit || 100,
      },
    });
    return data;
  },

  /**
   * Obtener una incapacidad por ID
   * GET /api/v1/incapacidades/{incapacidad_id}
   */
  async getById(id: string): Promise<Incapacidad> {
    const { data } = await api.get<Incapacidad>(`/incapacidades/${id}`);
    return data;
  },

  /**
   * Consultar incapacidad pública (sin autenticación)
   * GET /api/v1/incapacidades/consultar
   * Query params: numero OR (documento + tipo_documento)
   * 
   * NOTA: Este endpoint NO requiere autenticación (Portal Externo)
   * Para búsqueda autenticada usar list() con filtros
   */
  async consultarPublica(params: {
    numero?: string;
    documento?: string;
    tipo_documento?: string;
  }): Promise<Incapacidad> {
    const { data } = await api.get<Incapacidad>('/incapacidades/consultar', {
      params,
    });
    return data;
  },

  /**
   * WORKFLOW: Radicar incapacidad
   * POST /api/v1/incapacidades/{incapacidad_id}/radicar
   * Transición: RADICADA → EN_AUDITORIA
   */
  async radicar(id: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/radicar`);
    return data;
  },

  /**
   * WORKFLOW: Auditar incapacidad
   * POST /api/v1/incapacidades/{incapacidad_id}/auditar
   * Body: { accion: string, observaciones: string }
   * Acciones: "SOLICITAR_INFORMACION", "APROBAR_PARA_PAGO", "RECHAZAR"
   */
  async auditar(
    id: string,
    accion: 'SOLICITAR_INFORMACION' | 'APROBAR_PARA_PAGO' | 'RECHAZAR',
    observaciones: string
  ): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/auditar`, {
      accion,
      observaciones,
    });
    return data;
  },

  /**
   * WORKFLOW: Aprobar incapacidad para pago
   * POST /api/v1/incapacidades/{incapacidad_id}/aprobar
   * No requiere body
   */
  async aprobar(id: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/aprobar`);
    return data;
  },

  /**
   * WORKFLOW: Rechazar incapacidad
   * POST /api/v1/incapacidades/{incapacidad_id}/rechazar
   * Body: { motivo: string } (mínimo 10 caracteres)
   */
  async rechazar(id: string, motivo: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/rechazar`, {
      motivo,
    });
    return data;
  },

  /**
   * WORKFLOW: Enviar incapacidad aprobada a pago
   * POST /api/v1/incapacidades/{incapacidad_id}/enviar-pago
   * Genera orden de pago automáticamente
   */
  async enviarPago(id: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/enviar-pago`);
    return data;
  },

  /**
   * WORKFLOW: Marcar incapacidad como pagada
   * POST /api/v1/incapacidades/{incapacidad_id}/marcar-pagada
   */
  async marcarPagada(id: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/marcar-pagada`);
    return data;
  },

  /**
   * Obtener historial de estados de una incapacidad
   * GET /api/v1/incapacidades/{incapacidad_id}/historial
   * Query params: skip, limit
   */
  async getHistorial(id: string, skip = 0, limit = 100): Promise<HistorialEstado[]> {
    const { data } = await api.get<HistorialEstado[]>(`/incapacidades/${id}/historial`, {
      params: { skip, limit },
    });
    return data;
  },

  /**
   * Obtener documentos de una incapacidad
   * GET /api/v1/incapacidades/{incapacidad_id}/documentos
   */
  async getDocumentos(id: string): Promise<Documento[]> {
    const { data } = await api.get<Documento[]>(`/incapacidades/${id}/documentos`);
    return data;
  },

  /**
   * Descargar documento autenticado
   * GET /api/v1/documentos/{documento_id}/download
   * Returns: Blob (archivo)
   */
  async descargarDocumento(documentoId: string): Promise<Blob> {
    const { data } = await api.get(`/documentos/${documentoId}/download`, {
      responseType: 'blob',
    });
    return data;
  },

  /**
   * Descargar documento público (sin autenticación)
   * GET /api/v1/incapacidades/{numero}/documentos/{documento_id}/download
   * Returns: PresignedUrlResponse con URL temporal
   * 
   * NOTA: Solo documentos públicos (INCAPACIDAD_MEDICA)
   */
  async descargarDocumentoPublico(
    numero: string,
    documentoId: string
  ): Promise<{ url: string; expires_in: number }> {
    const { data } = await api.get(`/incapacidades/${numero}/documentos/${documentoId}/download`);
    return data;
  },

  /**
   * Obtener URL de descarga firmada (autenticado)
   * GET /api/v1/documentos/{documento_id}/download-url
   * Returns: PresignedUrlResponse
   */
  async getDownloadUrl(documentoId: string): Promise<string> {
    const { data } = await api.get<{ url: string; expires_in: number }>(
      `/documentos/${documentoId}/download-url`
    );
    return data.url;
  },
};
