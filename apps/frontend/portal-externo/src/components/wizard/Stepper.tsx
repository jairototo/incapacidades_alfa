import { Check } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface StepperProps {
  currentStep: number;
  totalSteps: number;
  steps?: string[];
}

/**
 * Stepper component para mostrar el progreso del wizard
 * Muestra los pasos completados, el paso actual y los pasos pendientes
 */
export function Stepper({ currentStep, totalSteps, steps }: StepperProps) {
  const defaultSteps = [
    'Tipo de Incapacidad',
    'Datos Personales',
    'Datos Incapacidad',
    'Documentos',
    'Confirmación',
  ];

  const stepLabels = steps || defaultSteps.slice(0, totalSteps);

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between">
        {stepLabels.map((label, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;
          const isPending = stepNumber > currentStep;

          return (
            <div key={stepNumber} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center flex-shrink-0">
                <div
                  className={cn(
                    'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300',
                    isCompleted &&
                      'bg-blue-600 border-blue-600 text-white',
                    isCurrent &&
                      'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-200',
                    isPending &&
                      'bg-white border-gray-300 text-gray-400'
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-semibold">{stepNumber}</span>
                  )}
                </div>
                
                {/* Step Label - Hidden on mobile */}
                <span
                  className={cn(
                    'mt-2 text-xs font-medium text-center transition-colors duration-300 hidden sm:block',
                    (isCompleted || isCurrent) && 'text-blue-600',
                    isPending && 'text-gray-400'
                  )}
                >
                  {label}
                </span>
              </div>

              {/* Connector Line */}
              {index < totalSteps - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 mx-2 transition-all duration-300',
                    isCompleted ? 'bg-blue-600' : 'bg-gray-300'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Current Step Label - Visible on mobile */}
      <div className="mt-4 text-center sm:hidden">
        <span className="text-sm font-medium text-blue-600">
          {stepLabels[currentStep - 1]}
        </span>
      </div>
    </div>
  );
}
