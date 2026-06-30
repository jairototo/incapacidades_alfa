import { useState } from 'react';
import { AlertCircle, AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { ValidationInconsistenciaRead, Severidad, Categoria } from '@/types/validationInconsistencia';

interface Props {
  issues: ValidationInconsistenciaRead[];
}

const SEVERIDAD_CONFIG: Record<Severidad, { icon: typeof AlertCircle; className: string; label: string }> = {
  ERROR: { icon: AlertCircle, className: 'text-red-600 bg-red-50 border-red-200', label: 'Error' },
  WARNING: { icon: AlertTriangle, className: 'text-yellow-700 bg-yellow-50 border-yellow-200', label: 'Aviso' },
  INFO: { icon: Info, className: 'text-blue-600 bg-blue-50 border-blue-200', label: 'Info' },
};

const CATEGORIA_LABELS: Record<Categoria, string> = {
  FIELD_VALIDATION: 'Validación de campo',
  BUSINESS_RULE: 'Regla de negocio',
  FRAUD_ALERT: 'Alerta de fraude',
  INTEGRATION_CHECK: 'Verificación de integración',
};

function IssueRow({ issue }: { issue: ValidationInconsistenciaRead }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERIDAD_CONFIG[issue.severidad];
  const Icon = config.icon;

  return (
    <div className={cn('border rounded-lg p-3 mb-2', config.className)}>
      <div
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-2 flex-1">
          <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{issue.descripcion}</p>
            <p className="text-xs opacity-70 mt-0.5">
              {CATEGORIA_LABELS[issue.categoria]} · <code className="font-mono">{issue.codigo}</code>
              {issue.campo_afectado && <> · campo: <code className="font-mono">{issue.campo_afectado}</code></>}
            </p>
          </div>
        </div>
        <button className="ml-2 flex-shrink-0 opacity-60 hover:opacity-100">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
      {expanded && (issue.valor_encontrado || issue.valor_esperado) && (
        <div className="mt-2 pt-2 border-t border-current border-opacity-20 grid grid-cols-2 gap-2 text-xs">
          {issue.valor_encontrado && (
            <div>
              <span className="opacity-70">Valor encontrado:</span>
              <code className="block font-mono mt-0.5">{issue.valor_encontrado}</code>
            </div>
          )}
          {issue.valor_esperado && (
            <div>
              <span className="opacity-70">Valor esperado:</span>
              <code className="block font-mono mt-0.5">{issue.valor_esperado}</code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ValidationInconsistenciasList({ issues }: Props) {
  const errors = issues.filter((i) => i.severidad === 'ERROR');
  const warnings = issues.filter((i) => i.severidad === 'WARNING');
  const infos = issues.filter((i) => i.severidad === 'INFO');

  if (issues.length === 0) {
    return (
      <Card className="p-4 text-center bg-green-50 border-green-200">
        <AlertCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
        <p className="font-medium text-green-800">Sin inconsistencias detectadas</p>
        <p className="text-sm text-green-600 mt-1">Esta pre-incapacidad puede ser promovida.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {errors.length > 0 && (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3.5 w-3.5" />
            {errors.length} error{errors.length > 1 ? 'es' : ''}
          </Badge>
        )}
        {warnings.length > 0 && (
          <Badge variant="outline" className="gap-1 border-yellow-400 text-yellow-700">
            <AlertTriangle className="h-3.5 w-3.5" />
            {warnings.length} aviso{warnings.length > 1 ? 's' : ''}
          </Badge>
        )}
        {infos.length > 0 && (
          <Badge variant="secondary" className="gap-1">
            <Info className="h-3.5 w-3.5" />
            {infos.length} info
          </Badge>
        )}
      </div>

      {errors.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">Errores bloqueantes</p>
          {errors.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
      {warnings.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-yellow-700 uppercase tracking-wide mb-2">Avisos</p>
          {warnings.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
      {infos.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Información</p>
          {infos.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
    </div>
  );
}
