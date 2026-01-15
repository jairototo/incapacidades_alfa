import { useState } from 'react';
import { Stepper } from './Stepper';
import { TipoIncapacidadSelector } from './TipoIncapacidadSelector';

export interface WizardFormData {
  tipo?: string;
  // Campos para pasos futuros:
  // empleado?: EmpleadoData;
  // afiliado?: AfiliadoData;
  // incapacidad?: IncapacidadData;
  // documentos?: File[];
}

/**
 * Componente principal del wizard de radicación de incapacidades
 * Maneja el estado y navegación entre los 5 pasos
 */
export function RadicarIncapacidadWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<WizardFormData>({});

  const handleTipoContinue = (tipo: string) => {
    setFormData({ ...formData, tipo });
    setCurrentStep(2);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Radicar Incapacidad
          </h1>
          <p className="text-gray-600">
            Complete los siguientes pasos para radicar su incapacidad
          </p>
        </div>

        {/* Stepper */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <Stepper currentStep={currentStep} totalSteps={5} />
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {currentStep === 1 && (
            <TipoIncapacidadSelector onContinue={handleTipoContinue} />
          )}

          {currentStep === 2 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Paso 2: Datos Personales
              </h2>
              <p className="text-gray-600 mb-4">
                Tipo seleccionado: <span className="font-semibold">{formData.tipo}</span>
              </p>
              <p className="text-gray-500 italic">
                Este paso se implementará en la siguiente fase
              </p>
              <button
                onClick={() => setCurrentStep(1)}
                className="mt-6 px-6 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                Volver al Paso 1
              </button>
            </div>
          )}

          {currentStep > 2 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Paso {currentStep}
              </h2>
              <p className="text-gray-500 italic">
                Este paso se implementará en las siguientes fases
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
