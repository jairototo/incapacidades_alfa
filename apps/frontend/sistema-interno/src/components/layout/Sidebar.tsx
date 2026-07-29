import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/authStore';
import {
  LayoutDashboard,
  FileText,
  DollarSign,
  Building2,
  Users,
  UserCircle,
  UserCog,
  BarChart3,
  Settings,
  ChevronDown,
  ChevronRight,
  Search,
  ClipboardList,
  Inbox,
  Link2,
  Calculator,
} from 'lucide-react';

interface MenuItem {
  label: string;
  icon: React.ElementType;
  href?: string;
  children?: MenuItem[];
  roles?: string[];
}

const menuItems: MenuItem[] = [
  {
    label: 'Dashboard',
    icon: LayoutDashboard,
    href: '/dashboard',
  },
  {
    label: 'Incapacidades',
    icon: FileText,
    children: [
      {
        label: 'Consulta',
        icon: Search,
        href: '/incapacidades/consulta',
        roles: ['ADMIN', 'AUDITOR'],
      },
      {
        label: 'Pendientes',
        icon: ClipboardList,
        href: '/incapacidades/pendientes',
        roles: ['ADMIN', 'AUDITOR'],
      },
      {
        label: 'Creación Siniestro',
        icon: Link2,
        href: '/incapacidades/creacion-siniestro',
        roles: ['ADMIN'],
      },
      {
        label: 'Liquidación',
        icon: Calculator,
        href: '/incapacidades/liquidacion',
        roles: ['ADMIN', 'AUDITOR'],
      },
    ],
  },
  {
    label: 'Pre-Incapacidades',
    icon: Inbox,
    children: [
      {
        label: 'Bandeja',
        icon: ClipboardList,
        href: '/pre-incapacidades/bandeja',
        roles: ['ADMIN', 'AUDITOR'],
      },
    ],
  },
  {
    label: 'Órdenes de Pago',
    icon: DollarSign,
    href: '/ordenes-pago',
    roles: ['ADMIN', 'APROBADOR'],
  },
  {
    label: 'Empresas',
    icon: Building2,
    href: '/empresas',
    roles: ['ADMIN', 'AUDITOR', 'LIQUIDADOR'],
  },
  {
    label: 'Empleados',
    icon: UserCog,
    href: '/empleados',
    roles: ['ADMIN', 'AUDITOR', 'LIQUIDADOR'],
  },
  {
    label: 'Afiliados',
    icon: Users,
    href: '/afiliados',
    roles: ['ADMIN'],
  },
  {
    label: 'Usuarios',
    icon: UserCircle,
    href: '/usuarios',
    roles: ['ADMIN'],
  },
  {
    label: 'Reportes',
    icon: BarChart3,
    href: '/reportes',
    roles: ['ADMIN', 'AUDITOR'],
  },
  {
    label: 'Configuración',
    icon: Settings,
    href: '/configuracion',
    roles: ['ADMIN'],
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuthStore();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Incapacidades']);

  const toggleExpanded = (label: string) => {
    setExpandedItems((prev) =>
      prev.includes(label)
        ? prev.filter((item) => item !== label)
        : [...prev, label]
    );
  };

  const isActive = (href?: string) => {
    if (!href) return false;
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  const hasPermission = (roles?: string[]) => {
    if (!roles || roles.length === 0) return true;
    if (!user) return false;
    return roles.includes(user.rol);
  };

  const renderMenuItem = (item: MenuItem, level = 0) => {
    // Filtrar por permisos
    if (!hasPermission(item.roles)) {
      return null;
    }

    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.label);
    const Icon = item.icon;

    if (hasChildren) {
      return (
        <div key={item.label} className="space-y-1">
          <button
            onClick={() => toggleExpanded(item.label)}
            className={cn(
              'w-full flex items-center justify-between px-2.5 py-1.5 text-sm font-medium rounded-md transition-colors',
              'hover:bg-slate-100 text-slate-700'
            )}
            style={{ paddingLeft: `${12 + level * 16}px` }}
          >
            <div className="flex items-center">
              <Icon className="mr-2.5 h-4 w-4" />
              {item.label}
            </div>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {isExpanded && (
            <div className="space-y-1">
              {item.children?.map((child) => renderMenuItem(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link
        key={item.label}
        to={item.href!}
        className={cn(
          'flex items-center px-2.5 py-1.5 text-sm font-medium rounded-md transition-colors',
          isActive(item.href)
            ? 'bg-blue-50 text-blue-700'
            : 'text-slate-700 hover:bg-slate-100'
        )}
        style={{ paddingLeft: `${12 + level * 16}px` }}
      >
        <Icon className="mr-3 h-5 w-5" />
        {item.label}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        'w-64 bg-white border-r border-slate-200 flex flex-col transition-all duration-300',
        !isOpen && 'hidden lg:flex'
      )}
    >
      {/* Logo */}
      <div className="h-12 flex items-center px-4 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <img
            src="/LOGO_SEGUROS_ALFA.png"
            alt="Logo Seguros Alfa"
            className="h-8 w-auto"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {menuItems.map((item) => renderMenuItem(item))}
      </nav>

      {/* User Info */}
      <div className="p-3 border-t border-slate-200">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 bg-slate-200 rounded-full flex items-center justify-center">
            <UserCircle className="h-4 w-4 text-slate-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">
              {user?.nombres} {user?.apellidos}
            </p>
            <p className="text-xs text-slate-500 truncate">{user?.rol}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
