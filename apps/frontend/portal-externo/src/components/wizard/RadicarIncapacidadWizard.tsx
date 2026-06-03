import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stepper } from './Stepper';
import { Paso1SolicitanteEmpresaEmpleado } from './Paso1SolicitanteEmpresaEmpleado';
import { Paso2IncapacidadDocumentos, type Paso2FormData } from './Paso2IncapacidadDocumentos';
import { ConfirmacionExitosa } from './ConfirmacionExitosa';
import {
  crearPreIncapacidad,
  subirTodosLosDocumentos,
  formatDateForApi,
} from '@/services/preIncapacidadService';
import { useToast } from '@/hooks/use-toast';
import type { Paso1FormData } from '@/schemas/radicacionSchema';

const WIZARD_STEPS = ['Datos del Solicitante', 'Incapacidad y Documentos'];

export interface WizardFormData {
  paso1?: Paso1FormData;
  paso2?: Paso2FormData;
}

/**
 * Wizard de radicación de incapacidades ARL — Portal Externo.
 * 2 pasos:
 *   1. Solicitante + Empresa + Empleado (datos planos, sin búsqueda en BD)
 *   2. Datos de incapacidad + Documentos adjuntos
 *
 * Envía a POST /api/v1/pre-incapacidades/radicar y luego sube documentos.
 */
