/**
 * Servicio del módulo Previsionales.
 *
 * Endpoints (backend `app/api/v1/router.py`, Fase 4):
 *   POST /previsionales/lotes                          — cargar lote (multipart)
 *   GET  /previsionales/lotes                           — listar lotes
 *   GET  /previsionales/lotes/{id}                       — detalle de lote
 *   GET  /previsionales/lotes/{id}/incapacidades         — incapacidades del lote (filtros)
 *   GET  /previsionales/lotes/{id}/arpis.xlsx            — exportar libro ARPIS (blob)
 *   POST /previsionales/lotes/{id}/liquidar              — re-liquidar lote
 *   GET  /previsionales/lotes/{id}/respuesta.xlsx        — exportar respuesta AFP (blob)
 *   POST /previsionales/referencia/importar?tipo=...     — importar hoja de referencia (multipart)
 *   GET  /previsionales/parametros/smlmv                 — listar SMLMV
 *   GET  /previsionales/incapacidades/{id}/senales        — señales AB-AT persistidas
 *   PATCH /previsionales/incapacidades/{id}               — actualizar dia_181_alfa
 *   POST /previsionales/incapacidades/{id}/aval           — registrar aval
 *   POST /previsionales/incapacidades/{id}/duplicar       — duplicar incapacidad
 *   POST /previsionales/siniestros                        — registrar siniestro manual
 *
 * Nota deliberada: `POST /previsionales/lotes/{id}/actualizar` (re-cruce de
 * siniestros) NO se expone aquí -- el backend lo documenta como un gap real
 * (devuelve 501 siempre, ver docstring de `actualizar_lote` en
 * `endpoints/previsionales/lotes.py`). No tiene sentido envolver en el
 * servicio un endpoint que el propio backend advierte que no hace nada
 * todavía.
 */
import api from '@/lib/api';
import type {
  AvalRequest,
  DuplicarRequest,
  FiltrosIncapacidadesLote,
  IncapacidadPrevisional,
  LiquidarLoteResponse,
  LotePrevisional,
  PatchIncapacidadRequest,
  ReferenciaImportarResponse,
  SenalAuditoriaPrevisional,
  SiniestroManualRequest,
  SiniestroPrevisional,
  SmlmvParametros,
  TipoReferenciaPrevisional,
} from '@/types/previsional';

