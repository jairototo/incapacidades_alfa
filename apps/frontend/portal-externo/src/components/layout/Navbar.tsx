import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { User, ChevronDown, LogOut, Menu, X } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

const NAV = [
  { to: '/radicar/individual', label: 'Radicación Individual' },
  { to: '/radicar/masiva', label: 'Radicación Masiva' },
  { to: '/consulta', label: 'Consulta' },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150',
    isActive
      ? 'bg-primary/10 text-primary'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
  ].join(' ');

/**
 * Barra superior persistente de las pantallas autenticadas (vía AppLayout):
 * logo + nombre del portal a la izquierda; navegación + menú de usuario a la derecha.
 * En móvil, la navegación colapsa en un drawer (hamburguesa).
 */
export function Navbar() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const [userOpen, setUserOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Cerrar el menú de usuario al hacer clic fuera
  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserOpen(false);
      }
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white shadow-[0_2px_12px_rgba(0,73,83,0.05)]">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Izquierda: logo + nombre del portal */}
        <Link to="/" className="flex items-center gap-3">
          <img src="/LOGO_SEGUROS_ALFA.png" alt="Seguros Alfa" className="h-8 w-auto" />
          <span className="hidden text-base font-bold text-foreground sm:inline">Portal Empresas</span>
        </Link>

        {/* Derecha: navegación (desktop) + usuario + hamburguesa (móvil) */}
        <div className="flex items-center gap-2">
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} className={linkClass}>
                {n.label}
              </NavLink>
            ))}
          </nav>

          {/* Menú de usuario */}
          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setUserOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={userOpen}
              aria-label="Menú de usuario"
              className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-foreground transition-colors duration-150 hover:bg-muted"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                <User className="h-4 w-4" />
              </span>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </button>

            {userOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-64 rounded-lg border border-border bg-white p-1 shadow-[0_10px_36px_rgba(0,73,83,0.12)]"
              >
                <div className="px-3 py-2">
                  <p className="text-sm font-semibold text-foreground">
                    {user?.empresa?.razon_social ?? 'Empresa'}
                  </p>
                  {user?.nombre_completo && (
                    <p className="mt-0.5 text-xs text-muted-foreground">{user.nombre_completo}</p>
                  )}
                  {user?.email && <p className="text-xs text-muted-foreground">{user.email}</p>}
                </div>
                <div className="my-1 border-t border-border" />
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-foreground transition-colors duration-150 hover:bg-muted"
                >
                  <LogOut className="h-4 w-4" />
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>

          {/* Hamburguesa (móvil) */}
          <button
            type="button"
            className="rounded-md p-2 text-foreground transition-colors duration-150 hover:bg-muted md:hidden"
            aria-label={mobileOpen ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((o) => !o)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Drawer de navegación (móvil) */}
      {mobileOpen && (
        <nav className="border-t border-border bg-white px-4 py-2 md:hidden">
          <div className="flex flex-col gap-1">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} className={linkClass} onClick={() => setMobileOpen(false)}>
                {n.label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
