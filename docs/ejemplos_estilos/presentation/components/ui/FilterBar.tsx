import type { ReactNode } from 'react';
import { cn } from './cn';

interface FilterBarProps {
  children: ReactNode;
  columns?: 2 | 3 | 4;
  className?: string;
}

const colsMap = {
  2: 'md:grid-cols-2',
  3: 'md:grid-cols-3',
  4: 'md:grid-cols-4',
} as const;

/**
 * Barra de filtros responsive (selects, búsqueda, fechas).
 * Sigue lineamiento Alfa: simplicidad, alineación izquierda.
 */
export function FilterBar({ children, columns = 3, className }: FilterBarProps) {
  return (
    <section className={cn('mb-4 grid grid-cols-1 gap-3', colsMap[columns], className)}>
      {children}
    </section>
  );
}
