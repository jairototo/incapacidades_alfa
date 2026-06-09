import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Inbox, Search, AlertCircle, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/shared/DataTable';
import { preIncapacidadService } from '@/services/preIncapacidadService';
import type { PreIncapacidadListItem, EstadoPreIncapacidad } from '@/types/preIncapacidad';
import { useDebounce } from '@/hooks/useDebounce';
import { formatDate, formatRelativeDate } from '@/utils/formatters';

// ── Sub-components ────────────────────────────────────────────────────────────

function EstadoBadge({ estado }: { estado: EstadoPreIncapacidad }) {
  const config: Record<
    EstadoPreIncapacidad,
    { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }
  > = {
    PENDIENTE: { variant: 'default', label: 'Pendiente' },
    RECHAZADA: { variant: 'destructive', label: 'Rechazada' },
    ERROR: { variant: 'outline', label: 'Error' },
    DEVUELTA: { variant: 'secondary', label: 'Devuelta' },
    PROCESADA: { variant: 'default', label: 'Procesada' },
  };
  const { variant, label } = config[estado] ?? { variant: 'outline', label: estado };
  return <Badge variant={variant}>{label}</Badge>;
}

function IssueCount({ errors, warnings }: { errors: number; warnings: number }) {
  if (errors === 0 && warnings === 0)
    return <span className="text-slate-400 text-sm">—</span>;
  return (
    <div className="flex items-center gap-2">
      {errors > 0 && (
        <span className="flex items-center gap-1 text-red-600 text-sm font-medium">
          <AlertCircle className="h-3.5 w-3.5" />
          {errors}
        </span>
      )}
      {warnings > 0 && (
        <span className="flex items-center gap-1 text-yellow-600 text-sm">
          <AlertTriangle className="h-3.5 w-3.5" />
          {warnings}
        </span>
      )}
    </div>
  );
}

// ── Columns ───────────────────────────────────────────────────────────────────

function useColumns(): ColumnDef<PreIncapacidadListItem>[] {
  const navigate = useNavigate();
  return [
    {
      accessorKey: 'numero_radicacion',
      header: 'N° Radicación',
      cell: ({ row }) => (
        <span className="font-mono text-sm font-semibold">
          {row.original.numero_radicacion}
        </span>
      ),
    },
    {
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => <EstadoBadge estado={row.original.estado} />,
    },
    {
      accessorKey: 'empleado_nombres',
      header: 'Empleado',
      cell: ({ row }) => (
        <div>
          <p className="font-medium">{row.original.empleado_nombres}</p>
          <p className="text-sm text-slate-500">{row.original.empleado_numero_documento}</p>
        </div>
      ),
    },
    {
      accessorKey: 'empresa_nombre',
      header: 'Empresa',
      cell: ({ row }) =>
        row.original.empresa_nombre ? (
          <div>
            <p className="font-medium text-sm">{row.original.empresa_nombre}</p>
            <p className="text-xs text-slate-500">NIT: {row.original.empresa_nit}</p>
          </div>
        ) : (
          <span className="text-slate-400 text-sm">Independiente</span>
        ),
    },
    {
      accessorKey: 'fecha_inicio',
      header: 'Período',
      cell: ({ row }) => (
        <div className="text-sm">
          <p>{formatDate(row.original.fecha_inicio)}</p>
          <p className="text-slate-500">{row.original.dias_totales} días</p>
        </div>
      ),
    },
    {
      id: 'issues',
      header: 'Issues',
      cell: ({ row }) => (
        <IssueCount
          errors={row.original.total_errores}
          warnings={row.original.total_warnings}
        />
      ),
    },
    {
      accessorKey: 'created_at',
      header: 'Radicado',
      cell: ({ row }) => (
        <div className="text-sm">
          <p>{formatDate(row.original.created_at)}</p>
          <p className="text-slate-500 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatRelativeDate(row.original.created_at)}
          </p>
        </div>
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button
          size="sm"
          variant="default"
          onClick={() => navigate(`/pre-incapacidades/${row.original.id}/gestionar`)}
        >
          Gestionar
        </Button>
      ),
    },
  ];
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function BandejaPage() {
  const [search, setSearch] = useState('');
  const [estado, setEstado] = useState<string>('');
  const debouncedSearch = useDebounce(search, 300);
  const columns = useColumns();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pre-incapacidades-bandeja', debouncedSearch, estado],
    queryFn: () =>
      preIncapacidadService.listar({
        search: debouncedSearch || undefined,
        estado: (estado as EstadoPreIncapacidad) || undefined,
      }),
    staleTime: 30_000,
    refetchInterval: 2 * 60_000,
  });

  const total = data?.length ?? 0;
  const totalErrores = data?.reduce((s, i) => s + i.total_errores, 0) ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Inbox className="h-8 w-8 text-blue-600" />
            Bandeja Pre-Incapacidades
            {total > 0 && (
              <Badge variant="destructive" className="text-base">
                {total}
              </Badge>
            )}
          </h1>
          <p className="text-slate-500 mt-1">
            Pre-radicaciones que requieren revisión o corrección manual
          </p>
        </div>
        {totalErrores > 0 && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm font-medium">{totalErrores} errores críticos</span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Buscar por nombre o documento..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={estado || 'ALL'} onValueChange={(v) => setEstado(v === 'ALL' ? '' : v)}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Todos</SelectItem>
            <SelectItem value="PENDIENTE">Pendiente</SelectItem>
            <SelectItem value="RECHAZADA">Rechazada</SelectItem>
            <SelectItem value="ERROR">Error</SelectItem>
            <SelectItem value="DEVUELTA">Devuelta</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => refetch()}>
          Actualizar
        </Button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          {!isLoading && total === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h3 className="mt-4 text-xl font-medium text-slate-900">¡Bandeja vacía!</h3>
              <p className="mt-2 text-slate-500">
                No hay pre-incapacidades pendientes de revisión.
              </p>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={data ?? []}
              isLoading={isLoading}
              emptyMessage="No se encontraron pre-incapacidades con los filtros aplicados."
            />
          )}
        </div>
      </div>
    </div>
  );
}
