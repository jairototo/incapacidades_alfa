import { Loader2 } from 'lucide-react';
import { cn } from './cn';

interface SpinnerProps {
  size?: number;
  className?: string;
  label?: string;
}

export function Spinner({ size = 20, className, label }: SpinnerProps) {
  return (
    <span className={cn('inline-flex items-center gap-2 text-brand-600', className)} role="status">
      <Loader2 size={size} strokeWidth={1.75} className="animate-spin" aria-hidden />
      {label ? <span className="text-sm">{label}</span> : <span className="sr-only">Cargando</span>}
    </span>
  );
}
