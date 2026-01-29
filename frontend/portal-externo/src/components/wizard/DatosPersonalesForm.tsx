import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, UserCheck } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { AutocompleteEmpresa } from './AutocompleteEmpresa';
import { useSearchEmpleado, useEmpleado } from '@/services/empleadoService';
import { useSearchAfiliado } from '@/services/afiliadoService';
import { useEmpresa } from '@/services/empresaService';
import {
  getDatosPersonalesSchema,
  cleanTelefono,
} from '@/schemas/radicacionSchema';
import type { DatosPersonalesARL, DatosPersonalesSalud } from '@/schemas/radicacionSchema';
import type { EmpresaResponse } from '@/types/api';

export type DatosPersonalesFormData = DatosPersonalesARL | DatosPersonalesSalud;

export interface DatosPersonalesFormProps {
  tipo: 'ARL' | 'SALUD';
  initialData?: Partial<DatosPersonalesFormData>;
  onContinue: (data: DatosPersonalesFormData) => void;
  onBack: () => void;
}

/**
 * Formulario de datos personales del wizard de radicación (Paso 2)
 * Renderiza campos condicionales según el tipo de incapacidad (ARL/SALUD)
 */
export function DatosPersonalesForm({
  tipo,
  initialData,
  onContinue,
  onBack,
}: DatosPersonalesFormProps) {
  const schema = getDatosPersonalesSchema(tipo);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<DatosPersonalesFormData>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: {
      tipo,
      ...initialData,
    } as DatosPersonalesFormData,
  });

  const documento = watch('numero_documento') || '';
  const [shouldSearch, setShouldSearch] = useState(false);
  const [searchDocumento, setSearchDocumento] = useState('');

  // Autocomplete empleado (ARL) - Búsqueda al salir del campo
  const { data: empleadoExistente } = useSearchEmpleado(searchDocumento, {
    enabled: tipo === 'ARL' && shouldSearch && searchDocumento.length >= 6,
  });
  // Obtener empleado completo con empresa_id
  const { data: empleadoCompleto } = useEmpleado(empleadoExistente?.id);

  // Obtener empresa relacionada con el empleado
  const { data: empresaRelacionada } = useEmpresa(empleadoCompleto?.empresa_id);

  // Autocomplete afiliado (SALUD) - Búsqueda al salir del campo
  const { data: afiliadoExistente } = useSearchAfiliado(searchDocumento, {
    enabled: tipo === 'SALUD' && shouldSearch && searchDocumento.length >= 6,
  });

  // Handler para búsqueda al salir del campo documento
  const handleDocumentoBlur = () => {
    if (documento.length >= 6) {
      console.log('[Autocomplete] Buscando por documento al salir del campo:', documento);
      setSearchDocumento(documento);
      setShouldSearch(true);
    } else {
      // Limpiar búsqueda si el documento es muy corto
      setSearchDocumento('');
      setShouldSearch(false);
    }
  };

  // Limpiar campos cuando el documento cambie y no haya datos
  useEffect(() => {
    if (documento.length < 6) {
      // Limpiar campos si el documento es muy corto
      setValue('nombres', '');
      setValue('apellidos', '');
      setValue('email', '');
      setValue('telefono', '');
      if (tipo === 'ARL') {
        setValue('empresa_id', '');
        setValue('empresa_nombre', '');
      }
      // Resetear búsqueda
      setShouldSearch(false);
      setSearchDocumento('');
    }
  }, [documento, tipo, setValue]);

  // Autorellenar datos del empleado cuando se encuentre (ARL)
  useEffect(() => {
    if (empleadoCompleto && tipo === 'ARL') {
      console.log('[Autocomplete] Autorellenando empleado:', empleadoCompleto.id);
      setValue('nombres', empleadoCompleto.nombres);
      setValue('apellidos', empleadoCompleto.apellidos);
      setValue('email', empleadoCompleto.email || '');
      setValue('telefono', empleadoCompleto.telefono || '');
      setValue('cargo', empleadoCompleto.cargo || '');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setValue('fecha_ingreso' as any, empleadoCompleto.fecha_ingreso || new Date().toISOString().split('T')[0]);
      setValue('id', empleadoCompleto.id);
    }
  }, [empleadoCompleto?.id, tipo, setValue]);

  // Autorellenar empresa cuando se encuentre (ARL)
  useEffect(() => {
    if (empresaRelacionada && tipo === 'ARL') {
      console.log('[Autocomplete] Autorellenando empresa:', empresaRelacionada.id);
      setValue('empresa_id', empresaRelacionada.id, { shouldValidate: true });
      setValue('empresa_nombre', empresaRelacionada.razon_social);
    }
  }, [empresaRelacionada?.id, tipo, setValue]);

  // Autorellenar datos del afiliado si existe
  useEffect(() => {
    if (afiliadoExistente && tipo === 'SALUD') {
      setValue('nombres', afiliadoExistente.nombres);
      setValue('apellidos', afiliadoExistente.apellidos);
      setValue('email', afiliadoExistente.email || '');
      setValue('telefono', afiliadoExistente.telefono || '');
    }
  }, [afiliadoExistente, tipo, setValue]);

  const onSubmit = (data: DatosPersonalesFormData) => {
    // Limpiar teléfono (quitar guiones)
    if (data.telefono) {
      data.telefono = cleanTelefono(data.telefono);
    }
    onContinue(data);
  };

  const handleEmpresaSelect = (empresa: EmpresaResponse) => {
    if (tipo === 'ARL') {
      setValue('empresa_id', empresa.id, { shouldValidate: true });
      setValue('empresa_nombre', empresa.razon_social);
    }
  };

  const personaEncontrada = tipo === 'ARL' ? empleadoExistente : afiliadoExistente;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Datos Personales
        </h2>
        <p className="text-gray-600">
          {tipo === 'ARL'
            ? 'Ingrese los datos del empleado que sufrió el accidente laboral'
            : 'Ingrese los datos del afiliado'}
        </p>
      </div>

      {/* Indicador de persona encontrada */}
      {personaEncontrada && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
          <UserCheck className="w-5 h-5 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-900">
              {tipo === 'ARL' ? 'Empleado' : 'Afiliado'} encontrado
            </p>
            <p className="text-xs text-green-700">
              Los datos se han completado automáticamente
            </p>
          </div>
        </div>
      )}

      {/* Grid de campos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tipo de Documento */}
        <Select
          {...register('tipo_documento')}
          label="Tipo de Documento"
          error={errors.tipo_documento?.message}
          required
        >
          <option value="">Seleccione...</option>
          <option value="CC">Cédula de Ciudadanía</option>
          <option value="CE">Cédula de Extranjería</option>
          <option value="PA">Pasaporte</option>
          <option value="TI">Tarjeta de Identidad</option>
          {tipo === 'ARL' && <option value="NIT">NIT</option>}
        </Select>

        {/* Número de Documento */}
        <Input
          {...register('numero_documento')}
          label="Número de Documento"
          placeholder="Ej: 1234567890"
          error={errors.numero_documento?.message}
          required
          helperText="Solo números, entre 6 y 15 dígitos"
          onBlur={handleDocumentoBlur}
        />

        {/* Nombres */}
        <Input
          {...register('nombres')}
          label="Nombres"
          placeholder="Ej: Juan Carlos"
          error={errors.nombres?.message}
          required
        />

        {/* Apellidos */}
        <Input
          {...register('apellidos')}
          label="Apellidos"
          placeholder="Ej: Pérez García"
          error={errors.apellidos?.message}
          required
        />

        {/* Email */}
        <Input
          {...register('email')}
          type="email"
          label="Email"
          placeholder="ejemplo@correo.com"
          error={errors.email?.message}
        />

        {/* Teléfono */}
        <Input
          {...register('telefono')}
          label="Teléfono"
          placeholder="3001234567"
          error={errors.telefono?.message}
          helperText="10 dígitos sin espacios ni guiones"
        />
      </div>

      {/* Campos específicos ARL */}
      {tipo === 'ARL' && (
        <div className="space-y-6 pt-4 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Información Laboral
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Empresa (Autocomplete) */}
            <div className="md:col-span-2">
              <AutocompleteEmpresa
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                value={watch('empresa_id' as any) as string}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                nombre={watch('empresa_nombre' as any) as string}
                onSelect={handleEmpresaSelect}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                error={(errors as any).empresa_id?.message}
                readOnly={!!empresaRelacionada}
              />
            </div>

            {/* Cargo */}
            {/*<Input
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...register('cargo' as any)}
              label="Cargo"
              placeholder="Ej: Operario de producción"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              error={(errors as any).cargo?.message}
              required
            />*/}

            {/* Fecha de Ingreso */}
            {/*<Input
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...register('fecha_ingreso' as any, {
                valueAsDate: true,
              })}
              type="date"
              label="Fecha de Ingreso"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              error={(errors as any).fecha_ingreso?.message}
              required
            />*/}
          </div>
        </div>
      )}

      {/* Campos específicos SALUD */}
      {tipo === 'SALUD' && (
        <div className="space-y-6 pt-4 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Información de Póliza
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Número de Póliza */}
            <Input
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...register('numero_poliza' as any)}
              label="Número de Póliza"
              placeholder="Ej: POL-2024-001"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              error={(errors as any).numero_poliza?.message}
              required
            />

            {/* Tipo de Póliza */}
            <Select
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              {...register('tipo_poliza' as any)}
              label="Tipo de Póliza"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              error={(errors as any).tipo_poliza?.message}
              required
            >
              <option value="">Seleccione...</option>
              <option value="INDIVIDUAL">Individual</option>
              <option value="FAMILIAR">Familiar</option>
              <option value="COLECTIVA">Colectiva</option>
            </Select>
          </div>
        </div>
      )}

      {/* Botones de Navegación */}
      <div className="flex justify-between pt-6 border-t border-gray-200">
        <Button
          type="button"
          variant="outline"
          size="lg"
          onClick={onBack}
        >
          <ChevronLeft className="mr-2 w-5 h-5" />
          Volver
        </Button>

        <Button
          type="submit"
          size="lg"
          disabled={!isValid}
          className="min-w-[200px]"
        >
          Continuar
          <ChevronRight className="ml-2 w-5 h-5" />
        </Button>
      </div>
    </form>
  );
}
