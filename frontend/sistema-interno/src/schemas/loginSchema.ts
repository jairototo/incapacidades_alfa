import { z } from 'zod';

/**
 * Schema de validación para el formulario de login
 * Usado por LoginForm con React Hook Form + zodResolver
 */
export const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'El usuario es requerido')
    .min(3, 'El usuario debe tener al menos 3 caracteres')
    .email('Debe ser un email válido'),
  
  password: z
    .string()
    .min(1, 'La contraseña es requerida')
    .min(6, 'La contraseña debe tener al menos 6 caracteres'),
});

/**
 * Tipo inferido del schema para TypeScript
 */
export type LoginFormData = z.infer<typeof loginSchema>;
