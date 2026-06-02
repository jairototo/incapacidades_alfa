import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from './cn';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-gray-300 bg-white px-6 py-12 text-center',
        className,
      )}
    >
      <div className="text-brand-600">
        {icon ?? <Inbox size={40} strokeWidth={1.5} aria-hidden />}
      </div>
      <h3 className="text-base font-medium text-brand-900">{title}</h3>
      {description ? <p className="max-w-sm text-sm text-gray-600">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
