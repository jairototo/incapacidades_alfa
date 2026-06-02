import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/presentation/components/ui/Button';

interface PaginationProps {
  total: number;
  offset: number;
  limit: number;
  onChange: (offset: number) => void;
}

export function Pagination({ total, offset, limit, onChange }: PaginationProps) {
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));
  const prev = () => onChange(Math.max(0, offset - limit));
  const next = () => onChange(Math.min((pages - 1) * limit, offset + limit));
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <div className="flex items-center justify-between gap-3 text-sm text-gray-600">
      <span>
        Mostrando <span className="font-medium text-gray-900">{from}–{to}</span> de{' '}
        <span className="font-medium text-gray-900">{total}</span>
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={prev}
          disabled={page <= 1}
          leftIcon={<ChevronLeft size={16} strokeWidth={1.75} aria-hidden />}
        >
          Anterior
        </Button>
        <span className="px-2 text-xs text-gray-500">
          Página <span className="font-medium text-gray-900">{page}</span> / {pages}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={next}
          disabled={page >= pages}
          rightIcon={<ChevronRight size={16} strokeWidth={1.75} aria-hidden />}
        >
          Siguiente
        </Button>
      </div>
    </div>
  );
}

