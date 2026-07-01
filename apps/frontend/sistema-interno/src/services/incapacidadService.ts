import api from '@/lib/api';
import type {
  Incapacidad,
  IncapacidadFiltros,
  IncapacidadPendiente,
  FiltrosPendientes,
  HistorialEstado,
  Documento,
  AuditoriaDatosAprobados,
  IncapacidadAuditarRequest,
  ValidacionesResponse,
  SiniestroBasic,
  AuditoriaResultado,
} from '@/types/incapacidad';

/**
 * Servicio de incapacidades basado en OpenAPI specification
 * Endpoints: /api/v1/incapacidades/*
 */
export const incapacidadService = {
  /**
   * Listar incapacidades con filtros y paginación
   * GET /api/v1/incapacidades/
   * Query params: skip, limit, numero, tipo, estado, empleado_documento, empresa_nit, fecha_inicio, fecha_fin
   */
  async list(filtros: IncapacidadFiltros = {}): Promise<Incapacidad[]> {
    // Filtrar parámetros inválidos (undefined, null, string vacío)
    const paramsLimpios = Object.fromEntries(
      Object.entries({
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 100,
        numero: filtros.numero,
        tipo: filtros.tipo,
        estado: filtros.estado,
        empleado_documento: filtros.empleado_documento,
        afiliado_documento: filtros.afiliado_documento,
        empresa_nit: filtros.empresa_nit,
        fecha_inicio_desde: filtros.fecha_inicio_desde,
        fecha_inicio_hasta: filtros.fecha_inicio_hasta,
      }).filter(([_, value]) => {
        // Excluir undefined, null, y strings vacíos
        if (value === undefined || value === null || value === '') return false;
        if (typeof value === 'number' && isNaN(value)) return false;
        return true;
      })
    );

    console.log('Enviando parámetros al backend:', paramsLimpios); // Debug

    const { data } = await api.get<Incapacidad[]>('/incapacidades/', {
      params: paramsLimpios,
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
   * Listar incapacidades pendientes de auditoría
   * GET /api/v1/incapacidades/pendientes
   * Incluye: RADICADA, EN_AUDITORIA, OBSERVADA
   * Ordenado por prioridad y antigüedad
   */
  async listarPendientes(filtros: FiltrosPendientes = {}): Promise<IncapacidadPendiente[]> {
    // Filtrar parámetros inválidos (undefined, null, NaN, string vacío)
    const paramsLimpios = Object.fromEntries(
      Object.entries({
        tipo: filtros.tipo,
        prioridad: filtros.prioridad,
        empresa_nit: filtros.empresa_nit,
        dias_antiguedad_min: filtros.dias_antiguedad_min,
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 100,
      }).filter(([_, value]) => {
        // Excluir undefined, null, NaN, y strings vacíos
        if (value === undefined || value === null || value === '') return false;
        if (typeof value === 'number' && isNaN(value)) return false;
        return true;
      })
    );

    const { data } = await api.get<IncapacidadPendiente[]>('/incapacidades/pendientes', {
      params: paramsLimpios,
    });
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
   * Soporta aprobación parcial con datos modificados
   */
  async auditar(id: string, data: IncapacidadAuditarRequest): Promise<Incapacidad> {
    const { data: response } = await api.post<Incapacidad>(`/incapacidades/${id}/auditar`, data);
    return response;
  },

  /**
   * Obtener datos aprobados de una incapacidad (si existen)
   * GET /api/v1/incapacidades/{incapacidad_id}/datos-aprobados
   * Returns: AuditoriaDatosAprobados | null
   */
  async getDatosAprobados(id: string): Promise<AuditoriaDatosAprobados | null> {
    try {
      const { data } = await api.get<AuditoriaDatosAprobados>(`/incapacidades/${id}/datos-aprobados`);
      return data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null; // No hay datos aprobados
      }
      throw error; // Re-lanzar otros errores
    }
  },

  /**
   * WORKFLOW: Aprobar incapacidad para pago
   * POST /api/v1/incapacidades/{incapacidad_id}/aprobar
   * Body: 
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
    // const { data } = await api.get<Documento[]>(`/incapacidades/${id}/documentos`);
    const { data } = await api.get<Documento[]>(`/documentos/incapacidades/${id}`);
    return data;
  },
  
  /**
   * GET /api/v1/documentos/{documento_id}/download-url
   * Returns: PresignedUrlResponse
   */
  async getDownloadUrl(documentoId: string): Promise<string> {
    const { data } = await api.get<{ url: string; expires_in: number }>(
      `/documentos/${documentoId}/download`
    );
    return data.url;
  },

  /**
   * Cambiar estado de incapacidad (método genérico)
   * Utiliza el endpoint apropiado según el nuevo estado
   */
  async cambiarEstado(
    id: string,
    nuevoEstado: string,
    observacion?: string
  ): Promise<Incapacidad> {
    switch (nuevoEstado) {
      case 'EN_AUDITORIA':
        return this.radicar(id);

      case 'APROBADA':
        return this.aprobar(id);

      case 'RECHAZADA':
        if (!observacion) {
          throw new Error('Se requiere motivo para rechazar la incapacidad');
        }
        return this.rechazar(id, observacion);

      case 'OBSERVADA':
        if (!observacion) {
          throw new Error('Se requiere observación');
        }
        return this.auditar(id, { accion: 'SOLICITAR_INFORMACION', observaciones: observacion });

      case 'EN_PAGO':
        return this.enviarPago(id);

      case 'PAGADA':
        return this.marcarPagada(id);

      default:
        throw new Error(`Estado no válido: ${nuevoEstado}`);
    }
  },

  /**
   * Obtener validaciones de una incapacidad
   * GET /api/v1/incapacidades/{id}/validaciones
   * Returns: ValidacionesResponse con lista de issues, flags de error/fraude, y total
   */
  async getValidaciones(id: string): Promise<ValidacionesResponse> {
    const { data } = await api.get<ValidacionesResponse>(
      `/incapacidades/${id}/validaciones`
    );
    return data;
  },

  /**
   * WORKFLOW: Crear siniestro y retornar incapacidad a EN_AUDITORIA (solo ADMIN)
   * POST /api/v1/incapacidades/{incapacidad_id}/creacion-siniestro
   * Transición: CREACION_SINIESTRO → EN_AUDITORIA
   */
  async iniciarCreacionSiniestro(
    id: string,
    payload: {
      fecha_siniestro: string;
      tipo_siniestro: string;
      descripcion: string;
      observacion: string;
    }
  ): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(
      `/incapacidades/${id}/creacion-siniestro`,
      payload
    );
    return data;
  },

  /**
   * BANDEJA: Incapacidades en CREACION_SINIESTRO (solo ADMIN)
   * GET /api/v1/incapacidades/bandeja/creacion-siniestro
   */
  async listarBandejaCreacionSiniestro(filtros: FiltrosPendientes = {}): Promise<IncapacidadPendiente[]> {
    const paramsLimpios = Object.fromEntries(
      Object.entries({
        tipo: filtros.tipo,
        prioridad: filtros.prioridad,
        empresa_nit: filtros.empresa_nit,
        dias_antiguedad_min: filtros.dias_antiguedad_min,
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 100,
      }).filter(([_, value]) => value !== undefined && value !== null && value !== '')
    );
    const { data } = await api.get<IncapacidadPendiente[]>('/incapacidades/bandeja/creacion-siniestro', {
      params: paramsLimpios,
    });
    return data;
  },

  /**
   * BANDEJA: Incapacidades en LIQUIDACION o LIQUIDACION_PARCIAL
   * GET /api/v1/incapacidades/bandeja/liquidacion
   */
  async listarBandejaLiquidacion(filtros: FiltrosPendientes = {}): Promise<IncapacidadPendiente[]> {
    const paramsLimpios = Object.fromEntries(
      Object.entries({
        tipo: filtros.tipo,
        prioridad: filtros.prioridad,
        empresa_nit: filtros.empresa_nit,
        dias_antiguedad_min: filtros.dias_antiguedad_min,
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 100,
      }).filter(([_, value]) => value !== undefined && value !== null && value !== '')
    );
    const { data } = await api.get<IncapacidadPendiente[]>('/incapacidades/bandeja/liquidacion', {
      params: paramsLimpios,
    });
    return data;
  },

  /**
   * NOTIFICACIÓN: Reenviar notificación de glosa al solicitante (solo ADMIN/AUDITOR)
   * POST /api/v1/incapacidades/{incapacidad_id}/reenviar-notificacion-glosada
   * Solo disponible cuando estado === 'GLOSADA'
   */
  async reenviarNotificacionGlosada(id: string): Promise<void> {
    await api.post(`/incapacidades/${id}/reenviar-notificacion-glosada`);
  },

  /**
   * Obtener siniestros candidatos para vincular a una incapacidad ARL
   * GET /api/v1/incapacidades/{id}/siniestros-candidatos
   * Returns: SiniestroBasic[] (vacío si ya tiene siniestro o es SALUD)
   */
  async getSiniestrosCandidatos(id: string): Promise<SiniestroBasic[]> {
    const { data } = await api.get<SiniestroBasic[]>(
      `/incapacidades/${id}/siniestros-candidatos`
    );
    return data;
  },

  /**
   * Vincular siniestro a incapacidad ARL (solo AUDITOR o ADMIN)
   * POST /api/v1/incapacidades/{id}/vincular-siniestro
   * Body: { siniestro_id: string }
   * Returns: Incapacidad actualizada
   */
  async vincularSiniestro(id: string, siniestro_id: string): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(
      `/incapacidades/${id}/vincular-siniestro`,
      { siniestro_id }
    );
    return data;
  },

  /**
   * Obtener resultados de auditoría automática
   * GET /api/v1/incapacidades/{id}/auditoria-resultados
   * Returns: AuditoriaResultado[] ordenados por regla (alfabético)
   */
  async getAuditoriaResultados(id: string): Promise<AuditoriaResultado[]> {
    const { data } = await api.get<AuditoriaResultado[]>(
      `/incapacidades/${id}/auditoria-resultados`
    );
    return data;
  },
};
