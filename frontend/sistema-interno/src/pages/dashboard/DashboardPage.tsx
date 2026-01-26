import { useAuthStore } from '@/store/authStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LayoutDashboard, FileText, Clock, CheckCircle, AlertCircle } from 'lucide-react';

/**
 * Dashboard principal del sistema
 * Muestra resumen de métricas y estado de incapacidades
 */
export function DashboardPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-slate-600">
          Bienvenido, {user?.nombres} {user?.apellidos}
        </p>
      </div>

      {/* Métricas Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Incapacidades
            </CardTitle>
            <FileText className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">245</div>
            <p className="text-xs text-slate-600">
              +12% respecto al mes anterior
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pendientes
            </CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">23</div>
            <p className="text-xs text-slate-600">
              En revisión
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Aprobadas
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">198</div>
            <p className="text-xs text-slate-600">
              80.8% del total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Rechazadas
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-slate-600">
              9.8% del total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5" />
            Panel Principal
          </CardTitle>
          <CardDescription>
            Vista general del sistema de gestión de incapacidades
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Rol actual: {user?.rol}</h3>
            <p className="text-sm text-slate-600">
              Tienes acceso a las funcionalidades según tu rol en el sistema.
            </p>
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold mb-2">Funciones disponibles:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
              {user?.rol === 'ADMIN' && (
                <>
                  <li>Gestión completa de incapacidades</li>
                  <li>Administración de usuarios</li>
                  <li>Configuración del sistema</li>
                  <li>Reportes avanzados</li>
                </>
              )}
              {user?.rol === 'AUDITOR' && (
                <>
                  <li>Auditoría de incapacidades</li>
                  <li>Aprobación/rechazo de solicitudes</li>
                  <li>Reportes de auditoría</li>
                </>
              )}
              {user?.rol === 'APROBADOR' && (
                <>
                  <li>Aprobación de órdenes de pago</li>
                  <li>Consulta de incapacidades aprobadas</li>
                </>
              )}
              {(user?.rol === 'EMPRESA' || user?.rol === 'EMPLEADO') && (
                <>
                  <li>Consulta de incapacidades</li>
                  <li>Descarga de documentos</li>
                </>
              )}
            </ul>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <p className="text-sm text-blue-800">
              <strong>Nota:</strong> Este es un dashboard placeholder. Las métricas mostradas son datos de ejemplo.
              La implementación completa incluirá datos en tiempo real desde el backend.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
