import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import { loginSchema, type LoginFormData } from '@/schemas/loginSchema';
import type { AxiosError } from 'axios';

interface LoginFormProps {
  /**
   * Callback ejecutado después de un login exitoso
   * Usar para redireccionar a dashboard o página principal
   */
  onSuccess?: () => void;
}

interface ErrorResponse {
  detail?: string;
  message?: string;
}

/**
 * Formulario de autenticación con validación completa
 * 
 * Features:
 * - Validación en tiempo real con Zod
 * - Manejo de errores específicos del backend
 * - Toggle show/hide password
 * - Loading state durante autenticación
 * - Integración con authStore (Zustand)
 * 
 * @example
 * ```tsx
 * <LoginForm onSuccess={() => navigate('/dashboard')} />
 * ```
 */
export function LoginForm({ onSuccess }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const { login: setAuthState } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur', // Validar al perder foco
  });

  /**
   * Mapear códigos de error HTTP a mensajes amigables
   */
  const getErrorMessage = (error: AxiosError<ErrorResponse>): string => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.response?.data?.message;

    // Errores específicos por mensaje del backend (verificar primero)
    if (detail?.toLowerCase().includes('inactiv')) {
      return 'Tu cuenta está inactiva. Contacta al administrador.';
    }

    if (detail?.toLowerCase().includes('bloqueado') || detail?.toLowerCase().includes('blocked')) {
      return 'Tu cuenta ha sido bloqueada. Contacta al administrador.';
    }

    // Errores específicos del backend por código
    const errorMessages: Record<number, string> = {
      401: 'Usuario o contraseña incorrectos',
      403: 'Tu cuenta ha sido bloqueada por múltiples intentos fallidos. Contacta al administrador.',
      422: 'Los datos ingresados no son válidos',
      500: 'Error del servidor. Por favor intenta más tarde.',
    };

    // Error de red
    if (error.code === 'ERR_NETWORK') {
      return 'No se pudo conectar al servidor. Verifica tu conexión.';
    }

    // Mensaje por código de estado
    return errorMessages[status || 0] || detail || 'Error al iniciar sesión. Intenta nuevamente.';
  };

  /**
   * Submit handler - autenticación y guardado de tokens
   */
  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      // Llamar al servicio de autenticación
      const response = await authService.login(data);

      // Guardar tokens y usuario en el store (persiste en localStorage)
      setAuthState(
        {
          access_token: response.access_token,
          refresh_token: response.refresh_token,
          token_type: response.token_type,
        },
        response.user
      );

      // Ejecutar callback de éxito (redirección)
      onSuccess?.();
    } catch (error) {
      // Manejo robusto de errores
      const axiosError = error as AxiosError<ErrorResponse>;
      const message = getErrorMessage(axiosError);
      setErrorMessage(message);
      
      console.error('Login error:', axiosError);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Error Alert */}
      {errorMessage && (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      {/* Campo Usuario (Email) */}
      <div className="space-y-2">
        <Label htmlFor="username">
          Usuario (Email)
          <span className="text-destructive ml-1" aria-label="requerido">*</span>
        </Label>
        <Input
          id="username"
          type="email"
          placeholder="usuario@ejemplo.com"
          autoComplete="username"
          disabled={isLoading}
          aria-invalid={errors.username ? 'true' : 'false'}
          aria-describedby={errors.username ? 'username-error' : undefined}
          {...register('username')}
        />
        {errors.username && (
          <p 
            id="username-error" 
            className="text-sm text-destructive" 
            role="alert"
          >
            {errors.username.message}
          </p>
        )}
      </div>

      {/* Campo Contraseña */}
      <div className="space-y-2">
        <Label htmlFor="password">
          Contraseña
          <span className="text-destructive ml-1" aria-label="requerido">*</span>
        </Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            autoComplete="current-password"
            disabled={isLoading}
            aria-invalid={errors.password ? 'true' : 'false'}
            aria-describedby={errors.password ? 'password-error' : undefined}
            className="pr-10"
            {...register('password')}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isLoading}
            aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Eye className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
        </div>
        {errors.password && (
          <p 
            id="password-error" 
            className="text-sm text-destructive" 
            role="alert"
          >
            {errors.password.message}
          </p>
        )}
      </div>

      {/* Link Olvidé mi contraseña (Placeholder para Fase 3) */}
      <div className="flex justify-end">
        <a
          href="#"
          className="text-sm text-primary hover:underline"
          onClick={(e) => {
            e.preventDefault();
            // TODO: Implementar en Fase 3
            alert('Funcionalidad en desarrollo');
          }}
        >
          ¿Olvidaste tu contraseña?
        </a>
      </div>

      {/* Botón Submit */}
      <Button
        type="submit"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Iniciando sesión...
          </>
        ) : (
          'Iniciar Sesión'
        )}
      </Button>
    </form>
  );
}
