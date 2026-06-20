import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { unzipSync } from 'fflate';
import { SeleccionEmpleadosModal } from './SeleccionEmpleadosModal';
import { TablaValidacion, type DocMap } from './TablaValidacion';
import { ZipUpload } from './ZipUpload';
import { Button } from '@/components/ui/Button';
import { Download, PencilLine, Upload } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  descargarPlantilla, validarExcel, mapearZip, radicarMasiva, type ValidacionFila,
} from '@/services/bulkRadicacionService';

const PASOS = [
  { icon: Download, title: 'Descargue la plantilla', desc: 'Con o sin empleados pre-diligenciados desde su empresa.' },
  { icon: PencilLine, title: 'Diligencie la información', desc: 'Complete los datos de la incapacidad de cada empleado.' },
  { icon: Upload, title: 'Suba y radique', desc: 'Cargue el archivo y los soportes para radicar las incapacidades.' },
];

// Formato esperado por columna de la plantilla. Refleja las reglas reales del
// backend (validate_field_level / _parse_date / bulk_radicacion_service).
const CAMPOS: { campo: string; req: boolean; formato: string }[] = [
  { campo: 'numero_documento', req: true, formato: 'Documento de un empleado de su empresa' },
  { campo: 'tipo_documento', req: false, formato: 'CC, CE, PA o TI' },
  { campo: 'empleado_nombres', req: false, formato: 'Texto (informativo)' },
  { campo: 'empleado_apellidos', req: false, formato: 'Texto (informativo)' },
  { campo: 'tipo_enfermedad', req: true, formato: 'ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL o ACCIDENTE_TRAYECTO' },
  { campo: 'fecha_inicio', req: true, formato: 'Fecha AAAA-MM-DD (ej: 2026-06-01)' },
  { campo: 'fecha_fin', req: true, formato: 'Fecha AAAA-MM-DD, no anterior a fecha_inicio' },
  { campo: 'dias_totales', req: false, formato: 'Número entero. Debe coincidir con el rango de fechas' },
  { campo: 'diagnostico_cie10', req: true, formato: 'Código CIE-10 (ej: A00 o M54.5)' },
  { campo: 'descripcion_diagnostico', req: false, formato: 'Texto libre' },
  { campo: 'nombre_medico', req: true, formato: 'Texto' },
  { campo: 'registro_medico', req: true, formato: 'Letras, números y guiones' },
  { campo: 'ips', req: false, formato: 'Texto libre' },
  { campo: 'prorroga', req: false, formato: 'SI o NO (por defecto NO)' },
  { campo: 'observaciones', req: false, formato: 'Texto libre' },
];

