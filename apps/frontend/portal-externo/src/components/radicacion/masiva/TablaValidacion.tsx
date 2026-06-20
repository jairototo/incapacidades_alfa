import { Trash2, AlertTriangle, Check } from 'lucide-react';
import type { ValidacionFila } from '@/services/bulkRadicacionService';
import { FileUpload } from '@/components/ui/FileUpload';

const SLOTS = ['INCAPACIDAD', 'HISTORIA_CLINICA', 'SOPORTE'] as const;
export type DocMap = Record<string, Partial<Record<(typeof SLOTS)[number], File>>>; // key: empleado_id

interface Props {
  filas: ValidacionFila[];
  documentos: DocMap;
  onAddDoc: (empleadoId: string, tipo: string, file: File) => void;
  onDelete: (fila: number) => void;
  blocking?: Set<number>;
}

export function TablaValidacion({ filas, documentos, onAddDoc, onDelete, blocking }: Props) {
  return (
    <div className="space-y-3">
      {filas.map((f) => {
        const isBlocking = blocking?.has(f.fila) ?? false;
        const errors = f.errores.filter((e) => e.severidad === 'ERROR');
        const warnings = f.errores.filter((e) => e.severidad === 'WARNING');
        return (
          <div
            key={f.fila}
            id={`fila-${f.fila}`}
            className={[
              'rounded-lg border p-4 transition-shadow',
              errors.length > 0 || isBlocking ? 'border-[#D92D20]' : 'border-border',
              isBlocking ? 'ring-2 ring-[#D92D20] bg-[#D92D20]/5' : '',
            ].join(' ')}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground">
                  Documento: {String(f.datos.numero_documento ?? '')}
                </p>
                {errors.length > 0 && (
                  <ul className="mt-2 list-disc pl-5 text-sm text-[#D92D20]">
                    {errors.map((e, i) => (
                      <li key={i}>{e.descripcion}</li>
                    ))}
                  </ul>
                )}
                {warnings.length > 0 && (
                  <ul className="mt-2 space-y-1 text-sm text-[#8a6d00]">
                    {warnings.map((e, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                        <span>{e.descripcion}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                type="button"
                aria-label="Eliminar fila"
                onClick={() => onDelete(f.fila)}
                className="ml-3 shrink-0 text-muted-foreground hover:text-[#D92D20]"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            {f.valida && f.empleado_id && (
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {SLOTS.map((tipo) => (
                  <div key={tipo}>
                    <p className="flex items-center gap-1 text-xs font-medium text-foreground mb-1">
                      {tipo}
                      {documentos[f.empleado_id!]?.[tipo] && (
                        <Check className="h-3.5 w-3.5 text-primary" aria-label="cargado" />
                      )}
                    </p>
                    <FileUpload
                      multiple={false}
                      maxFiles={1}
                      onFileSelect={(files) => files[0] && onAddDoc(f.empleado_id!, tipo, files[0])}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
