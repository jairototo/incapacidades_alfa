import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginForm } from '@/components/auth/LoginForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/store/authStore';

/**
 * Página de inicio de sesión del Sistema Interno
 * 
 * Features:
 * - Layout centrado con gradient background
 * - Card con logo y título
 * - Auto-redirect si el usuario ya está autenticado
 * - Footer con copyright
 * - Integración con LoginForm component
 */
export function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuthStore();

  // Auto-redirect si ya está autenticado
  useEffect(() => {
    if (isAuthenticated && user) {
      // Redirigir según rol del usuario
      const redirectPath = getRedirectPath(user.rol);
      navigate(redirectPath, { replace: true });
    }
  }, [isAuthenticated, user, navigate]);

  const handleLoginSuccess = () => {
    // El redirect se maneja automáticamente por el useEffect
    // después de que LoginForm actualice el store
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            {/* Logo placeholder - puede ser reemplazado con imagen real */}
            <div 
              className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg"
              aria-label="Logo Sistema Interno"
            >
              SI
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            Sistema Interno de Incapacidades
          </CardTitle>
          <CardDescription>
            Ingrese sus credenciales para acceder
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={handleLoginSuccess} />
        </CardContent>
      </Card>

      {/* Footer con copyright */}
      <footer className="mt-8 text-center text-sm text-slate-600">
        <p>© {new Date().getFullYear()} Sistema de Incapacidades</p>
        <p className="mt-1 text-xs text-slate-500">
          Todos los derechos reservados
        </p>
      </footer>
    </div>
  );
}

/**
 * Determina la ruta de redirección según el rol del usuario
 */
function getRedirectPath(rol: string): string {
  switch (rol) {
    case 'ADMIN':
    case 'AUDITOR':
      return '/dashboard';
    case 'APROBADOR':
      return '/ordenes-pago';
    case 'EMPRESA':
      return '/incapacidades/consulta';
    case 'EMPLEADO':
      return '/incapacidades/mis-incapacidades';
    default:
      return '/dashboard';
  }
}
