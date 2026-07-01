import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublicRoute } from '@/components/auth/PublicRoute';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/pages/auth/LoginPage';
import { UnauthorizedPage } from '@/pages/UnauthorizedPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { ConsultaPage } from '@/pages/incapacidades/ConsultaPage';
import { PendientesPage } from '@/pages/incapacidades/PendientesPage';
import { GestionarPage } from '@/pages/incapacidades/GestionarPage';
import { LiquidacionPage } from '@/pages/incapacidades/LiquidacionPage';
import { BandejaPage } from '@/pages/pre-incapacidades/BandejaPage';
import { GestionarPreIncapacidadPage } from '@/pages/pre-incapacidades/GestionarPreIncapacidadPage';
import { RolUsuario } from '@/types/auth';
import { CreacionSiniestroPage } from '@/pages/incapacidades/CreacionSiniestroPage';
import { BandejaSiniestroPage } from '@/pages/incapacidades/BandejaSiniestroPage';
import { BandejaLiquidacionPage } from '@/pages/incapacidades/BandejaLiquidacionPage';

/**
 * Configuración de rutas del sistema
 * 
 * Estructura:
 * - Rutas públicas: /login (con PublicRoute), /unauthorized
 * - Rutas protegidas con AppShell: Todas las rutas internas
 * - Rutas protegidas con RBAC: Según rol del usuario
 * - Catch-all: 404 NotFound
 */
export const router = createBrowserRouter([
  // Redirect raíz a dashboard
  {
    path: '/',
    element: <Navigate to="/incapacidades/consulta" replace />,
  },

  // Rutas públicas
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
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
              {
                path: ':id/liquidacion',
                element: <LiquidacionPage />,
              },
              {
                path: ':id/creacion-siniestro',
                element: <CreacionSiniestroPage />,
              },
              {
                path: 'creacion-siniestro',
                element: <BandejaSiniestroPage />,
              },
              {
                path: 'liquidacion',
                element: <BandejaLiquidacionPage />,
              },
            ],
          },
          
          // Pre-Incapacidades - Solo ADMIN y AUDITOR
          {
            path: '/pre-incapacidades',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR]} />,
            children: [
              {
                path: 'bandeja',
                element: <BandejaPage />,
              },
              {
                path: ':id/gestionar',
                element: <GestionarPreIncapacidadPage />,
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

