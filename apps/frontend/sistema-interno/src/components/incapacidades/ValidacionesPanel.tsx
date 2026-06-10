import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import type { ValidationIssue } from '@/types/incapacidad';
import { cn } from '@/lib/utils';

type Categoria = 'FIELD_VALIDATION' | 'BUSINESS_RULE' | 'FRAUD_ALERT' | 'INTEGRATION_CHECK';

const CATEGORIA_LABELS: Record<Categoria, string> = {
  FIELD_VALIDATION: 'Validación de campos',
  BUSINESS_RULE: 'Reglas de negocio',
  FRAUD_ALERT: 'Alerta de fraude',
  INTEGRATION_CHECK: 'Verificación de integración',
};

const SEVERIDAD_ORDER: Record<string, number> = { ERROR: 0, WARNING: 1, INFO: 2 };

interface ValidacionesPanelProps {
  issues: ValidationIssue[];
  isLoading: boolean;
}

export function ValidacionesPanel({ issues, isLoading }: ValidacionesPanelProps) {
  if (isLoading) {
    return (
      <div className="py-8 text-center text-slate-500 text-sm">Cargando validaciones…</div>
    );
  }

  const sorted = [...issues].sort(
    (a, b) => (SEVERIDAD_ORDER[a.severidad] ?? 3) - (SEVERIDAD_ORDER[b.severidad] ?? 3)
  );

  const categoriasConIssues = new Set(issues.map(i => i.categoria));
  const categoriasSinIssues = (Object.keys(CATEGORIA_LABELS) as Categoria[]).filter(
    c => !categoriasConIssues.has(c)
  );

  return (
    <div className="space-y-4">
      {sorted.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Alertas y problemas detectados ({sorted.length})
          </h3>
          <ul className="space-y-1.5" role="list">
            {sorted.map(issue => (
              <IssueRow key={issue.id} issue={issue} />
            ))}
          </ul>
        </div>
      )}

      {categoriasSinIssues.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Sin problemas detectados
          </h3>
          <ul className="space-y-1" role="list">
            {categoriasSinIssues.map(cat => (
              <li
                key={cat}
                className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-1.5"
              >
                <CheckCircle className="h-3.5 w-3.5 flex-shrink-0" />
                <span className="font-mono text-xs font-medium">{cat}</span>
                <span className="text-green-600">— {CATEGORIA_LABELS[cat]} sin problemas</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sorted.length === 0 && categoriasSinIssues.length === 0 && (
        <p className="text-sm text-slate-500 py-4 text-center">
          No se encontraron validaciones registradas.
        </p>
      )}
    </div>
  );
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
  const config = {
    ERROR: {
      icon: <AlertCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-red-50 border-red-200 text-red-900',
      badgeCls: 'bg-red-100 text-red-700 border-red-200',
    },
    WARNING: {
      icon: <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-amber-50 border-amber-200 text-amber-900',
      badgeCls: 'bg-amber-100 text-amber-700 border-amber-200',
    },
    INFO: {
      icon: <Info className="h-3.5 w-3.5 text-blue-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-blue-50 border-blue-200 text-blue-900',
      badgeCls: 'bg-blue-100 text-blue-700 border-blue-200',
    },
  }[issue.severidad] ?? {
    icon: <Info className="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />,
    className: 'bg-slate-50 border-slate-200 text-slate-700',
    badgeCls: 'bg-slate-100 text-slate-600 border-slate-200',
  };

  return (
    <li
      className={cn('flex items-start gap-2 border rounded px-3 py-2 text-sm', config.className)}
      role="listitem"
    >
      {config.icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn('font-mono text-xs font-semibold border rounded px-1.5 py-0.5 leading-none', config.badgeCls)}>
            {issue.codigo}
          </span>
          {issue.campo_afectado && (
            <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1.5 py-0.5 leading-none">
              {issue.campo_afectado}
            </span>
          )}
        </div>
        <p className="mt-0.5 leading-snug">{issue.descripcion}</p>
        {issue.valor_encontrado && (
          <p className="text-xs opacity-75 mt-0.5">
            Encontrado: <span className="font-mono">{issue.valor_encontrado}</span>
            {issue.valor_esperado && (
              <> · Esperado: <span className="font-mono">{issue.valor_esperado}</span></>
            )}
          </p>
        )}
      </div>
    </li>
  );
}
