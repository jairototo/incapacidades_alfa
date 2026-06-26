import { Button } from '@/components/ui/Button';

export interface ResultadoRadicacionItem {
  empleado_id: string;
  numero: string | null;
  numero_documento: string;
  dias_totales: number;
  success: boolean;
  error?: string;
}

interface Props {
  open: boolean;
  items: ResultadoRadicacionItem[];
  onIrAConsulta: () => void;
}

export function ResumenRadicacionModal({ open, items, onIrAConsulta }: Props) {
  if (!open) return null;
  const exitosas = items.filter((i) => i.success);
  const fallidas = items.filter((i) => !i.success);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resumen-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="w-full max-w-lg rounded-xl bg-white shadow-[0_8px_30px_rgba(0,73,83,0.15)] p-6 space-y-5">
        <div>
          <h2 id="resumen-title" className="text-xl font-bold text-foreground">
            Radicación completada
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {exitosas.length} de {items.length} incapacidad(es) radicada(s) exitosamente.
          </p>
        </div>

        {exitosas.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                    Nº Documento
                  </th>
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                    Número de Radicado
                  </th>
                  <th className="py-2 px-3 text-right font-medium text-muted-foreground">Días</th>
                </tr>
              </thead>
              <tbody>
                {exitosas.map((item) => (
                  <tr key={item.empleado_id} className="border-t border-border">
                    <td className="py-2 px-3 text-foreground">{item.numero_documento}</td>
                    <td className="py-2 px-3 font-mono text-foreground">{item.numero ?? '—'}</td>
                    <td className="py-2 px-3 text-right text-foreground">{item.dias_totales}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {fallidas.length > 0 && (
          <div className="rounded-lg border border-[#D92D20] bg-[#D92D20]/5 p-3">
            <p className="text-sm font-semibold text-[#D92D20]">
              {fallidas.length} registro(s) no radicado(s):
            </p>
            <ul className="mt-1 list-disc pl-4 text-sm text-[#D92D20]">
              {fallidas.map((item) => (
                <li key={item.empleado_id}>
                  Documento {item.numero_documento}: {item.error ?? 'error desconocido'}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button onClick={onIrAConsulta}>Ir a consulta</Button>
        </div>
      </div>
    </div>
  );
}
