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
import { AuditoresPage } from '@/pages/admin/AuditoresPage';
import { EmpresasPage } from '@/pages/admin/EmpresasPage';
import { EmpleadosPage } from '@/pages/admin/EmpleadosPage';
import { CargaLotePage } from '@/pages/previsionales/CargaLotePage';
import { RadicacionLotePage } from '@/pages/previsionales/RadicacionLotePage';
import { SiniestroManualPage } from '@/pages/previsionales/SiniestroManualPage';
import { AuditoriaPrevisionalPage } from '@/pages/previsionales/AuditoriaPrevisionalPage';
import { LiquidacionPrevisionalPage } from '@/pages/previsionales/LiquidacionPrevisionalPage';
import { RespuestaAfpPage } from '@/pages/previsionales/RespuestaAfpPage';

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
          
          // Empresas - ADMIN, AUDITOR, LIQUIDADOR (lectura); escritura gateada por botón
          {
            path: '/empresas',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR]} />,
            children: [
              {
                index: true,
                element: <EmpresasPage />,
              },
            ],
          },

          // Empleados - ADMIN, AUDITOR, LIQUIDADOR (lectura); escritura gateada por botón
          {
            path: '/empleados',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR]} />,
            children: [
              {
                index: true,
                element: <EmpleadosPage />,
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

          // Previsionales - ADMIN, AUDITOR_PREVISIONALES y AUDITOR_JURIDICO
          //
          // Rutas de la Fase 5 (Task 5.1). Las 6 pantallas reales (Tasks
          // 5.2-5.7) están completas -- ya no quedan placeholders bajo este
          // árbol. `index` no tiene tarea propia: en vez de un placeholder
          // huérfano, redirige al punto de entrada natural del flujo (carga
          // de lote, Task 5.2).
          {
            path: '/previsionales',
            element: (
              <ProtectedRoute
                allowedRoles={[
                  RolUsuario.ADMIN,
                  RolUsuario.AUDITOR_PREVISIONALES,
                  RolUsuario.AUDITOR_JURIDICO,
                ]}
              />
            ),
            children: [
              {
                index: true,
                element: <Navigate to="carga" replace />,
              },
              {
                // Task 5.2 - Carga de lote (excel AFP): entrada del flujo Previsionales.
                path: 'carga',
                element: <CargaLotePage />,
              },
              {
                // Task 5.3 - Panel de radicación: detalle de un lote + sus incapacidades.
                path: 'lotes/:loteId',
                element: <RadicacionLotePage />,
              },
              {
                // Task 5.4 - Registro manual de un siniestro previsional.
                path: 'siniestros/nuevo',
                element: <SiniestroManualPage />,
              },
              {
                // Task 5.5 - Auditoría (señales AB-AT, aval, día 181, duplicar) de una incapacidad.
                path: 'incapacidades/:incapacidadId/auditoria',
                element: <AuditoriaPrevisionalPage />,
              },
              {
                // Task 5.6 - Liquidación (re-liquidar) de un lote.
                path: 'lotes/:loteId/liquidacion',
                element: <LiquidacionPrevisionalPage />,
              },
              {
                // Task 5.7 - Exportación de la respuesta AFP de un lote.
                path: 'lotes/:loteId/respuesta',
                element: <RespuestaAfpPage />,
              },
            ],
          },

          // Usuarios (Gestión de Auditores) - Solo ADMIN
          {
            path: '/usuarios',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <AuditoresPage />,
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

