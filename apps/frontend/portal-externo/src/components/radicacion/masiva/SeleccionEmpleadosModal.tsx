import { useState } from 'react';
import { useEmpleadosDeMiEmpresa } from '@/services/empresaEmpleadoService';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Props {
  open: boolean;
  onClose: () => void;
  onDownload: (ids: string[]) => void;
}

export function SeleccionEmpleadosModal({ open, onClose, onDownload }: Props) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { data: empleados = [], isLoading } = useEmpleadosDeMiEmpresa(search);

  if (!open) return null;

  const toggle = (id: string) =>
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">
            Seleccionar empleados para la plantilla
          </h2>
          <p className="text-sm text-muted-foreground">
            Sin selección, la plantilla se descarga solo con encabezados.
          </p>
        </div>

        <div className="p-4">
          <Input
            placeholder="Buscar…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <ul className="flex-1 overflow-auto px-4 divide-y">
          {isLoading && (
            <li className="py-2 text-sm text-muted-foreground">Cargando…</li>
          )}
          {empleados.map((e) => (
            <li key={e.id} className="py-2 flex items-center gap-2">
              <input
                type="checkbox"
                aria-label={`Seleccionar ${e.nombres} ${e.apellidos}`}
                checked={selected.has(e.id)}
                onChange={() => toggle(e.id)}
              />
              <span className="text-sm">
                {e.nombres} {e.apellidos} — {e.numero_documento}
              </span>
            </li>
          ))}
        </ul>

        <div className="p-4 border-t border-border flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={() => onDownload([...selected])}>
            Descargar plantilla
          </Button>
        </div>
      </div>
    </div>
  );
}
