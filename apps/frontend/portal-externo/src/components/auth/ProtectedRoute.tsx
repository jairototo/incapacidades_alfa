import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { AccesoDenegado } from './AccesoDenegado';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  if (user.rol !== 'EMPRESA' || !user.empresa_id) return <AccesoDenegado />;
  return <Outlet />;
}
