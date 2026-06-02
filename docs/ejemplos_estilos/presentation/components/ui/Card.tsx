import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from './cn';

/**
 * Contenedor "Ventana" Alfa (brand book Contenedores):
 * - Agrupa y organiza elementos
 * - Crea jerarquía visual
 * - Bordes suaves redondeados
 */
export function Card({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-lg border border-gray-200 bg-white shadow-sm', className)}
      {...rest}
    >
      {children}
    </div>
  );
}

interface CardSectionProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
  actions?: ReactNode;
}

export function CardHeader({ title, description, actions, className, ...rest }: CardSectionProps) {
  return (
    <div
      className={cn('flex items-start justify-between gap-4 border-b border-gray-100 px-6 py-4', className)}
      {...rest}
    >
      <div className="min-w-0">
        {title ? <h3 className="text-lg font-medium text-brand-900">{title}</h3> : null}
        {description ? <p className="mt-0.5 text-sm text-gray-600">{description}</p> : null}
      </div>
      {actions ? <div className="shrink-0">{actions}</div> : null}
    </div>
  );
}

export function CardBody({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-6 py-4', className)} {...rest}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-center justify-between gap-4 border-t border-gray-100 px-6 py-4', className)}
      {...rest}
    >
      {children}
    </div>
  );
}
