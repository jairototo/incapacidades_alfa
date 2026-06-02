import type { ReactNode } from 'react';
import { cn } from './cn';

interface PageLayoutProps {
  children: ReactNode;
  className?: string;
  width?: 'narrow' | 'default' | 'wide' | 'full';
}

const widthMap = {
  narrow: 'max-w-3xl',
  default: 'max-w-6xl',
  wide: 'max-w-7xl',
  full: 'max-w-full',
} as const;

/**
 * Layout estándar de página — sigue brand book Alfa:
 * - Contenedor ventana (jerarquía visual)
 * - Alineación izquierda por defecto
 * - Padding consistente
 */
export function PageLayout({ children, className, width = 'default' }: PageLayoutProps) {
  return (
    <main className={cn('mx-auto px-6 py-10', widthMap[width], className)}>{children}</main>
  );
}
