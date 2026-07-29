import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { PaginationState, SortingState } from '@tanstack/react-table';
import { StatsCards } from '@/components/dashboard/StatsCards';
import { FiltersBar } from '@/components/dashboard/FiltersBar';
import { IncapacidadesTable } from '@/components/dashboard/IncapacidadesTable';
import {
  TopEmpresasChart,
  TopDiagnosticosChart,
  TopEmpleadosTable,
  DistribucionEstadosPieChart,
  DistribucionTiposDonut,
  TendenciaMensualLineChart,
} from '@/components/dashboard/charts';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, TrendingUp } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { dashboardService } from '@/services/dashboardService';
import { empresaService } from '@/services/empresaService';
import { useExtendedStats } from '@/hooks/useExtendedStats';
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

  // Query de estadísticas extendidas (gráficos)
  const {
    data: extendedStats,
    isLoading: isLoadingExtended,
    error: extendedError,
  } = useExtendedStats({
    empresa_id: filters.empresa_id || undefined,
    tipo: filters.tipo !== 'TODAS' ? filters.tipo : undefined,
    fecha_desde: filters.fecha_desde || undefined,
    fecha_hasta: filters.fecha_hasta || undefined,
    top_limit: 10,
  });

  const error = statsError || incapacidadesError;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Dashboard de Auditoría</h1>
        <p className="text-slate-500 mt-1">
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

      {/* Gráficos y Análisis */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h2 className="text-base font-bold">Análisis y Tendencias</h2>
        </div>

        {/* Error State para gráficos */}
        {extendedError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Error al cargar gráficos: {extendedError instanceof Error ? extendedError.message : 'Error desconocido'}
            </AlertDescription>
          </Alert>
        )}

        {/* Loading State para gráficos */}
        {isLoadingExtended ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-[300px]" />
            ))}
          </div>
        ) : extendedStats ? (
          <>
            {/* Grid de gráficos - Primera fila */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TopEmpresasChart data={extendedStats.top_empresas} />
              <TopDiagnosticosChart data={extendedStats.top_diagnosticos} />
            </div>

            {/* Grid de gráficos - Segunda fila */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <DistribucionEstadosPieChart data={extendedStats.distribucion_estados} />
              <DistribucionTiposDonut data={extendedStats.distribucion_tipos} />
            </div>

            {/* Tabla de top empleados */}
            <TopEmpleadosTable data={extendedStats.top_empleados} />

            {/* Gráfico de tendencia mensual (ancho completo) */}
            <TendenciaMensualLineChart data={extendedStats.tendencia_mensual} />
          </>
        ) : null}
      </div>

      {/* Filtros */}
      <FiltersBar
        filters={filters}
        onFiltersChange={(newFilters) => {
          setFilters(newFilters);
          setPagination({ ...pagination, pageIndex: 0 }); // Reset a primera página
        }}
        empresas={(empresasData || []).map((e) => ({
          id: e.id,
          nit: e.nit,
          razon_social: e.razon_social,
          // GET /empresas (list) doesn't return contact fields — see EmpresaListItem.
          email_contacto: '',
          ciudad: e.ciudad,
        }))}
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
