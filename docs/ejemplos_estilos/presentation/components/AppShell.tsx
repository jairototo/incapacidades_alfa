import { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Activity,
  Building2,
  ClipboardList,
  FileText,
  AlertTriangle,
  HeartPulse,
  CalendarOff,
  Coins,
  ScrollText,
  ShieldCheck,
  LogOut,
  Users,
} from 'lucide-react';

import { useAuth } from '@/application/hooks/useAuth';
import { cn } from '@/presentation/components/ui/cn';

interface NavItem {
  to: string;
  label: string;
  icon: typeof Building2;
  permission?: string;
}

const NAV_GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: 'General',
    items: [
      { to: '/health', label: 'Inicio', icon: Activity },
    ],
  },
  {
    title: 'Maestros',
    items: [
      { to: '/companies', label: 'Empresas', icon: Building2, permission: 'companies:read' },
      { to: '/workers', label: 'Trabajadores', icon: Users, permission: 'workers:read' },
    ],
  },
  {
    title: 'SGRL',
    items: [
      {
        to: '/worker-novelties',
        label: 'Novedades',
        icon: ClipboardList,
        permission: 'workers:read',
      },
      {
        to: '/affiliations',
        label: 'Afiliaciones',
        icon: FileText,
        permission: 'affiliations:read',
      },
    ],
  },
  {
    title: 'Siniestros',
    items: [
      { to: '/furat', label: 'FURAT', icon: AlertTriangle, permission: 'furat:read' },
      { to: '/furep', label: 'FUREP', icon: HeartPulse, permission: 'furep:read' },
      { to: '/claims-events', label: 'Eventos', icon: AlertTriangle, permission: 'claims:read' },
    ],
  },
  {
    title: 'Operación',
    items: [
      { to: '/absences', label: 'Ausencias', icon: CalendarOff, permission: 'absences:read' },
      { to: '/contributions', label: 'Aportes', icon: Coins, permission: 'contributions:read' },
    ],
  },
  {
    title: 'Administración',
    items: [
      { to: '/portal-users', label: 'Usuarios', icon: Users, permission: 'users:read' },
      { to: '/audit-logs', label: 'Bitácora', icon: ScrollText, permission: 'audit:read' },
      { to: '/admin', label: 'Operaciones', icon: ShieldCheck, permission: 'admin:demo_reset' },
    ],
  },
];

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const permissions = new Set(user?.permissions ?? []);

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => navigate('/login', { replace: true }),
    });
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-200 bg-white lg:flex">
        <div className="border-b border-gray-200 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">
            Portal FAAL
          </p>
          <p className="text-lg font-bold text-brand-900">Seguros Alfa</p>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {NAV_GROUPS.map((group) => {
            const items = group.items.filter(
              (it) => !it.permission || permissions.has(it.permission) || user?.role === 'admin',
            );
            if (items.length === 0) return null;
            return (
              <div key={group.title} className="mb-5">
                <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                  {group.title}
                </p>
                <ul className="space-y-0.5">
                  {items.map((it) => {
                    const Icon = it.icon;
                    return (
                      <li key={it.to}>
                        <NavLink
                          to={it.to}
                          className={({ isActive }) =>
                            cn(
                              'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors',
                              isActive
                                ? 'bg-brand-50 text-brand-700 font-semibold'
                                : 'text-gray-700 hover:bg-gray-100',
                            )
                          }
                        >
                          <Icon size={16} strokeWidth={1.75} aria-hidden />
                          {it.label}
                        </NavLink>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </nav>

        {user ? (
          <div className="border-t border-gray-200 px-4 py-3">
            <p className="truncate text-sm font-medium text-brand-900">{user.full_name}</p>
            <p className="truncate text-xs text-gray-500">{user.email}</p>
            <p className="mt-0.5 text-[10px] uppercase tracking-wider text-brand-600">
              {user.role}
            </p>
            <button
              type="button"
              onClick={handleLogout}
              className="mt-2 inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-gray-300 px-2 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              <LogOut size={12} strokeWidth={1.75} aria-hidden />
              Cerrar sesión
            </button>
          </div>
        ) : null}
      </aside>

      <div className="flex-1 overflow-x-hidden">{children}</div>
    </div>
  );
}
