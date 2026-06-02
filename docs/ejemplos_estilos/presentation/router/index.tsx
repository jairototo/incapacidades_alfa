import { ReactNode } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';

import { HealthPage } from '@/presentation/pages/Health';
import { LoginPage } from '@/presentation/pages/Login';
import { CompaniesPage } from '@/presentation/pages/CompaniesPage';
import { CompanyDetailPage } from '@/presentation/pages/CompanyDetailPage';
import { WorkersPage } from '@/presentation/pages/WorkersPage';
import { WorkerNoveltiesPage } from '@/presentation/pages/WorkerNoveltiesPage';
import { AffiliationsPage } from '@/presentation/pages/AffiliationsPage';
import { FuratPage } from '@/presentation/pages/FuratPage';
import { FurepPage } from '@/presentation/pages/FurepPage';
import { ClaimsEventsPage } from '@/presentation/pages/ClaimsEventsPage';
import { AbsencesPage } from '@/presentation/pages/AbsencesPage';
import { ContributionsPage } from '@/presentation/pages/ContributionsPage';
import { AuditLogsPage } from '@/presentation/pages/AuditLogsPage';
import { PortalUsersPage } from '@/presentation/pages/PortalUsersPage';
import { AdminPage } from '@/presentation/pages/AdminPage';
import { ProtectedRoute } from '@/presentation/components/ProtectedRoute';
import { AppShell } from '@/presentation/components/AppShell';

function Protected({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/health" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/health', element: <Protected><HealthPage /></Protected> },
  { path: '/companies', element: <Protected><CompaniesPage /></Protected> },
  { path: '/companies/:id', element: <Protected><CompanyDetailPage /></Protected> },
  { path: '/workers', element: <Protected><WorkersPage /></Protected> },
  { path: '/worker-novelties', element: <Protected><WorkerNoveltiesPage /></Protected> },
  { path: '/affiliations', element: <Protected><AffiliationsPage /></Protected> },
  { path: '/furat', element: <Protected><FuratPage /></Protected> },
  { path: '/furep', element: <Protected><FurepPage /></Protected> },
  { path: '/claims-events', element: <Protected><ClaimsEventsPage /></Protected> },
  { path: '/absences', element: <Protected><AbsencesPage /></Protected> },
  { path: '/contributions', element: <Protected><ContributionsPage /></Protected> },
  { path: '/audit-logs', element: <Protected><AuditLogsPage /></Protected> },
  { path: '/portal-users', element: <Protected><PortalUsersPage /></Protected> },
  { path: '/admin', element: <Protected><AdminPage /></Protected> },
]);
