import type { FiltrosConsulta } from '@/services/consultaEmpresaService';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

const ESTADOS = ['', 'RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 'RECHAZADA', 'EN_PAGO', 'PAGADA'];

interface Props { value: FiltrosConsulta; onChange: (f: FiltrosConsulta) => void; }

export function FiltrosConsultaEmpresa({ value, onChange }: Props) {
  const set = (patch: Partial<FiltrosConsulta>) => onChange({ ...value, ...patch });
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 bg-white rounded-lg shadow-sm border border-border p-4">
      <div className="space-y-1">
        <Label htmlFor="f-estado">Estado</Label>
        <select
          id="f-estado"
          className="w-full rounded-md border border-input p-2 text-sm"
          value={value.estado ?? ''}
          onChange={(e) => set({ estado: e.target.value || undefined })}
        >
          {ESTADOS.map((s) => <option key={s} value={s}>{s || 'Todos'}</option>)}
        </select>
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-doc">Documento empleado</Label>
        <Input
          id="f-doc"
          value={value.empleado_documento ?? ''}
          onChange={(e) => set({ empleado_documento: e.target.value || undefined })}
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-desde">Inicio desde</Label>
        <Input
          id="f-desde"
          type="date"
          value={value.fecha_inicio_desde ?? ''}
          onChange={(e) => set({ fecha_inicio_desde: e.target.value || undefined })}
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-hasta">Inicio hasta</Label>
        <Input
          id="f-hasta"
          type="date"
          value={value.fecha_inicio_hasta ?? ''}
          onChange={(e) => set({ fecha_inicio_hasta: e.target.value || undefined })}
        />
      </div>
    </div>
  );
}
