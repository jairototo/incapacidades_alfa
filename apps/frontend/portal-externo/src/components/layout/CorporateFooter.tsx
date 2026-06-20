import { APP_VERSION } from '@/lib/version';

/**
 * Pie de página corporativo discreto, usado en todas las pantallas autenticadas
 * (vía AppLayout). Texto pequeño y atenuado; no compite con el contenido.
 */
export function CorporateFooter() {
  return (
    <footer className="border-t border-border bg-white">
      <div className="mx-auto w-full max-w-6xl px-6 py-4">
        <p className="text-xs text-muted-foreground">
          © 2026 Seguros Alfa · v{APP_VERSION}
        </p>
      </div>
    </footer>
  );
}
