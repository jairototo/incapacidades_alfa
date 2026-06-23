import { z } from 'zod';
import { TipoIncapacidad, EstadoIncapacidad, TipoDocumento } from '@/types/enums';

/**
 * Schema de validación para filtros de búsqueda de incapacidades
 */
export const incapacidadFiltrosSchema = z.object({
  numero: z.string().optional(),
  numero_documento: z.string().optional(),
  tipo: z.enum([TipoIncapacidad.ARL, TipoIncapacidad.SALUD]).optional(),
  estado: z.enum([
    EstadoIncapacidad.RADICADA,
    EstadoIncapacidad.EN_AUDITORIA,
    EstadoIncapacidad.PENDIENTE,
    EstadoIncapacidad.CREACION_SINIESTRO,
    EstadoIncapacidad.LIQUIDACION,
    EstadoIncapacidad.LIQUIDACION_PARCIAL,
    EstadoIncapacidad.GLOSADA,
    EstadoIncapacidad.PAGADA,
    EstadoIncapacidad.PAGADA_PARCIAL,
  ]).optional(),
  fecha_inicio_desde: z.string().optional(),
  fecha_inicio_hasta: z.string().optional(),
  empresa_nit: z.string().optional(),
  skip: z.number().int().min(0).optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

export type IncapacidadFiltrosFormData = z.infer<typeof incapacidadFiltrosSchema>;

/**
 * Schema de validación para cambio de estado
 */
export const cambiarEstadoSchema = z.object({
  nuevo_estado: z.enum([
    EstadoIncapacidad.RADICADA,
    EstadoIncapacidad.EN_AUDITORIA,
    EstadoIncapacidad.PENDIENTE,
    EstadoIncapacidad.CREACION_SINIESTRO,
    EstadoIncapacidad.LIQUIDACION,
    EstadoIncapacidad.LIQUIDACION_PARCIAL,
    EstadoIncapacidad.GLOSADA,
    EstadoIncapacidad.PAGADA,
    EstadoIncapacidad.PAGADA_PARCIAL,
  ]),
  observacion: z.string().optional(),
});

export type CambiarEstadoFormData = z.infer<typeof cambiarEstadoSchema>;

/**
 * Schema de validación para datos de empleado (ARL)
 */
export const empleadoSchema = z.object({
  tipo_documento: z.enum([
    TipoDocumento.CEDULA,
    TipoDocumento.PASAPORTE,
    TipoDocumento.CEDULA_EXTRANJERIA,
    TipoDocumento.PERMISO_ESPECIAL,
    TipoDocumento.NIT,
  ]),
  numero_documento: z.string().min(1, 'El número de documento es requerido'),
  nombres: z.string().min(1, 'Los nombres son requeridos'),
  apellidos: z.string().min(1, 'Los apellidos son requeridos'),
  email: z.string().email('Email inválido').optional(),
  telefono: z.string().optional(),
  cargo: z.string().optional(),
});

export type EmpleadoFormData = z.infer<typeof empleadoSchema>;
