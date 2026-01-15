/**
 * Enumeraciones compartidas con el backend
 */

export const TipoIncapacidad = {
  ARL: 'ARL',
  SALUD: 'SALUD',
} as const;
export type TipoIncapacidad = typeof TipoIncapacidad[keyof typeof TipoIncapacidad];

export const EstadoIncapacidad = {
  RADICADA: 'RADICADA',
  EN_AUDITORIA: 'EN_AUDITORIA',
  OBSERVADA: 'OBSERVADA',
  APROBADA: 'APROBADA',
  RECHAZADA: 'RECHAZADA',
  EN_PAGO: 'EN_PAGO',
  PAGADA: 'PAGADA',
  ANULADA: 'ANULADA',
} as const;
export type EstadoIncapacidad = typeof EstadoIncapacidad[keyof typeof EstadoIncapacidad];

export const TipoDocumento = {
  CEDULA: 'CEDULA',
  PASAPORTE: 'PASAPORTE',
  CEDULA_EXTRANJERIA: 'CEDULA_EXTRANJERIA',
} as const;
export type TipoDocumento = typeof TipoDocumento[keyof typeof TipoDocumento];

export const TipoDocumentoArchivo = {
  INCAPACIDAD_MEDICA: 'INCAPACIDAD_MEDICA',
  HISTORIA_CLINICA: 'HISTORIA_CLINICA',
  SOPORTE_ARL: 'SOPORTE_ARL',
  DOCUMENTO_IDENTIDAD: 'DOCUMENTO_IDENTIDAD',
  OTRO: 'OTRO',
} as const;
export type TipoDocumentoArchivo = typeof TipoDocumentoArchivo[keyof typeof TipoDocumentoArchivo];

/**
 * Interfaces de respuesta de la API
 */

export interface EmpleadoResponse {
  id: string;
  numero_documento: string;
  tipo_documento: TipoDocumento;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string | null;
  cargo: string | null;
  created_at: string;
  updated_at: string;
}

export interface AfiliadoResponse {
  id: string;
  numero_poliza: string;
  numero_documento: string;
  tipo_documento: TipoDocumento;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string | null;
  fecha_nacimiento: string;
  created_at: string;
  updated_at: string;
}

export interface IncapacidadResponse {
  id: string;
  numero: string;
  tipo: TipoIncapacidad;
  estado: EstadoIncapacidad;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico: string | null;
  valor_dia: number;
  valor_total: number;
  observaciones: string | null;
  empleado?: EmpleadoResponse;
  afiliado?: AfiliadoResponse;
  created_at: string;
  updated_at: string;
}

export interface DocumentoResponse {
  id: string;
  tipo_documento: TipoDocumentoArchivo;
  nombre_archivo: string;
  mime_type: string;
  tamanio_bytes: number;
  created_at: string;
}

/**
 * Interfaces de creación (DTOs)
 */

export interface CreateEmpleadoDTO {
  numero_documento: string;
  tipo_documento: TipoDocumento;
  nombres: string;
  apellidos: string;
  email: string;
  telefono?: string;
  cargo?: string;
}

export interface CreateAfiliadoDTO {
  numero_poliza: string;
  numero_documento: string;
  tipo_documento: TipoDocumento;
  nombres: string;
  apellidos: string;
  email: string;
  telefono?: string;
  fecha_nacimiento: string;
}

export interface CreateIncapacidadARLDTO {
  empleado_id: string;
  empresa_id: string;
  siniestro_id?: string;
  fecha_inicio: string;
  fecha_fin: string;
  diagnostico_cie10: string;
  descripcion_diagnostico?: string;
  valor_dia: number;
  observaciones?: string;
}

export interface CreateIncapacidadSaludDTO {
  afiliado_id: string;
  fecha_inicio: string;
  fecha_fin: string;
  diagnostico_cie10: string;
  descripcion_diagnostico?: string;
  valor_dia: number;
  observaciones?: string;
}

/**
 * Tipos de respuesta de la API
 */

export interface APIResponse<T> {
  success: boolean;
  data: T;
  meta?: {
    timestamp: string;
    request_id: string;
  };
}

export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Array<{
      field: string;
      message: string;
    }>;
  };
  meta?: {
    timestamp: string;
    request_id: string;
  };
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> extends APIResponse<T[]> {
  pagination: PaginationMeta;
}

/**
 * Parámetros de consulta
 */

export interface QueryParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  order?: 'asc' | 'desc';
  [key: string]: string | number | boolean | undefined;
}
