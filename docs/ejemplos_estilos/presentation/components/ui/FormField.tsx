import type { ReactNode } from 'react';
import { cn } from './cn';

interface FormFieldProps {
  label?: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  className?: string;
  children: ReactNode;
}

/**
 * Wrapper de campo de formulario con label + hint + error.
 * Sigue tipografía Alfa: label medium en brand-900, hint regular, error en rojo.
 */
export function FormField({
  label,
  htmlFor,
  hint,
  error,
  required,
  className,
  children,
}: FormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {label ? (
        <label htmlFor={htmlFor} className="text-sm font-medium text-brand-900">
          {label}
          {required ? <span className="ml-0.5 text-red-600" aria-hidden>*</span> : null}
        </label>
      ) : null}
      {children}
      {error ? (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-gray-500">{hint}</p>
      ) : null}
    </div>
  );
}
