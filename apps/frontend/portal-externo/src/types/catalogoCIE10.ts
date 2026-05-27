/**
 * Tipos para el Catálogo CIE-10
 * Clasificación Internacional de Enfermedades, 10ª revisión
 */

export interface CatalogoCIE10 {
  id: string;
  codigo: string;
  descripcion: string;
  created_at: string;
  updated_at: string;
}

export interface SearchCIE10Params {
  q: string;
  limit?: number;
}

export interface CIE10Stats {
  count: number;
}
