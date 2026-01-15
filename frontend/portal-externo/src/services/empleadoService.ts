import { useQuery } from '@tanstack/react-query';
import api from './api';
import type { EmpleadoResponse } from '@/types/api';

/**
 * Hook para buscar empleado por número de documento
 * Útil para autocomplete de datos personales
 * 
 * @param documento - Número de documento
 * @param options - Opciones adicionales (enabled)
 * @returns Query result con datos del empleado
 * 
 * @example
 * const documento = watch('numero_documento');
 * const { data: empleado } = useSearchEmpleado(documento, { 
 *   enabled: documento.length >= 6 
 * });
 */
export function useSearchEmpleado(
  documento: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['empleado', 'search', documento],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoResponse[]>(
        '/empleados',
        {
          params: {
            documento,
          },
        }
      );
      // La API devuelve directamente un array de empleados
      return data[0] || null;
    },
    enabled: options?.enabled ?? false,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

/**
 * Hook para obtener un empleado por ID
 * 
 * @param id - ID del empleado
 * @returns Query result con datos del empleado
 */
export function useEmpleado(id: string | undefined) {
  return useQuery({
    queryKey: ['empleado', id],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoResponse>(`/empleados/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutos
  });
}
