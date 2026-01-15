import { z } from 'zod';

/**
 * Schemas de validación para el wizard de radicación de incapacidades
 */

// ============================================================================
// PASO 2: DATOS PERSONALES
// ============================================================================

/**
 * Schema base para datos personales (campos comunes ARL y SALUD)
 */
export const datosPersonalesBaseSchema = z.object({
  tipo_documento: z.enum(['CC', 'CE', 'PA', 'TI', 'NIT'], {
    message: 'Seleccione un tipo de documento',
  }),
  numero_documento: z
    .string()
    .min(6, 'El documento debe tener al menos 6 dígitos')
    .max(15, 'El documento no puede exceder 15 dígitos')
    .regex(/^[0-9]+$/, 'El documento solo puede contener números'),
  nombres: z
    .string()
    .min(3, 'Los nombres deben tener al menos 3 caracteres')
    .max(100, 'Los nombres no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Los nombres solo pueden contener letras'),
  apellidos: z
    .string()
    .min(3, 'Los apellidos deben tener al menos 3 caracteres')
    .max(100, 'Los apellidos no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Los apellidos solo pueden contener letras'),
  email: z
    .string()
    .email('Ingrese un email válido')
    .optional()
    .or(z.literal('')),
  telefono: z
    .string()
    .regex(/^[0-9]{10}$/, 'El teléfono debe tener exactamente 10 dígitos')
    .optional()
    .or(z.literal('')),
});

/**
 * Schema para datos personales ARL (empleado)
 * Incluye campos específicos: empresa, cargo, fecha_ingreso
 */
export const datosPersonalesARLSchema = datosPersonalesBaseSchema.extend({
  tipo: z.literal('ARL'),
  empresa_id: z.string().uuid('Debe seleccionar una empresa válida'),
  empresa_nombre: z.string().optional(), // Para mostrar en UI
  cargo: z
    .string()
    .min(3, 'El cargo debe tener al menos 3 caracteres')
    .max(100, 'El cargo no puede exceder 100 caracteres'),
  fecha_ingreso: z.date({
    message: 'Debe seleccionar la fecha de ingreso',
  }),
});

/**
 * Schema para datos personales SALUD (afiliado)
 * Incluye campos específicos: numero_poliza, tipo_poliza
 */
export const datosPersonalesSaludSchema = datosPersonalesBaseSchema.extend({
  tipo: z.literal('SALUD'),
  numero_poliza: z
    .string()
    .min(5, 'El número de póliza debe tener al menos 5 caracteres')
    .max(50, 'El número de póliza no puede exceder 50 caracteres'),
  tipo_poliza: z.enum(['INDIVIDUAL', 'FAMILIAR', 'COLECTIVA'], {
    message: 'Seleccione un tipo de póliza válido',
  }),
});

/**
 * Union type para datos personales (discriminated union)
 */
export const datosPersonalesSchema = z.discriminatedUnion('tipo', [
  datosPersonalesARLSchema,
  datosPersonalesSaludSchema,
]);

// ============================================================================
// TYPES
// ============================================================================

export type DatosPersonalesBase = z.infer<typeof datosPersonalesBaseSchema>;
export type DatosPersonalesARL = z.infer<typeof datosPersonalesARLSchema>;
export type DatosPersonalesSalud = z.infer<typeof datosPersonalesSaludSchema>;
export type DatosPersonales = z.infer<typeof datosPersonalesSchema>;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Obtiene el schema apropiado según el tipo de incapacidad
 */
export function getDatosPersonalesSchema(tipo: 'ARL' | 'SALUD') {
  return tipo === 'ARL' ? datosPersonalesARLSchema : datosPersonalesSaludSchema;
}

/**
 * Formatea número de teléfono para display (XXX-XXX-XXXX)
 */
export function formatTelefono(telefono: string): string {
  const cleaned = telefono.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return telefono;
}

/**
 * Limpia formato de teléfono para enviar a API (solo números)
 */
export function cleanTelefono(telefono: string): string {
  return telefono.replace(/\D/g, '');
}
