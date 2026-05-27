import { useQuery } from '@tanstack/react-query';
import { catalogoCIE10Api } from '../api';
import type { SearchCIE10Params } from '@/types/catalogoCIE10';

/**
 * Query Keys para Catálogo CIE-10
 */
export const cie10Keys = {
  all: ['cie10'] as const,
  search: (params: SearchCIE10Params) => ['cie10', 'search', params] as const,
  byCodigo: (codigo: string) => ['cie10', codigo] as const,
  stats: () => ['cie10', 'stats'] as const,
};

/**
 * Hook para buscar códigos CIE-10 (autocomplete)
 */
export function useSearchCIE10(q: string, limit: number = 20) {
  return useQuery({
    queryKey: cie10Keys.search({ q, limit }),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.search({ q, limit });
      return data;
    },
    enabled: q.length >= 2, // Min 2 caracteres
    staleTime: 10 * 60 * 1000, // 10 minutos (datos estáticos)
    retry: 1,
  });
}

/**
 * Hook para obtener código CIE-10 exacto
 */
export function useCIE10ByCodigo(codigo: string, enabled: boolean = true) {
  return useQuery({
    queryKey: cie10Keys.byCodigo(codigo),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.getByCodigo(codigo);
      return data;
    },
    enabled: enabled && !!codigo,
    staleTime: 10 * 60 * 1000,
  });
}

/**
 * Hook para obtener estadísticas del catálogo
 */
export function useCIE10Stats() {
  return useQuery({
    queryKey: cie10Keys.stats(),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.stats();
      return data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutos
  });
}

/**
 * Hook para listar códigos con paginación
 */
export function useListCIE10(skip: number = 0, limit: number = 100) {
  return useQuery({
    queryKey: ['cie10', 'list', skip, limit],
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.list(skip, limit);
      return data;
    },
    staleTime: 10 * 60 * 1000,
  });
}
