import { z } from 'zod';

/**
 * Schema de validación para Solicitante
 */
export const solicitanteSchema = z.object({
  correo: z
    .string()
    .min(5, 'El correo debe tener al menos 5 caracteres')
    .email('Formato de correo inválido')
    .toLowerCase()
    .trim(),
  
  nombres: z
    .string()
    .min(2, 'Los nombres deben tener al menos 2 caracteres')
    .max(100, 'Los nombres no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Solo se permiten letras y espacios')
    .trim()
    .transform(val => val.replace(/\s+/g, ' ')), // Normalizar espacios múltiples
  
  apellidos: z
    .string()
    .min(2, 'Los apellidos deben tener al menos 2 caracteres')
    .max(100, 'Los apellidos no pueden exceder 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Solo se permiten letras y espacios')
    .trim()
    .transform(val => val.replace(/\s+/g, ' ')),
  
  telefono: z
    .string()
    .regex(/^\d{7,20}$/, 'El teléfono debe tener entre 7 y 20 dígitos')
    .optional()
    .or(z.literal('')),
});

/**
 * Tipo inferido del schema
 */
export type SolicitanteFormData = z.infer<typeof solicitanteSchema>;
