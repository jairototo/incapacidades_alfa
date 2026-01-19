import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { differenceInDays, addDays } from 'date-fns';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { DatePicker } from '@/components/ui/DatePicker';
import { CIE10Autocomplete } from '@/components/shared/CIE10Autocomplete';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';
import {
  getDatosIncapacidadSchema,
  type DatosIncapacidadARL,
  type DatosIncapacidadSalud,
} from '@/schemas/radicacionSchema';

interface DatosIncapacidadFormProps {
  tipo: 'ARL' | 'SALUD';
  initialData?: Partial<DatosIncapacidadARL | DatosIncapacidadSalud>;
  onBack: () => void;
  onContinue: (data: DatosIncapacidadARL | DatosIncapacidadSalud) => void;
}

export function DatosIncapacidadForm({
  tipo,
  initialData,
  onBack,
  onContinue,
}: DatosIncapacidadFormProps) {
  const schema = getDatosIncapacidadSchema(tipo);
  const [selectedCIE10, setSelectedCIE10] = useState<CatalogoCIE10 | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      tipo,
      ...initialData,
    } as any,
  });

  const fecha_inicio = watch('fecha_inicio');
  const fecha_fin = watch('fecha_fin');
  const dias_totales = watch('dias_totales');

  // Auto-calcular días totales cuando cambian las fechas
  useEffect(() => {
    if (fecha_inicio && fecha_fin) {
      const dias = differenceInDays(fecha_fin, fecha_inicio) + 1;
      if (dias > 0 && dias !== dias_totales) {
        setValue('dias_totales', dias);
      }
    }
  }, [fecha_inicio, fecha_fin, setValue, dias_totales]);

  // Actualizar valor en formulario cuando se selecciona CIE-10
  useEffect(() => {
    if (selectedCIE10) {
      setValue('diagnostico_cie10', selectedCIE10.codigo);
    } else {
      setValue('diagnostico_cie10', '');
    }
  }, [selectedCIE10, setValue]);

  const onSubmit = (data: any) => {
    onContinue(data);
  };

  const maxDate = addDays(new Date(), 30); // Permitir hasta 30 días en el futuro

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Título del formulario */}
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          Datos de la Incapacidad
        </h2>
        <p className="mt-1 text-sm text-gray-600">
          Ingrese los datos médicos y período de la incapacidad {tipo === 'ARL' ? '(Accidente Laboral)' : '(Salud)'}
        </p>
      </div>

      {/* Fechas de Incapacidad */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DatePicker
          label="Fecha de Inicio"
          value={fecha_inicio}
          onChange={(date) => setValue('fecha_inicio', date as Date)}
          error={errors.fecha_inicio?.message as string}
          required
          maxDate={maxDate}
        />
        <DatePicker
          label="Fecha de Fin"
          value={fecha_fin}
          onChange={(date) => setValue('fecha_fin', date as Date)}
          error={errors.fecha_fin?.message as string}
          required
          minDate={fecha_inicio}
          maxDate={maxDate}
        />
        <Input
          label="Días Totales"
          type="number"
          {...register('dias_totales', { valueAsNumber: true })}
          error={errors.dias_totales?.message as string}
          required
          disabled
          helperText="Calculado automáticamente"
          className="bg-gray-50"
        />
      </div>

      {/* Tipo de Enfermedad (solo ARL) o Subtipo (solo SALUD) */}
      {tipo === 'ARL' && (
        <Select
          label="Tipo de Enfermedad"
          {...register('tipo_enfermedad')}
          error={errors.tipo_enfermedad?.message as string}
          required
        >
          <option value="">Seleccione un tipo</option>
          <option value="ACCIDENTE_TRABAJO">Accidente de Trabajo</option>
          <option value="ENFERMEDAD_LABORAL">Enfermedad Laboral</option>
          <option value="ACCIDENTE_TRAYECTO">Accidente de Trayecto</option>
        </Select>
      )}

      {tipo === 'SALUD' && (
        <Select
          label="Subtipo de Incapacidad"
          {...register('subtipo')}
          error={errors.subtipo?.message as string}
          required
        >
          <option value="">Seleccione un subtipo</option>
          <option value="ENFERMEDAD_GENERAL">Enfermedad General</option>
          <option value="MATERNIDAD">Maternidad</option>
          <option value="LICENCIA">Licencia</option>
        </Select>
      )}

      {/* Diagnóstico CIE-10 */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Diagnóstico Médico
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Código CIE-10 <span className="text-red-500">*</span>
            </label>
            <CIE10Autocomplete
              value={selectedCIE10}
              onChange={setSelectedCIE10}
              error={errors.diagnostico_cie10?.message as string}
            />
          </div>

          <Textarea
            label="Descripción del Diagnóstico (Opcional)"
            {...register('descripcion_diagnostico')}
            error={errors.descripcion_diagnostico?.message as string}
            placeholder="Describa detalladamente el diagnóstico médico..."
            maxCount={500}
            showCount
            rows={4}
          />
        </div>
      </div>

      {/* Datos del Médico Tratante */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Datos del Médico Tratante (Opcional)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Nombre del Médico"
            {...register('nombre_medico')}
            error={errors.nombre_medico?.message as string}
            placeholder="Ej: Dr. Juan Pérez"
            helperText="Nombre completo del médico que emitió la incapacidad"
          />
          <Input
            label="Registro Médico"
            {...register('registro_medico')}
            error={errors.registro_medico?.message as string}
            placeholder="Ej: RM-12345"
            helperText="Número de registro profesional del médico"
          />
        </div>
      </div>

      {/* Información IPS/EPS */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Información de Atención Médica (Opcional)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="IPS"
            {...register('ips')}
            error={errors.ips?.message as string}
            placeholder="Clínica Santa María"
            helperText="Institución Prestadora de Salud"
          />
          <Input
            label="EPS"
            {...register('eps')}
            error={errors.eps?.message as string}
            placeholder="Sura EPS"
            helperText="Entidad Promotora de Salud"
          />
        </div>
      </div>

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
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Validando...' : 'Continuar'}
        </Button>
      </div>
    </form>
  );
}
