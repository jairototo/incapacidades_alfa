import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type PaginationState,
  type SortingState,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';
import type { Incapacidad } from '@/types/incapacidad';
import { formatDate } from '@/utils/formatters';

interface IncapacidadesTableProps {
  data: Incapacidad[];
  isLoading: boolean;
  pagination: PaginationState;
  onPaginationChange: (pagination: PaginationState) => void;
  sorting: SortingState;
  onSortingChange: (sorting: SortingState) => void;
  totalItems: number;
}

export function IncapacidadesTable({
  data,
  isLoading,
  pagination,
  onPaginationChange,
  sorting,
  onSortingChange,
  totalItems,
}: IncapacidadesTableProps) {
  const navigate = useNavigate();

  const columns = useMemo<ColumnDef<Incapacidad>[]>(
    () => [
      {
        accessorKey: 'numero',
        header: 'Número',
        cell: ({ row }) => (
          <div className="font-mono font-medium">{row.original.numero}</div>
        ),
      },
      {
        accessorKey: 'created_at',
        header: 'Fecha Radicación',
        cell: ({ row }) => formatDate(row.original.created_at),
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
        id: 'solicitante',
        header: 'Solicitante',
        cell: ({ row }) => {
          const nombre = row.original.empleado
            ? `${row.original.empleado.nombres} ${row.original.empleado.apellidos}`
            : row.original.afiliado
            ? `${row.original.afiliado.nombres} ${row.original.afiliado.apellidos}`
            : 'N/A';
          return <div className="max-w-[200px] truncate">{nombre}</div>;
        },
      },
      {
        id: 'empresa',
        header: 'Empresa',
        cell: ({ row }) => {
          const empresa = row.original.empresa?.razon_social || 'N/A';
          return <div className="max-w-[200px] truncate">{empresa}</div>;
        },
      },
      {
        accessorKey: 'dias_totales',
        header: 'Días',
        cell: ({ row }) => (
          <div className="text-center">
            {row.original.dias_totales}
            {row.original.dias_totales > 7 && (
              <AlertTriangle
                className="ml-1 inline h-4 w-4 text-orange-500"
                aria-label="Prioridad alta"
              />
            )}
          </div>
        ),
      },
      {
        accessorKey: 'estado',
        header: 'Estado',
        cell: ({ row }) => {
          const STATE_COLORS: Record<string, string> = {
            RADICADA: 'bg-blue-100 text-blue-800',
            EN_AUDITORIA: 'bg-yellow-100 text-yellow-800',
            PENDIENTE: 'bg-orange-100 text-orange-800',
            LIQUIDACION: 'bg-purple-100 text-purple-800',
            LIQUIDACION_PARCIAL: 'bg-indigo-100 text-indigo-800',
            GLOSADA: 'bg-red-100 text-red-800',
            PAGADA: 'bg-green-100 text-green-800',
            PAGADA_PARCIAL: 'bg-teal-100 text-teal-800',
          };

          const STATE_LABELS: Record<string, string> = {
            RADICADA: 'Radicada',
            EN_AUDITORIA: 'En Auditoría',
            PENDIENTE: 'Pendiente',
            LIQUIDACION: 'En Liquidación',
            LIQUIDACION_PARCIAL: 'En Liquidación Parcial',
            GLOSADA: 'Glosada',
            PAGADA: 'Pagada',
            PAGADA_PARCIAL: 'Pagada Parcialmente',
          };

          return (
            <div
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                STATE_COLORS[row.original.estado] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {STATE_LABELS[row.original.estado] || row.original.estado}
            </div>
          );
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    pageCount: Math.ceil(totalItems / pagination.pageSize),
    state: {
      pagination,
      sorting,
    },
    onPaginationChange: (updater) => {
      const newState =
        typeof updater === 'function' ? updater(pagination) : updater;
      onPaginationChange(newState);
    },
    onSortingChange: (updater) => {
      const newState = typeof updater === 'function' ? updater(sorting) : updater;
      onSortingChange(newState);
    },
  });

  const handleRowClick = (incapacidad: Incapacidad) => {
    navigate(`/incapacidades/${incapacidad.id}/gestionar`);
  };

  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {[1, 2, 3, 4, 5].map((i) => (
              <TableRow key={i}>
                <TableCell colSpan={columns.length}>
                  <div className="h- w-full animate-pulse rounded bg-slate-200" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground">
          No se encontraron incapacidades con los filtros aplicados
        </p>
      </div>
    );
  }

  const totalPages = table.getPageCount();
  const currentPage = pagination.pageIndex + 1;

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleRowClick(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Mostrando {pagination.pageIndex * pagination.pageSize + 1} a{' '}
          {Math.min((pagination.pageIndex + 1) * pagination.pageSize, totalItems)} de{' '}
          {totalItems} incapacidades
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-4 w-4" />
            Anterior
          </Button>

          <div className="text-sm">
            Página {currentPage} de {totalPages}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Siguiente
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
