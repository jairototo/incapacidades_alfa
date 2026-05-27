/**
 * Schemas de validación Zod para formularios de consulta.
 * 
 * Define reglas de validación estrictas con mensajes en español para:
 * - Consulta por número de radicación
 * - Consulta por documento de identidad
 * 
 * Los schemas se usan con React Hook Form para validación en tiempo real.
 */

import { z } from 'zod';

/**
 * Tipos de documento válidos para consulta.
 * Sincronizado con el enum del backend.
 */
export const TIPOS_DOCUMENTO = ['CC', 'CE', 'TI', 'PASAPORTE', 'PEP'] as const;

/**
 * Schema de validación para consulta por número de radicación.
 * 
 * Formato esperado: INC-{TIPO}-{FECHA}-{CONSECUTIVO}
 * - TIPO: ARL o SALUD (3-5 letras mayúsculas)
 * - FECHA: 8 dígitos (YYYYMMDD)
 * - CONSECUTIVO: 4 dígitos
 * 
 * Ejemplos válidos:
 * - INC-ARL-20260117-0001
 * - INC-SALUD-20251225-1234
 * 
 * @example
 * ```typescript
 * const formData = consultaPorNumeroSchema.parse({ numero: 'INC-ARL-20260117-0001' });
 * // ✅ { numero: 'INC-ARL-20260117-0001' }
 * 
 * consultaPorNumeroSchema.parse({ numero: 'INC-123' });
 * // ❌ ZodError: Formato de número de radicación inválido
 * ```
 */
export const consultaPorNumeroSchema = z.object({
  numero: z
    .string({
      message: 'El número de radicación es obligatorio',
    })
    .min(1, 'El número de radicación no puede estar vacío')
    .regex(
      /^INC-[A-Z]+-\d{8}-\d{4}$/,
      'Formato inválido. Ejemplo: INC-ARL-20260117-0001'
    )
    .transform((val) => val.trim().toUpperCase()),
});

/**
 * Schema de validación para consulta por documento de identidad.
 * 
 * Validaciones:
 * - Documento: 6-20 caracteres alfanuméricos
 * - Tipo de documento: Uno de los tipos válidos (CC, CE, TI, PASAPORTE, PEP)
 * 
 * @example
 * ```typescript
 * const formData = consultaPorDocumentoSchema.parse({
 *   documento: '1234567890',
 *   tipo_documento: 'CC'
 * });
 * // ✅ { documento: '1234567890', tipo_documento: 'CC' }
 * 
 * consultaPorDocumentoSchema.parse({
 *   documento: '123',
 *   tipo_documento: 'INVALIDO'
 * });
 * // ❌ ZodError: Múltiples errores (documento corto, tipo inválido)
 * ```
 */
export const consultaPorDocumentoSchema = z.object({
  documento: z
    .string({
      message: 'El número de documento es obligatorio',
    })
    .min(6, 'El documento debe tener al menos 6 caracteres')
    .max(20, 'El documento no puede tener más de 20 caracteres')
    .regex(
      /^[A-Z0-9]+$/i,
      'El documento solo puede contener letras y números'
    )
    .transform((val) => val.trim()),

  tipo_documento: z.enum(TIPOS_DOCUMENTO, {
    message: 'El tipo de documento es obligatorio',
  }),
});

/**
 * Tipos inferidos de los schemas.
 * Se exportan para usar en React Hook Form.
 */
export type ConsultaPorNumeroFormData = z.infer<typeof consultaPorNumeroSchema>;
export type ConsultaPorDocumentoFormData = z.infer<typeof consultaPorDocumentoSchema>;
