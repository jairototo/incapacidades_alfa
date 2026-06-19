import { LoginForm } from '@/components/auth/LoginForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Página de inicio de sesión del Sistema Interno
 * 
 * Features:
 * - Layout centrado con gradient background
 * - Card con logo y título
 * - Footer con copyright
 * - Integración con LoginForm component
 * 
 * Note: El redirect después del login es manejado automáticamente por PublicRoute
 * cuando detecta que isAuthenticated cambió a true en el authStore
 */
export function LoginPage() {
  // No necesitamos callback de navegación
  // PublicRoute maneja el redirect automáticamente después del login

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center items-center mb-6">
            {/* Logo Alfa - Aseguradora */}
            <img 
              src="/LOGO_SEGUROS_ALFA.png" 
              // src="/logoimagine.jpeg" 
              alt="Logo Seguros Alfa" 
              // alt="Logo Imagine SAS"
              className="h-24 w-auto"
            />
          </div>
          <CardTitle className="text-2xl font-bold">
            Sistema Interno de Incapacidades
          </CardTitle>
          <CardDescription>
            Ingrese sus credenciales para acceder
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
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
