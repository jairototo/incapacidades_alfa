import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FileText } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { FileUpload } from '@/components/ui/FileUpload';
import { FileList } from '@/components/ui/FilePreview';
import { documentosSchema, type DocumentosFormData } from '@/schemas/radicacionSchema';

interface DocumentosFormProps {
  tipo: 'ARL' | 'SALUD';
  initialData?: Partial<DocumentosFormData>;
  onBack: () => void;
  onContinue: (data: DocumentosFormData) => void;
}

export function DocumentosForm({
  tipo,
  initialData,
  onBack,
  onContinue,
}: DocumentosFormProps) {
  const {
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DocumentosFormData>({
    resolver: zodResolver(documentosSchema) as any,
    defaultValues: {
      incapacidad_medica: initialData?.incapacidad_medica || [],
      historia_clinica: initialData?.historia_clinica || [],
      soportes_adicionales: initialData?.soportes_adicionales || [],
    },
  });

  const incapacidad_medica = watch('incapacidad_medica');
  const historia_clinica = watch('historia_clinica');
  const soportes_adicionales = watch('soportes_adicionales');

  const handleIncapacidadMedicaSelect = (files: File[]) => {
    // Solo permitir 1 archivo
    setValue('incapacidad_medica', [files[0]], { shouldValidate: true });
  };

  const handleHistoriaClinicaSelect = (files: File[]) => {
    const current = historia_clinica || [];
    const newFiles = [...current, ...files].slice(0, 3); // Máximo 3
    setValue('historia_clinica', newFiles, { shouldValidate: true });
  };

  const handleSoportesAdicionalesSelect = (files: File[]) => {
    const current = soportes_adicionales || [];
    const newFiles = [...current, ...files].slice(0, 5); // Máximo 5
    setValue('soportes_adicionales', newFiles, { shouldValidate: true });
  };

  const handleRemoveIncapacidadMedica = () => {
    setValue('incapacidad_medica', [], { shouldValidate: true });
  };

  const handleRemoveHistoriaClinica = (index: number) => {
    const current = historia_clinica || [];
    const updated = current.filter((_, i) => i !== index);
    setValue('historia_clinica', updated, { shouldValidate: true });
  };

  const handleRemoveSoportesAdicionales = (index: number) => {
    const current = soportes_adicionales || [];
    const updated = current.filter((_, i) => i !== index);
    setValue('soportes_adicionales', updated, { shouldValidate: true });
  };

  const onSubmit = (data: DocumentosFormData) => {
    onContinue(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* Título del formulario */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          Documentos
        </h2>
        <p className="mt-1 text-sm text-gray-600">
          Adjunte los documentos requeridos para la radicación de la incapacidad
        </p>
      </div>

      {/* Incapacidad Médica - REQUERIDO */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Incapacidad Médica
            <span className="text-red-500 ml-1">*</span>
          </h3>
        </div>
        <p className="text-sm text-gray-600">
          Documento de incapacidad emitido por el médico tratante (1 archivo requerido)
        </p>

        {incapacidad_medica.length === 0 ? (
          <FileUpload
            onFileSelect={handleIncapacidadMedicaSelect}
            maxFiles={1}
            multiple={false}
            error={errors.incapacidad_medica?.message}
          />
        ) : (
          <FileList
            files={incapacidad_medica}
            onRemove={handleRemoveIncapacidadMedica}
          />
        )}
      </div>

      {/* Historia Clínica - OPCIONAL */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Historia Clínica
            <span className="text-gray-500 text-sm font-normal ml-2">(Opcional)</span>
          </h3>
        </div>
        <p className="text-sm text-gray-600">
          Documentos de historia clínica relacionados (hasta 3 archivos)
        </p>

        {(!historia_clinica || historia_clinica.length < 3) && (
          <FileUpload
            onFileSelect={handleHistoriaClinicaSelect}
            maxFiles={3 - (historia_clinica?.length || 0)}
            error={errors.historia_clinica?.message}
          />
        )}

        {historia_clinica && historia_clinica.length > 0 && (
          <FileList
            files={historia_clinica}
            onRemove={handleRemoveHistoriaClinica}
          />
        )}
      </div>

      {/* Soportes Adicionales - OPCIONAL */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Soportes Adicionales
            <span className="text-gray-500 text-sm font-normal ml-2">(Opcional)</span>
          </h3>
        </div>
        <p className="text-sm text-gray-600">
          {tipo === 'ARL' 
            ? 'Documentos de siniestro, accidente laboral u otros soportes (hasta 5 archivos)'
            : 'Exámenes médicos, fórmulas u otros soportes (hasta 5 archivos)'}
        </p>

        {(!soportes_adicionales || soportes_adicionales.length < 5) && (
          <FileUpload
            onFileSelect={handleSoportesAdicionalesSelect}
            maxFiles={5 - (soportes_adicionales?.length || 0)}
            error={errors.soportes_adicionales?.message}
          />
        )}

        {soportes_adicionales && soportes_adicionales.length > 0 && (
          <FileList
            files={soportes_adicionales}
            onRemove={handleRemoveSoportesAdicionales}
          />
        )}
      </div>

      {/* Error general del formulario */}
      {errors.root && (
        <div className="rounded-lg bg-red-50 p-4">
          <p className="text-sm text-red-800">{errors.root.message}</p>
        </div>
      )}

      {/* Botones de navegación */}
      <div className="flex justify-between pt-6 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={isSubmitting}
        >
          Atrás
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting || incapacidad_medica.length === 0}
        >
          {isSubmitting ? 'Validando...' : 'Continuar'}
        </Button>
      </div>
    </form>
  );
}
