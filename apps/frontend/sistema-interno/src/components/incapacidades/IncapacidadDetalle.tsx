import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Incapacidad } from '@/types/incapacidad';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { FileText, Calendar, DollarSign, User, Building2, Activity } from 'lucide-react';

interface IncapacidadDetalleProps {
  incapacidad: Incapacidad;
}

/**
 * Componente para mostrar los datos generales de una incapacidad
 * Incluye información del paciente, empresa, diagnóstico y valores
 */
export function IncapacidadDetalle({ incapacidad }: IncapacidadDetalleProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {/* Información General */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Información General
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-500">N° Radicación</label>
            <p className="text-base font-mono font-semibold">{incapacidad.numero}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-500">Tipo</label>
              <div className="mt-1">
                <Badge variant={incapacidad.tipo === 'ARL' ? 'default' : 'secondary'}>
                  {incapacidad.tipo}
                </Badge>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-500">Estado</label>
              <div className="mt-1">
                <Badge variant={getEstadoBadgeVariant(incapacidad.estado)}>
                  {incapacidad.estado}
                </Badge>
              </div>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-500">Prioridad</label>
            <div className="mt-1">
              <Badge variant={getPrioridadBadgeVariant(incapacidad.prioridad)}>
                {incapacidad.prioridad}
              </Badge>
            </div>
          </div>

          {incapacidad.observaciones && (
            <div>
              <label className="text-sm font-medium text-slate-500">Observaciones</label>
              <p className="text-sm text-slate-700 mt-1 p-3 bg-slate-50 rounded-md">
                {incapacidad.observaciones}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Paciente/Afiliado */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            {incapacidad.tipo === 'ARL' ? 'Empleado' : 'Afiliado'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {incapacidad.empleado && (
            <>
              <div>
                <label className="text-sm font-medium text-slate-500">Nombre Completo</label>
                <p className="text-base font-medium">
                  {incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-500">Tipo Documento</label>
                  <p className="text-sm text-slate-700">{incapacidad.empleado.tipo_documento}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-500">N° Documento</label>
                  <p className="text-sm text-slate-700 font-mono">
                    {incapacidad.empleado.numero_documento}
                  </p>
                </div>
              </div>

              {incapacidad.empleado.cargo && (
                <div>
                  <label className="text-sm font-medium text-slate-500">Cargo</label>
                  <p className="text-sm text-slate-700">{incapacidad.empleado.cargo}</p>
                </div>
              )}

              {incapacidad.empleado.email && (
                <div>
                  <label className="text-sm font-medium text-slate-500">Email</label>
                  <p className="text-sm text-slate-700">{incapacidad.empleado.email}</p>
                </div>
              )}
            </>
          )}

          {incapacidad.afiliado && (
            <>
              <div>
                <label className="text-sm font-medium text-slate-500">Nombre Completo</label>
                <p className="text-base font-medium">
                  {incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-500">Tipo Documento</label>
                  <p className="text-sm text-slate-700">{incapacidad.afiliado.tipo_documento}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-500">N° Documento</label>
                  <p className="text-sm text-slate-700 font-mono">
                    {incapacidad.afiliado.numero_documento}
                  </p>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Empresa (solo para ARL) */}
      {incapacidad.empresa && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Empresa
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-500">Razón Social</label>
              <p className="text-base font-medium">{incapacidad.empresa.razon_social}</p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-slate-500">NIT</label>
              <p className="text-sm text-slate-700 font-mono">{incapacidad.empresa.nit}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-500">Email Contacto</label>
              <p className="text-sm text-slate-700">{incapacidad.empresa.email_contacto}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Diagnóstico */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Diagnóstico
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-500">Código CIE-10</label>
            <p className="text-base font-mono font-semibold">{incapacidad.diagnostico_cie10}</p>
          </div>
          
          <div>
            <label className="text-sm font-medium text-slate-500">Descripción</label>
            <p className="text-sm text-slate-700">{incapacidad.diagnostico_descripcion}</p>
          </div>
        </CardContent>
      </Card>

      {/* Fechas y Duración */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Fechas y Duración
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-500">Fecha Inicio</label>
              <p className="text-sm text-slate-700">{formatDate(incapacidad.fecha_inicio)}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-500">Fecha Fin</label>
              <p className="text-sm text-slate-700">{formatDate(incapacidad.fecha_fin)}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-500">Total Días</label>
            <p className="text-xl font-bold text-blue-600">{incapacidad.dias_totales} días</p>
          </div>
        </CardContent>
      </Card>

      {/* Valores */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Valores
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-500">Valor Total</label>
            <p className="text-xl font-bold text-green-600">
              {formatCurrency(incapacidad.valor_total)}
            </p>
          </div>

          {incapacidad.orden_pago && (
            <div className="pt-4 border-t border-slate-200">
              <label className="text-sm font-medium text-slate-500">Estado Pago</label>
              <div className="mt-1">
                <Badge variant={getEstadoPagoBadgeVariant(incapacidad.orden_pago.estado)}>
                  {incapacidad.orden_pago.estado}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadatos */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Información de Sistema</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <label className="text-sm font-medium text-slate-500">Fecha de Creación</label>
              <p className="text-slate-700">{formatDate(incapacidad.created_at)}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-500">Última Actualización</label>
              <p className="text-slate-700">{formatDate(incapacidad.updated_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper functions para badges
function getEstadoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'RADICADA':
      return 'secondary';
    case 'EN_AUDITORIA':
      return 'default';
    case 'PENDIENTE':
      return 'outline';
    case 'CREACION_SINIESTRO':
      return 'secondary';
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
      return 'default';
    case 'GLOSADA':
      return 'destructive';
    case 'PAGADA':
    case 'PAGADA_PARCIAL':
      return 'default';
    default:
      return 'secondary';
  }
}

function getPrioridadBadgeVariant(prioridad: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (prioridad) {
    case 'URGENTE':
      return 'destructive';
    case 'ALTA':
      return 'destructive';
    case 'NORMAL':
      return 'default';
    case 'BAJA':
      return 'secondary';
    default:
      return 'outline';
  }
}

function getEstadoPagoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'GENERADA':
      return 'secondary';
    case 'APROBADA':
      return 'default';
    case 'EN_PROCESO':
      return 'default';
    case 'PAGADA':
      return 'default';
    case 'RECHAZADA':
    case 'AN ULADA':
      return 'destructive';
    default:
      return 'outline';
  }
}
