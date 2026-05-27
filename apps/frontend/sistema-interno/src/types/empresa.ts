export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  activa: boolean;
  created_at: string;
  updated_at: string;
}
