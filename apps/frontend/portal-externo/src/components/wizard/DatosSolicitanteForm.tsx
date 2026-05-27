import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SolicitanteAutocomplete } from '@/components/shared/SolicitanteAutocomplete';
import { useCreateSolicitante } from '@/services/queries/useSolicitantes';
import { solicitanteSchema, type SolicitanteFormData } from '@/schemas/solicitante';
import type { Solicitante } from '@/types/solicitante';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { UserCheck, UserPlus, Loader2, AlertCircle } from 'lucide-react';

interface DatosSolicitanteFormProps {
  onNext: (solicitante: Solicitante) => void;
  onBack: () => void;
  initialData?: Solicitante | null;
}

/**
 * Paso 0: Formulario para capturar datos del solicitante
 * Permite buscar solicitante existente o crear uno nuevo
 */
export function DatosSolicitanteForm({
  onNext,
  onBack,
  initialData,
}: DatosSolicitanteFormProps) {
  const [selectedSolicitante, setSelectedSolicitante] = useState<Solicitante | null>(
    initialData || null
  );
  const [emailInput, setEmailInput] = useState('');
  const [isNewSolicitante, setIsNewSolicitante] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<SolicitanteFormData>({
    resolver: zodResolver(solicitanteSchema),
    defaultValues: initialData ? {
      correo: initialData.correo,
      nombres: initialData.nombres,
      apellidos: initialData.apellidos,
      telefono: initialData.telefono || '',
    } : undefined,
  });

  const createMutation = useCreateSolicitante();

  // Determinar si es nuevo solicitante cuando no hay selección
  useEffect(() => {
    setIsNewSolicitante(!selectedSolicitante && emailInput.length >= 5);
  }, [selectedSolicitante, emailInput]);

  // Prellenar formulario con solicitante seleccionado
  useEffect(() => {
    if (selectedSolicitante) {
      setValue('correo', selectedSolicitante.correo);
      setValue('nombres', selectedSolicitante.nombres);
      setValue('apellidos', selectedSolicitante.apellidos);
      setValue('telefono', selectedSolicitante.telefono || '');
    }
  }, [selectedSolicitante, setValue]);

  const handleSolicitanteChange = (solicitante: Solicitante | null) => {
    setSelectedSolicitante(solicitante);
    if (!solicitante) {
      reset();
    }
  };

  const handleEmailChange = (email: string) => {
    setEmailInput(email);
    setValue('correo', email);
    
    if (selectedSolicitante && email !== selectedSolicitante.correo) {
      setSelectedSolicitante(null);
    }
  };

  const onSubmit = async (data: SolicitanteFormData) => {
    if (selectedSolicitante) {
      onNext(selectedSolicitante);
      return;
    }

    try {
      const newSolicitante = await createMutation.mutateAsync(data);
      onNext(newSolicitante);
    } catch (error) {
      console.error('Error creando solicitante:', error);
    }
  };

  const isFormDisabled = !!selectedSolicitante;
  const isLoading = createMutation.isPending;

  return (
    <Card>
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            {isNewSolicitante ? (
              <>
                <UserPlus className="h-5 w-5 text-blue-600" />
                Nuevo Solicitante
              </>
            ) : (
              <>
                <UserCheck className="h-5 w-5 text-gray-600" />
                Datos del Solicitante
              </>
            )}
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Busque si ya está registrado o ingrese sus datos para crear uno nuevo
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Autocompletado de solicitante */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Correo Electrónico
            </label>
            <SolicitanteAutocomplete
              value={selectedSolicitante}
              onChange={handleSolicitanteChange}
              onEmailChange={handleEmailChange}
            />
            {errors.correo && (
              <p className="text-sm text-red-600">{errors.correo.message}</p>
            )}
          </div>

          {/* Badge de estado */}
          {selectedSolicitante && (
            <div className="p-3 bg-green-50 border border-green-300 rounded-lg flex items-start gap-2">
              <UserCheck className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-sm text-green-700">
                <span className="font-semibold">Solicitante registrado:</span>{' '}
                Los datos están bloqueados. Si desea modificarlos, contacte al administrador.
              </div>
            </div>
          )}

          {isNewSolicitante && (
            <div className="p-3 bg-blue-50 border border-blue-300 rounded-lg flex items-start gap-2">
              <UserPlus className="h-4 w-4 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-700">
                <span className="font-semibold">Nuevo solicitante:</span>{' '}
                Complete los datos para registrar este solicitante.
              </div>
            </div>
          )}

          {/* Nombres */}
          <div className="space-y-2">
            <label htmlFor="nombres" className="block text-sm font-medium text-gray-700">
              Nombres <span className="text-red-600">*</span>
            </label>
            <Input
              id="nombres"
              {...register('nombres')}
              placeholder="Ej: Juan Carlos"
              disabled={isFormDisabled || isLoading}
              error={errors.nombres?.message}
            />
          </div>

          {/* Apellidos */}
          <div className="space-y-2">
            <label htmlFor="apellidos" className="block text-sm font-medium text-gray-700">
              Apellidos <span className="text-red-600">*</span>
            </label>
            <Input
              id="apellidos"
              {...register('apellidos')}
              placeholder="Ej: Pérez Gómez"
              disabled={isFormDisabled || isLoading}
              error={errors.apellidos?.message}
            />
          </div>

          {/* Teléfono (opcional) */}
          <div className="space-y-2">
            <label htmlFor="telefono" className="block text-sm font-medium text-gray-700">
              Teléfono (opcional)
            </label>
            <Input
              id="telefono"
              {...register('telefono')}
              placeholder="Ej: 3001234567"
              disabled={isFormDisabled || isLoading}
              error={errors.telefono?.message}
              helperText="Solo números, de 7 a 20 dígitos"
            />
          </div>

          {/* Error de creación */}
          {createMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-300 rounded-lg flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
              <div className="text-sm text-red-700">
                {createMutation.error?.message || 'Error al crear solicitante. Intente nuevamente.'}
              </div>
            </div>
          )}

          {/* Botones de acción */}
          <div className="flex justify-between pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={isLoading}
            >
              Cancelar
            </Button>

            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isNewSolicitante ? 'Creando...' : 'Procesando...'}
                </>
              ) : (
                <>
                  {isNewSolicitante ? 'Crear y Continuar' : 'Continuar'}
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
}
