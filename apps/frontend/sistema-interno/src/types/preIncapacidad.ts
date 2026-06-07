import type { ValidationInconsistenciaRead } from './validationInconsistencia';

export type EstadoPreIncapacidad =
  | 'PENDIENTE'
  | 'PROCESADA'
  | 'RECHAZADA'
  | 'DEVUELTA'
  | 'ERROR';

export interface PreIncapacidadListItem {
  id: string;
  numero_radicacion: number;
  estado: EstadoPreIncapacidad;
  tipo: 'ARL' | 'SALUD';
  empleado_nombres: string;
  empleado_numero_documento: string;
  empresa_nit: string | null;
  empresa_nombre: string | null;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  total_errores: number;
  total_warnings: number;
  created_at: string;
}

export interface PreDocumento {
  id: string;
  tipo_documento: string;
  nombre_original: string;
  estado_subida: 'OK' | 'ERROR';
  created_at: string;
}

export interface PreIncapacidadDetalle {
  id: string;
  numero_radicacion: number;
  estado: EstadoPreIncapacidad;
  tipo: string;
  tipo_enfermedad: string;
  solicitante_correo: string;
  solicitante_nombres: string;
  solicitante_apellidos: string | null;
  solicitante_telefono: string | null;
  empresa_nit: string | null;
  empresa_nombre: string | null;
  empleado_tipo_documento: string;
  empleado_numero_documento: string;
  empleado_nombres: string;
  empleado_apellidos: string | null;
  empleado_email: string | null;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico: string | null;
  nombre_medico: string;
  registro_medico: string;
  ips: string | null;
  valor_dia: string | null;
  error_procesamiento: string | null;
  motivo_devolucion: string | null;
  created_at: string;
  documentos: PreDocumento[];
  validation_inconsistencias: ValidationInconsistenciaRead[];
}

export interface PreIncapacidadUpdate {
  empresa_nit?: string;
  empresa_nombre?: string;
  empleado_tipo_documento?: string;
  empleado_numero_documento?: string;
  empleado_nombres?: string;
  empleado_apellidos?: string;
  empleado_email?: string;
  tipo_enfermedad?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  diagnostico_cie10?: string;
  descripcion_diagnostico?: string;
  nombre_medico?: string;
  registro_medico?: string;
  ips?: string;
  valor_dia?: number;
}

export interface DevolucionRequest {
  motivo: string;
}

export interface DevolucionResponse {
  id: string;
  estado: string;
  motivo_devolucion: string;
  email_enviado: boolean;
}

export interface PromocionResponse {
  success: boolean;
  pre_incapacidad_id: string;
  incapacidad_id: string | null;
  errors: number;
  warnings: number;
  message: string;
}

export interface BandejaFiltros {
  estado?: EstadoPreIncapacidad;
  search?: string;
  skip?: number;
  limit?: number;
}
