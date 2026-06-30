import { Badge } from '@/components/ui/badge';
import type { AuditoriaResultado } from '@/types/incapacidad';

interface AuditoriaResultadosPanelProps {
  resultados: AuditoriaResultado[];
  isLoading: boolean;
}

const SEVERIDAD_BADGE: Record<string, string> = {
  ERROR: 'bg-red-100 text-red-700 border-red-200',
  WARNING: 'bg-amber-100 text-amber-700 border-amber-200',
  INFO: 'bg-blue-100 text-blue-700 border-blue-200',
};

export function AuditoriaResultadosPanel({ resultados, isLoading }: AuditoriaResultadosPanelProps) {
  if (isLoading) {
    return (
      <div className="py-4 text-center text-sm text-slate-500">
        Cargando resultados de auditoría…
      </div>
    );
  }

  const sorted = [...resultados].sort((a, b) => {
    // Failed first (aprobado === false), then passed
    if (a.aprobado === b.aprobado) return 0;
    return a.aprobado ? 1 : -1;
  });

  const total = sorted.length;
  const aprobadas = sorted.filter((r) => r.aprobado).length;
  const fallidas = total - aprobadas;

  return (
    <details open data-testid="auditoria-resultados-details">
      <summary
        className="cursor-pointer select-none text-sm font-semibold text-blue-800 py-1"
        data-testid="auditoria-resultados-summary"
      >
        Reglas evaluadas ({total} total — {aprobadas} aprobadas, {fallidas} fallidas)
      </summary>

      <ul className="mt-2 space-y-1.5" role="list" data-testid="auditoria-resultados-list">
        {sorted.map((r) => {
          const badgeCls =
            SEVERIDAD_BADGE[r.severidad] ??
            'bg-slate-100 text-slate-600 border-slate-200';

          return (
            <li
              key={r.id}
              className="flex items-start gap-2 rounded border px-3 py-2 text-sm bg-white"
              data-testid={`resultado-item-${r.regla}`}
            >
              <span className="flex-shrink-0 mt-0.5" aria-label={r.aprobado ? 'aprobado' : 'fallido'}>
                {r.aprobado ? '✅' : '❌'}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold font-mono text-xs">{r.regla}</span>
                  <span
                    className={`border rounded px-1.5 py-0.5 text-xs leading-none font-medium ${badgeCls}`}
                    data-testid={`severidad-badge-${r.regla}`}
                  >
                    {r.severidad}
                  </span>
                  <Badge variant="outline" className="text-xs px-1.5 py-0.5 leading-none">
                    {r.categoria}
                  </Badge>
                </div>
                {r.detalle && (
                  <p className="mt-0.5 text-slate-600 leading-snug">{r.detalle}</p>
                )}
              </div>
            </li>
          );
        })}

        {sorted.length === 0 && (
          <li className="text-sm text-slate-500 py-2 text-center">
            No hay resultados de auditoría registrados.
          </li>
        )}
      </ul>
    </details>
  );
}
