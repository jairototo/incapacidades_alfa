export interface ReglaLabel {
  nombre: string;
  descripcion: string;
}

export const REGLAS_AUDITORIA_LABELS: Record<string, ReglaLabel> = {
  EMPTY_EMPLEADO_NUMERO: {
    nombre: 'Número de empleado vacío',
    descripcion: 'Verifica que el número de documento del empleado esté presente.',
  },
  EMPTY_TIPO_ENFERMEDAD: {
    nombre: 'Tipo de enfermedad vacío',
    descripcion: 'Verifica que el tipo de enfermedad esté especificado (Accidente de Trabajo, Enfermedad Laboral o Accidente de Trayecto).',
  },
  EMPTY_DIAGNOSTICO_CIE10: {
    nombre: 'Diagnóstico CIE-10 vacío',
    descripcion: 'Verifica que el código de diagnóstico CIE-10 esté presente.',
  },
  EMPTY_NOMBRE_MEDICO: {
    nombre: 'Nombre del médico vacío',
    descripcion: 'Verifica que el nombre del médico tratante esté registrado.',
  },
  EMPTY_REGISTRO_MEDICO: {
    nombre: 'Registro médico vacío',
    descripcion: 'Verifica que el número de registro médico del profesional esté presente.',
  },
  INVALID_DATE_RANGE: {
    nombre: 'Rango de fechas inválido',
    descripcion: 'Verifica que la fecha de fin sea posterior a la fecha de inicio de la incapacidad.',
  },
  DIAS_TOTALES_MISMATCH: {
    nombre: 'Coincidencia de días totales',
    descripcion: 'Verifica que los días totales declarados coincidan con el rango de fechas calculado.',
  },
  RETROACTIVE_BEYOND_LIMIT: {
    nombre: 'Retroactividad fuera de límite',
    descripcion: 'Verifica que la fecha de inicio no exceda el límite de retroactividad permitido.',
  },
  DURATION_EXCEEDS_LIMIT: {
    nombre: 'Duración excede el límite',
    descripcion: 'Verifica que la duración de la incapacidad no exceda el límite máximo permitido.',
  },
  SINIESTRO_REQUERIDO: {
    nombre: 'Siniestro requerido',
    descripcion: 'Verifica que la incapacidad ARL tenga un siniestro vinculado antes de ser aprobada.',
  },
  PRIMER_DIA_NO_PAGABLE: {
    nombre: 'Primer día no pagable',
    descripcion: 'Verifica si el primer día de la incapacidad coincide con la fecha del siniestro (el primer día no es pagable).',
  },
};
