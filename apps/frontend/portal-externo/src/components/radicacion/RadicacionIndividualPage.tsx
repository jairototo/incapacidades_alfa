import { useState, useEffect } from 'react';
import type { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { format, differenceInDays, addDays } from 'date-fns';
import { FileText, Stethoscope, User } from 'lucide-react';

import { radicacionIndividualSchema, type RadicacionIndividualFormData } from '@/schemas/radicacionIndividualSchema';
import { radicarIndividual } from '@/services/radicacionService';
import { useToast } from '@/hooks/use-toast';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { DatePicker } from '@/components/ui/DatePicker';
import { FileUpload } from '@/components/ui/FileUpload';
import { FileList } from '@/components/ui/FilePreview';
import { EmpleadoSelector } from '@/components/radicacion/EmpleadoSelector';
import { ProrrogaSwitch } from '@/components/radicacion/ProrrogaSwitch';
import { CIE10Autocomplete } from '@/components/shared/CIE10Autocomplete';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';

/**
 * Página de radicación individual de incapacidades ARL.
 * No requiere paso de empresa/solicitante — se resuelven server-side con el JWT.
 * Submite a POST /incapacidades/radicar con FormData multipart.
 */
export function RadicacionIndividualPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  // CIE-10 selection is managed separately (component manages its own object state)
  const [selectedCIE10, setSelectedCIE10] = useState<CatalogoCIE10 | null>(null);

  // File state — managed in local state (not in react-hook-form to keep types clean)
  const [filesIncapacidad, setFilesIncapacidad] = useState<File[]>([]);
  const [filesHistoria, setFilesHistoria] = useState<File[]>([]);
  const [filesSoportes, setFilesSoportes] = useState<File[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RadicacionIndividualFormData>({
    resolver: zodResolver(radicacionIndividualSchema),
    defaultValues: { prorroga: false },
  });

  const fecha_inicio = watch('fecha_inicio');
  const fecha_fin = watch('fecha_fin');

  // Sync CIE-10 selection into form fields
  useEffect(() => {
    if (selectedCIE10) {
      setValue('diagnostico_cie10', selectedCIE10.codigo, { shouldValidate: true });
      setValue('descripcion_diagnostico', selectedCIE10.descripcion);
    } else {
      setValue('diagnostico_cie10', '');
      setValue('descripcion_diagnostico', '');
    }
  }, [selectedCIE10, setValue]);

  // File handlers — incapacidad médica (max 1)
  const handleIncapacidadSelect = (files: File[]) => {
    setFilesIncapacidad([files[0]]);
  };
  const handleRemoveIncapacidad = () => {
    setFilesIncapacidad([]);
  };

  // File handlers — historia clínica (max 3)
  const handleHistoriaSelect = (files: File[]) => {
    setFilesHistoria((prev) => [...prev, ...files].slice(0, 3));
  };
  const handleRemoveHistoria = (index: number) => {
    setFilesHistoria((prev) => prev.filter((_, i) => i !== index));
  };

  // File handlers — soportes adicionales (max 5)
  const handleSoportesSelect = (files: File[]) => {
    setFilesSoportes((prev) => [...prev, ...files].slice(0, 5));
  };
  const handleRemoveSoportes = (index: number) => {
    setFilesSoportes((prev) => prev.filter((_, i) => i !== index));
  };

  // Compute dias_totales for FormData (not a form field — calculated on submit)
  const computeDias = (inicio?: Date, fin?: Date): number => {
    if (!inicio || !fin) return 1;
    return Math.max(1, Math.round(differenceInDays(fin, inicio)) + 1);
  };

  const onSubmit = async (data: RadicacionIndividualFormData) => {
    // Gate: require at least the incapacidad médica file
    if (filesIncapacidad.length === 0) {
      toast({
        title: 'Documento requerido',
        description: 'Debe adjuntar el documento de incapacidad médica.',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const fd = new FormData();

      // Required fields
      fd.append('empleado_id', data.empleado_id);
      fd.append('tipo_enfermedad', data.tipo_enfermedad);
      fd.append('fecha_inicio', format(data.fecha_inicio, 'yyyy-MM-dd'));
      fd.append('fecha_fin', format(data.fecha_fin, 'yyyy-MM-dd'));
      fd.append('dias_totales', String(computeDias(data.fecha_inicio, data.fecha_fin)));
      fd.append('diagnostico_cie10', data.diagnostico_cie10);
      fd.append('nombre_medico', data.nombre_medico);
      fd.append('registro_medico', data.registro_medico);
      fd.append('prorroga', String(data.prorroga));

      // Optional text fields
      if (data.descripcion_diagnostico) fd.append('descripcion_diagnostico', data.descripcion_diagnostico);
      if (data.ips) fd.append('ips', data.ips);
      if (data.observaciones) fd.append('observaciones', data.observaciones);

      // Required file
      fd.append('incapacidad_medica', filesIncapacidad[0]);

      // Optional files
      filesHistoria.forEach((f) => fd.append('historia_clinica', f));
      filesSoportes.forEach((f) => fd.append('soportes_adicionales', f));

      const result = await radicarIndividual(fd);
      const item = result.items[0];

      if (item?.success) {
        toast({
          title: 'Incapacidad radicada',
          description: `Número de radicado: ${item.numero ?? '—'}`,
        });
        navigate('/consulta');
      } else {
        toast({
          title: 'Error al radicar',
          description: item?.error ?? 'No se pudo radicar la incapacidad.',
          variant: 'destructive',
        });
      }
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ detail?: string | unknown[] }>;
      const detail = axiosErr?.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : err instanceof Error
            ? err.message
            : 'Error de red. Intente nuevamente.';
      toast({ title: 'Error de red', description: msg, variant: 'destructive' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const maxDate = addDays(new Date(), 30);

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="bg-white rounded-lg shadow-sm border border-border p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8" noValidate>
          {/* Heading */}
          <div className="border-b pb-4">
            <h1 className="text-2xl font-bold text-foreground">Radicación Individual</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Radique una incapacidad ARL para el empleado seleccionado.
            </p>
          </div>

          {/* ── Sección Empleado ─────────────────────────────────────────────── */}
          <section className="space-y-6">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Empleado</h2>
            </div>

            <Controller
              name="empleado_id"
              control={control}
              render={({ field }) => (
                <EmpleadoSelector
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.empleado_id?.message}
                />
              )}
            />

            {/* Prórroga */}
            <Controller
              name="prorroga"
              control={control}
              render={({ field }) => (
                <ProrrogaSwitch checked={field.value} onChange={field.onChange} />
              )}
            />
          </section>

          {/* ── Sección Incapacidad ──────────────────────────────────────────── */}
          <section className="space-y-6 border-t pt-6">
            <div className="flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Información médica</h2>
            </div>

            {/* Tipo de enfermedad */}
            <Select
              id="tipo_enfermedad"
              label="Tipo de enfermedad"
              {...register('tipo_enfermedad')}
              error={errors.tipo_enfermedad?.message}
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
                onChange={(date) =>
                  setValue('fecha_inicio', date as Date, { shouldValidate: true })
                }
                error={errors.fecha_inicio?.message as string}
                required
                maxDate={maxDate}
              />
              <DatePicker
                label="Fecha de fin"
                value={fecha_fin}
                onChange={(date) =>
                  setValue('fecha_fin', date as Date, { shouldValidate: true })
                }
                error={errors.fecha_fin?.message as string}
                required
                minDate={fecha_inicio}
                maxDate={maxDate}
              />
              <Input
                label="Días totales"
                type="number"
                value={fecha_inicio && fecha_fin ? computeDias(fecha_inicio, fecha_fin) : ''}
                readOnly
                disabled
                helperText="Calculado automáticamente"
                className="bg-gray-50"
              />
            </div>

            {/* Diagnóstico CIE-10 */}
            <div className="border-t pt-4 space-y-4">
              <div>
                <label htmlFor="cie10-input" className="block text-sm font-medium text-foreground mb-2">
                  Código CIE-10 <span className="text-red-500">*</span>
                </label>
                <CIE10Autocomplete
                  id="cie10-input"
                  value={selectedCIE10}
                  onChange={setSelectedCIE10}
                  error={errors.diagnostico_cie10?.message as string}
                />
              </div>

              <Textarea
                label="Descripción del diagnóstico"
                {...register('descripcion_diagnostico')}
                error={errors.descripcion_diagnostico?.message as string}
                placeholder="Describa el diagnóstico médico..."
                maxCount={500}
                showCount
                rows={3}
              />
            </div>

            {/* Médico tratante */}
            <div className="border-t pt-4">
              <h3 className="text-base font-semibold text-foreground mb-4">
                Médico tratante <span className="text-red-500">*</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Nombre del médico"
                  {...register('nombre_medico')}
                  error={errors.nombre_medico?.message as string}
                  placeholder="Ej: Dr. Juan Pérez"
                  required
                />
                <Input
                  label="Registro médico"
                  {...register('registro_medico')}
                  error={errors.registro_medico?.message as string}
                  placeholder="Ej: RM-12345"
                  required
                />
              </div>
            </div>

            {/* IPS y observaciones */}
            <div className="border-t pt-4">
              <h3 className="text-base font-semibold text-foreground mb-4">
                Información adicional
              </h3>
              <div className="space-y-4">
                <Input
                  label="IPS (Institución Prestadora de Salud)"
                  {...register('ips')}
                  error={errors.ips?.message as string}
                  placeholder="Clínica Santa María"
                />
                <Textarea
                  label="Observaciones"
                  {...register('observaciones')}
                  error={errors.observaciones?.message as string}
                  placeholder="Observaciones adicionales sobre la incapacidad..."
                  maxCount={1000}
                  showCount
                  rows={3}
                />
              </div>
            </div>
          </section>

          {/* ── Sección Documentos ──────────────────────────────────────────── */}
          <section className="space-y-6 border-t pt-6">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Documentos adjuntos</h2>
            </div>

            {/* Incapacidad Médica — REQUERIDA */}
            <div className="space-y-3">
              <h3 className="text-base font-semibold text-foreground">
                Incapacidad Médica <span className="text-red-500">*</span>
              </h3>
              <p className="text-sm text-muted-foreground">
                Documento de incapacidad emitido por el médico tratante (1 archivo — PDF, JPG, PNG, máx. 10 MB)
              </p>
              {filesIncapacidad.length === 0 ? (
                <FileUpload
                  onFileSelect={handleIncapacidadSelect}
                  maxFiles={1}
                  multiple={false}
                />
              ) : (
                <FileList files={filesIncapacidad} onRemove={handleRemoveIncapacidad} />
              )}
            </div>

            {/* Historia Clínica — OPCIONAL */}
            <div className="space-y-3 border-t pt-4">
              <h3 className="text-base font-semibold text-foreground">
                Historia Clínica{' '}
                <span className="text-muted-foreground text-sm font-normal">(Opcional)</span>
              </h3>
              <p className="text-sm text-muted-foreground">
                Documentos de historia clínica relacionados (hasta 3 archivos)
              </p>
              {filesHistoria.length < 3 && (
                <FileUpload
                  onFileSelect={handleHistoriaSelect}
                  maxFiles={3 - filesHistoria.length}
                />
              )}
              {filesHistoria.length > 0 && (
                <FileList files={filesHistoria} onRemove={handleRemoveHistoria} />
              )}
            </div>

            {/* Soportes Adicionales — OPCIONAL */}
            <div className="space-y-3 border-t pt-4">
              <h3 className="text-base font-semibold text-foreground">
                Soportes Adicionales{' '}
                <span className="text-muted-foreground text-sm font-normal">(Opcional)</span>
              </h3>
              <p className="text-sm text-muted-foreground">
                Documentos de siniestro, accidente laboral u otros soportes (hasta 5 archivos)
              </p>
              {filesSoportes.length < 5 && (
                <FileUpload
                  onFileSelect={handleSoportesSelect}
                  maxFiles={5 - filesSoportes.length}
                />
              )}
              {filesSoportes.length > 0 && (
                <FileList files={filesSoportes} onRemove={handleRemoveSoportes} />
              )}
            </div>
          </section>

          {/* ── Acciones ────────────────────────────────────────────────────── */}
          <div className="flex justify-between pt-6 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/')}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting || filesIncapacidad.length === 0}
            >
              {isSubmitting ? 'Radicando…' : 'Radicar Incapacidad'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
