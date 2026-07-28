import { Button } from '@/components/ui/button';

interface TablePaginationProps {
  skip: number;
  limit: number;
  resultCount: number;
  onPrev: () => void;
  onNext: () => void;
}

export function TablePagination({ skip, limit, resultCount, onPrev, onNext }: TablePaginationProps) {
  const hasPrev = skip > 0;
  const hasNext = resultCount === limit;

  return (
    <div className="flex items-center justify-between pt-2">
      <span className="text-sm text-slate-500">
        Mostrando {resultCount === 0 ? 0 : skip + 1}–{skip + resultCount}
      </span>
      <div className="space-x-2">
        <Button variant="outline" size="sm" onClick={onPrev} disabled={!hasPrev}>
          Anterior
        </Button>
        <Button variant="outline" size="sm" onClick={onNext} disabled={!hasNext}>
          Siguiente
        </Button>
      </div>
    </div>
  );
}
