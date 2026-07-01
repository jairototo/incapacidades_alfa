import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Clock, CheckCircle, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/shared/DataTable';
import { PendientesFilters } from '@/components/incapacidades/PendientesFilters';
import { incapacidadService } from '@/services/incapacidadService';
import type { IncapacidadPendiente, FiltrosPendientes } from '@/types/incapacidad';
import { formatDate, formatRelativeDate } from '@/utils/formatters';

const columns: ColumnDef<IncapacidadPendiente>[] = [
  {
    accessorKey: 'numero',
    header: 'N° Radicación',
    cell: ({ row }) => (
      <div className="flex items-center space-x-2">
        <DollarSign className="h-4 w-4 text-slate-400" />
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
            <p className="font-medium">{empleado.nombres} {empleado.apellidos}</p>
            <p className="text-sm text-slate-500">{empleado.numero_documento}</p>
          </div>
        );
      }
      if (afiliado) {
        return (
          <div>
            <p className="font-medium">{afiliado.nombres} {afiliado.apellidos}</p>
            <p className="text-sm text-slate-500">{afiliado.numero_documento}</p>
          </div>
        );
      }
      if (fallback) {
        return (
          <div>
            <p className="font-medium">{fallback.nombres}</p>
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
      if (fallback) return <p className="font-medium">{fallback.nombre}</p>;
      return <span className="text-slate-500">Afiliado</span>;
    },
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => (
      <Badge variant={row.original.estado === 'LIQUIDACION' ? 'default' : 'secondary'}>
        {row.original.estado}
      </Badge>
    ),
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
    id: 'actions',
    header: 'Acciones',
    cell: ({ row }) => {
      const navigate = useNavigate();
      return (
        <Button
          variant="default"
          size="sm"
          onClick={() => navigate(`/incapacidades/${row.original.id}/liquidacion`)}
        >
          Liquidar
        </Button>
      );
    },
  },
];

export function BandejaLiquidacionPage() {
  const [filtros, setFiltros] = useState<FiltrosPendientes>({ skip: 0, limit: 100 });
  const [filtersOpen, setFiltersOpen] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['incapacidades-bandeja-liquidacion', filtros],
    queryFn: () => incapacidadService.listarBandejaLiquidacion(filtros),
    staleTime: 30 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });

  const total = data?.length || 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-3">
            Liquidación
            {total > 0 && (
              <Badge variant="destructive" className="text-base">
                {total}
              </Badge>
            )}
          </h1>
          <p className="text-slate-500 mt-1">
            Incapacidades aprobadas pendientes de liquidación
          </p>
        </div>
        <p className="text-sm text-slate-500">Auto-actualización cada 2 min</p>
      </div>

      <div>
        <Button
          variant="outline"
          className="mb-4"
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <Filter className="mr-2 h-4 w-4" />
          {filtersOpen ? 'Ocultar Filtros' : 'Mostrar Filtros'}
          {filtersOpen ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
        </Button>
        {filtersOpen && (
          <PendientesFilters
            onSearch={(f) => setFiltros({ ...f, skip: 0, limit: 100 })}
            isLoading={isLoading}
          />
        )}
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4">
          {!isLoading && total === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h3 className="mt-4 text-xl font-medium text-slate-900">
                No hay liquidaciones pendientes
              </h3>
              <p className="mt-2 text-slate-500">
                No hay incapacidades en estado LIQUIDACION.
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
              emptyMessage="No se encontraron incapacidades con los filtros aplicados."
            />
          )}
        </div>
      </div>
    </div>
  );
}
