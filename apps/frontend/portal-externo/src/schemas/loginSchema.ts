import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'El usuario es obligatorio'),
  password: z.string().min(1, 'La contraseña es obligatoria'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
