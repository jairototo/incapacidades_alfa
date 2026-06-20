import { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { useEmpleadosDeMiEmpresa } from '@/services/empresaEmpleadoService';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

interface Props {
  value?: string;
  onChange: (empleadoId: string) => void;
  error?: string;
}

export function EmpleadoSelector({ value, onChange, error }: Props) {
  const [search, setSearch] = useState('');
  const { data: empleados = [], isLoading } = useEmpleadosDeMiEmpresa(search);
  const seleccionado = empleados.find((e) => e.id === value);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <Label htmlFor="empleado-search">Empleado</Label>
        <span
          aria-label="ayuda"
          title="Si no encuentra al empleado, reporte el caso a Servicio al Cliente."
          className="text-muted-foreground cursor-help"
        >
          <HelpCircle className="h-4 w-4" />
        </span>
      </div>
      <Input
        id="empleado-search"
        placeholder="Buscar por nombre o documento…"
        value={seleccionado ? `${seleccionado.nombres} ${seleccionado.apellidos}` : search}
        onChange={(e) => {
          setSearch(e.target.value);
          if (value) onChange('');
        }}
      />
      {!seleccionado && (
        <ul className="max-h-48 overflow-auto rounded-md border border-border divide-y">
          {isLoading && (
            <li className="p-2 text-sm text-muted-foreground">Cargando…</li>
          )}
          {!isLoading && empleados.length === 0 && (
            <li className="p-2 text-sm text-muted-foreground">Sin resultados.</li>
          )}
          {empleados.map((e) => (
            <li key={e.id}>
              <button
                type="button"
                onClick={() => onChange(e.id)}
                className="w-full text-left p-2 text-sm hover:bg-muted"
              >
                {e.nombres} {e.apellidos} — {e.numero_documento}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="text-sm text-[#D92D20]">{error}</p>}
    </div>
  );
}
