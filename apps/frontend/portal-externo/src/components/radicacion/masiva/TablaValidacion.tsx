import { Trash2, AlertTriangle, Check, Paperclip, FileWarning } from 'lucide-react';
import type { ValidacionFila } from '@/services/bulkRadicacionService';
import { FileUpload } from '@/components/ui/FileUpload';

const SLOTS = ['INCAPACIDAD', 'HISTORIA_CLINICA', 'SOPORTE'] as const;
const SLOT_REQUERIDO: Record<(typeof SLOTS)[number], boolean> = {
  INCAPACIDAD: true,
  HISTORIA_CLINICA: false,
  SOPORTE: false,
};
export type DocMap = Record<string, Partial<Record<(typeof SLOTS)[number], File>>>; // key: empleado_id

interface Props {
  filas: ValidacionFila[];
  documentos: DocMap;
  onAddDoc: (empleadoId: string, tipo: string, file: File) => void;
  onDelete: (fila: number) => void;
  blocking?: Set<number>;
}

const txt = (v: unknown): string => {
  const s = String(v ?? '').trim();
  return s === '' || s === 'None' ? '—' : s;
};

const fmtFecha = (v: unknown): string => {
  const m = String(v ?? '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : txt(v);
};

function Campo({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="truncate text-sm text-foreground" title={value}>{value}</dd>
    </div>
  );
}

export function TablaValidacion({ filas, documentos, onAddDoc, onDelete, blocking }: Props) {
  return (
    <div className="space-y-3">
      {filas.map((f) => {
        const isBlocking = blocking?.has(f.fila) ?? false;
        const errors = f.errores.filter((e) => e.severidad === 'ERROR');
        const warnings = f.errores.filter((e) => e.severidad === 'WARNING');
        const d = f.datos;
        const nombre = `${txt(d.empleado_nombres)} ${txt(d.empleado_apellidos)}`.replace(/—/g, '').trim();
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
                  {nombre || 'Empleado'}{' '}
                  <span className="text-sm font-normal text-muted-foreground">
                    · Documento {txt(d.numero_documento)} · Fila {f.fila}
                  </span>
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

            {/* Datos parseados del Excel para esta fila */}
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 rounded-md bg-muted/40 p-3 sm:grid-cols-3 lg:grid-cols-4">
              <Campo label="Tipo enfermedad" value={txt(d.tipo_enfermedad)} />
              <Campo label="Inicio" value={fmtFecha(d.fecha_inicio)} />
              <Campo label="Fin" value={fmtFecha(d.fecha_fin)} />
              <Campo label="Días" value={txt(d.dias_totales)} />
              <Campo label="CIE-10" value={txt(d.diagnostico_cie10)} />
              <Campo label="Prórroga" value={d.prorroga ? 'Sí' : 'No'} />
              <Campo label="Médico" value={txt(d.nombre_medico)} />
              <Campo label="IPS" value={txt(d.ips)} />
            </dl>

            {/* Estado de documentos requeridos por tipo */}
            {f.valida && f.empleado_id ? (
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {SLOTS.map((tipo) => {
                  const file = documentos[f.empleado_id!]?.[tipo];
                  const requerido = SLOT_REQUERIDO[tipo];
                  const falta = requerido && !file;
                  return (
                    <div key={tipo}>
                      <p className="flex items-center gap-1 text-xs font-medium text-foreground mb-1">
                        {tipo}
                        {requerido && <span className="text-[#D92D20]" aria-hidden="true">*</span>}
                        {file ? (
                          <Check className="h-3.5 w-3.5 text-primary" aria-label="cargado" />
                        ) : falta ? (
                          <FileWarning className="h-3.5 w-3.5 text-[#D92D20]" aria-label="falta documento requerido" />
                        ) : null}
                      </p>
                      {file ? (
                        <p className="mb-1 flex items-center gap-1 text-xs text-muted-foreground" title={file.name}>
                          <Paperclip className="h-3 w-3 shrink-0" />
                          <span className="truncate">{file.name}</span>
                        </p>
                      ) : (
                        <p className={`mb-1 text-xs ${falta ? 'text-[#D92D20]' : 'text-muted-foreground'}`}>
                          {falta ? 'Falta (requerido)' : 'Sin adjuntar (opcional)'}
                        </p>
                      )}
                      <FileUpload
                        multiple={false}
                        maxFiles={1}
                        onFileSelect={(files) => files[0] && onAddDoc(f.empleado_id!, tipo, files[0])}
                      />
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="mt-3 text-xs text-muted-foreground">
                Corrija los errores de la fila para poder adjuntar los documentos.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
