import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { LogIn, AlertCircle } from 'lucide-react';

import { useAuth } from '@/application/hooks/useAuth';
import { Button, FormField, Input } from '@/presentation/components/ui';

interface FormValues {
  email: string;
  password: string;
}

interface LocationState {
  from?: { pathname: string };
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, login } = useAuth();
  const { register, handleSubmit, formState } = useForm<FormValues>({
    defaultValues: { email: '', password: '' },
  });
  const [serverError, setServerError] = useState<string | null>(null);

  if (isAuthenticated) {
    const from = (location.state as LocationState | undefined)?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      await login.mutateAsync(values);
      const from = (location.state as LocationState | undefined)?.from?.pathname ?? '/';
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'No fue posible iniciar sesión';
      setServerError(message);
    }
  });

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-brand-900">PORTAL FAAL IMA</h1>
          <p className="mt-1 text-sm text-gray-600">Inicio de sesión</p>
        </header>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <FormField label="Correo electrónico" htmlFor="email" required>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="usuario@portalfaal.app"
              {...register('email', { required: true })}
            />
          </FormField>

          <FormField label="Contraseña" htmlFor="password" required>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password', { required: true, minLength: 1 })}
            />
          </FormField>

          {serverError && (
            <div
              className="flex items-start gap-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
              role="alert"
            >
              <AlertCircle size={16} strokeWidth={1.75} className="mt-0.5 shrink-0" aria-hidden />
              <span>{serverError}</span>
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            loading={formState.isSubmitting || login.isPending}
            leftIcon={<LogIn size={16} strokeWidth={1.75} aria-hidden />}
          >
            Ingresar
          </Button>
        </form>
      </div>
    </main>
  );
}

