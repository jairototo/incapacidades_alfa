import { useQuery } from '@tanstack/react-query';
import api from './api';
import type { AfiliadoResponse } from '@/types/api';

/**
 * Hook para buscar afiliado por número de documento
 * Útil para autocomplete de datos personales
 * 
 * @param documento - Número de documento
 * @param options - Opciones adicionales (enabled)
 * @returns Query result con datos del afiliado
 * 
 * @example
 * const documento = watch('numero_documento');
 * const { data: afiliado } = useSearchAfiliado(documento, { 
 *   enabled: documento.length >= 6 
 * });
 */
export function useSearchAfiliado(
  documento: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['afiliado', 'search', documento],
    queryFn: async () => {
      const { data } = await api.get<{ items: AfiliadoResponse[]; total: number }>(
        '/afiliados',
        {
          params: {
            documento,
          },
        }
      );
      // Retornar primer resultado si existe
      return data.items[0] || null;
    },
    enabled: options?.enabled ?? false,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

/**
 * Hook para obtener un afiliado por ID
 * 
 * @param id - ID del afiliado
 * @returns Query result con datos del afiliado
 */
export function useAfiliado(id: string | undefined) {
  return useQuery({
    queryKey: ['afiliado', id],
    queryFn: async () => {
      const { data } = await api.get<AfiliadoResponse>(`/afiliados/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutos
  });
}
