import { z } from 'zod';

/**
 * Schema de validación para login
 */
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, 'El usuario debe tener al menos 3 caracteres')
    .max(50, 'El usuario no puede exceder 50 caracteres'),
  password: z
    .string()
    .min(6, 'La contraseña debe tener al menos 6 caracteres')
    .max(100, 'La contraseña no puede exceder 100 caracteres'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Schema de validación para cambio de contraseña
 */
export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'La contraseña actual es requerida'),
    new_password: z
      .string()
      .min(8, 'La nueva contraseña debe tener al menos 8 caracteres')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'La contraseña debe contener al menos una mayúscula, una minúscula y un número'
      ),
    confirm_password: z.string().min(1, 'Confirme la nueva contraseña'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Las contraseñas no coinciden',
    path: ['confirm_password'],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;
