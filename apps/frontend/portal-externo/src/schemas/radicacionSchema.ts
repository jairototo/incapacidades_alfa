import { z } from 'zod';

/**
 * Schemas de validación para el wizard de radicación — 2 pasos, solo ARL.
 * Validaciones únicamente de formato (tipo, longitud, regex).
 * Sin IDs de BD — datos planos de texto.
 */

// ── Paso 1: Solicitante + Empresa + Empleado ────────────────────────────────

export const solicitanteSchema = z.object({
  correo: z
    .string()
    .min(1, 'El correo es obligatorio')
    .email('Ingrese un correo válido'),
  nombres: z
    .string()
    .min(2, 'Los nombres deben tener al menos 2 caracteres')
    .max(100, 'Los nombres no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/, 'Solo se permiten letras'),
  apellidos: z
    .string()
    .max(100, 'Los apellidos no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/, 'Solo se permiten letras')
    .optional()
    .or(z.literal('')),
  telefono: z
    .string()
    .regex(/^\d{7,20}$/, 'El teléfono debe tener entre 7 y 20 dígitos')
    .optional()
    .or(z.literal('')),
});

export const empresaSchema = z
  .object({
    nit: z
      .string()
      .max(20, 'El NIT no puede exceder 20 caracteres')
      .regex(/^\d{6,15}(-\d)?$/, 'Formato de NIT inválido (ej: 900123456-1)')
      .optional()
      .or(z.literal('')),
    nombre: z
      .string()
      .min(2, 'El nombre debe tener al menos 2 caracteres')
      .max(255, 'El nombre no puede exceder 255 caracteres')
      .optional()
      .or(z.literal('')),
  })
  .optional();

export const empleadoSchema = z.object({
  tipo_documento: z.enum(['CC', 'CE', 'PA', 'TI'], {
    message: 'Seleccione un tipo de documento',
  }),
  numero_documento: z
    .string()
    .min(6, 'El documento debe tener al menos 6 dígitos')
    .max(20, 'El documento no puede exceder 20 dígitos')
    .regex(/^\d+$/, 'El documento solo puede contener números'),
  nombres: z
    .string()
    .min(2, 'Los nombres deben tener al menos 2 caracteres')
    .max(100, 'Los nombres no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/, 'Solo se permiten letras'),
  apellidos: z
    .string()
    .max(100, 'Los apellidos no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$/, 'Solo se permiten letras')
    .optional()
    .or(z.literal('')),
  email: z
    .string()
    .email('Ingrese un email válido')
    .optional()
    .or(z.literal('')),
  telefono: z
    .string()
    .regex(/^\d{10}$/, 'El teléfono debe tener exactamente 10 dígitos')
    .optional()
    .or(z.literal('')),
});

export const paso1Schema = z.object({
  solicitante: solicitanteSchema,
  empresa: empresaSchema,
  empleado: empleadoSchema,
});

export type Paso1FormData = z.infer<typeof paso1Schema>;

// ── Paso 2: Datos de la incapacidad ────────────────────────────────────────

export const datosIncapacidadSchema = z
  .object({
    tipo_enfermedad: z.enum(
      ['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'],
      { message: 'Seleccione el tipo de enfermedad' }
    ),
    fecha_inicio: z.date({ error: 'La fecha de inicio es obligatoria' }),
    fecha_fin: z.date({ error: 'La fecha de fin es obligatoria' }),
    dias_totales: z.number().int().positive().optional(),
    diagnostico_cie10: z
      .string()
      .min(1, 'El diagnóstico CIE-10 es obligatorio')
      .max(10, 'Código CIE-10 inválido')
      .regex(/^[A-Z]\d{2}[0-9X]$/, 'Formato CIE-10 inválido (ej: A048, M545 o A09X)'),
    descripcion_diagnostico: z
      .string()
      .max(500, 'La descripción no puede exceder 500 caracteres')
      .optional()
      .or(z.literal('')),
    nombre_medico: z
      .string()
      .min(2, 'El nombre del médico es obligatorio')
      .max(200, 'El nombre no puede exceder 200 caracteres'),
    registro_medico: z
      .string()
      .min(3, 'El registro médico es obligatorio')
      .max(50, 'El registro no puede exceder 50 caracteres')
      .regex(/^[a-zA-Z0-9\-]+$/, 'Solo letras, números y guiones'),
    ips: z
      .string()
      .max(255, 'La IPS no puede exceder 255 caracteres')
      .optional()
      .or(z.literal('')),
    observaciones: z
      .string()
      .max(1000, 'Las observaciones no pueden exceder 1000 caracteres')
      .optional()
      .or(z.literal('')),
  })
  .refine((data) => !data.fecha_fin || !data.fecha_inicio || data.fecha_fin >= data.fecha_inicio, {
    message: 'La fecha de fin debe ser igual o posterior a la fecha de inicio',
    path: ['fecha_fin'],
  });

export type DatosIncapacidadFormData = z.infer<typeof datosIncapacidadSchema>;

// ── Documentos ──────────────────────────────────────────────────────────────

export const documentosSchema = z
  .object({
    incapacidad_medica: z
      .array(z.instanceof(File))
      .min(1, 'Debe adjuntar el documento de incapacidad médica'),
    historia_clinica: z.array(z.instanceof(File)).max(3).optional(),
    soportes_adicionales: z.array(z.instanceof(File)).max(5).optional(),
  })
  .refine(
    (data) => {
      const total = [
        ...(data.incapacidad_medica || []),
        ...(data.historia_clinica || []),
        ...(data.soportes_adicionales || []),
      ].reduce((acc, f) => acc + f.size, 0);
      return total <= 50 * 1024 * 1024; // 50 MB total
    },
    { message: 'El tamaño total de los archivos no puede superar 50 MB', path: ['incapacidad_medica'] }
  );

export type DocumentosFormData = z.infer<typeof documentosSchema>;
