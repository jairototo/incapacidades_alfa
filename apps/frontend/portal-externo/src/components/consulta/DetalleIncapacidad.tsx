/**
 * Componente de detalle de incapacidad.
 * 
 * Muestra toda la información de una incapacidad consultada:
 * - Datos básicos (número, tipo, estado, fechas)
 * - Datos del solicitante (nombre, documento)
 * - Datos de la empresa (solo para tipo ARL)
 * - Información médica (diagnóstico, días)
 * - Valores económicos
 * 
 * Características:
 * - Grid responsive (1-2 columnas)
 * - Badges de estado con colores
 * - Formateo de fechas y moneda
 * - Manejo de campos opcionales
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import type { ConsultaIncapacidadResponse, EstadoIncapacidad, TipoIncapacidad } from '@/types/consulta';
import { FileText, User, Building2, Calendar, DollarSign, Stethoscope, ClipboardCheck } from 'lucide-react';

export interface DetalleIncapacidadProps {
  /**
   * Datos completos de la incapacidad a mostrar
   */
  incapacidad: ConsultaIncapacidadResponse;
  
  /**
   * Clase CSS adicional para el contenedor
   */
  className?: string;
}

/**
 * Mapeo de estados a colores de badge.
 */
const ESTADO_COLORS: Record<EstadoIncapacidad, string> = {
  RADICADA: 'bg-blue-100 text-blue-800 border-blue-200',
  EN_AUDITORIA: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  OBSERVADA: 'bg-orange-100 text-orange-800 border-orange-200',
  APROBADA: 'bg-green-100 text-green-800 border-green-200',
  RECHAZADA: 'bg-red-100 text-red-800 border-red-200',
  EN_PAGO: 'bg-purple-100 text-purple-800 border-purple-200',
  PAGADA: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  CANCELADA: 'bg-gray-100 text-gray-800 border-gray-200',
};

/**
 * Mapeo de tipos a colores de badge.
 */
const TIPO_COLORS: Record<TipoIncapacidad, string> = {
  ARL: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  SALUD: 'bg-teal-100 text-teal-800 border-teal-200',
};

/**
 * Formatea una fecha ISO a formato local.
 */
const formatearFecha = (fechaISO: string): string => {
  return new Date(fechaISO).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

/**
 * Formatea un número como moneda colombiana.
 */
const formatearMoneda = (valor: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(valor);
};

/**
 * Componente de campo de información.
 */
interface CampoInfoProps {
  label: string;
  valor: string | number | null;
  icon?: React.ReactNode;
}

const CampoInfo = ({ label, valor, icon }: CampoInfoProps) => (
  <div className="space-y-1">
    <div className="flex items-center gap-2">
      {icon && <span className="text-gray-400">{icon}</span>}
      <p className="text-sm font-medium text-gray-500">{label}</p>
    </div>
    <p className="text-base font-semibold text-gray-900">
      {valor ?? <span className="text-gray-400 font-normal">No especificado</span>}
    </p>
  </div>
);

/**
 * Componente Badge de estado.
 */
interface BadgeProps {
  children: React.ReactNode;
  className?: string;
}

const Badge = ({ children, className = '' }: BadgeProps) => (
  <span
    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${className}`}
  >
    {children}
  </span>
);

/**
 * Componente principal de detalle de incapacidad.
 * 
 * @example
 * ```tsx
 * <DetalleIncapacidad 
 *   incapacidad={incapacidadEncontrada}
 * />
 * ```
 */
export function DetalleIncapacidad({ incapacidad, className = '' }: DetalleIncapacidadProps) {
  const esARL = incapacidad.tipo === 'ARL';

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2 mb-2">
              <FileText className="h-6 w-6" />
              Detalle de Incapacidad
            </CardTitle>
            <CardDescription className="text-base">
              {incapacidad.numero}
            </CardDescription>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Badge className={TIPO_COLORS[incapacidad.tipo]}>
              {incapacidad.tipo}
            </Badge>
            <Badge className={ESTADO_COLORS[incapacidad.estado]}>
              {incapacidad.estado.replace(/_/g, ' ')}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Sección: Datos del Solicitante */}
        <section>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <User className="h-5 w-5" />
            Datos del Solicitante
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CampoInfo
              label="Nombre completo"
              valor={incapacidad.nombre_completo}
            />
            <CampoInfo
              label="Documento de identidad"
              valor={`${incapacidad.tipo_documento} ${incapacidad.documento}`}
            />
          </div>
        </section>

        {/* Sección: Datos de la Empresa (solo para ARL) */}
        {esARL && incapacidad.empresa_razon_social && (
          <section className="pt-4 border-t">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
              <Building2 className="h-5 w-5" />
              Empresa
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CampoInfo
                label="Razón social"
                valor={incapacidad.empresa_razon_social}
              />
              <CampoInfo
                label="NIT"
                valor={incapacidad.empresa_nit}
              />
            </div>
          </section>
        )}

        {/* Sección: Información Médica */}
        <section className="pt-4 border-t">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <Stethoscope className="h-5 w-5" />
            Información Médica
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CampoInfo
              label="Diagnóstico (CIE-10)"
              valor={incapacidad.diagnostico_cie10}
            />
            {incapacidad.descripcion_diagnostico && (
              <CampoInfo
                label="Descripción del diagnóstico"
                valor={incapacidad.descripcion_diagnostico}
              />
            )}
          </div>
          {incapacidad.observaciones && (
            <div className="mt-4">
              <CampoInfo
                label="Observaciones médicas"
                valor={incapacidad.observaciones}
              />
            </div>
          )}
        </section>

        {/* Sección: Fechas y Períodos */}
        <section className="pt-4 border-t">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <Calendar className="h-5 w-5" />
            Fechas y Períodos
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <CampoInfo
              label="Fecha de inicio"
              valor={formatearFecha(incapacidad.fecha_inicio)}
            />
            <CampoInfo
              label="Fecha de fin"
              valor={formatearFecha(incapacidad.fecha_fin)}
            />
            <CampoInfo
              label="Días totales"
              valor={`${incapacidad.dias_totales} ${incapacidad.dias_totales === 1 ? 'día' : 'días'}`}
            />
          </div>
        </section>

        {/* Sección: Valores Económicos */}
        <section className="pt-4 border-t">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <DollarSign className="h-5 w-5" />
            Valores Económicos
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CampoInfo
              label="Valor por día"
              valor={formatearMoneda(incapacidad.valor_dia)}
            />
            <CampoInfo
              label="Valor total"
              valor={formatearMoneda(incapacidad.valor_total)}
            />
          </div>
        </section>

        {/* Sección: Información Adicional */}
        <section className="pt-4 border-t">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
            <ClipboardCheck className="h-5 w-5" />
            Información Adicional
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CampoInfo
              label="Fecha de radicación"
              valor={formatearFecha(incapacidad.created_at)}
            />
            <CampoInfo
              label="Estado actual"
              valor={incapacidad.estado.replace(/_/g, ' ')}
            />
          </div>
        </section>

        {/* Footer con información de ayuda */}
        <div className="pt-4 border-t bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-blue-900 font-medium mb-2">
            ℹ️ ¿Necesitas más información?
          </p>
          <p className="text-sm text-blue-700">
            Consulta el historial de estados y documentos disponibles en las secciones siguientes.
            Si tienes dudas sobre el estado de tu incapacidad, comunícate con nuestro centro de atención.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
