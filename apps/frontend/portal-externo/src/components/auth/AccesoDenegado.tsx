import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';

export function AccesoDenegado() {
  const logout = useAuthStore((s) => s.logout);
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div role="alert" className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-bold text-foreground">No tiene acceso a este portal</h1>
        <p className="text-sm text-muted-foreground">
          Este portal es exclusivo para usuarios de empresa vinculados a una compañía.
          Si cree que es un error, contacte a Servicio al Cliente.
        </p>
        {/* Hard redirect intentional: flushes persisted store state and the React tree on logout */}
        <Button onClick={() => { logout(); window.location.href = '/login'; }}>
          Volver al inicio de sesión
        </Button>
      </div>
    </div>
  );
}
