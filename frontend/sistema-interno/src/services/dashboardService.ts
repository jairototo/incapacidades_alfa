import api from '@/lib/api';
import type { 
  GetIncapacidadesParams, 
  PaginatedResponse, 
  DashboardStats 
} from '@/types/dashboard';
import type { Incapacidad } from '@/types/incapacidad';

/**
 * Servicio para el Dashboard de Auditoría
 */
class DashboardService {
  private readonly baseUrl = '/incapacidades';

  /**
   * Obtener lista de incapacidades con filtros y paginación
   */
  async getIncapacidades(params: GetIncapacidadesParams): Promise<PaginatedResponse<Incapacidad>> {
    const queryParams: Record<string, string | number> = {
      skip: params.skip,
      limit: params.limit,
    };

    // Aplicar filtros opcionales
    if (params.tipo && params.tipo !== 'TODAS') {
      queryParams.tipo = params.tipo;
    }

    if (params.estado && params.estado !== 'TODOS') {
      queryParams.estado = params.estado;
    }

    if (params.fecha_desde) {
      queryParams.fecha_desde = params.fecha_desde.toISOString().split('T')[0];
    }

    if (params.fecha_hasta) {
      queryParams.fecha_hasta = params.fecha_hasta.toISOString().split('T')[0];
    }

    if (params.empresa_id) {
      queryParams.empresa_id = params.empresa_id;
    }

    if (params.search) {
      queryParams.search = params.search;
    }

    if (params.order_by) {
      queryParams.order_by = params.order_by;
    }

    if (params.direction) {
      queryParams.direction = params.direction;
    }

    const { data } = await api.get<PaginatedResponse<Incapacidad>>(this.baseUrl, {
      params: queryParams,
    });

    return data;
  }

  /**
   * Obtener estadísticas del dashboard
   * Si el endpoint no existe en backend, calcular desde la lista completa
   */
  async getStats(): Promise<DashboardStats> {
    try {
      // Intentar obtener stats desde endpoint específico
      const { data } = await api.get<DashboardStats>(`${this.baseUrl}/stats`);
      console.log('Stats obtenidas desde backend', data );
      return data;
    } catch (error) {
      // Si no existe el endpoint, calcular en frontend
      console.warn('Endpoint /stats no disponible, calculando en frontend');
      return this.calculateStatsFromList();
    }
  }

  /**
   * Calcular estadísticas desde la lista completa de incapacidades
   * Fallback si el backend no proporciona endpoint de stats
   */
  private async calculateStatsFromList(): Promise<DashboardStats> {
    // Obtener todas las incapacidades (límite alto para obtener todas)
    const { data } = await api.get<PaginatedResponse<Incapacidad>>(this.baseUrl, {
      params: { skip: 0, limit: 1000 },
    });

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    const stats: DashboardStats = {
      pendientes: 0,
      auditadas_hoy: 0,
      proximas_vencer: 0,
      rechazadas_observadas: 0,
    };

    data.items.forEach((incapacidad) => {
      // Pendientes: RADICADA + EN_AUDITORIA
      if (incapacidad.estado === 'RADICADA' || incapacidad.estado === 'EN_AUDITORIA') {
        stats.pendientes++;

        // Próximas a vencer: más de 3 días desde radicación
        const fechaRadicacion = new Date(incapacidad.created_at);
        const diasTranscurridos = Math.floor(
          (hoy.getTime() - fechaRadicacion.getTime()) / (1000 * 60 * 60 * 24)
        );

        if (diasTranscurridos > 3) {
          stats.proximas_vencer++;
        }
      }

      // Auditadas hoy: cambio a estado final hoy
      if (
        incapacidad.estado === 'APROBADA' ||
        incapacidad.estado === 'RECHAZADA' ||
        incapacidad.estado === 'OBSERVADA'
      ) {
        const fechaActualizacion = new Date(incapacidad.updated_at);
        fechaActualizacion.setHours(0, 0, 0, 0);

        if (fechaActualizacion.getTime() === hoy.getTime()) {
          stats.auditadas_hoy++;
        }

        // Rechazadas/Observadas
        if (incapacidad.estado === 'RECHAZADA' || incapacidad.estado === 'OBSERVADA') {
          stats.rechazadas_observadas++;
        }
      }
    });

    return stats;
  }
}

export const dashboardService = new DashboardService();
export default dashboardService;
