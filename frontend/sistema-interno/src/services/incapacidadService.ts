import api from '@/lib/api';
import type {
  Incapacidad,
  IncapacidadFiltros,
  PaginatedResponse,
  HistorialEstado,
  Documento,
} from '@/types/incapacidad';
import { EstadoIncapacidad } from '@/types/enums';

/**
 * Servicio de incapacidades
 */
export const incapacidadService = {
  /**
   * Listar incapacidades con filtros
   */
  async list(filtros: IncapacidadFiltros = {}): Promise<PaginatedResponse<Incapacidad>> {
    const { data } = await api.get<PaginatedResponse<Incapacidad>>('/incapacidades', {
      params: filtros,
    });
    return data;
  },

  /**
   * Obtener una incapacidad por ID
   */
  async getById(id: string): Promise<Incapacidad> {
    const { data } = await api.get<Incapacidad>(`/incapacidades/${id}`);
    return data;
  },

  /**
   * Buscar incapacidad por número
   */
  async buscarPorNumero(numero: string): Promise<Incapacidad> {
    const { data } = await api.get<Incapacidad>(`/incapacidades/buscar/${numero}`);
    return data;
  },

  /**
   * Cambiar estado de incapacidad
   */
  async cambiarEstado(
    id: string,
    nuevoEstado: EstadoIncapacidad,
    observacion?: string
  ): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/cambiar-estado`, {
      nuevo_estado: nuevoEstado,
      observacion,
    });
    return data;
  },

  /**
   * Obtener historial de estados
   */
  async getHistorial(id: string): Promise<HistorialEstado[]> {
    const { data } = await api.get<HistorialEstado[]>(`/incapacidades/${id}/historial`);
    return data;
  },

  /**
   * Obtener documentos de una incapacidad
   */
  async getDocumentos(id: string): Promise<Documento[]> {
    const { data } = await api.get<Documento[]>(`/incapacidades/${id}/documentos`);
    return data;
  },

  /**
   * Descargar documento
   */
  async descargarDocumento(documentoId: string): Promise<Blob> {
    const { data } = await api.get(`/documentos/${documentoId}/download`, {
      responseType: 'blob',
    });
    return data;
  },

  /**
   * Obtener URL de descarga firmada
   */
  async getDownloadUrl(documentoId: string): Promise<string> {
    const { data } = await api.get<{ url: string }>(`/documentos/${documentoId}/download-url`);
    return data.url;
  },
};
