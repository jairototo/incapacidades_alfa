import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { FileText, User, Calendar, Briefcase, FileCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import type { WizardFormData } from './RadicarIncapacidadWizard';

interface ResumenRadicacionFormProps {
  wizardData: WizardFormData;
  onBack: () => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
}

/**
 * Componente del Paso 5: Resumen de datos antes de radicar
 * Muestra todos los datos capturados en formato de solo lectura
 */
export function ResumenRadicacionForm({
  wizardData,
  onBack,
  onSubmit,
  isSubmitting = false,
}: ResumenRadicacionFormProps) {
  const { solicitante, tipo, datosPersonales, datosIncapacidad, documentos } = wizardData;

  // Helper para formatear fechas
  const formatDate = (date: Date | string | undefined) => {
    if (!date) return 'N/A';
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return format(dateObj, 'dd/MM/yyyy', { locale: es });
  };

  // Helper para formatear tamaño de archivo
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Mapeo de tipos de documento
  const tipoDocumentoLabels: Record<string, string> = {
    CC: 'Cédula de Ciudadanía',
    CE: 'Cédula de Extranjería',
    PA: 'Pasaporte',
    TI: 'Tarjeta de Identidad',
    NIT: 'NIT',
  };

  // Mapeo de tipos de póliza
  const tipoPolizaLabels: Record<string, string> = {
    INDIVIDUAL: 'Individual',
    FAMILIAR: 'Familiar',
    COLECTIVA: 'Colectiva',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Resumen de Radicación
        </h2>
        <p className="text-gray-600">
          Revise los datos antes de confirmar la radicación de su incapacidad
        </p>
      </div>

      {/* Sección 1: Datos del Solicitante */}
      {solicitante && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Datos del Solicitante
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-600">Correo Electrónico:</span>
              <p className="text-base text-gray-900 mt-1">{solicitante.correo}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Nombres:</span>
              <p className="text-base text-gray-900 mt-1">{solicitante.nombres}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Apellidos:</span>
              <p className="text-base text-gray-900 mt-1">{solicitante.apellidos}</p>
            </div>
            {solicitante.telefono && (
              <div>
                <span className="text-sm font-medium text-gray-600">Teléfono:</span>
                <p className="text-base text-gray-900 mt-1">{solicitante.telefono}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sección 2: Tipo de Incapacidad */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <Briefcase className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Tipo de Incapacidad
          </h3>
        </div>
        <div className="grid grid-cols-1 gap-3">
          <div>
            <span className="text-sm font-medium text-gray-600">Tipo:</span>
            <p className="text-base text-gray-900 font-medium mt-1">
              {tipo === 'ARL' ? 'ARL - Administradora de Riesgos Laborales' : 'SALUD - Incapacidad de Salud'}
            </p>
          </div>
          {tipo === 'ARL' && datosIncapacidad && 'tipo_enfermedad' in datosIncapacidad && (
            <div>
              <span className="text-sm font-medium text-gray-600">Tipo de Enfermedad:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.tipo_enfermedad || 'No especificado'}
              </p>
            </div>
          )}
          {tipo === 'SALUD' && datosIncapacidad && 'subtipo' in datosIncapacidad && (
            <div>
              <span className="text-sm font-medium text-gray-600">Subtipo:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.subtipo || 'No especificado'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Sección 2: Datos Personales */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <User className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Datos Personales
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-sm font-medium text-gray-600">Documento:</span>
            <p className="text-base text-gray-900 mt-1">
              {tipoDocumentoLabels[datosPersonales?.tipo_documento || ''] || datosPersonales?.tipo_documento} - {datosPersonales?.numero_documento}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Nombre Completo:</span>
            <p className="text-base text-gray-900 mt-1">
              {datosPersonales?.nombres} {datosPersonales?.apellidos}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Email:</span>
            <p className="text-base text-gray-900 mt-1">
              {datosPersonales?.email || 'No especificado'}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Teléfono:</span>
            <p className="text-base text-gray-900 mt-1">
              {datosPersonales?.telefono || 'No especificado'}
            </p>
          </div>

          {/* Campos específicos ARL */}
          {tipo === 'ARL' && datosPersonales && 'empresa_nombre' in datosPersonales && (
            <>
              <div>
                <span className="text-sm font-medium text-gray-600">Empresa:</span>
                <p className="text-base text-gray-900 mt-1">
                  {datosPersonales.empresa_nombre || 'No especificado'}
                </p>
              </div>
              {'cargo' in datosPersonales && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Cargo:</span>
                  <p className="text-base text-gray-900 mt-1">
                    {datosPersonales.cargo || 'No especificado'}
                  </p>
                </div>
              )}
              {'fecha_ingreso' in datosPersonales && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Fecha de Ingreso:</span>
                  <p className="text-base text-gray-900 mt-1">
                    {formatDate(datosPersonales.fecha_ingreso)}
                  </p>
                </div>
              )}
            </>
          )}

          {/* Campos específicos SALUD */}
          {tipo === 'SALUD' && datosPersonales && 'numero_poliza' in datosPersonales && (
            <>
              <div>
                <span className="text-sm font-medium text-gray-600">Número de Póliza:</span>
                <p className="text-base text-gray-900 mt-1">
                  {datosPersonales.numero_poliza}
                </p>
              </div>
              {'tipo_poliza' in datosPersonales && (
                <div>
                  <span className="text-sm font-medium text-gray-600">Tipo de Póliza:</span>
                  <p className="text-base text-gray-900 mt-1">
                    {tipoPolizaLabels[datosPersonales.tipo_poliza] || datosPersonales.tipo_poliza}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Sección 3: Datos de la Incapacidad */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="h-5 w-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Datos de la Incapacidad
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-sm font-medium text-gray-600">Fecha de Inicio:</span>
            <p className="text-base text-gray-900 mt-1">
              {formatDate(datosIncapacidad?.fecha_inicio)}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Fecha de Fin:</span>
            <p className="text-base text-gray-900 mt-1">
              {formatDate(datosIncapacidad?.fecha_fin)}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Días Totales:</span>
            <p className="text-base text-gray-900 font-semibold mt-1">
              {datosIncapacidad?.dias_totales || 0} días
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Valor por Día:</span>
            <p className="text-base text-gray-900 font-semibold mt-1">
              ${(datosIncapacidad && 'valor_dia' in datosIncapacidad ? datosIncapacidad.valor_dia : 0)?.toLocaleString('es-CO') || 0}
            </p>
          </div>
          <div className="md:col-span-2">
            <span className="text-sm font-medium text-gray-600">Diagnóstico (CIE-10):</span>
            <p className="text-base text-gray-900 mt-1">
              {datosIncapacidad?.diagnostico_cie10 || 'No especificado'}
            </p>
          </div>
          {datosIncapacidad?.descripcion_diagnostico && (
            <div className="md:col-span-2">
              <span className="text-sm font-medium text-gray-600">Descripción del Diagnóstico:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.descripcion_diagnostico}
              </p>
            </div>
          )}
          {datosIncapacidad && 'nombre_medico' in datosIncapacidad && datosIncapacidad.nombre_medico && (
            <div>
              <span className="text-sm font-medium text-gray-600">Médico Tratante:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.nombre_medico}
              </p>
            </div>
          )}
          {datosIncapacidad && 'registro_medico' in datosIncapacidad && datosIncapacidad.registro_medico && (
            <div>
              <span className="text-sm font-medium text-gray-600">Registro Médico:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.registro_medico}
              </p>
            </div>
          )}
          {datosIncapacidad && 'ips' in datosIncapacidad && datosIncapacidad.ips && (
            <div>
              <span className="text-sm font-medium text-gray-600">IPS:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.ips}
              </p>
            </div>
          )}
          {datosIncapacidad && 'eps' in datosIncapacidad && datosIncapacidad.eps && (
            <div>
              <span className="text-sm font-medium text-gray-600">EPS:</span>
              <p className="text-base text-gray-900 mt-1">
                {datosIncapacidad.eps}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Sección 4: Documentos Adjuntos */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <FileCheck className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Documentos Adjuntos
          </h3>
        </div>
        <div className="space-y-3">
          {documentos && (
            <>
              {documentos.incapacidad_medica && documentos.incapacidad_medica.length > 0 && (
                documentos.incapacidad_medica.map((file, index) => (
                  <div
                    key={`incap-${index}`}
                    className="flex items-center gap-3 bg-white p-3 rounded-lg border border-gray-200"
                  >
                    <FileText className="h-5 w-5 text-gray-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)} • Incapacidad Médica
                      </p>
                    </div>
                  </div>
                ))
              )}
              {documentos.historia_clinica && documentos.historia_clinica.length > 0 && (
                documentos.historia_clinica.map((file, index) => (
                  <div
                    key={`hc-${index}`}
                    className="flex items-center gap-3 bg-white p-3 rounded-lg border border-gray-200"
                  >
                    <FileText className="h-5 w-5 text-gray-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)} • Historia Clínica
                      </p>
                    </div>
                  </div>
                ))
              )}
              {documentos.soportes_adicionales && documentos.soportes_adicionales.length > 0 && (
                documentos.soportes_adicionales.map((file, index) => (
                  <div
                    key={`soporte-${index}`}
                    className="flex items-center gap-3 bg-white p-3 rounded-lg border border-gray-200"
                  >
                    <FileText className="h-5 w-5 text-gray-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)} • Soporte Adicional
                      </p>
                    </div>
                  </div>
                ))
              )}
            </>
          )}
          {(!documentos || 
            ((!documentos.incapacidad_medica || documentos.incapacidad_medica.length === 0) &&
             (!documentos.historia_clinica || documentos.historia_clinica.length === 0) &&
             (!documentos.soportes_adicionales || documentos.soportes_adicionales.length === 0))) && (
            <p className="text-sm text-gray-500 italic">
              No se adjuntaron documentos
            </p>
          )}
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex justify-between pt-6 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={isSubmitting}
        >
          Volver
        </Button>
        <Button
          type="button"
          onClick={onSubmit}
          disabled={isSubmitting}
          className="min-w-[200px]"
        >
          {isSubmitting ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Procesando...
            </>
          ) : (
            'Confirmar y Radicar'
          )}
        </Button>
      </div>
    </div>
  );
}
