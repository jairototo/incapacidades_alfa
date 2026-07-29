export interface UsuarioGenerado {
  username: string;
  password: string;
}

export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  estado: string;
  email_contacto?: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
  created_at: string;
  updated_at?: string;
}

/** Shape actually returned by GET /empresas (list) — see backend EmpresaListItem, apps/backend/app/schemas/empresa.py. */
export interface EmpresaListItem {
  id: string;
  nit: string;
  razon_social: string;
  estado: string;
  ciudad?: string;
  created_at: string;
}

export interface EmpresaCreatePayload {
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
}

export interface EmpresaCreateResponse extends Empresa {
  usuario_generado: UsuarioGenerado;
}

export interface EmpresaUpdatePayload {
  razon_social?: string;
  email_contacto?: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
  estado?: string;
}

export interface RegenerarPasswordResponse {
  message: string;
  username: string;
  password: string;
}

export interface EmpresaTopItem {
  empresa_id: string;
  razon_social: string;
  nit: string;
  total_radicadas: number;
}

export interface TendenciaMensualItem {
  periodo: string;
  total: number;
}

export interface AnaliticaEmpresasResponse {
  top_empresas: EmpresaTopItem[];
  tendencia_mensual: TendenciaMensualItem[];
}
