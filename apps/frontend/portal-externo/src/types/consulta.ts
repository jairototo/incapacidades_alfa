/**
 * Tipos TypeScript para el módulo de Consulta de Incapacidades.
 * 
 * Estos tipos mapean exactamente con los schemas del backend:
 * - ConsultaIncapacidadPublicResponse
 * - PresignedUrlResponse
 */

// ========== TIPOS BASE (ENUMS) ==========

/**
 * Tipo de incapacidad: ARL (Accidente de trabajo) o SALUD (Enfermedad general).
 */
export type TipoIncapacidad = 'ARL' | 'SALUD';

/**
 * Estados posibles de una incapacidad en el workflow.
 */
export type EstadoIncapacidad =
  | 'RADICADA'
  | 'EN_AUDITORIA'
  | 'OBSERVADA'
  | 'APROBADA'
  | 'RECHAZADA'
  | 'EN_PAGO'
  | 'PAGADA'
  | 'CANCELADA';

/**
 * Tipos de documento de identidad.
 */
export type TipoDocumento = 'CC' | 'CE' | 'TI' | 'PASAPORTE' | 'PEP';

/**
 * Tipos de documentos adjuntos/archivos.
 */
export type TipoDocumentoArchivo =
  | 'INCAPACIDAD_MEDICA'
  | 'CEDULA'
  | 'HISTORIA_CLINICA'
  | 'SOPORTE_PAGO'
  | 'OTROS';

// ========== INTERFACES PRINCIPALES ==========

/**
 * Representa un cambio de estado en el historial de la incapacidad.
 * Versión simplificada para consulta pública (sin datos sensibles).
 */
export interface HistorialEstadoSimple {
  /** Estado al que cambió */
  estado: EstadoIncapacidad;
  
  /** Fecha y hora del cambio (ISO string) */
  fecha_cambio: string;
  
  /** Observaciones del auditor (solo visible si estado es OBSERVADA) */
  observaciones: string | null;
}

/**
 * Representa un documento adjunto público.
 * Solo incluye documentos descargables sin autenticación.
 */
export interface DocumentoPublico {
  /** ID único del documento */
  id: string;
  
  /** Nombre del archivo con extensión */
  nombre_archivo: string;
  
  /** Tipo de documento */
  tipo_documento: TipoDocumentoArchivo;
  
  /** Tamaño del archivo en kilobytes */
  tamanio_kb: number;
  
  /** Fecha de carga del documento (ISO string) */
  fecha_upload: string;
}

/**
 * Response completo de la consulta pública de incapacidad.
 * Mapea con ConsultaIncapacidadPublicResponse del backend.
 */
export interface ConsultaIncapacidadResponse {
  /** Número de radicación único (ej: INC-ARL-20260117-0001) */
  numero: string;
  
  /** Estado actual de la incapacidad */
  estado: EstadoIncapacidad;
  
  /** Tipo de incapacidad */
  tipo: TipoIncapacidad;
  
  /** Fecha de inicio de la incapacidad (ISO date) */
  fecha_inicio: string;
  
  /** Fecha de fin de la incapacidad (ISO date) */
  fecha_fin: string;
  
  /** Total de días de incapacidad */
  dias_totales: number;
  
  /** Nombre completo del empleado/afiliado (sanitizado) */
  nombre_completo: string;
  
  /** Tipo de documento de identidad */
  tipo_documento: string;
  
  /** Código CIE-10 del diagnóstico */
  diagnostico_cie10: string;
  
  /** Descripción del diagnóstico */
  descripcion_diagnostico: string;
  
  /** EPS o entidad de salud */
  eps: string | null;
  
  /** Historial completo de cambios de estado */
  historial_estados: HistorialEstadoSimple[];
  
  /** Lista de documentos públicos descargables */
  documentos: DocumentoPublico[];
  
  /** Observaciones públicas (solo si estado es OBSERVADA) */
  observaciones_publicas: string | null;
  
  /** Fecha de creación del registro (ISO datetime) */
  created_at: string;
  
  /** Fecha de última actualización (ISO datetime) */
  updated_at: string;
}

/**
 * Response de la generación de URL pre-firmada para descarga de documento.
 * Mapea con PresignedUrlResponse del backend.
 */
export interface PresignedUrlResponse {
  /** URL pre-firmada para descargar el documento (válida 15 minutos) */
  url: string;
  
  /** Tiempo de expiración en segundos (900 = 15 minutos) */
  expires_in: number;
  
  /** Nombre del archivo a descargar */
  nombre_archivo: string;
  
  /** Tipo de documento */
  tipo_documento: TipoDocumentoArchivo;
}

// ========== TIPOS PARA FORMULARIOS ==========

/**
 * Datos del formulario de consulta por número de radicación.
 */
export interface ConsultaPorNumeroForm {
  /** Número de radicación (ej: INC-ARL-20260117-0001) */
  numero: string;
}

/**
 * Datos del formulario de consulta por documento de identidad.
 */
export interface ConsultaPorDocumentoForm {
  /** Número de documento de identidad */
  documento: string;
  
  /** Tipo de documento */
  tipo_documento: TipoDocumento;
}

/**
 * Union type de los dos tipos de formulario de consulta.
 */
export type ConsultaForm = ConsultaPorNumeroForm | ConsultaPorDocumentoForm;
