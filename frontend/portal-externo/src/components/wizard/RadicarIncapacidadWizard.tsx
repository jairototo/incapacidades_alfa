import { useState } from 'react';
import { Stepper } from './Stepper';
import { TipoIncapacidadSelector } from './TipoIncapacidadSelector';
import { DatosPersonalesForm } from './DatosPersonalesForm';
import { DatosIncapacidadForm } from './DatosIncapacidadForm';
import { DocumentosForm } from './DocumentosForm';
import type { DatosPersonalesFormData } from './DatosPersonalesForm';
import type { DatosIncapacidadARL, DatosIncapacidadSalud, DocumentosFormData } from '@/schemas/radicacionSchema';

export interface WizardFormData {
  tipo?: string;
  datosPersonales?: DatosPersonalesFormData;
  datosIncapacidad?: DatosIncapacidadARL | DatosIncapacidadSalud;
  documentos?: DocumentosFormData;
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

  const handleDatosPersonalesBack = () => {
    setCurrentStep(1);
  };

  const handleDatosPersonalesContinue = (datosPersonales: DatosPersonalesFormData) => {
    setFormData({ ...formData, datosPersonales });
    setCurrentStep(3);
  };

  const handleDatosIncapacidadBack = () => {
    setCurrentStep(2);
  };

  const handleDatosIncapacidadContinue = (datosIncapacidad: DatosIncapacidadARL | DatosIncapacidadSalud) => {
    setFormData({ ...formData, datosIncapacidad });
    setCurrentStep(4);
  };

  const handleDocumentosBack = () => {
    setCurrentStep(3);
  };

  const handleDocumentosContinue = (documentos: DocumentosFormData) => {
    setFormData({ ...formData, documentos });
    // TODO: Paso 5 - Resumen y envío
    console.log('Wizard completado:', { ...formData, documentos });
    setCurrentStep(5);
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

        {/* Wizard Content */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {/* Paso 1: Tipo de Incapacidad */}
          {currentStep === 1 && (
            <TipoIncapacidadSelector onContinue={handleTipoContinue} />
          )}

          {/* Paso 2: Datos Personales */}
          {currentStep === 2 && formData.tipo && (
            <DatosPersonalesForm
              tipo={formData.tipo as 'ARL' | 'SALUD'}
              initialData={formData.datosPersonales}
              onContinue={handleDatosPersonalesContinue}
              onBack={handleDatosPersonalesBack}
            />
          )}

          {/* Paso 3: Datos de Incapacidad */}
          {currentStep === 3 && formData.tipo && (
            <DatosIncapacidadForm
              tipo={formData.tipo as 'ARL' | 'SALUD'}
              initialData={formData.datosIncapacidad}
              onContinue={handleDatosIncapacidadContinue}
              onBack={handleDatosIncapacidadBack}
            />
          )}

          {/* Paso 4: Documentos */}
          {currentStep === 4 && formData.tipo && (
            <DocumentosForm
              tipo={formData.tipo as 'ARL' | 'SALUD'}
              initialData={formData.documentos}
              onBack={handleDocumentosBack}
              onContinue={handleDocumentosContinue}
            />
          )}

          {/* Paso 2: Fallback si no hay tipo */}
          {currentStep === 2 && !formData.tipo && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Paso 2: Datos Personales
              </h2>
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

          {/* Pasos 5+: Placeholder */}
          {currentStep > 4 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Paso {currentStep}
              </h2>
              <p className="text-gray-500 italic">
                Este paso se implementará en las siguientes fases
              </p>
              <button
                onClick={() => setCurrentStep(4)}
                className="mt-6 px-6 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                Volver al Paso 4
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
