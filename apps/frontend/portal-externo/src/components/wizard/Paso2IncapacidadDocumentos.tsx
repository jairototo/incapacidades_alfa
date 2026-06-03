import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { differenceInDays, addDays } from 'date-fns';
import { useEffect, useState } from 'react';
import { FileText, Stethoscope } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { DatePicker } from '@/components/ui/DatePicker';
import { FileUpload } from '@/components/ui/FileUpload';
import { FileList } from '@/components/ui/FilePreview';
import { CIE10Autocomplete } from '@/components/shared/CIE10Autocomplete';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';
import {
  datosIncapacidadSchema,
  documentosSchema,
  type DatosIncapacidadFormData,
  type DocumentosFormData,
} from '@/schemas/radicacionSchema';

export interface Paso2FormData {
  incapacidad: DatosIncapacidadFormData;
  documentos: DocumentosFormData;
}

interface Paso2Props {
  initialData?: Partial<Paso2FormData>;
  onBack: () => void;
  onContinue: (data: Paso2FormData) => void;
}

/**
 * Paso 2 del wizard de radicación.
 * Captura los datos de la incapacidad ARL y los documentos adjuntos.
 * Combina ambas secciones en un solo paso con un único submit.
 */
export function Paso2IncapacidadDocumentos({ initialData, onBack, onContinue }: Paso2Props) {
  const [selectedCIE10, setSelectedCIE10] = useState<CatalogoCIE10 | null>(null);

  // Form de incapacidad
  const incapacidadForm = useForm<DatosIncapacidadFormData>({
    resolver: zodResolver(datosIncapacidadSchema),
    defaultValues: initialData?.incapacidad,
  });

  // Form de documentos
  const documentosForm = useForm<DocumentosFormData>({
    resolver: zodResolver(documentosSchema) as any,
    defaultValues: {
      incapacidad_medica: initialData?.documentos?.incapacidad_medica || [],
      historia_clinica: initialData?.documentos?.historia_clinica || [],
      soportes_adicionales: initialData?.documentos?.soportes_adicionales || [],
    },
  });

  const fecha_inicio = incapacidadForm.watch('fecha_inicio');
  const fecha_fin = incapacidadForm.watch('fecha_fin');
  const dias_totales = incapacidadForm.watch('dias_totales');
  const incapacidad_medica = documentosForm.watch('incapacidad_medica');
  const historia_clinica = documentosForm.watch('historia_clinica');
  const soportes_adicionales = documentosForm.watch('soportes_adicionales');

  // Auto-calcular días totales
  useEffect(() => {
    if (fecha_inicio && fecha_fin) {
      const dias = differenceInDays(fecha_fin, fecha_inicio) + 1;
      if (dias > 0 && dias !== dias_totales) {
        incapacidadForm.setValue('dias_totales', dias);
      }
    }
  }, [fecha_inicio, fecha_fin, dias_totales, incapacidadForm]);

  // Sincronizar selección CIE-10
  useEffect(() => {
    if (selectedCIE10) {
      incapacidadForm.setValue('diagnostico_cie10', selectedCIE10.codigo, { shouldValidate: true });
      incapacidadForm.setValue('descripcion_diagnostico', selectedCIE10.descripcion);
    } else {
      incapacidadForm.setValue('diagnostico_cie10', '');
      incapacidadForm.setValue('descripcion_diagnostico', '');
    }
  }, [selectedCIE10, incapacidadForm]);

  const maxDate = addDays(new Date(), 30);

  // Handlers documentos
  const handleIncapacidadMedicaSelect = (files: File[]) => {
    documentosForm.setValue('incapacidad_medica', [files[0]], { shouldValidate: true });
  };
  const handleHistoriaClinicaSelect = (files: File[]) => {
    const current = historia_clinica || [];
    documentosForm.setValue('historia_clinica', [...current, ...files].slice(0, 3), { shouldValidate: true });
  };
  const handleSoportesSelect = (files: File[]) => {
    const current = soportes_adicionales || [];
    documentosForm.setValue('soportes_adicionales', [...current, ...files].slice(0, 5), { shouldValidate: true });
  };
  const handleRemoveIncapacidadMedica = () => {
    documentosForm.setValue('incapacidad_medica', [], { shouldValidate: true });
  };
  const handleRemoveHistoriaClinica = (index: number) => {
    const updated = (historia_clinica || []).filter((_, i) => i !== index);
    documentosForm.setValue('historia_clinica', updated, { shouldValidate: true });
  };
  const handleRemoveSoportes = (index: number) => {
    const updated = (soportes_adicionales || []).filter((_, i) => i !== index);
    documentosForm.setValue('soportes_adicionales', updated, { shouldValidate: true });
  };

  // Submit doble — valida ambos formularios antes de continuar
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const [incapacidadValid, documentosValid] = await Promise.all([
      incapacidadForm.trigger(),
      documentosForm.trigger(),
    ]);

    if (!incapacidadValid || !documentosValid) return;

    const incapacidadData = incapacidadForm.getValues();
    const documentosData = documentosForm.getValues();

    onContinue({ incapacidad: incapacidadData, documentos: documentosData });
  };

  const incErrors = incapacidadForm.formState.errors;
  const docErrors = documentosForm.formState.errors;

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Título */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-foreground">Datos de la Incapacidad</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Ingrese los datos médicos, el período de incapacidad y adjunte los documentos requeridos.
        </p>
      </div>

      {/* ── Sección Incapacidad ─────────────────────────────────────────────── */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <Stethoscope className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">Información médica</h3>
        </div>

        {/* Tipo de enfermedad */}
        <Select
          label="Tipo de enfermedad"
          {...incapacidadForm.register('tipo_enfermedad')}
          error={incErrors.tipo_enfermedad?.message}
          required
        >
          <option value="">Seleccione un tipo</option>
          <option value="ACCIDENTE_TRABAJO">Accidente de Trabajo</option>
          <option value="ENFERMEDAD_LABORAL">Enfermedad Laboral</option>
          <option value="ACCIDENTE_TRAYECTO">Accidente de Trayecto</option>
        </Select>

        {/* Fechas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DatePicker
            label="Fecha de inicio"
            value={fecha_inicio}
            onChange={(date) => incapacidadForm.setValue('fecha_inicio', date as Date, { shouldValidate: true })}
            error={incErrors.fecha_inicio?.message as string}
            required
            maxDate={maxDate}
          />
          <DatePicker
            label="Fecha de fin"
            value={fecha_fin}
            onChange={(date) => incapacidadForm.setValue('fecha_fin', date as Date, { shouldValidate: true })}
            error={incErrors.fecha_fin?.message as string}
            required
            minDate={fecha_inicio}
            maxDate={maxDate}
          />
          <Input
            label="Días totales"
            type="number"
            {...incapacidadForm.register('dias_totales', { valueAsNumber: true })}
            error={incErrors.dias_totales?.message as string}
            disabled
            helperText="Calculado automáticamente"
            className="bg-gray-50"
          />
        </div>

        {/* Diagnóstico CIE-10 */}
        <div className="border-t pt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Código CIE-10 <span className="text-red-500">*</span>
            </label>
            <CIE10Autocomplete
              value={selectedCIE10}
              onChange={setSelectedCIE10}
              error={incErrors.diagnostico_cie10?.message as string}
            />
          </div>

          <Textarea
            label="Descripción del diagnóstico"
            {...incapacidadForm.register('descripcion_diagnostico')}
            error={incErrors.descripcion_diagnostico?.message as string}
            placeholder="Describa el diagnóstico médico..."
            maxCount={500}
            showCount
            rows={3}
          />
        </div>

        {/* Médico tratante */}
        <div className="border-t pt-4">
          <h4 className="text-base font-semibold text-foreground mb-4">
            Médico tratante <span className="text-red-500">*</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nombre del médico"
              {...incapacidadForm.register('nombre_medico')}
              error={incErrors.nombre_medico?.message as string}
              placeholder="Ej: Dr. Juan Pérez"
              required
            />
            <Input
              label="Registro médico"
              {...incapacidadForm.register('registro_medico')}
              error={incErrors.registro_medico?.message as string}
              placeholder="Ej: RM-12345"
              required
            />
          </div>
        </div>

        {/* IPS y observaciones */}
        <div className="border-t pt-4">
          <h4 className="text-base font-semibold text-foreground mb-4">
            Información adicional
          </h4>
          <div className="space-y-4">
            <Input
              label="IPS (Institución Prestadora de Salud)"
              {...incapacidadForm.register('ips')}
              error={incErrors.ips?.message as string}
              placeholder="Clínica Santa María"
            />
            <Textarea
              label="Observaciones"
              {...incapacidadForm.register('observaciones')}
              error={incErrors.observaciones?.message as string}
              placeholder="Observaciones adicionales sobre la incapacidad..."
              maxCount={1000}
              showCount
              rows={3}
            />
          </div>
        </div>
      </section>

      {/* ── Sección Documentos ──────────────────────────────────────────────── */}
      <section className="space-y-6 border-t pt-8">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">Documentos adjuntos</h3>
        </div>

        {/* Incapacidad Médica — REQUERIDO */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h4 className="text-base font-semibold text-foreground">
              Incapacidad Médica
              <span className="text-red-500 ml-1">*</span>
            </h4>
          </div>
          <p className="text-sm text-muted-foreground">
            Documento de incapacidad emitido por el médico tratante (1 archivo requerido — PDF, JPG, PNG, máx. 10 MB)
          </p>

          {incapacidad_medica.length === 0 ? (
            <FileUpload
              onFileSelect={handleIncapacidadMedicaSelect}
              maxFiles={1}
              multiple={false}
              error={docErrors.incapacidad_medica?.message}
            />
          ) : (
            <FileList files={incapacidad_medica} onRemove={handleRemoveIncapacidadMedica} />
          )}
        </div>

        {/* Historia Clínica — OPCIONAL */}
        <div className="space-y-3 border-t pt-4">
            <h4 className="text-base font-semibold text-foreground">
            Historia Clínica
            <span className="text-muted-foreground text-sm font-normal ml-2">(Opcional)</span>
          </h4>
          <p className="text-sm text-muted-foreground">
            Documentos de historia clínica relacionados (hasta 3 archivos)
          </p>

          {(!historia_clinica || historia_clinica.length < 3) && (
            <FileUpload
              onFileSelect={handleHistoriaClinicaSelect}
              maxFiles={3 - (historia_clinica?.length || 0)}
              error={docErrors.historia_clinica?.message}
            />
          )}
          {historia_clinica && historia_clinica.length > 0 && (
            <FileList files={historia_clinica} onRemove={handleRemoveHistoriaClinica} />
          )}
        </div>

        {/* Soportes Adicionales — OPCIONAL */}
        <div className="space-y-3 border-t pt-4">
            <h4 className="text-base font-semibold text-foreground">
            Soportes Adicionales
            <span className="text-muted-foreground text-sm font-normal ml-2">(Opcional)</span>
          </h4>
          <p className="text-sm text-muted-foreground">
            Documentos de siniestro, accidente laboral u otros soportes (hasta 5 archivos)
          </p>

          {(!soportes_adicionales || soportes_adicionales.length < 5) && (
            <FileUpload
              onFileSelect={handleSoportesSelect}
              maxFiles={5 - (soportes_adicionales?.length || 0)}
              error={docErrors.soportes_adicionales?.message}
            />
          )}
          {soportes_adicionales && soportes_adicionales.length > 0 && (
            <FileList files={soportes_adicionales} onRemove={handleRemoveSoportes} />
          )}
        </div>

        {/* Error total del form de documentos */}
        {docErrors.root && (
          <div className="rounded-lg bg-red-50 p-4">
            <p className="text-sm text-red-800">{docErrors.root.message}</p>
          </div>
        )}
      </section>

      {/* ── Navegación ──────────────────────────────────────────────────────── */}
      <div className="flex justify-between pt-6 border-t">
        <Button type="button" variant="outline" onClick={onBack}>
          Atrás
        </Button>
        <Button
          type="submit"
          variant="primary"
          disabled={incapacidad_medica.length === 0}
        >
          Radicar Incapacidad
        </Button>
      </div>
    </form>
  );
}
