/**
 * Enumeraciones del sistema
 * Sincronizado con backend: app/utils/enums.py
 * Usando const objects en lugar de enums para compatibilidad con verbatimModuleSyntax
 */

/**
 * Roles de usuario en el sistema
 */
export const RolUsuario = {
  ADMIN: 'ADMIN',
  AUDITOR: 'AUDITOR',
  APROBADOR: 'APROBADOR',
  EMPRESA: 'EMPRESA',
  EMPLEADO: 'EMPLEADO',
  READONLY: 'READONLY',
} as const;

export type RolUsuario = (typeof RolUsuario)[keyof typeof RolUsuario];

/**
 * Estados de usuario
 */
export const EstadoUsuario = {
  ACTIVO: 'ACTIVO',
  INACTIVO: 'INACTIVO',
  BLOQUEADO: 'BLOQUEADO',
} as const;

export type EstadoUsuario = (typeof EstadoUsuario)[keyof typeof EstadoUsuario];

/**
 * Tipos de incapacidad
 */
export const TipoIncapacidad = {
  ARL: 'ARL',
  SALUD: 'SALUD',
} as const;

export type TipoIncapacidad = (typeof TipoIncapacidad)[keyof typeof TipoIncapacidad];

/**
 * Estados de incapacidad
 */
export const EstadoIncapacidad = {
  RADICADA: 'RADICADA',
  EN_AUDITORIA: 'EN_AUDITORIA',
  PENDIENTE: 'PENDIENTE',
  CREACION_SINIESTRO: 'CREACION_SINIESTRO',
  LIQUIDACION: 'LIQUIDACION',
  LIQUIDACION_PARCIAL: 'LIQUIDACION_PARCIAL',
  GLOSADA: 'GLOSADA',
  EN_PAGO: 'EN_PAGO',
  EN_PAGO_PARCIAL: 'EN_PAGO_PARCIAL',
  PAGADA: 'PAGADA',
  PAGADA_PARCIAL: 'PAGADA_PARCIAL',
} as const;

export type EstadoIncapacidad = (typeof EstadoIncapacidad)[keyof typeof EstadoIncapacidad];

/**
 * Tipos de documento de identidad
 */
export const TipoDocumento = {
  CEDULA: 'CEDULA',
  PASAPORTE: 'PASAPORTE',
  CEDULA_EXTRANJERIA: 'CEDULA_EXTRANJERIA',
  PERMISO_ESPECIAL: 'PERMISO_ESPECIAL',
  NIT: 'NIT',
} as const;

export type TipoDocumento = (typeof TipoDocumento)[keyof typeof TipoDocumento];

/**
 * Estados de orden de pago
 */
export const EstadoOrdenPago = {
  GENERADA: 'GENERADA',
  APROBADA: 'APROBADA',
  RECHAZADA: 'RECHAZADA',
  EN_PROCESO: 'EN_PROCESO',
  PAGADA: 'PAGADA',
  ANULADA: 'ANULADA',
} as const;

export type EstadoOrdenPago = (typeof EstadoOrdenPago)[keyof typeof EstadoOrdenPago];

/**
 * Prioridades
 */
export const Prioridad = {
  BAJA: 'BAJA',
  NORMAL: 'NORMAL',
  ALTA: 'ALTA',
  URGENTE: 'URGENTE',
} as const;

export type Prioridad = (typeof Prioridad)[keyof typeof Prioridad];