export const previsionalesService = {
  /**
   * Cargar un lote previsional desde el excel de la AFP (multipart).
   * POST /previsionales/lotes
   */
  async cargarLote(
    file: File,
    password?: string,
    nombreArchivo?: string
  ): Promise<LotePrevisional> {
    const formData = new FormData();
    formData.append('file', file);
    if (password) formData.append('password', password);
    if (nombreArchivo) formData.append('nombre_archivo', nombreArchivo);

    const { data } = await api.post<LotePrevisional>('/previsionales/lotes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  /**
   * Listar lotes previsionales (paginado).
   * GET /previsionales/lotes
   */
  async listarLotes(skip = 0, limit = 100): Promise<LotePrevisional[]> {
    const { data } = await api.get<LotePrevisional[]>('/previsionales/lotes', {
      params: { skip, limit },
    });
    return data;
  },

  /**
   * Obtener el detalle de un lote.
   * GET /previsionales/lotes/{loteId}
   */
  async obtenerLote(loteId: string): Promise<LotePrevisional> {
    const { data } = await api.get<LotePrevisional>(`/previsionales/lotes/${loteId}`);
    return data;
  },

  /**
   * Listar las incapacidades de un lote, con filtros opcionales.
   * GET /previsionales/lotes/{loteId}/incapacidades
   */
  async listarIncapacidadesDelLote(
    loteId: string,
    filtros?: FiltrosIncapacidadesLote
  ): Promise<IncapacidadPrevisional[]> {
    const { data } = await api.get<IncapacidadPrevisional[]>(
      `/previsionales/lotes/${loteId}/incapacidades`,
      { params: filtros }
    );
    return data;
  },

  /**
   * Exportar el libro de cargue ARPIS de un lote.
   * GET /previsionales/lotes/{loteId}/arpis.xlsx
   * Descarga autenticada -- devuelve el Blob para que el llamador construya
   * el enlace de descarga (ver patrón en `DocumentosViewer.tsx`).
   */
  async exportarArpis(loteId: string): Promise<Blob> {
    const { data } = await api.get(`/previsionales/lotes/${loteId}/arpis.xlsx`, {
      responseType: 'blob',
    });
    return data as Blob;
  },

  /**
   * Importar una hoja de datos de referencia previsionales (multipart).
   * POST /previsionales/referencia/importar?tipo=siniestros|solicitudes|ite_historico
   */
  async importarReferencia(
    tipo: TipoReferenciaPrevisional,
    file: File
  ): Promise<ReferenciaImportarResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post<ReferenciaImportarResponse>(
      '/previsionales/referencia/importar',
      formData,
      { params: { tipo }, headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  /**
   * Listar los parámetros SMLMV configurados por año.
   * GET /previsionales/parametros/smlmv
   */
  async listarSmlmv(): Promise<SmlmvParametros[]> {
    const { data } = await api.get<SmlmvParametros[]>('/previsionales/parametros/smlmv');
    return data;
  },

  /**
   * Listar las señales de auditoría (AB-AT) persistidas de una incapacidad.
   * GET /previsionales/incapacidades/{incapacidadId}/senales
   */
  async obtenerSenales(incapacidadId: string): Promise<SenalAuditoriaPrevisional[]> {
    const { data } = await api.get<SenalAuditoriaPrevisional[]>(
      `/previsionales/incapacidades/${incapacidadId}/senales`
    );
    return data;
  },

  /**
   * Actualizar el día 181 auditado (Alfa) de una incapacidad.
   * PATCH /previsionales/incapacidades/{incapacidadId}
   */
  async patchIncapacidad(
    incapacidadId: string,
    body: PatchIncapacidadRequest
  ): Promise<IncapacidadPrevisional> {
    const { data } = await api.patch<IncapacidadPrevisional>(
      `/previsionales/incapacidades/${incapacidadId}`,
      body
    );
    return data;
  },

  /**
   * Registrar el aval de auditoría (decisión humana SI/NO).
   * POST /previsionales/incapacidades/{incapacidadId}/aval
   */
  async registrarAval(
    incapacidadId: string,
    body: AvalRequest
  ): Promise<IncapacidadPrevisional> {
    const { data } = await api.post<IncapacidadPrevisional>(
      `/previsionales/incapacidades/${incapacidadId}/aval`,
      body
    );
    return data;
  },

  /**
   * Duplicar una incapacidad en un nuevo rango de fechas.
   * POST /previsionales/incapacidades/{incapacidadId}/duplicar
   */
  async duplicarIncapacidad(
    incapacidadId: string,
    body: DuplicarRequest
  ): Promise<IncapacidadPrevisional> {
    const { data } = await api.post<IncapacidadPrevisional>(
      `/previsionales/incapacidades/${incapacidadId}/duplicar`,
      body
    );
    return data;
  },

  /**
   * Re-liquidar todas las incapacidades no duplicadas de un lote.
   * POST /previsionales/lotes/{loteId}/liquidar
   */
  async liquidarLote(loteId: string): Promise<LiquidarLoteResponse> {
    const { data } = await api.post<LiquidarLoteResponse>(
      `/previsionales/lotes/${loteId}/liquidar`
    );
    return data;
  },

  /**
   * Exportar el excel de respuesta al fondo (AFP) de un lote.
   * GET /previsionales/lotes/{loteId}/respuesta.xlsx
   * Descarga autenticada -- devuelve el Blob (mismo patrón que `exportarArpis`).
   */
  async descargarRespuesta(loteId: string): Promise<Blob> {
    const { data } = await api.get(`/previsionales/lotes/${loteId}/respuesta.xlsx`, {
      responseType: 'blob',
    });
    return data as Blob;
  },

  /**
   * Registrar manualmente un siniestro previsional.
   * POST /previsionales/siniestros
   */
  async crearSiniestroManual(body: SiniestroManualRequest): Promise<SiniestroPrevisional> {
    const { data } = await api.post<SiniestroPrevisional>('/previsionales/siniestros', body);
    return data;
  },
};
