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
  tipo_documento: string;
  nombre_original: string; // nombre_original
  extension: string; // mime_type
  tamano_bytes: number;
  mime_type: string;
  uploaded_by: string;
  created_at: string; // created_at
}

/**
 * Filtros de búsqueda de incapacidades
 */
export interface IncapacidadFiltros {
  numero?: string;
  numero_documento?: string;
  empleado_documento?: string;
  afiliado_documento?: string;
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

/**
 * Datos aprobados en auditoría (relación 1:1 con Incapacidad)
 */
export interface AuditoriaDatosAprobados {
  id: string;
  incapacidad_id: string;
  fecha_inicio_aprobada: string;
  fecha_fin_aprobada: string;
  dias_aprobados: number;
  cie10_aprobado: string;
  diagnostico_aprobado: string;
  observacion_auditoria: string;
  auditado_por_id: string;
  fecha_auditoria: string;
  created_at: string;
  updated_at: string;
}

/**
 * Request para auditar incapacidad con soporte para aprobación parcial
 * POST /api/v1/incapacidades/{id}/auditar
 */
export interface IncapacidadAuditarRequest {
  accion: 'SOLICITAR_INFORMACION' | 'APROBAR_PARA_PAGO' | 'APROBAR_PARA_PAGO_PARCIAL' | 'RECHAZAR';
  observaciones: string;
  // Campos modificables (solo para aprobación parcial)
  fecha_inicio_aprobada?: string;
  fecha_fin_aprobada?: string;
  dias_aprobados?: number;
  cie10_aprobado?: string;
  diagnostico_aprobado?: string;
}

/**
 * Request para rechazar incapacidad
 * POST /api/v1/incapacidades/{id}/rechazar
 */
export interface IncapacidadRechazarRequest {
  motivo: string; // mínimo 10 caracteres
}

/**
 * Request para consulta pública
 * GET /api/v1/incapacidades/consultar
 */
export interface ConsultaPublicaParams {
  numero?: string;
  documento?: string;
  tipo_documento?: string;
}

/**
 * Response con URL pre-firmada para descarga de documento
 */
export interface PresignedUrlResponse {
  url: string;
  expires_in: number;
  nombre_archivo: string;
  tipo_documento: string;
}

/**
 * Incapacidad Pendiente (para módulo de pendientes)
 * Extiende Incapacidad con campos calculados de antigüedad
 */
export interface IncapacidadPendiente extends Incapacidad {
  dias_desde_radicacion: number;
  dias_en_estado_actual: number;
}

/**
 * Filtros para módulo de pendientes
 */
export interface FiltrosPendientes {
  tipo?: TipoIncapacidad;
  prioridad?: Prioridad;
  empresa_nit?: string;
  dias_antiguedad_min?: number;
  skip?: number;
  limit?: number;
}
