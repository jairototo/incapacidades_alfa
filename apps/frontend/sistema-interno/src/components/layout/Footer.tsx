/**
 * Footer del sistema interno
 * Muestra información de copyright y versión
 */
export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="h-8 bg-white border-t border-slate-200 flex items-center justify-between px-4">
      <p className="text-xs text-slate-600">
        © {currentYear} Sistema de Gestión de Incapacidades - Imagine SAS. Todos los derechos reservados.
      </p>
      <p className="text-xs text-slate-500">
        Versión 1.0.0
      </p>
    </footer>
  );
}
