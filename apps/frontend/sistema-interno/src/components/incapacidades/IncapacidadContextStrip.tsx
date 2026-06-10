/**
 * IncapacidadContextStrip - Compact summary strip for auditor context
 * Displays employee, company, CIE-10, and period without switching tabs
 */
import { AlertTriangle } from 'lucide-react';
import type { Incapacidad, EmpleadoFallback } from '@/types/incapacidad';
import { cn } from '@/lib/utils';

interface IncapacidadContextStripProps {
  incapacidad: Incapacidad;
  hasFraudAlert: boolean;
  empleadoFallback?: EmpleadoFallback | null;
}

function formatDateShort(dateStr: string): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr + 'T00:00:00').toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'short',
    });
  } catch {
    return dateStr;
  }
}

export function IncapacidadContextStrip({
  incapacidad,
  hasFraudAlert,
  empleadoFallback,
}: IncapacidadContextStripProps) {
  const empleado = incapacidad.empleado;
  const empresa = incapacidad.empresa;
  const sinEmpleadoBD = !empleado;

  const empleadoNombre = empleado
    ? `${empleado.nombres} ${empleado.apellidos}`
    : empleadoFallback?.nombres ?? '—';

  const empleadoDoc = empleado?.numero_documento ?? empleadoFallback?.numero_documento ?? '';
  const empresaNombre = empresa?.razon_social ?? '—';

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-md p-3 flex flex-wrap gap-3 text-sm mb-4">
      {/* Empleado */}
      <div
        data-testid="empleado-section"
        className={cn(
          'flex flex-col rounded px-2 py-1 border',
          hasFraudAlert
            ? 'bg-red-50 border-red-300 text-red-900'
            : sinEmpleadoBD
              ? 'bg-amber-50 border-amber-300 text-amber-900'
              : 'bg-white border-slate-200 text-slate-700'
        )}
      >
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Empleado
        </span>
        <div className="flex items-center gap-1.5">
          {hasFraudAlert && <AlertTriangle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="font-medium">{empleadoNombre}</span>
          {sinEmpleadoBD && (
            <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 rounded px-1 leading-none">
              Sin ficha
            </span>
          )}
        </div>
        {empleadoDoc && <span className="text-xs opacity-75">{empleadoDoc}</span>}
      </div>

      {/* Empresa */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Empresa
        </span>
        <span className="font-medium">{empresaNombre}</span>
        {empresa?.nit && <span className="text-xs text-slate-500">NIT {empresa.nit}</span>}
      </div>

      {/* Diagnóstico */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Diagnóstico
        </span>
        <span className="font-medium font-mono">{incapacidad.diagnostico_cie10 ?? '—'}</span>
        {incapacidad.diagnostico_descripcion && (
          <span className="text-xs text-slate-500 max-w-[160px] truncate">
            {incapacidad.diagnostico_descripcion}
          </span>
        )}
      </div>

      {/* Período */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Período
        </span>
        <span className="font-medium">
          {formatDateShort(incapacidad.fecha_inicio)} → {formatDateShort(incapacidad.fecha_fin)}
        </span>
        <span className="text-xs text-slate-500">{incapacidad.dias_totales} días</span>
      </div>
    </div>
  );
}
