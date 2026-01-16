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
  id: z.string().uuid('Debe seleccionar un empleado válido'),
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

// ============================================================================
// PASO 3: DATOS INCAPACIDAD
// ============================================================================

/**
 * Schema base para datos de incapacidad (campos comunes ARL y SALUD)
 */
export const datosIncapacidadBaseSchema = z.object({
  fecha_inicio: z.date({
    message: 'Debe seleccionar la fecha de inicio',
  }),
  fecha_fin: z.date({
    message: 'Debe seleccionar la fecha de fin',
  }),
  dias_totales: z.number().int().positive('Los días totales deben ser un número positivo'),
  diagnostico_cie10: z
    .string()
    .max(10, 'El código CIE-10 no puede exceder 10 caracteres')
    .regex(/^[A-Z]\d{2}(\.\d{1,2})?$/, 'Formato CIE-10 inválido. Ejemplo: A00, A00.1')
    .optional()
    .or(z.literal('')),
  descripcion_diagnostico: z
    .string()
    .max(500, 'La descripción no puede exceder 500 caracteres')
    .optional()
    .or(z.literal('')),
  ips: z
    .string()
    .max(255, 'El nombre de la IPS no puede exceder 255 caracteres')
    .optional()
    .or(z.literal('')),
  eps: z
    .string()
    .max(255, 'El nombre de la EPS no puede exceder 255 caracteres')
    .optional()
    .or(z.literal('')),
  valor_dia: z
    .number()
    .positive('El valor por día debe ser un número positivo')
    .optional(),
}).refine(
  (data) => data.fecha_fin >= data.fecha_inicio,
  {
    message: 'La fecha de fin debe ser igual o posterior a la fecha de inicio',
    path: ['fecha_fin'],
  }
).refine(
  (data) => data.dias_totales <= 180,
  {
    message: 'El período de incapacidad no puede exceder 180 días',
    path: ['dias_totales'],
  }
);

/**
 * Schema para datos de incapacidad ARL
 * Incluye campo específico: tipo_enfermedad
 */
export const datosIncapacidadARLSchema = datosIncapacidadBaseSchema.extend({
  tipo: z.literal('ARL'),
  tipo_enfermedad: z.enum(['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'], {
    message: 'Seleccione un tipo de enfermedad válido',
  }),
});

/**
 * Schema para datos de incapacidad SALUD
 * Incluye campo específico: subtipo
 */
export const datosIncapacidadSaludSchema = datosIncapacidadBaseSchema.extend({
  tipo: z.literal('SALUD'),
  subtipo: z.enum(['ENFERMEDAD_GENERAL', 'MATERNIDAD', 'LICENCIA'], {
    message: 'Seleccione un subtipo válido',
  }),
});

/**
 * Union type para datos de incapacidad (discriminated union)
 */
export const datosIncapacidadSchema = z.discriminatedUnion('tipo', [
  datosIncapacidadARLSchema,
  datosIncapacidadSaludSchema,
]);

// ============================================================================
// TYPES - PASO 3
// ============================================================================

export type DatosIncapacidadBase = z.infer<typeof datosIncapacidadBaseSchema>;
export type DatosIncapacidadARL = z.infer<typeof datosIncapacidadARLSchema>;
export type DatosIncapacidadSalud = z.infer<typeof datosIncapacidadSaludSchema>;

// ========================================
// PASO 4: DOCUMENTOS
// ========================================

export const documentosSchema = z.object({
  incapacidad_medica: z
    .array(z.instanceof(File))
    .min(1, 'Debe cargar al menos un documento de incapacidad médica')
    .max(1, 'Solo se permite un documento de incapacidad médica'),
  historia_clinica: z
    .array(z.instanceof(File))
    .max(3, 'Máximo 3 archivos de historia clínica')
    .optional()
    .default([]),
  soportes_adicionales: z
    .array(z.instanceof(File))
    .max(5, 'Máximo 5 archivos de soportes adicionales')
    .optional()
    .default([]),
}).refine(
  (data) => {
    // Validar tamaño total (no más de 50 MB)
    const totalSize = [
      ...data.incapacidad_medica,
      ...(data.historia_clinica || []),
      ...(data.soportes_adicionales || []),
    ].reduce((acc, file) => acc + file.size, 0);
    
    const MAX_TOTAL_SIZE = 50 * 1024 * 1024; // 50 MB
    return totalSize <= MAX_TOTAL_SIZE;
  },
  {
    message: 'El tamaño total de todos los archivos no puede exceder 50 MB',
  }
);

export type DocumentosFormData = z.infer<typeof documentosSchema>;
export type DatosIncapacidad = z.infer<typeof datosIncapacidadSchema>;

// ============================================================================
// HELPER FUNCTIONS - PASO 3
// ============================================================================

/**
 * Obtiene el schema apropiado según el tipo de incapacidad
 */
export function getDatosIncapacidadSchema(tipo: 'ARL' | 'SALUD') {
  return tipo === 'ARL' ? datosIncapacidadARLSchema : datosIncapacidadSaludSchema;
}
