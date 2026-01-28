import { TipoIncapacidad, EstadoIncapacidad } from './enums';

export interface DashboardStats {
  pendientes: number;
  auditadas_hoy: number;
  proximas_vencer: number;
  rechazadas_observadas: number;
}

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
