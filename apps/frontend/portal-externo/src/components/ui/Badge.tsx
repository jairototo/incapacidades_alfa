/**
 * Badge - Componente para mostrar etiquetas/badges.
 * 
 * Basado en shadcn/ui Badge component.
 * Utilizado para mostrar estados, tipos, y otras etiquetas visuales.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

// ========== TIPOS ==========

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Variante del badge (futuro: primary, secondary, destructive, outline) */
  variant?: 'default';
}

// ========== COMPONENTE ==========

/**
 * Badge - Componente de etiqueta visual.
 * 
 * @example
 * ```tsx
 * <Badge className="bg-blue-100 text-blue-800">
 *   RADICADA
 * </Badge>
 * ```
 */
export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <div
      role="status"
      className={cn(
        'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        className
      )}
      {...props}
    />
  );
}
