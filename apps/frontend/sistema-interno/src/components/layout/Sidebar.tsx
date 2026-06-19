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
  BarChart3,
  Settings,
  ChevronDown,
  ChevronRight,
  Search,
  ClipboardList,
  Inbox,
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
    roles: ['ADMIN'],
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
              'w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors',
              'hover:bg-slate-100 text-slate-700'
            )}
            style={{ paddingLeft: `${12 + level * 16}px` }}
          >
            <div className="flex items-center">
              <Icon className="mr-3 h-5 w-5" />
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
          'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
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
      <div className="h-16 flex items-center px-6 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          {/* <svg x="0px" y="0px" width="190px" height="841.891px" viewBox="64.14 0 467 841.891" space="preserve"><title>Icono de Alfa Verde</title><g><g><path d="M179.783,426.278c0.399,2.949,2.64,4.436,6.72,4.436c1.574,0,2.816-0.311,3.726-0.909s1.375-1.397,1.375-2.351 c0-1.441-1.197-2.417-3.593-2.95l-6.652-1.374c-2.95-0.6-5.234-1.73-6.831-3.327c-1.597-1.618-2.395-3.593-2.395-5.943 c0-3.171,1.197-5.766,3.614-7.762c2.418-1.995,5.655-2.993,9.691-2.993c3.792,0,6.964,0.887,9.491,2.683 c2.551,1.797,4.103,4.125,4.68,6.986l-8.228,1.641c-0.178-1.353-0.82-2.439-1.93-3.26c-1.108-0.82-2.527-1.242-4.279-1.242 c-1.575,0-2.706,0.311-3.394,0.954c-0.688,0.643-1.042,1.375-1.042,2.262c0,1.397,0.976,2.307,2.949,2.75l7.762,1.707 c2.794,0.599,4.901,1.73,6.364,3.371c1.464,1.642,2.196,3.57,2.196,5.854c0,3.526-1.286,6.231-3.881,8.095 c-2.595,1.862-6.055,2.816-10.423,2.816c-3.881,0-7.186-0.799-9.936-2.396s-4.302-3.991-4.701-7.207L179.783,426.278z"></path><path d="M234.183,422.686h-24.815c0.443,2.307,1.396,4.147,2.904,5.522c1.509,1.375,3.261,2.063,5.256,2.063 c3.704,0,6.409-1.441,8.095-4.303l7.695,1.642c-1.397,3.304-3.46,5.81-6.209,7.518c-2.75,1.707-5.943,2.55-9.603,2.55 c-4.702,0-8.671-1.618-11.887-4.834s-4.835-7.362-4.835-12.419c0-5.056,1.619-9.203,4.857-12.44 c3.237-3.238,7.229-4.857,11.975-4.857c4.436,0,8.272,1.553,11.466,4.68c3.193,3.104,4.879,7.118,5.056,11.976v2.904H234.183z M212.671,412.174c-1.552,1.043-2.55,2.528-3.038,4.436h15.745c-0.532-1.996-1.485-3.504-2.86-4.502 c-1.397-0.998-3.017-1.508-4.835-1.508C215.887,410.6,214.201,411.132,212.671,412.174z"></path><path d="M269.243,433.53c0,4.923-1.574,8.737-4.701,11.465s-7.385,4.081-12.729,4.081c-7.584,0-12.862-2.396-15.878-7.186 l6.985-5.3c1.353,1.707,2.661,2.905,3.925,3.614c1.265,0.71,2.928,1.087,4.968,1.087c2.794,0,4.989-0.799,6.631-2.417 c1.641-1.619,2.439-3.837,2.439-6.653v-0.532c-2.484,1.996-5.899,2.994-10.246,2.994c-4.169,0-7.85-1.553-11.044-4.635 c-3.171-3.083-4.768-6.831-4.768-11.222c0-4.347,1.597-8.072,4.768-11.133c3.172-3.06,6.853-4.612,11.044-4.612 c4.258,0,7.695,0.998,10.246,2.994v-2.019h8.294L269.243,433.53z M258.288,424.948c1.752-1.597,2.616-3.615,2.616-6.099 c0-2.484-0.864-4.524-2.616-6.099c-1.752-1.597-3.792-2.373-6.143-2.373c-2.617,0-4.769,0.776-6.476,2.351 c-1.708,1.575-2.551,3.615-2.551,6.143c0,2.528,0.843,4.568,2.551,6.144c1.707,1.574,3.858,2.351,6.476,2.351 C254.496,427.32,256.536,426.522,258.288,424.948z"></path><path d="M306.211,436.657h-8.627v-2.949c-2.616,2.616-6.031,3.925-10.245,3.925c-3.925,0-7.074-1.264-9.469-3.814 c-2.396-2.55-3.593-5.854-3.593-9.891V404.08h8.626v18.029c0,2.307,0.6,4.169,1.797,5.544c1.197,1.397,2.794,2.085,4.79,2.085 c5.389,0,8.094-3.748,8.094-11.244v-14.437h8.627V436.657z"></path><path d="M334.686,403.881l-0.466,8.293h-1.885c-7.74,0-11.621,4.657-11.621,13.972v10.512h-8.626v-32.6h8.626v5.943 c2.95-4.258,6.853-6.409,11.688-6.409C333.4,403.614,334.154,403.703,334.686,403.881z"></path><path d="M364.091,408.094c3.415,3.193,5.123,7.296,5.123,12.308c0,5.013-1.708,9.115-5.123,12.309s-7.562,4.79-12.44,4.79 c-4.968,0-9.159-1.597-12.597-4.79c-3.437-3.193-5.167-7.296-5.167-12.309c0-5.012,1.73-9.114,5.167-12.308 c3.438-3.193,7.651-4.79,12.597-4.79C356.53,403.281,360.676,404.9,364.091,408.094z M358.06,427.432 c1.862-1.796,2.816-4.146,2.816-7.03c0-2.883-0.932-5.211-2.816-7.029c-1.863-1.797-4.015-2.706-6.409-2.706 c-2.484,0-4.68,0.888-6.564,2.684s-2.839,4.147-2.839,7.052c0,2.905,0.954,5.278,2.839,7.053c1.885,1.773,4.08,2.683,6.564,2.683 C354.045,430.137,356.197,429.228,358.06,427.432z"></path><path d="M378.44,426.278c0.399,2.949,2.639,4.436,6.719,4.436c1.575,0,2.816-0.311,3.727-0.909 c0.909-0.599,1.374-1.397,1.374-2.351c0-1.441-1.197-2.417-3.592-2.95l-6.653-1.374c-2.949-0.6-5.233-1.73-6.83-3.327 c-1.597-1.618-2.396-3.593-2.396-5.943c0-3.171,1.198-5.766,3.615-7.762c2.417-1.995,5.655-2.993,9.69-2.993 c3.793,0,6.964,0.887,9.492,2.683c2.55,1.797,4.103,4.125,4.679,6.986l-8.228,1.641c-0.177-1.353-0.82-2.439-1.929-3.26 c-1.109-0.82-2.528-1.242-4.28-1.242c-1.574,0-2.705,0.311-3.393,0.954c-0.688,0.643-1.043,1.375-1.043,2.262 c0,1.397,0.976,2.307,2.949,2.75l7.763,1.707c2.794,0.599,4.9,1.73,6.364,3.371c1.464,1.642,2.195,3.57,2.195,5.854 c0,3.526-1.286,6.231-3.881,8.095c-2.595,1.862-6.054,2.816-10.423,2.816c-3.881,0-7.186-0.799-9.935-2.396 c-2.75-1.597-4.303-3.991-4.702-7.207L378.44,426.278z"></path><path d="M447.452,436.657h-8.627v-2.551c-2.927,2.351-6.52,3.526-10.777,3.526c-4.302,0-8.05-1.641-11.243-4.901 c-3.172-3.26-4.769-7.385-4.769-12.352c0-4.968,1.597-9.093,4.79-12.375s6.941-4.923,11.199-4.923 c4.303,0,7.896,1.197,10.778,3.593v-2.617h8.626v32.6H447.452z M436.031,427.432c1.863-1.796,2.816-4.146,2.816-7.03 c0-2.883-0.932-5.233-2.816-7.052c-1.862-1.818-4.036-2.75-6.476-2.75c-2.661,0-4.834,0.888-6.564,2.684 c-1.729,1.796-2.572,4.169-2.572,7.118c0,2.95,0.865,5.322,2.572,7.097c1.73,1.774,3.903,2.639,6.564,2.639 C431.995,430.137,434.147,429.228,436.031,427.432z"></path><path d="M453.329,436.657v-47.014h8.626v47.014H453.329z"></path><path d="M488.013,404.08v7.052h-9.868v25.525h-8.627v-25.525h-4.968v-7.052h4.968v-2.949c0-3.793,1.176-6.786,3.526-9.004 s5.455-3.327,9.336-3.327c2.085,0,4.036,0.421,5.811,1.242l-1.952,6.986c-1.175-0.399-2.262-0.577-3.26-0.577 c-1.441,0-2.595,0.421-3.504,1.242c-0.887,0.82-1.33,1.974-1.33,3.459v2.95h9.868V404.08z"></path><path d="M521.433,436.657h-8.627v-2.551c-2.927,2.351-6.52,3.526-10.777,3.526c-4.303,0-8.05-1.641-11.243-4.901 c-3.172-3.26-4.769-7.385-4.769-12.352c0-4.968,1.597-9.093,4.79-12.375s6.941-4.923,11.199-4.923 c4.303,0,7.895,1.197,10.778,3.593v-2.617h8.626v32.6H521.433z M510.012,427.432c1.862-1.796,2.816-4.146,2.816-7.03 c0-2.883-0.932-5.233-2.816-7.052c-1.863-1.818-4.036-2.75-6.476-2.75c-2.661,0-4.834,0.888-6.564,2.684 c-1.729,1.796-2.572,4.169-2.572,7.118c0,2.95,0.865,5.322,2.572,7.097c1.73,1.774,3.903,2.639,6.564,2.639 C505.976,430.137,508.149,429.228,510.012,427.432z"></path></g><g><polygon fill="#00917B" points="114.873,382.547 78.726,390.309 114.364,398.025 152.418,390.597"></polygon><path fill="#00917B" d="M87.974,409.668c-4.014,0-7.274,6.299-7.274,14.061s3.261,14.06,7.274,14.06s7.273-6.298,7.273-14.06 S91.988,409.668,87.974,409.668z"></path><path fill="#00917B" d="M73.825,392.371l0.021,54.354l38.897,12.619v-58.59L73.825,392.371z M105.56,453.422 c0,0-4.324-15.39-6.986-19.16l-0.754-1.286c-1.773,7.03-5.521,11.909-9.846,11.909c-6.055,0-10.955-9.47-10.955-21.156 c0-11.688,4.9-21.156,10.955-21.156c4.9,0,9.025,6.187,10.445,14.747l0.62-1.197c0,0,5.411-9.936,6.144-14.326l3.792,0.133 c0,0-4.103,13.306-9.514,22.664c0,0,9.514,22.51,10.245,27.344L105.56,453.422z"></path><path fill="#00917B" d="M130.929,411.42c-4.235-0.266-8.027,5.922-8.471,13.816c-0.444,7.895,2.616,14.503,6.853,14.747 c4.235,0.267,8.027-5.921,8.471-13.815C138.247,418.295,135.165,411.687,130.929,411.42z"></path><path fill="#00917B" d="M115.716,400.864l-0.11,58.413l39.673-12.663v-54.443L115.716,400.864z M149.757,446.969 c0,0-5.434-14.148-8.338-17.452l-0.045-0.244c-1.353,10.467-6.631,18.317-12.485,17.94c-6.364-0.399-10.999-10.334-10.312-22.221 c0.665-11.887,6.387-21.179,12.751-20.779c3.726,0.222,6.83,3.726,8.648,8.959l0.355-0.843c0,0,4.368-9.912,4.701-14.126 l0.066-1.131l3.881-0.954l-0.266,1.863c0,0-2.816,12.885-7.208,22.221c0,0.044,0,0.111,0.022,0.178 c0.532,0.976,11.021,20.402,12.108,24.793L149.757,446.969z"></path></g></g></svg> */}
          <img 
                src="/LOGO_SEGUROS_ALFA.png" 
                // src="/logoimagine.jpeg" 
                alt="Logo Seguros Alfa" 
                // alt="Logo Imagine SAS"
              className="h-16 w-auto"
            />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {menuItems.map((item) => renderMenuItem(item))}
      </nav>

      {/* User Info */}
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center">
            <UserCircle className="h-6 w-6 text-slate-600" />
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
