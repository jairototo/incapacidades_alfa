import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from './cn';

// ─────────────────────────────────────────────────────────────────────────────
// DataTable — wrapper estandarizado sobre <table> nativo.
// Sigue brand book Alfa: contenedor "ventana", tipografía Roboto, simplicidad.
// ─────────────────────────────────────────────────────────────────────────────

export interface DataTableColumn<T> {
  key: string;
  header: ReactNode;
  /** Renderiza la celda. Recibe la fila completa. */
  cell: (row: T) => ReactNode;
  /** Clases extra para la celda (alineación, fuente mono, etc.). */
  className?: string;
  /** Clases extra para el header. */
  headerClassName?: string;
  /** Ancho fijo opcional (ej: 'w-32', 'w-1/4'). */
  width?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[] | undefined;
  rowKey: (row: T) => string | number;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  isLoading,
  isError,
  errorMessage = 'Error al cargar los datos.',
  emptyMessage = 'Sin resultados.',
  onRowClick,
  className,
}: DataTableProps<T>) {
  const colSpan = columns.length;
  return (
    <div className={cn('overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm', className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((c) => (
                <th
                  key={c.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-600',
                    c.width,
                    c.headerClassName,
                  )}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={colSpan} className="px-4 py-10 text-center text-gray-500">
                  <span className="inline-flex items-center gap-2">
                    <Loader2 size={16} strokeWidth={1.75} className="animate-spin" aria-hidden />
                    Cargando...
                  </span>
                </td>
              </tr>
            ) : isError ? (
              <tr>
                <td colSpan={colSpan} className="px-4 py-10 text-center text-red-600">
                  {errorMessage}
                </td>
              </tr>
            ) : !data || data.length === 0 ? (
              <tr>
                <td colSpan={colSpan} className="px-4 py-10 text-center text-gray-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <tr
                  key={rowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(
                    'transition-colors',
                    onRowClick ? 'cursor-pointer hover:bg-brand-50' : 'hover:bg-gray-50',
                  )}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={cn('px-4 py-3 text-gray-700', c.className)}>
                      {c.cell(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
