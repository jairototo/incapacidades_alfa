import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/pages/auth/LoginPage';
import { UnauthorizedPage } from '@/pages/UnauthorizedPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { ConsultaPage } from '@/pages/incapacidades/ConsultaPage';
import { PendientesPage } from '@/pages/incapacidades/PendientesPage';
import { GestionarPage } from '@/pages/incapacidades/GestionarPage';
import { RolUsuario } from '@/types/auth';

/**
 * Configuración de rutas del sistema
 * 
 * Estructura:
 * - Rutas públicas: /login, /unauthorized
 * - Rutas protegidas con AppShell: Todas las rutas internas
 * - Rutas protegidas con RBAC: Según rol del usuario
 * - Catch-all: 404 NotFound
 */
export const router = createBrowserRouter([
  // Redirect raíz a dashboard
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },

  // Rutas públicas
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },

  // Rutas protegidas con AppShell Layout
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          // Dashboard - Acceso para todos los usuarios autenticados
          {
            path: '/dashboard',
            element: <DashboardPage />,
          },
          
          // Incapacidades - Solo ADMIN y AUDITOR
          {
            path: '/incapacidades',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR]} />,
            children: [
              {
                path: 'consulta',
                element: <ConsultaPage />,
              },
              {
                path: 'pendientes',
                element: <PendientesPage />,
              },
              {
                path: ':id/gestionar',
                element: <GestionarPage />,
              },
            ],
          },
          
          // Órdenes de Pago - Solo ADMIN y APROBADOR
          {
            path: '/ordenes-pago',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.APROBADOR]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Órdenes de Pago (Placeholder)</div>,
              },
            ],
          },
          
          // Empresas - Solo ADMIN
          {
            path: '/empresas',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Empresas (Placeholder)</div>,
              },
            ],
          },
          
          // Afiliados - Solo ADMIN
          {
            path: '/afiliados',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Afiliados (Placeholder)</div>,
              },
            ],
          },
          
          // Usuarios - Solo ADMIN
          {
            path: '/usuarios',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Usuarios (Placeholder)</div>,
              },
            ],
          },
          
          // Configuración - Solo ADMIN
          {
            path: '/configuracion',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Configuración (Placeholder)</div>,
              },
            ],
          },
          
          // Reportes - ADMIN y AUDITOR
          {
            path: '/reportes',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR]} />,
            children: [
              {
                index: true,
                element: <div className="p-6">Módulo Reportes (Placeholder)</div>,
              },
            ],
          },
        ],
      },
    ],
  },

  // Catch-all - 404
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);

