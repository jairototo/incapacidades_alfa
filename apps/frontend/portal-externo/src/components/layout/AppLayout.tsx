import { Outlet } from 'react-router-dom';
import { CorporateFooter } from './CorporateFooter';

/**
 * Layout de las pantallas autenticadas: contenido + pie corporativo consistente.
 * El contenido ocupa el alto disponible y empuja el footer al fondo.
 */
export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex-1">
        <Outlet />
      </div>
      <CorporateFooter />
    </div>
  );
}
