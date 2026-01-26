import { useNavigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Página mostrada cuando un usuario autenticado intenta acceder
 * a una ruta para la cual no tiene permisos (RBAC)
 */
export function UnauthorizedPage() {
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-yellow-500 rounded-full flex items-center justify-center">
              <ShieldAlert className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            Acceso Denegado
          </CardTitle>
          <CardDescription>
            No tienes permisos para acceder a esta sección
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-sm text-slate-600">
            <p>
              Tu rol de usuario no tiene los privilegios necesarios para acceder a este recurso.
            </p>
            <p className="mt-2">
              Si crees que esto es un error, contacta al administrador del sistema.
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={handleGoHome} className="w-full">
              Ir al Dashboard
            </Button>
            <Button onClick={handleGoBack} variant="outline" className="w-full">
              Volver
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
