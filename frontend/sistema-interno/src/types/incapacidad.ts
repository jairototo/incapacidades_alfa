import { TipoIncapacidad, EstadoIncapacidad, TipoDocumento, EstadoOrdenPago, Prioridad } from './enums';

/**
 * Incapacidad (Response del API)
 */
export interface Incapacidad {
  id: string;
  numero: string;
  tipo: TipoIncapacidad;
  estado: EstadoIncapacidad;
  prioridad: Prioridad;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  diagnostico_descripcion: string;
  valor_total: number;
  observaciones?: string;
  empleado?: Empleado;
  afiliado?: Afiliado;
  empresa?: Empresa;
  orden_pago?: OrdenPago;
  created_at: string;
  updated_at: string;
}

/**
 * Empleado (para incapacidades ARL)
 */
export interface Empleado {
  id: string;
  tipo_documento: TipoDocumento;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  cargo?: string;
  empresa_id: string;
  empresa?: Empresa;
}

/**
 * Afiliado (para incapacidades SALUD)
 */
export interface Afiliado {
  id: string;
  tipo_documento: TipoDocumento;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
}

/**
 * Empresa
 */
export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
}

/**
 * Orden de pago
 */
export interface OrdenPago {
  id: string;
  numero: string;
  estado: EstadoOrdenPago;
  fecha_generacion: string;
  fecha_aprobacion?: string;
  fecha_pago?: string;
  valor_total: number;
  incapacidad_id: string;
}

/**
 * Historial de estados
 */
export interface HistorialEstado {
  id: string;
  estado_anterior?: string;
  estado_nuevo: string;
  observacion?: string;
  cambiado_por: string;
  cambiado_por_nombre: string;
  created_at: string;
}

/**
 * Documento adjunto
 */
export interface Documento {
  id: string;
  nombre_archivo: string;
  tipo_documento: string;
  extension: string;
  tamano_bytes: number;
  mime_type: string;
  uploaded_by: string;
  uploaded_at: string;
}

/**
 * Filtros de búsqueda de incapacidades
 */
export interface IncapacidadFiltros {
  numero?: string;
  numero_documento?: string;
  tipo?: TipoIncapacidad;
  estado?: EstadoIncapacidad;
  fecha_inicio_desde?: string;
  fecha_inicio_hasta?: string;
  empresa_nit?: string;
  skip?: number;
  limit?: number;
}

/**
 * Respuesta paginada
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
