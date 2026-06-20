import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import type { EmpleadoResponse } from '@/types/api';

/**
 * Hook para listar empleados pertenecientes a la empresa del usuario autenticado.
 * Filtra siempre por empresa_id del store (contexto EMPRESA) y estado ACTIVO.
 *
 * La query está deshabilitada si el usuario no tiene empresa_id asignado.
 *
 * @param search - Texto libre para filtrar por nombre o documento
 * @returns React Query result con array de EmpleadoResponse
 */
export function useEmpleadosDeMiEmpresa(search: string) {
  const empresaId = useAuthStore((s) => s.user?.empresa_id);
  return useQuery({
    queryKey: ['empleados', 'mi-empresa', empresaId, search],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoResponse[]>('/empleados', {
        params: {
          empresa_id: empresaId,
          search: search || undefined,
          estado: 'ACTIVO',
          limit: 50,
        },
      });
      // La API devuelve directamente un array de empleados (sin paginación)
      return data;
    },
    enabled: !!empresaId,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}
