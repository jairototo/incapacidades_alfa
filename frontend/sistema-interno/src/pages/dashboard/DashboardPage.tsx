import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { PaginationState, SortingState } from '@tanstack/react-table';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { FiltersBar } from '@/components/dashboard/FiltersBar';
import { IncapacidadesTable } from '@/components/dashboard/IncapacidadesTable';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { dashboardService } from '@/services/dashboardService';
import { empresaService } from '@/services/empresaService';
import type { FilterState } from '@/types/dashboard';

export function DashboardPage() {
  // Estado de filtros
  const [filters, setFilters] = useState<FilterState>({
    tipo: 'TODAS',
    estado: 'TODOS',
    fecha_desde: null,
    fecha_hasta: null,
    empresa_id: null,
    search: '',
  });

  // Estado de paginación
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  // Estado de ordenamiento
  const [sorting, setSorting] = useState<SortingState>([]);

  // Query de stats
  const {
    data: stats,
    isLoading: isLoadingStats,
    error: statsError,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardService.getStats(),
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Query de incapacidades
  const {
    data: incapacidades,
    isLoading: isLoadingIncapacidades,
    error: incapacidadesError,
  } = useQuery({
    queryKey: ['incapacidades-dashboard', filters, pagination, sorting],
    queryFn: () =>
      dashboardService.getIncapacidades({
        ...filters,
        skip: pagination.pageIndex * pagination.pageSize,
        limit: pagination.pageSize,
        order_by: sorting[0]?.id,
        direction: sorting[0]?.desc ? 'desc' : 'asc',
      }),
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Query de empresas para el filtro
  const { data: empresasData } = useQuery({
    queryKey: ['empresas-list'],
    queryFn: () => empresaService.list({ skip: 0, limit: 100 }),
    staleTime: 10 * 60 * 1000, // 10 minutos
  });

  const error = statsError || incapacidadesError;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard de Auditoría</h1>
        <p className="text-slate-500 mt-2">
          Gestión y auditoría de incapacidades
        </p>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error instanceof Error ? error.message : 'Error al cargar datos'}
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <StatsCards
        stats={stats || { pendientes: 0, auditadas_hoy: 0, proximas_vencer: 0, rechazadas_observadas: 0 }}
        isLoading={isLoadingStats}
      />

      {/* Filtros */}
      <FiltersBar
        filters={filters}
        onFiltersChange={(newFilters) => {
          setFilters(newFilters);
          setPagination({ ...pagination, pageIndex: 0 }); // Reset a primera página
        }}
        empresas={empresasData?.items || []}
      />

      {/* Tabla */}
      <IncapacidadesTable
        data={incapacidades?.items || []}
        isLoading={isLoadingIncapacidades}
        pagination={pagination}
        onPaginationChange={setPagination}
        sorting={sorting}
        onSortingChange={setSorting}
        totalItems={incapacidades?.total || 0}
      />
    </div>
  );
}
