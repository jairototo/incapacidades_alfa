import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-primary">
                Sistema de Incapacidades
              </h1>
            </div>
            <nav className="hidden md:flex items-center space-x-6">
              <a href="/" className="text-sm font-medium hover:text-primary transition-colors">
                Inicio
              </a>
              <a href="/radicar" className="text-sm font-medium hover:text-primary transition-colors">
                Radicar Incapacidad
              </a>
              <a href="/consultar" className="text-sm font-medium hover:text-primary transition-colors">
                Consultar
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-auto">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Sistema de Gestión de Incapacidades - Imagine SAS. Todos los derechos reservados.
            </p>
            <div className="flex space-x-6">
              <a href="/terminos" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Términos y Condiciones
              </a>
              <a href="/privacidad" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                Política de Privacidad
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
