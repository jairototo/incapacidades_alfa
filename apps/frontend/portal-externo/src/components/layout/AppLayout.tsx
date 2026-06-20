import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { CorporateFooter } from './CorporateFooter';

/**
 * Layout de las pantallas autenticadas: barra superior + contenido + pie corporativo,
 * consistentes en todas las rutas internas. El contenido ocupa el alto disponible
 * y empuja el footer al fondo.
 */
export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <CorporateFooter />
    </div>
  );
}
