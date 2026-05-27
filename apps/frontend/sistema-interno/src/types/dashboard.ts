import { TipoIncapacidad, EstadoIncapacidad } from './enums';

export interface DashboardStats {
  pendientes: number;
  auditadas_hoy: number;
  proximas_vencer: number;
  rechazadas_observadas: number;
}

// ========== TIPOS PARA ESTADÍSTICAS EXTENDIDAS ==========

export interface TopEmpresaStats {
  empresa_id: string;
  razon_social: string;
  nit: string;
  total_incapacidades: number;
  valor_total: number;
}

export interface TopCIE10Stats {
  codigo_cie10: string;
  descripcion: string;
  total_incapacidades: number;
  porcentaje: number;
}

export interface TopEmpleadoStats {
  empleado_id: string;
  nombres: string;
  apellidos: string;
  numero_documento: string;
  empresa_razon_social: string;
  total_dias: number;
  total_incapacidades: number;
}

export interface DistribucionEstados {
  estado: EstadoIncapacidad;
  cantidad: number;
  porcentaje: number;
}

export interface DistribucionTipos {
  tipo: TipoIncapacidad;
  cantidad: number;
  valor_total: number;
  promedio_dias: number;
}

export interface TendenciaMensual {
  mes: string; // formato: "2026-01"
  radicadas: number;
  aprobadas: number;
  rechazadas: number;
  valor_total_aprobado: number;
}

export interface ExtendedStats extends DashboardStats {
  top_empresas: TopEmpresaStats[];
  top_diagnosticos: TopCIE10Stats[];
  top_empleados: TopEmpleadoStats[];
  distribucion_estados: DistribucionEstados[];
  distribucion_tipos: DistribucionTipos[];
  tendencia_mensual: TendenciaMensual[];
  fecha_calculo: string;
  filtros_aplicados?: Record<string, any>;
}

export interface GetExtendedStatsParams {
  empresa_id?: string;
  tipo?: TipoIncapacidad;
  fecha_desde?: Date;
  fecha_hasta?: Date;
  top_limit?: number;
}

// ========== TIPOS ORIGINALES ==========

export interface FilterState {
  tipo: TipoIncapacidad | 'TODAS';
  estado: EstadoIncapacidad | 'TODOS';
  fecha_desde: Date | null;
  fecha_hasta: Date | null;
  empresa_id: string | null;
  search: string;
}

export interface GetIncapacidadesParams extends FilterState {
  skip: number;
  limit: number;
  order_by?: string;
  direction?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
