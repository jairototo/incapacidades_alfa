import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { RolUsuario } from '@/types/auth';

interface ProtectedRouteProps {
  /**
   * Roles permitidos para acceder a esta ruta
   * Si no se especifica, cualquier usuario autenticado puede acceder
   */
  allowedRoles?: RolUsuario[];
}

/**
 * Componente de ruta protegida con autenticación y RBAC
 * 
 * Features:
 * - Bloquea acceso a usuarios no autenticados
 * - Soporta control de acceso basado en roles (RBAC)
 * - Preserva la ruta solicitada para redirect después de login
 * - Redirect a /unauthorized si el usuario no tiene permisos
 * 
 * @example
 * // Ruta protegida sin restricción de roles
 * <Route element={<ProtectedRoute />}>
 *   <Route path="/dashboard" element={<DashboardPage />} />
 * </Route>
 * 
 * @example
 * // Ruta protegida solo para ADMIN y AUDITOR
 * <Route element={<ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR]} />}>
 *   <Route path="/incapacidades/pendientes" element={<PendientesPage />} />
 * </Route>
 */
export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();

  // Redirect a login si no está autenticado
  // Preservar la ruta solicitada en state para redirect después de login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Verificar permisos de rol si se especificaron roles permitidos
  if (allowedRoles && user) {
    const hasPermission = allowedRoles.includes(user.rol);
    
    if (!hasPermission) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  // Usuario autenticado y con permisos, renderizar contenido
  return <Outlet />;
}
