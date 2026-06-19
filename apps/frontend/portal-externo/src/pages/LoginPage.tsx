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

export function LoginPage() {
  const navigate = useNavigate();
  const loginStore = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState<string | null>(null);
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-[#f6faf9] p-4">
      <form onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md bg-white rounded-lg shadow-sm border border-border p-8 space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Portal de Incapacidades</h1>
        <p className="text-sm text-muted-foreground">Ingrese con sus credenciales de empresa.</p>
        {serverError && (
          <div role="alert" className="rounded-md bg-red-50 text-[#D92D20] text-sm p-3">{serverError}</div>
        )}
        <div className="space-y-2">
          <Label htmlFor="username">Usuario</Label>
          <Input id="username" autoFocus autoComplete="username"
            aria-invalid={!!errors.username}
            aria-describedby={errors.username ? 'username-error' : undefined}
            {...register('username')} />
          {errors.username && (
            <p id="username-error" className="text-sm text-[#D92D20]" aria-live="polite">{errors.username.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Contraseña</Label>
          <Input id="password" type="password" autoComplete="current-password"
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? 'password-error' : undefined}
            {...register('password')} />
          {errors.password && (
            <p id="password-error" className="text-sm text-[#D92D20]" aria-live="polite">{errors.password.message}</p>
          )}
        </div>
        <Button type="submit" variant="primary" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Ingresando…' : 'Ingresar'}
        </Button>
      </form>
    </div>
  );
}
