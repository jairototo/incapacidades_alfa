import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Building2, Heart, Check, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { TipoIncapacidad } from '@/types/api';

// Schema de validación Zod
const tipoIncapacidadSchema = z.object({
  tipo: z.enum(['ARL', 'SALUD'], {
    message: 'Debe seleccionar un tipo de incapacidad',
  }),
});

type TipoIncapacidadFormData = z.infer<typeof tipoIncapacidadSchema>;

export interface TipoIncapacidadSelectorProps {
  onContinue: (tipo: string) => void;
}

interface TipoOption {
  value: typeof TipoIncapacidad.ARL | typeof TipoIncapacidad.SALUD;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

const tipoOptions: TipoOption[] = [
  {
    value: TipoIncapacidad.ARL,
    label: 'ARL - Riesgos Laborales',
    description: 'Accidentes de trabajo o enfermedades laborales',
    icon: <Building2 className="w-12 h-12" />,
    color: 'blue',
  },
  {
    value: TipoIncapacidad.SALUD,
    label: 'SALUD - Enfermedad General',
    description: 'Incapacidades por enfermedad general o maternidad',
    icon: <Heart className="w-12 h-12" />,
    color: 'green',
  },
];

/**
 * Componente para seleccionar el tipo de incapacidad (ARL o SALUD)
 * Primer paso del wizard de radicación
 */
export function TipoIncapacidadSelector({ onContinue }: TipoIncapacidadSelectorProps) {
  const {
    watch,
    setValue,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<TipoIncapacidadFormData>({
    resolver: zodResolver(tipoIncapacidadSchema),
    mode: 'onChange',
  });

  const selectedTipo = watch('tipo');

  const handleSelectTipo = (tipo: string) => {
    setValue('tipo', tipo as 'ARL' | 'SALUD', {
      shouldValidate: true,
    });
  };

  const onSubmit = (data: TipoIncapacidadFormData) => {
    onContinue(data.tipo);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Seleccione el tipo de incapacidad
        </h2>
        <p className="text-gray-600">
          Escoja el tipo de incapacidad que desea radicar
        </p>
      </div>

      {/* Error message */}
      {errors.tipo && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{errors.tipo.message}</p>
        </div>
      )}

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tipoOptions.map((option) => {
          const isSelected = selectedTipo === option.value;

          return (
            <Card
              key={option.value}
              className={cn(
                'cursor-pointer transition-all duration-300 hover:shadow-lg',
                isSelected &&
                  'border-2 border-blue-600 shadow-xl ring-2 ring-blue-200',
                !isSelected && 'border-gray-200 hover:border-blue-300'
              )}
              onClick={() => handleSelectTipo(option.value)}
            >
              <CardHeader className="relative">
                {/* Check Icon - Positioned absolutely */}
                {isSelected && (
                  <div className="absolute top-4 right-4">
                    <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-full animate-in fade-in zoom-in duration-300">
                      <Check className="w-5 h-5 text-white" />
                    </div>
                  </div>
                )}

                {/* Icon */}
                <div
                  className={cn(
                    'mb-4 transition-colors duration-300',
                    isSelected && option.color === 'blue' && 'text-blue-600',
                    isSelected && option.color === 'green' && 'text-green-600',
                    !isSelected && 'text-gray-400'
                  )}
                >
                  {option.icon}
                </div>

                <CardTitle className="text-xl">{option.label}</CardTitle>
                <CardDescription className="mt-2 text-base">
                  {option.description}
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="flex items-center text-sm font-medium text-gray-500">
                  <span>
                    {isSelected ? 'Tipo seleccionado' : 'Click para seleccionar'}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Continue Button */}
      <div className="flex justify-end pt-4">
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
