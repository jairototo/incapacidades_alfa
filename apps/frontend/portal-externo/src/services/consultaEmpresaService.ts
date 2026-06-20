import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface FiltrosConsulta {
  estado?: string;
  numero?: string;
  empleado_documento?: string;
  fecha_inicio_desde?: string;
  fecha_inicio_hasta?: string;
}

export interface IncapacidadListItem {
  id: string;
  numero: string;
  estado: string;
  tipo: string;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10?: string;
  empleado?: { nombres?: string; apellidos?: string; numero_documento?: string } | null;
}

export function useIncapacidadesDeMiEmpresa(filtros: FiltrosConsulta) {
  return useQuery({
    queryKey: ['incapacidades', 'mi-empresa', filtros],
    queryFn: async () => {
      const params: Record<string, string> = {};
      Object.entries(filtros).forEach(([k, v]) => { if (v) params[k] = v; });
      const { data } = await api.get<IncapacidadListItem[]>('/incapacidades/mi-empresa', { params });
      return data;
    },
    staleTime: 60 * 1000,
  });
}
