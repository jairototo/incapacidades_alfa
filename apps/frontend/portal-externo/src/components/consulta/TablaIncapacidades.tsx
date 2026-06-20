import type { IncapacidadListItem } from '@/services/consultaEmpresaService';

const ESTADO_COLOR: Record<string, string> = {
  RADICADA: 'bg-[#0094B3]/10 text-[#0094B3]',
  EN_AUDITORIA: 'bg-[#FECB00]/15 text-[#8a6d00]',
  APROBADA: 'bg-[#009B76]/10 text-[#009B76]',
  RECHAZADA: 'bg-[#D92D20]/10 text-[#D92D20]',
};

interface Props {
  items: IncapacidadListItem[];
  isLoading: boolean;
  onSelect: (id: string) => void;
}

export function TablaIncapacidades({ items, isLoading, onSelect }: Props) {
  if (isLoading) return <p className="p-6 text-sm text-muted-foreground">Cargando…</p>;
  if (items.length === 0) return <p className="p-6 text-sm text-muted-foreground">No hay incapacidades para los filtros seleccionados.</p>;

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-white">
      <table className="w-full text-sm">
        <thead className="bg-muted text-left">
          <tr>
            <th className="p-3 font-medium">Número</th>
            <th className="p-3 font-medium">Empleado</th>
            <th className="p-3 font-medium">CIE-10</th>
            <th className="p-3 font-medium">Periodo</th>
            <th className="p-3 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr
              key={it.id}
              className="border-t border-border hover:bg-muted/50 cursor-pointer"
              onClick={() => onSelect(it.id)}
            >
              <td className="p-3 font-medium text-primary">{it.numero}</td>
              <td className="p-3">
                {it.empleado
                  ? `${it.empleado.nombres ?? ''} ${it.empleado.apellidos ?? ''}`
                  : '—'}
                <br />
                <span className="text-xs text-muted-foreground">{it.empleado?.numero_documento}</span>
              </td>
              <td className="p-3">{it.diagnostico_cie10 ?? '—'}</td>
              <td className="p-3">
                {it.fecha_inicio} → {it.fecha_fin}{' '}
                <span className="text-xs text-muted-foreground">({it.dias_totales}d)</span>
              </td>
              <td className="p-3">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_COLOR[it.estado] ?? 'bg-muted text-foreground'}`}
                >
                  {it.estado}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
