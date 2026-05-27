/**
 * Ejemplo de uso del componente BusquedaIncapacidad.
 * 
 * Este archivo demuestra cómo integrar el componente en una página
 * y manejar los resultados de la búsqueda.
 */

import { useState } from 'react';
import { BusquedaIncapacidad } from '@/components/consulta/BusquedaIncapacidad';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

export function ConsultarIncapacidadPage() {
  const [incapacidad, setIncapacidad] = useState<ConsultaIncapacidadResponse | null>(null);

  const handleResultado = (resultado: ConsultaIncapacidadResponse) => {
    console.log('Incapacidad encontrada:', resultado);
    setIncapacidad(resultado);
    
    // Scroll suave al resultado
    setTimeout(() => {
      document.getElementById('resultado')?.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Consulta de Incapacidades
          </h1>
          <p className="mt-2 text-gray-600">
            Ingresa tu número de radicación o documento de identidad para consultar el estado
          </p>
        </div>

        {/* Componente de búsqueda */}
        <BusquedaIncapacidad onResultado={handleResultado} />

        {/* Resultado de la búsqueda */}
        {incapacidad && (
          <div id="resultado" className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Detalles de la Incapacidad
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Número de radicación</p>
                <p className="font-semibold text-gray-900">{incapacidad.numero}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Estado</p>
                <p className="font-semibold text-gray-900">{incapacidad.estado}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Tipo</p>
                <p className="font-semibold text-gray-900">{incapacidad.tipo}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Nombre completo</p>
                <p className="font-semibold text-gray-900">{incapacidad.nombre_completo}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Documento</p>
                <p className="font-semibold text-gray-900">
                  {incapacidad.tipo_documento} {incapacidad.documento}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Días totales</p>
                <p className="font-semibold text-gray-900">{incapacidad.dias_totales}</p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Fecha inicio</p>
                <p className="font-semibold text-gray-900">
                  {new Date(incapacidad.fecha_inicio).toLocaleDateString('es-CO')}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500">Fecha fin</p>
                <p className="font-semibold text-gray-900">
                  {new Date(incapacidad.fecha_fin).toLocaleDateString('es-CO')}
                </p>
              </div>
              
              {incapacidad.empresa_razon_social && (
                <div className="md:col-span-2">
                  <p className="text-sm text-gray-500">Empresa</p>
                  <p className="font-semibold text-gray-900">
                    {incapacidad.empresa_razon_social} - NIT {incapacidad.empresa_nit}
                  </p>
                </div>
              )}
            </div>

            {/* Historial de estados */}
            {incapacidad.historial_estados.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Historial de Estados
                </h3>
                <div className="space-y-2">
                  {incapacidad.historial_estados.map((historial, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{historial.estado}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(historial.fecha_cambio).toLocaleString('es-CO')}
                        </p>
                        {historial.observaciones && (
                          <p className="text-sm text-gray-500 mt-1">{historial.observaciones}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Documentos públicos */}
            {incapacidad.documentos_publicos.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Documentos Disponibles
                </h3>
                <div className="space-y-2">
                  {incapacidad.documentos_publicos.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium text-gray-900">{doc.nombre_archivo}</p>
                        <p className="text-sm text-gray-600">
                          {doc.tipo_documento} • {doc.tamanio_kb} KB
                        </p>
                      </div>
                      <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                        Descargar
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
