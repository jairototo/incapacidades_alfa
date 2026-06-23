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
  PENDIENTE: 'PENDIENTE',
  CREACION_SINIESTRO: 'CREACION_SINIESTRO',
  LIQUIDACION: 'LIQUIDACION',
  LIQUIDACION_PARCIAL: 'LIQUIDACION_PARCIAL',
  GLOSADA: 'GLOSADA',
  PAGADA: 'PAGADA',
  PAGADA_PARCIAL: 'PAGADA_PARCIAL',
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

export interface EmpresaResponse {
  id: string;
  nit: string;
  razon_social: string;
  direccion: string | null;
  telefono: string | null;
  email: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmpleadoResponse {
  id: string;
  empresa_id: string; // ID de la empresa relacionada
  numero_documento: string;
  tipo_documento: TipoDocumento;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string | null;
  cargo: string | null;
  fecha_ingreso: string | null;
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

/**
 * DTO unificado para crear incapacidad (ARL o SALUD)
 * El backend diferencia por la presencia de empleado_id vs afiliado_id
 */
export interface CreateIncapacidadDTO {
  tipo: TipoIncapacidad;
  // Campos específicos ARL
  empleado_id?: string;
  empresa_id?: string;
  siniestro_id?: string;
  tipo_enfermedad?: string; // ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, etc.
  // Campos específicos SALUD
  afiliado_id?: string;
  subtipo?: string; // ENFERMEDAD_GENERAL, MATERNIDAD, etc.
  // Campos comunes
  fecha_inicio: string; // ISO date (YYYY-MM-DD)
  fecha_fin: string; // ISO date (YYYY-MM-DD)
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico?: string;
  valor_dia: number;
  ips?: string;
  eps?: string;
  observaciones?: string;
  // NUEVOS: Solicitante y Médico
  solicitante_id?: string;
  nombre_medico?: string;
  registro_medico?: string;
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
 * DTO para upload de documentos asociados a incapacidad
 */
export interface UploadDocumentoDTO {
  incapacidad_id: string;
  tipo_documento: TipoDocumentoArchivo;
  archivo: File;
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
