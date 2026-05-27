import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/dashboardService';
import type { GetExtendedStatsParams } from '@/types/dashboard';

/**
 * Hook para obtener estadísticas extendidas del dashboard
 * 
 * @param params - Parámetros de filtrado opcionales
 * @returns Query result con datos de estadísticas extendidas
 */
export function useExtendedStats(params?: GetExtendedStatsParams) {
  return useQuery({
    queryKey: ['dashboard-extended-stats', params],
    queryFn: () => dashboardService.getExtendedStats(params),
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000, // 10 minutos (antes cacheTime)
    refetchOnWindowFocus: false,
  });
}
