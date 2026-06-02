import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { cn } from './cn';

interface PageHeaderProps {
  title: string;
  description?: string;
  backTo?: string;
  backLabel?: string;
  actions?: ReactNode;
  className?: string;
}

/**
 * Encabezado de página estándar — sigue brand book Alfa:
 * - h1 bold en brand-900 (azul profundo)
 * - Descripción en regular
 * - Acción "Volver" como link discreto
 */
export function PageHeader({
  title,
  description,
  backTo,
  backLabel = 'Volver',
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn('mb-6 flex items-start justify-between gap-4', className)}>
      <div className="min-w-0">
        <h1 className="text-3xl font-bold text-brand-900 leading-tight">{title}</h1>
        {description ? <p className="mt-1 text-sm text-gray-600">{description}</p> : null}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {actions}
        {backTo ? (
          <Link
            to={backTo}
            className="inline-flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700 transition-colors"
          >
            <ArrowLeft size={16} strokeWidth={1.75} aria-hidden />
            {backLabel}
          </Link>
        ) : null}
      </div>
    </header>
  );
}
