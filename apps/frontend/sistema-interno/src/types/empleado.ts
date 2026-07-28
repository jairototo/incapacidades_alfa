export interface Empleado {
  id: string;
  empresa_id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso: string;
  fecha_retiro?: string;
  salario_base?: number;
  estado: string;
  created_at: string;
  updated_at?: string;
}

/** Shape actually returned by GET /empleados (list) — no empresa reference, see plan's Global Constraints. */
export interface EmpleadoListItem {
  id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  cargo?: string;
  estado: string;
  created_at: string;
}

export interface EmpleadoCreatePayload {
  empresa_id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso: string;
  salario_base?: number;
}

export interface EmpleadoUpdatePayload {
  nombres?: string;
  apellidos?: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso?: string;
  salario_base?: number;
  estado?: string;
}

export interface FilaError {
  fila: number;
  columna?: string;
  mensaje: string;
}

export interface ValidacionMasivaResponse {
  total_filas: number;
  validas: number;
  con_error: number;
  errores: FilaError[];
}

export interface ConfirmacionMasivaResponse {
  total_filas: number;
  insertadas: number;
  con_error: number;
  errores: FilaError[];
}
