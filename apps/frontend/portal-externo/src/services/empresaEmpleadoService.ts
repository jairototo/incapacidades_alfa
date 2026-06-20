import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

/**
 * Empleado tal como lo retorna GET /empresas/{empresa_id}/empleados
 * (schema backend EmpleadoListItem — subconjunto liviano para listados).
 */
export interface EmpleadoListItem {
  id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  cargo?: string | null;
  estado: string;
  created_at: string;
}

/**
 * Hook para listar empleados de la empresa del usuario autenticado.
 *
 * Llama el endpoint anidado y scopeado por token:
 *   GET /api/v1/empresas/{empresa_id}/empleados
 * (el backend rechaza con 403 si un usuario EMPRESA intenta consultar otra empresa).
 *
 * Deshabilitada si el usuario no tiene empresa_id asignado.
 *
 * @param search - Texto libre: filtra por nombres, apellidos, documento o email.
 */
export function useEmpleadosDeMiEmpresa(search: string) {
  const empresaId = useAuthStore((s) => s.user?.empresa_id);
  return useQuery({
    queryKey: ['empleados', 'mi-empresa', empresaId, search],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoListItem[]>(`/empresas/${empresaId}/empleados`, {
        params: {
          search: search || undefined,
          estado: 'ACTIVO',
          limit: 50,
        },
      });
      return data;
    },
    enabled: !!empresaId,
    staleTime: 5 * 60 * 1000,
  });
}
