/**
 * Página de consulta pública de incapacidades.
 * 
 * Integra 4 componentes principales:
 * - BusquedaIncapacidad: Formulario de búsqueda por número/documento
 * - DetalleIncapacidad: Información principal de la incapacidad
 * - TimelineEstados: Historial de cambios de estado
 * - DocumentosDescargables: Archivos disponibles para descarga
 * 
 * Características:
 * - Layout responsivo (grid desktop, stack mobile)
 * - Scroll automático a resultados
 * - Búsqueda integrada con React Query
 */

import { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';
import { BusquedaIncapacidad } from '@/components/consulta/BusquedaIncapacidad';
import { DetalleIncapacidad } from '@/components/consulta/DetalleIncapacidad';
import { TimelineEstados } from '@/components/consulta/TimelineEstados';
import { DocumentosDescargables } from '@/components/consulta/DocumentosDescargables';
import { Button } from '@/components/ui/Button';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

export function ConsultarIncapacidad() {
  // Estado de la incapacidad encontrada
  const [incapacidad, setIncapacidad] = useState<ConsultaIncapacidadResponse | null>(null);
  
  // Referencia para scroll automático
  const resultadosRef = useRef<HTMLDivElement>(null);

  // Scroll automático cuando se obtienen resultados
  useEffect(() => {
    if (incapacidad && resultadosRef.current) {
      setTimeout(() => {
        resultadosRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }, 100);
    }
  }, [incapacidad]);

  /**
   * Handler cuando se encuentra una incapacidad.
   */
  const handleResultado = (resultado: ConsultaIncapacidadResponse) => {
    setIncapacidad(resultado);
  };

  /**
   * Handler para nueva búsqueda.
   */
  const handleNuevaBusqueda = () => {
    setIncapacidad(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            Consulta de Incapacidades
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Consulta el estado de tu incapacidad de forma rápida y segura
          </p>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="space-y-6">
          {/* Formulario de búsqueda */}
          {!incapacidad && (
            <BusquedaIncapacidad onResultado={handleResultado} />
          )}

          {/* Resultados de la búsqueda */}
          {incapacidad && (
            <div ref={resultadosRef} className="space-y-6 scroll-mt-6">
              {/* Detalle principal */}
              <DetalleIncapacidad incapacidad={incapacidad} />

              {/* Grid: Timeline + Documentos */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Timeline de estados */}
                <TimelineEstados historial={incapacidad.historial_estados} />

                {/* Documentos descargables */}
                <DocumentosDescargables
                  documentos={incapacidad.documentos}
                  numeroIncapacidad={incapacidad.numero}
                />
              </div>

              {/* Botón para nueva búsqueda */}
              <div className="flex justify-center pt-4">
                <Button
                  onClick={handleNuevaBusqueda}
                  variant="outline"
                  size="lg"
                  className="min-w-[200px]"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Nueva búsqueda
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-600">
            Sistema de Gestión de Incapacidades © 2026 - Todos los derechos reservados
          </p>
        </div>
      </footer>
    </div>
  );
}
