import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { loginSchema, type LoginFormData } from '@/schemas/loginSchema';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { APP_VERSION } from '@/lib/version';

const LOGIN_BG = '/vitaly-gariev-egCFrNJ6Djw-unsplash.jpg';

export function LoginPage() {
  const navigate = useNavigate();
  const loginStore = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState<string | null>(null);
  const [forgotMsg, setForgotMsg] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<LoginFormData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormData) => {
    setServerError(null);
    try {
      const resp = await authService.login(values);
      if (resp.user.rol !== 'EMPRESA' || !resp.user.empresa_id) {
        setServerError('No tiene acceso a este portal. Contacte a Servicio al Cliente.');
        return;
      }
      const { user, ...tokens } = resp;
      loginStore(tokens, user);
      navigate('/', { replace: true });
    } catch {
      setServerError('Usuario o contraseña inválidos.');
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left — imagen institucional (oculta en móvil) */}
      <aside
        className="relative hidden md:flex md:w-1/2 lg:w-3/5 bg-cover bg-center"
        style={{ backgroundImage: `url('${LOGIN_BG}')` }}
        aria-hidden="true"
      >
        <div className="absolute inset-0 bg-black/45" />
        <div className="relative z-10 mt-auto p-10 lg:p-16 text-white">
          <h2 className="max-w-xl text-3xl lg:text-4xl font-bold leading-tight">
            Gestión Inteligente de Incapacidades
          </h2>
          <p className="mt-4 max-w-md text-base lg:text-lg leading-relaxed text-white/85">
            Automatice la radicación, auditoría y seguimiento de incapacidades desde una única plataforma.
          </p>
        </div>
      </aside>

      {/* Right — tarjeta de acceso */}
      <main className="flex w-full md:w-1/2 lg:w-2/5 items-center justify-center bg-gradient-to-b from-white to-[#f6faf9] p-6 sm:p-8">
        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-border bg-white p-8 shadow-[0_12px_44px_rgba(0,73,83,0.10)]">
            <img src="/LOGO_SEGUROS_ALFA.png" alt="Seguros Alfa" className="h-10 w-auto" />

            <div className="mt-6">
              <h1 className="text-2xl font-bold text-foreground">Bienvenido</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Ingrese con sus credenciales de empresa.
              </p>
            </div>

            {serverError && (
              <div role="alert" className="mt-5 rounded-md bg-red-50 p-3 text-sm text-[#D92D20]">
                {serverError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="username">Usuario</Label>
                <Input
                  id="username"
                  autoFocus
                  autoComplete="username"
                  aria-invalid={!!errors.username}
                  aria-describedby={errors.username ? 'username-error' : undefined}
                  {...register('username')}
                />
                {errors.username && (
                  <p id="username-error" className="text-sm text-[#D92D20]" aria-live="polite">
                    {errors.username.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  {...register('password')}
                />
                {errors.password && (
                  <p id="password-error" className="text-sm text-[#D92D20]" aria-live="polite">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between">
                {/* Recordarme: presente pero deshabilitado (funcionalidad pendiente) */}
                <label className="flex cursor-not-allowed select-none items-center gap-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    disabled
                    aria-disabled="true"
                    className="h-4 w-4 rounded border-input opacity-60"
                  />
                  Recordarme
                </label>
                <button
                  type="button"
                  onClick={() =>
                    setForgotMsg('Para restablecer su contraseña, contacte a Servicio al Cliente.')
                  }
                  className="text-sm font-medium text-primary transition-colors duration-150 hover:text-[#005D55] hover:underline"
                >
                  ¿Olvidó su contraseña?
                </button>
              </div>
              {forgotMsg && (
                <p className="text-xs text-muted-foreground" aria-live="polite">
                  {forgotMsg}
                </p>
              )}

              <Button type="submit" variant="primary" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? 'Ingresando…' : 'Ingresar'}
              </Button>
            </form>
          </div>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            © 2026 Seguros Alfa · v{APP_VERSION}
          </p>
        </div>
      </main>
    </div>
  );
}