export function RadicarIncapacidadWizard() {
  const [currentStep, setCurrentStep] = useState(1); // 1-indexed para Stepper
  const [formData, setFormData] = useState<WizardFormData>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [numeroRadicacion, setNumeroRadicacion] = useState<number | null>(null);
  const [showConfirmacion, setShowConfirmacion] = useState(false);

  const navigate = useNavigate();
  const { toast } = useToast();

  // ── Paso 1 ────────────────────────────────────────────────────────────────

  const handlePaso1Continue = (paso1: Paso1FormData) => {
    setFormData((prev) => ({ ...prev, paso1 }));
    setCurrentStep(2);
  };

  const handlePaso1Cancel = () => {
    navigate('/');
  };

  // ── Paso 2 ────────────────────────────────────────────────────────────────

  const handlePaso2Back = () => {
    setCurrentStep(1);
  };

  const handlePaso2Submit = async (paso2: Paso2FormData) => {
    if (!formData.paso1) return;

    setIsSubmitting(true);
    const paso1 = formData.paso1;
    const { incapacidad, documentos } = paso2;

    try {
      // ── 1. Crear pre-incapacidad ─────────────────────────────────────────
      const diasTotales =
        incapacidad.fecha_inicio && incapacidad.fecha_fin
          ? Math.max(
              1,
              Math.round(
                (incapacidad.fecha_fin.getTime() - incapacidad.fecha_inicio.getTime()) /
                  (1000 * 60 * 60 * 24)
              ) + 1
            )
          : 1;

      const preIncapacidad = await crearPreIncapacidad({
        solicitante: {
          correo: paso1.solicitante.correo,
          nombres: paso1.solicitante.nombres,
          apellidos: paso1.solicitante.apellidos || undefined,
          telefono: paso1.solicitante.telefono || undefined,
        },
        empresa:
          paso1.empresa && (paso1.empresa.nit || paso1.empresa.nombre)
            ? {
                nit: paso1.empresa.nit || undefined,
                nombre: paso1.empresa.nombre || undefined,
              }
            : undefined,
        empleado: {
          tipo_documento: paso1.empleado.tipo_documento,
          numero_documento: paso1.empleado.numero_documento,
          nombres: paso1.empleado.nombres,
          apellidos: paso1.empleado.apellidos || undefined,
          email: paso1.empleado.email || undefined,
          telefono: paso1.empleado.telefono || undefined,
        },
        incapacidad: {
          tipo_enfermedad: incapacidad.tipo_enfermedad,
          fecha_inicio: formatDateForApi(incapacidad.fecha_inicio),
          fecha_fin: formatDateForApi(incapacidad.fecha_fin),
          dias_totales: diasTotales,
          diagnostico_cie10: incapacidad.diagnostico_cie10,
          descripcion_diagnostico: incapacidad.descripcion_diagnostico || undefined,
          nombre_medico: incapacidad.nombre_medico,
          registro_medico: incapacidad.registro_medico,
          ips: incapacidad.ips || undefined,
          observaciones: incapacidad.observaciones || undefined,
        },
      });

      // ── 2. Subir documentos ──────────────────────────────────────────────
      const archivosParaSubir: {
        file: File;
        tipo: 'INCAPACIDAD_MEDICA' | 'HISTORIA_CLINICA' | 'SOPORTE_ADICIONAL';
      }[] = [];

      if (documentos.incapacidad_medica?.length) {
        archivosParaSubir.push(
          ...documentos.incapacidad_medica.map((file) => ({
            file,
            tipo: 'INCAPACIDAD_MEDICA' as const,
          }))
        );
      }
      if (documentos.historia_clinica?.length) {
        archivosParaSubir.push(
          ...documentos.historia_clinica.map((file) => ({
            file,
            tipo: 'HISTORIA_CLINICA' as const,
          }))
        );
      }
      if (documentos.soportes_adicionales?.length) {
        archivosParaSubir.push(
          ...documentos.soportes_adicionales.map((file) => ({
            file,
            tipo: 'SOPORTE_ADICIONAL' as const,
          }))
        );
      }

      if (archivosParaSubir.length > 0) {
        const resultados = await subirTodosLosDocumentos(
          preIncapacidad.id,
          archivosParaSubir
        );

        const errores = resultados.filter((r) => !r.success);
        if (errores.length > 0) {
          // No bloqueante — la radicación ya fue creada. El job reintentará.
          toast({
            title: 'Advertencia',
            description: `Radicación creada, pero ${errores.length} documento(s) presentaron fallas de subida. Serán reintentados automáticamente.`,
            variant: 'default',
          });
        }
      }

      // ── 3. Mostrar confirmación ──────────────────────────────────────────
      setNumeroRadicacion(preIncapacidad.numero_radicacion);
      setShowConfirmacion(true);
    } catch (error: any) {
      console.error('Error al radicar incapacidad:', error);

      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.error?.message ||
        'Ocurrió un error al radicar la incapacidad. Por favor intente nuevamente.';

      toast({
        title: 'Error al radicar',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Reinicio ──────────────────────────────────────────────────────────────

  const handleRadicarOtra = () => {
    setFormData({});
    setCurrentStep(1);
    setShowConfirmacion(false);
    setNumeroRadicacion(null);
  };

  const handleConsultarEstado = () => {
    navigate('/consultar');
  };

  return (
    <div className="min-h-screen bg-muted py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {showConfirmacion ? (
          <div className="bg-white rounded-lg shadow-sm p-8">
            <ConfirmacionExitosa
              numeroRadicacion={numeroRadicacion!}
              onRadicarOtra={handleRadicarOtra}
              onConsultarEstado={handleConsultarEstado}
            />
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground mb-2">Radicar Incapacidad</h1>
              <p className="text-muted-foreground">Complete los dos pasos para radicar su incapacidad ARL</p>
            </div>

            {/* Stepper */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
              <Stepper
                currentStep={currentStep}
                totalSteps={2}
                steps={WIZARD_STEPS}
              />
            </div>

            {/* Contenido del paso */}
            <div className="bg-white rounded-lg shadow-sm p-8">
              {currentStep === 1 && (
                <Paso1SolicitanteEmpresaEmpleado
                  initialData={formData.paso1}
                  onContinue={handlePaso1Continue}
                  onCancel={handlePaso1Cancel}
                />
              )}

              {currentStep === 2 && (
                <Paso2IncapacidadDocumentos
                  initialData={formData.paso2}
                  onBack={handlePaso2Back}
                  onContinue={handlePaso2Submit}
                />
              )}
            </div>

            {/* Overlay de envío */}
            {isSubmitting && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-8 max-w-sm mx-4 text-center shadow-xl">
                  <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-foreground mb-2">Radicando incapacidad...</h3>
                  <p className="text-sm text-muted-foreground">
                    Por favor espere. Estamos procesando su solicitud y subiendo los documentos.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