export function RadicacionMasivaPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [filas, setFilas] = useState<ValidacionFila[]>([]);
  const [documentos, setDocumentos] = useState<DocMap>({});
  const [submitting, setSubmitting] = useState(false);
  const [mostrarBloqueos, setMostrarBloqueos] = useState(false);

  const handleDownload = async (ids: string[]) => {
    const blob = await descargarPlantilla(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'plantilla_incapacidades.xlsx'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); setModalOpen(false);
  };

  const handleExcel = async (file: File) => {
    try {
      const res = await validarExcel(file);
      setFilas(res.filas);
      setDocumentos({});
      setMostrarBloqueos(false);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      const detail = err?.response?.data?.detail;
      toast({ title: 'No se pudo validar el Excel',
        description: typeof detail === 'string' ? detail : 'Archivo inválido. Verifique el formato .xlsx',
        variant: 'destructive' });
    }
  };

  const addDoc = (empleadoId: string, tipo: string, file: File) =>
    setDocumentos((p) => ({ ...p, [empleadoId]: { ...p[empleadoId], [tipo]: file } }));

  const deleteRow = (fila: number) => {
    const row = filas.find((f) => f.fila === fila);
    if (row?.empleado_id) {
      setDocumentos((p) => { const next = { ...p }; delete next[row.empleado_id!]; return next; });
    }
    setFilas((p) => p.filter((f) => f.fila !== fila));
  };

  const handleZip = async (file: File) => {
    if (file.size > 20 * 1024 * 1024) {
      toast({ title: 'ZIP demasiado grande', description: 'El máximo es 20 MB', variant: 'destructive' });
      return;
    }
    try {
      const docs = filas.map((f) => String(f.datos.numero_documento ?? '')).filter(Boolean);
      await mapearZip(file, docs); // backend validates the mapping/convention
      // client-side: extract matching entries into the per-row doc map
      const buf = new Uint8Array(await file.arrayBuffer());
      const entries = unzipSync(buf);
      let matched = 0;
      for (const [name, bytes] of Object.entries(entries)) {
        const base = name.split('/').pop() ?? name;
        const m = base.match(/^([A-Za-z0-9]+)_([A-Z_]+)\.([A-Za-z0-9]+)$/);
        if (!m) continue;
        const [, doc, tipoRaw] = m;
        const tipo = tipoRaw === 'INCAPACIDAD' ? 'INCAPACIDAD'
          : tipoRaw === 'HISTORIA_CLINICA' ? 'HISTORIA_CLINICA'
          : tipoRaw.startsWith('SOPORTE') ? 'SOPORTE' : null;
        if (!tipo) continue;
        const fila = filas.find((f) => String(f.datos.numero_documento ?? '') === doc && f.empleado_id);
        if (!fila || !fila.empleado_id) continue;
        addDoc(fila.empleado_id, tipo, new File([bytes as BlobPart], base));
        matched++;
      }
      toast({ title: 'ZIP procesado', description: `${matched} documento(s) reconocido(s)` });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      const detail = err?.response?.data?.detail;
      toast({ title: 'No se pudo procesar el ZIP',
        description: typeof detail === 'string' ? detail : 'Archivo inválido o corrupto',
        variant: 'destructive' });
    }
  };

  const blocking = useMemo(() => filas.filter((f) =>
    !f.valida || !f.empleado_id || !documentos[f.empleado_id ?? '']?.['INCAPACIDAD']), [filas, documentos]);
  const blockingSet = useMemo(() => new Set(blocking.map((f) => f.fila)), [blocking]);
  const canSubmit = filas.length > 0 && blocking.length === 0;

  const motivosBloqueo = useMemo(() => blocking.map((f) => {
    const razones: string[] = [];
    const errs = f.errores.filter((e) => e.severidad === 'ERROR');
    if (errs.length) razones.push(`${errs.length} error(es) de validación`);
    if (!f.empleado_id) razones.push('empleado no reconocido');
    if (f.empleado_id && !documentos[f.empleado_id]?.['INCAPACIDAD']) razones.push('falta documento INCAPACIDAD');
    return { fila: f.fila, doc: String(f.datos.numero_documento ?? ''), razones };
  }), [blocking, documentos]);

  const scrollToFila = (fila: number) => {
    const el = document.getElementById(`fila-${fila}`);
    if (el && typeof el.scrollIntoView === 'function') {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const onSubmitClick = async () => {
    if (!canSubmit) {
      setMostrarBloqueos(true);
      if (blocking[0]) scrollToFila(blocking[0].fila);
      return;
    }
    setMostrarBloqueos(false);
    setSubmitting(true);
    try {
      const payload = filas.map((f) => ({ empleado_id: f.empleado_id, ...f.datos }));
      const docs: { name: string; file: File }[] = [];
      filas.forEach((f) => {
        const m = f.empleado_id ? documentos[f.empleado_id] ?? {} : {};
        Object.entries(m).forEach(([tipo, file]) => {
          if (file) {
            const ext = file.name.split('.').pop() ?? 'pdf';
            docs.push({ name: `${f.empleado_id}__${tipo}.${ext}`, file });
          }
        });
      });
      const res = await radicarMasiva(payload, docs);
      const ignorados = res.documentos_ignorados?.length
        ? ` (${res.documentos_ignorados.length} documento(s) no almacenado(s))` : '';
      toast({ title: 'Radicación masiva completa', description: `${res.total_radicadas} incapacidad(es) radicada(s)${ignorados}` });
      navigate('/consulta');
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      const detail = err?.response?.data?.detail;
      toast({ title: 'Error al radicar',
        description: typeof detail === 'string' ? detail : 'Intente nuevamente', variant: 'destructive' });
    } finally { setSubmitting(false); }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Radicación Masiva</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Radique varias incapacidades ARL a la vez mediante una plantilla de Excel.
        </p>
      </div>

      {filas.length === 0 && (
        <section className="rounded-xl border border-border bg-white p-6 shadow-[0_8px_30px_rgba(0,73,83,0.06)]">
          <h2 className="text-lg font-semibold text-foreground">¿Cómo funciona?</h2>
          <p className="mt-1 text-sm text-muted-foreground">Complete la radicación masiva en tres pasos.</p>
          <ol className="mt-5 grid gap-5 sm:grid-cols-3">
            {PASOS.map((p, i) => (
              <li key={i} className="flex gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <p.icon className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-foreground">
                    {i + 1}. {p.title}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">{p.desc}</p>
                </div>
              </li>
            ))}
          </ol>

          <details className="mt-5 rounded-lg border border-border bg-muted/30 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-foreground">
              Ver formato de campos
            </summary>
            <p className="mt-2 text-xs text-muted-foreground">
              Las fechas usan el formato <span className="font-mono">AAAA-MM-DD</span>. Los campos
              marcados con <span className="text-[#D92D20]">*</span> son obligatorios.
            </p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="py-1.5 pr-4 font-medium">Columna</th>
                    <th className="py-1.5 font-medium">Formato / valores</th>
                  </tr>
                </thead>
                <tbody>
                  {CAMPOS.map((c) => (
                    <tr key={c.campo} className="border-b border-border/60 align-top">
                      <td className="py-1.5 pr-4 font-mono text-foreground">
                        {c.campo}
                        {c.req && <span className="text-[#D92D20]" aria-hidden="true"> *</span>}
                      </td>
                      <td className="py-1.5 text-muted-foreground">{c.formato}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>
      )}

      <div className="flex flex-wrap gap-3">
        <Button onClick={() => setModalOpen(true)}>Descargar plantilla</Button>
        <label className="inline-flex items-center px-4 py-2 rounded-md border border-input cursor-pointer text-sm">
          Subir Excel diligenciado
          <input type="file" accept=".xlsx" aria-label="subir excel" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleExcel(e.target.files[0])} />
        </label>
      </div>

      {filas.length > 0 && (
        <>
          {mostrarBloqueos && blocking.length > 0 && (
            <div role="alert" className="rounded-lg border border-[#D92D20] bg-[#D92D20]/5 p-4">
              <p className="font-bold text-[#D92D20]">{blocking.length} fila(s) impiden radicar. Corrija lo siguiente:</p>
              <ul className="mt-2 list-disc pl-5 text-sm text-[#D92D20]">
                {motivosBloqueo.map((m) => (
                  <li key={m.fila}>
                    <button type="button" className="underline" onClick={() => scrollToFila(m.fila)}>
                      Documento {m.doc} (fila {m.fila})
                    </button>: {m.razones.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <ZipUpload onZipSelected={handleZip} />
          <TablaValidacion filas={filas} documentos={documentos} onAddDoc={addDoc} onDelete={deleteRow}
            blocking={mostrarBloqueos ? blockingSet : undefined} />
          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="text-sm text-muted-foreground">{filas.length - blocking.length}/{filas.length} listas para radicar.</p>
            <Button
              onClick={onSubmitClick}
              aria-disabled={!canSubmit || submitting}
              className={!canSubmit || submitting ? 'opacity-50 cursor-not-allowed' : ''}
            >
              {submitting ? 'Radicando…' : 'Radicar Incapacidades'}
            </Button>
          </div>
        </>
      )}

      <SeleccionEmpleadosModal open={modalOpen} onClose={() => setModalOpen(false)} onDownload={handleDownload} />
    </div>
  );
}
