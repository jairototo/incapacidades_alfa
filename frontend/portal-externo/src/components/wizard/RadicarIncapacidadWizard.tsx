import { useState } from 'react';
import { Stepper } from './Stepper';
import { TipoIncapacidadSelector } from './TipoIncapacidadSelector';
import { DatosPersonalesForm } from './DatosPersonalesForm';
import { DatosIncapacidadForm } from './DatosIncapacidadForm';
import { DocumentosForm } from './DocumentosForm';
import { ResumenRadicacionForm } from './ResumenRadicacionForm';
import { ConfirmacionExitosa } from './ConfirmacionExitosa';
import { useCreateIncapacidad, transformWizardToDTO } from '@/services/incapacidadService';
import { uploadMultipleDocumentos } from '@/services/documentoService';
import { useToast } from '@/hooks/use-toast';
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [numeroRadicacion, setNumeroRadicacion] = useState<string>('');
  const [showConfirmacion, setShowConfirmacion] = useState(false);

  const { toast } = useToast();
  const createIncapacidadMutation = useCreateIncapacidad();

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
    setCurrentStep(5);
  };

  const handleResumenBack = () => {
    setCurrentStep(4);
  };

  const handleResumenSubmit = async () => {
    setIsSubmitting(true);

    try {
      // 1. Transformar datos del wizard al formato DTO del backend
      const incapacidadDTO = transformWizardToDTO(formData);

      // 2. Crear incapacidad en el backend
      const incapacidadCreada = await createIncapacidadMutation.mutateAsync(incapacidadDTO);

      // 3. Subir documentos si existen
      if (formData.documentos) {
        const documentosParaSubir = [];
        
        // Convertir documentos al formato esperado
        if (formData.documentos.incapacidad_medica) {
          documentosParaSubir.push(
            ...formData.documentos.incapacidad_medica.map((file) => ({
              file,
              tipo: 'INCAPACIDAD_MEDICA' as const,
            }))
          );
        }
        
        if (formData.documentos.historia_clinica) {
          documentosParaSubir.push(
            ...formData.documentos.historia_clinica.map((file) => ({
              file,
              tipo: 'HISTORIA_CLINICA' as const,
            }))
          );
        }
        
        if (formData.documentos.soportes_adicionales) {
          documentosParaSubir.push(
            ...formData.documentos.soportes_adicionales.map((file) => ({
              file,
              tipo: 'OTRO' as const,
            }))
          );
        }

        if (documentosParaSubir.length > 0) {
          const resultadosUpload = await uploadMultipleDocumentos(
            incapacidadCreada.id,
            documentosParaSubir
          );

          // Verificar si hubo errores en upload de documentos
          const errores = resultadosUpload.filter((r) => !r.success);
          if (errores.length > 0) {
            console.warn('Algunos documentos no se pudieron subir:', errores);
            toast({
              title: 'Advertencia',
              description: `Incapacidad creada, pero ${errores.length} documento(s) no se pudieron subir.`,
              variant: 'default',
            });
          }
        }
      }

      // 4. Mostrar confirmación exitosa
      setNumeroRadicacion(incapacidadCreada.numero);
      setShowConfirmacion(true);

      toast({
        title: 'Éxito',
        description: `Incapacidad ${incapacidadCreada.numero} radicada exitosamente`,
        variant: 'default',
      });
    } catch (error: any) {
      console.error('Error al radicar incapacidad:', error);

      // Mostrar mensaje de error detallado
      const errorMessage =
        error.response?.data?.error?.message ||
        error.response?.data?.detail ||
        'Ocurrió un error al radicar la incapacidad. Por favor intente nuevamente.';

      toast({
        title: 'Error al radicar incapacidad',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRadicarOtra = () => {
    // Reset completo del wizard
    setFormData({});
    setCurrentStep(1);
    setShowConfirmacion(false);
    setNumeroRadicacion('');
  };

  const handleConsultarEstado = () => {
    // TODO: Implementar en Fase 2 - redireccionar a consulta
    toast({
      title: 'Próximamente',
      description: 'La consulta de estado estará disponible en la siguiente fase',
      variant: 'default',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Mostrar confirmación exitosa si ya se completó */}
        {showConfirmacion ? (
          <div className="bg-white rounded-lg shadow-sm p-8">
            <ConfirmacionExitosa
              numeroRadicacion={numeroRadicacion}
              onRadicarOtra={handleRadicarOtra}
              onConsultarEstado={handleConsultarEstado}
            />
          </div>
        ) : (
          <>
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

              {/* Paso 5: Resumen y confirmación */}
              {currentStep === 5 && (
                <ResumenRadicacionForm
                  wizardData={formData}
                  onBack={handleResumenBack}
                  onSubmit={handleResumenSubmit}
                  isSubmitting={isSubmitting}
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

              {/* Pasos 6+: Placeholder */}
              {currentStep > 5 && (
                <div className="text-center py-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    Paso {currentStep}
                  </h2>
                  <p className="text-gray-500 italic">
                    Este paso se implementará en las siguientes fases
                  </p>
                  <button
                    onClick={() => setCurrentStep(5)}
                    className="mt-6 px-6 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
                  >
                    Volver al Paso 5
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
