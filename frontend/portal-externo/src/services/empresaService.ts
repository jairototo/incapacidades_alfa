import { useQuery } from '@tanstack/react-query';
import api from './api';
import type { EmpresaResponse } from '@/types/api';

/**
 * Hook para buscar empresas (autocomplete)
 * 
 * @param query - Texto de búsqueda (NIT o razón social)
 * @param options - Opciones adicionales de React Query
 * @returns Query result con lista de empresas
 * 
 * @example
 * const { data: empresas, isLoading } = useSearchEmpresas('900123');
 */
export function useSearchEmpresas(query: string) {
  return useQuery({
    queryKey: ['empresas', 'search', query],
    queryFn: async () => {
      const { data } = await api.get<{ items: EmpresaResponse[]; total: number }>(
        '/empresas',
        {
          params: {
            search: query,
            limit: 10,
          },
        }
      );
      return data.items;
    },
    enabled: query.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

/**
 * Hook para obtener una empresa por ID
 * 
 * @param id - ID de la empresa
 * @returns Query result con datos de la empresa
 */
export function useEmpresa(id: string | undefined) {
  return useQuery({
    queryKey: ['empresa', id],
    queryFn: async () => {
      const { data } = await api.get<EmpresaResponse>(`/empresas/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutos
  });
}
