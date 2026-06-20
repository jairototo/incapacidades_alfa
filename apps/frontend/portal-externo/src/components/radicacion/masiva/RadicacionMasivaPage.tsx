import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { unzipSync } from 'fflate';
import { SeleccionEmpleadosModal } from './SeleccionEmpleadosModal';
import { TablaValidacion, type DocMap } from './TablaValidacion';
import { ZipUpload } from './ZipUpload';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/use-toast';
import {
  descargarPlantilla, validarExcel, mapearZip, radicarMasiva, type ValidacionFila,
} from '@/services/bulkRadicacionService';

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
    URL.revokeObjectURL(url); setModalOpen(false);
  };

  const handleExcel = async (file: File) => {
    const res = await validarExcel(file);
    setFilas(res.filas);
    setDocumentos({});
    setMostrarBloqueos(false);
  };

  const addDoc = (empleadoId: string, tipo: string, file: File) =>
    setDocumentos((p) => ({ ...p, [empleadoId]: { ...p[empleadoId], [tipo]: file } }));

  const deleteRow = (fila: number) => setFilas((p) => p.filter((f) => f.fila !== fila));

  const handleZip = async (file: File) => {
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
      <h1 className="text-2xl font-bold text-foreground">Radicación Masiva</h1>
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
