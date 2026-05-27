/**
 * Tipos para el módulo de Solicitante
 * Persona que radica una incapacidad (puede ser diferente al empleado/afiliado)
 */

export interface Solicitante {
  id: string;
  correo: string;
  nombres: string;
  apellidos: string;
  telefono: string | null;
  created_at: string;
  updated_at: string;
}

export interface SolicitanteCreate {
  correo: string;
  nombres: string;
  apellidos: string;
  telefono?: string;
}

export interface SolicitanteUpdate {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
}

export interface SearchSolicitanteParams {
  correo: string;
  limit?: number;
}
