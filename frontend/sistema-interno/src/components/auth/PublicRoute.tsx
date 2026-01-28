import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { RolUsuario } from '@/types/auth';

interface PublicRouteProps {
  children: React.ReactNode;
}

/**
 * Componente de ruta pública
 * Redirige a dashboard si el usuario ya está autenticado
 * 
 * Usado principalmente para la página de login
 * para evitar que usuarios autenticados accedan
 * 
 * Si existe location.state.from, redirige allí.
 * Si no, redirige según el rol del usuario.
 */
export function PublicRoute({ children }: PublicRouteProps) {
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();

  if (isAuthenticated && user) {
    // Intentar usar la ruta desde donde vino (preservada por ProtectedRoute)
    const from = (location.state as any)?.from?.pathname;
    const redirectPath = from || getRedirectPath(user.rol as RolUsuario);
    
    return <Navigate to={redirectPath} replace />;
  }

  return <>{children}</>;
}

/**
 * Determina la ruta de redirección según el rol del usuario
 */
function getRedirectPath(rol: RolUsuario): string {
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
