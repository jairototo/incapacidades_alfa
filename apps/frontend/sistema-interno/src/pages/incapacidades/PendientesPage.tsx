import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, CheckCircle, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/shared/DataTable';
import { PendientesFilters } from '@/components/incapacidades/PendientesFilters';
import { incapacidadService } from '@/services/incapacidadService';
import { useAuthStore } from '@/store/authStore';
import type { IncapacidadPendiente, FiltrosPendientes } from '@/types/incapacidad';
import { RolUsuario } from '@/types/enums';
import { formatDate, formatRelativeDate } from '@/utils/formatters';

/**
 * Definición de columnas para la tabla de pendientes
 */
const columns: ColumnDef<IncapacidadPendiente>[] = [
  {
    accessorKey: 'numero',
    header: 'N° Radicación',
    cell: ({ row }) => (
      <div className="flex items-center space-x-2">
        <FileText className="h-4 w-4 text-slate-400" />
        <span className="font-mono text-sm font-medium">{row.original.numero}</span>
      </div>
    ),
  },
  {
    accessorKey: 'tipo',
    header: 'Tipo',
    cell: ({ row }) => (
      <Badge variant={row.original.tipo === 'ARL' ? 'default' : 'secondary'}>
        {row.original.tipo}
      </Badge>
    ),
  },
  {
    accessorKey: 'empleado',
    header: 'Empleado / Afiliado',
    cell: ({ row }) => {
      const empleado = row.original.empleado;
      const afiliado = row.original.afiliado;
      const fallback = row.original.empleado_fallback;

      if (empleado) {
        return (
          <div>
            <p className="font-medium">
              {empleado.nombres} {empleado.apellidos}
            </p>
            <p className="text-sm text-slate-500">{empleado.numero_documento}</p>
          </div>
        );
      }

      if (afiliado) {
        return (
          <div>
            <p className="font-medium">
              {afiliado.nombres} {afiliado.apellidos}
            </p>
            <p className="text-sm text-slate-500">{afiliado.numero_documento}</p>
          </div>
        );
      }

      if (fallback) {
        return (
          <div>
            <div className="flex items-center gap-1.5">
              <p className="font-medium">{fallback.nombres}</p>
              <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1 py-0.5 leading-none">
                Sin ficha
              </span>
            </div>
            <p className="text-sm text-slate-500">{fallback.numero_documento}</p>
          </div>
        );
      }

      return <span className="text-slate-400">—</span>;
    },
  },
  {
    accessorKey: 'empresa',
    header: 'Empresa',
    cell: ({ row }) => {
      const empresa = row.original.empresa;
      const fallback = row.original.empresa_fallback;

      if (empresa) {
        return (
          <div>
            <p className="font-medium">{empresa.razon_social}</p>
            <p className="text-sm text-slate-500">NIT: {empresa.nit}</p>
          </div>
        );
      }

      if (fallback) {
        return (
          <div>
            <div className="flex items-center gap-1.5">
              <p className="font-medium">{fallback.nombre}</p>
              <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1 py-0.5 leading-none">
                Sin ficha
              </span>
            </div>
            <p className="text-sm text-slate-500">NIT: {fallback.nit}</p>
          </div>
        );
      }

      return <span className="text-slate-500">Afiliado</span>;
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Radicación',
    cell: ({ row }) => (
      <div>
        <p className="font-medium">{formatDate(row.original.created_at)}</p>
        <p className="text-sm text-slate-500 flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          {formatRelativeDate(row.original.created_at)}
        </p>
      </div>
    ),
  },
  {
    accessorKey: 'dias_desde_radicacion',
    header: 'Antigüedad',
    cell: ({ row }) => {
      const dias = row.original.dias_desde_radicacion;
      const variant = dias > 7 ? 'destructive' : dias > 3 ? 'default' : 'secondary';
      
      return (
        <Badge variant={variant}>
          {dias} {dias === 1 ? 'día' : 'días'}
        </Badge>
      );
    },
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => {
      const estadoMap: Record<string, { variant: 'default' | 'secondary' | 'outline' | 'destructive', label: string }> = {
        'RADICADA': { variant: 'default', label: 'Radicada' },
        'EN_AUDITORIA': { variant: 'secondary', label: 'En Auditoría' },
        'PENDIENTE': { variant: 'outline', label: 'Pendiente' },
      };
      
      const config = estadoMap[row.original.estado] || { variant: 'outline', label: row.original.estado };
      
      return <Badge variant={config.variant}>{config.label}</Badge>;
    },
  },
  {
    accessorKey: 'prioridad',
    header: 'Prioridad',
    cell: ({ row }) => {
      const prioridadColors: Record<string, string> = {
        'URGENTE': 'bg-red-100 text-red-800 border-red-300',
        'ALTA': 'bg-orange-100 text-orange-800 border-orange-300',
        'NORMAL': 'bg-yellow-100 text-yellow-800 border-yellow-300',
        'BAJA': 'bg-gray-100 text-gray-800 border-gray-300',
      };
      
      const color = prioridadColors[row.original.prioridad] || 'bg-gray-100 text-gray-800';
      
      return (
        <Badge variant="outline" className={color}>
          {row.original.prioridad}
        </Badge>
      );
    },
  },
  {
    accessorKey: 'auditor_asignado',
    header: 'Auditor Asignado',
    cell: ({ row }) => {
      const auditor = row.original.auditor_asignado;
      return auditor ? (
        <span className="text-sm">{auditor.nombre_completo}</span>
      ) : (
        <span className="text-sm text-slate-400">Sin asignar</span>
      );
    },
  },
  {
    id: 'actions',
    header: 'Acciones',
    cell: ({ row }) => {
      const navigate = useNavigate();
      return (
        <Button
          variant="default"
          size="sm"
          onClick={() => navigate(`/incapacidades/${row.original.id}/gestionar`)}
        >
          Gestionar
        </Button>
      );
    },
  },
];

/**
 * Página de Incapacidades Pendientes
 *
 * Features:
 * - Listado de incapacidades pendientes (RADICADA, EN_AUDITORIA, PENDIENTE)
 * - Filtros colapsables (tipo, prioridad, empresa, antigüedad)
 * - Tabla ordenada por prioridad y antigüedad
 * - Auto-refresh cada 2 minutos
 * - Empty state cuando no hay pendientes
 */
export function PendientesPage() {
  const { user } = useAuthStore();
  // Un AUDITOR no puede gestionar incapacidades que no le fueron asignadas — la bandeja
  // siempre debe estar filtrada por su propio auditor_asignado_id, sin excepción y sin
  // posibilidad de elegir otro auditor desde el formulario de filtros.
  const isAuditor = user?.rol === RolUsuario.AUDITOR;
  const auditorAsignadoIdForzado = isAuditor && user ? user.id : undefined;

  const [filtros, setFiltros] = useState<FiltrosPendientes>(() => ({
    skip: 0,
    limit: 100,
    ...(auditorAsignadoIdForzado ? { auditor_asignado_id: auditorAsignadoIdForzado } : {}),
  }));
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Query para cargar pendientes
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['incapacidades-pendientes', filtros],
    queryFn: () => incapacidadService.listarPendientes(filtros),
    staleTime: 30 * 1000, // 30 segundos
    refetchInterval: 2 * 60 * 1000, // Refetch cada 2 minutos
  });

  const handleSearch = (nuevosFiltros: FiltrosPendientes) => {
    setFiltros({
      ...nuevosFiltros,
      skip: 0,
      limit: 100,
      ...(auditorAsignadoIdForzado ? { auditor_asignado_id: auditorAsignadoIdForzado } : {}),
    });
  };

  const totalPendientes = data?.length || 0;
  const hasActiveFilters = Object.keys(filtros).some(
    (key) => key !== 'skip' && key !== 'limit'
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-3">
            Incapacidades Pendientes
            <Badge variant="destructive" className="text-base">
              {totalPendientes}
            </Badge>
          </h1>
          <p className="text-slate-500 mt-1">
            Gestione las incapacidades que requieren auditoría
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-500">Auto-actualización cada 2 min</p>
        </div>
      </div>

      {/* Filtros colapsables */}
      <div>
        <Button 
          variant="outline" 
          className="mb-4"
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <Filter className="mr-2 h-4 w-4" />
          {filtersOpen ? 'Ocultar Filtros' : 'Mostrar Filtros'}
          {filtersOpen ? (
            <ChevronUp className="ml-2 h-4 w-4" />
          ) : (
            <ChevronDown className="ml-2 h-4 w-4" />
          )}
        </Button>
        
        {filtersOpen && (
          <PendientesFilters
            onSearch={handleSearch}
            isLoading={isLoading}
            showAuditorFilter={!isAuditor}
          />
        )}
      </div>

      {/* Tabla de pendientes */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4">
          {!isLoading && totalPendientes === 0 && !hasActiveFilters ? (
            // Empty state — solo cuando no hay pendientes en absoluto (sin filtros aplicados).
            // Si hay un filtro activo, un resultado vacío significa "sin coincidencias",
            // no "todo al día" — ese caso cae al DataTable, que muestra su propio
            // emptyMessage más preciso.
            <div className="text-center py-12">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h3 className="mt-4 text-xl font-medium text-slate-900">
                ¡No hay pendientes!
              </h3>
              <p className="mt-2 text-slate-500">
                Todas las incapacidades están al día.
              </p>
              <Button variant="outline" onClick={() => refetch()} className="mt-4">
                Actualizar
              </Button>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={data || []}
              isLoading={isLoading}
              emptyMessage="No se encontraron incapacidades pendientes con los filtros aplicados."
            />
          )}
        </div>
      </div>

      {/* Información adicional */}
      {totalPendientes > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Las incapacidades se ordenan automáticamente por prioridad
            (URGENTE → ALTA → NORMAL → BAJA) y antigüedad (más antiguas primero). Enfócate en las marcadas
            con prioridad URGENTE y ALTA primero.
          </p>
        </div>
      )}
    </div>
  );
}
