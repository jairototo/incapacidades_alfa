import type { HTMLAttributes } from 'react';
import { cn } from './cn';

type BadgeVariant = 'success' | 'warning' | 'info' | 'error' | 'neutral' | 'accent';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

// Variantes basadas en la paleta Alfa (brand book Paleta de color)
const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-brand-100 text-brand-700',          // verde claro institucional
  warning: 'bg-alfa-yellow-light/30 text-amber-800',
  info: 'bg-alfa-blue/15 text-alfa-blue-dark',
  error: 'bg-red-100 text-red-700',
  neutral: 'bg-gray-100 text-gray-700',
  accent: 'bg-lime-100 text-lime-800',             // verde limón
};

export function Badge({ variant = 'neutral', className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantStyles[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
