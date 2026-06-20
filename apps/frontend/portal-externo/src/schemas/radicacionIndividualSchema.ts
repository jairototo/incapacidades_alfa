import { z } from 'zod';

export const radicacionIndividualSchema = z
  .object({
    empleado_id: z.string().uuid('Seleccione un empleado'),
    prorroga: z.boolean(),
    tipo_enfermedad: z.enum(['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'], {
      error: 'Seleccione el tipo de enfermedad',
    }),
    fecha_inicio: z.date({ error: 'La fecha de inicio es obligatoria' }),
    fecha_fin: z.date({ error: 'La fecha de fin es obligatoria' }),
    diagnostico_cie10: z.string().regex(/^[A-Z]\d{2}[0-9X]$/, 'Formato CIE-10 inválido (ej: A048, M545 o A09X)'),
    descripcion_diagnostico: z.string().max(500).optional().or(z.literal('')),
    nombre_medico: z.string().min(2, 'El nombre del médico es obligatorio').max(200),
    registro_medico: z
      .string()
      .min(3)
      .max(50)
      .regex(/^[a-zA-Z0-9\-]+$/, 'Solo letras, números y guiones'),
    ips: z.string().max(255).optional().or(z.literal('')),
    observaciones: z.string().max(1000).optional().or(z.literal('')),
  })
  .refine((d) => !d.fecha_fin || !d.fecha_inicio || d.fecha_fin >= d.fecha_inicio, {
    message: 'La fecha de fin debe ser igual o posterior a la fecha de inicio',
    path: ['fecha_fin'],
  });

export type RadicacionIndividualFormData = z.infer<typeof radicacionIndividualSchema>;
