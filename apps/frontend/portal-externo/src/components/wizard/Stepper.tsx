import { Check } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface StepperProps {
  currentStep: number;
  totalSteps: number;
  steps?: string[];
}

/**
 * Stepper — Brand Book Seguros Alfa
 * Usa tokens semánticos: primary (#009B76), foreground (#004953), muted
 */
export function Stepper({ currentStep, totalSteps, steps }: StepperProps) {
  const defaultSteps = ['Datos del Solicitante', 'Incapacidad y Documentos'];
  const stepLabels = steps || defaultSteps.slice(0, totalSteps);

  return (
    <div className="w-full py-4">
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
                    isCompleted && 'bg-primary border-primary text-primary-foreground',
                    isCurrent && 'bg-primary border-primary text-primary-foreground shadow-md',
                    isPending && 'bg-background border-border text-muted-foreground'
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-semibold">{stepNumber}</span>
                  )}
                </div>

                {/* Step Label — oculto en mobile */}
                <span
                  className={cn(
                    'mt-2 text-xs font-medium text-center transition-colors duration-300 hidden sm:block',
                    (isCompleted || isCurrent) && 'text-primary',
                    isPending && 'text-muted-foreground'
                  )}
                >
                  {label}
                </span>
              </div>

              {/* Línea conectora */}
              {index < totalSteps - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 mx-2 transition-all duration-300',
                    isCompleted ? 'bg-primary' : 'bg-border'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Label del paso actual — visible solo en mobile */}
      <div className="mt-3 text-center sm:hidden">
        <span className="text-sm font-medium text-primary">
          {stepLabels[currentStep - 1]}
        </span>
      </div>
    </div>
  );
}
