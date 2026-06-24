/**
 * Servicio para Plantilla de Auditoría.
 *
 * Endpoints:
 *   POST /api/v1/incapacidades/{id}/plantilla-auditoria
 *   GET  /api/v1/incapacidades/{id}/plantilla-auditoria
 *   GET  /api/v1/incapacidades/{id}/plantilla-auditoria/texto-copiable
 */
import api from '@/lib/api';

export interface PlantillaAuditoriaCreate {
  canal_recepcion: string;
  dias_autorizados: number;
  fecha_inicio_autorizada: string; // ISO date string YYYY-MM-DD
  fecha_fin_autorizada: string;    // ISO date string YYYY-MM-DD
  diagnostico_cie10?: string;
  descripcion_cie10?: string;
  nombre_medico?: string;
  especialidad_medico?: string;
  nombre_ips?: string;
  fecha_emision_incapacidad?: string;
  dias_documento?: number;
  rango_pagado_inicio?: string;
  rango_pagado_fin?: string;
}

export interface PlantillaAuditoriaResponse {
  id: string;
  incapacidad_id: string;
  canal_recepcion: string;
  nombre_ips?: string | null;
  fecha_emision_incapacidad?: string | null;
  dias_autorizados: number;
  fecha_inicio_autorizada: string;
  fecha_fin_autorizada: string;
  diagnostico_cie10?: string | null;
  descripcion_cie10?: string | null;
  nombre_medico?: string | null;
  especialidad_medico?: string | null;
  linea_autorizacion?: string | null;
  dias_documento?: number | null;
  rango_pagado_inicio?: string | null;
  rango_pagado_fin?: string | null;
  auditado_por_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlantillaAuditoriaTextoResponse {
  texto: string;
}

export const plantillaAuditoriaService = {
  /**
   * Crear o actualizar la plantilla de auditoría de una incapacidad.
   * POST /api/v1/incapacidades/{id}/plantilla-auditoria
   */
  async createOrUpdate(
    incapacidadId: string,
    data: PlantillaAuditoriaCreate,
  ): Promise<PlantillaAuditoriaResponse> {
    const { data: response } = await api.post<PlantillaAuditoriaResponse>(
      `/incapacidades/${incapacidadId}/plantilla-auditoria`,
      data,
    );
    return response;
  },

  /**
   * Obtener la plantilla de auditoría de una incapacidad.
   * GET /api/v1/incapacidades/{id}/plantilla-auditoria
   */
  async getByIncapacidad(incapacidadId: string): Promise<PlantillaAuditoriaResponse> {
    const { data } = await api.get<PlantillaAuditoriaResponse>(
      `/incapacidades/${incapacidadId}/plantilla-auditoria`,
    );
    return data;
  },

  /**
   * Obtener texto copiable listo para pegar en Arpis.
   * GET /api/v1/incapacidades/{id}/plantilla-auditoria/texto-copiable
   */
  async getTextoCopiable(incapacidadId: string): Promise<string> {
    const { data } = await api.get<PlantillaAuditoriaTextoResponse>(
      `/incapacidades/${incapacidadId}/plantilla-auditoria/texto-copiable`,
    );
    return data.texto;
  },
};
