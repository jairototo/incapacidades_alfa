import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@/types/auth';

interface AuthState {
  // State
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => void;
  updateAccessToken: (token: string) => void;
  updateUser: (user: User) => void;
}

/**
 * Store de autenticación con persistencia
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // State inicial
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      // Login - Guardar tokens y usuario
      login: (tokens, user) => {
        // Guardar en localStorage también (para el interceptor de axios)
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(user));

        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          user,
          isAuthenticated: true,
        });
      },

      // Logout - Limpiar todo
      logout: () => {
        // Limpiar localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
      },

      // Actualizar solo el access token (después de refresh)
      updateAccessToken: (token) => {
        localStorage.setItem('access_token', token);
        
        set({
          accessToken: token,
        });
      },

      // Actualizar información del usuario
      updateUser: (user) => {
        localStorage.setItem('user', JSON.stringify(user));
        
        set({
          user,
        });
      },
    }),
    {
      name: 'auth-storage', // nombre en localStorage
      partialize: (state) => ({
        // Solo persistir estos campos
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Hook para verificar si el usuario tiene un rol específico
 */
export const useHasRole = (roles: string | string[]) => {
  const user = useAuthStore((state) => state.user);
  
  if (!user) return false;
  
  const allowedRoles = Array.isArray(roles) ? roles : [roles];
  return allowedRoles.includes(user.rol);
};

/**
 * Hook para verificar si el usuario puede realizar una acción
 */
export const useCanPerform = (action: string) => {
  const user = useAuthStore((state) => state.user);
  
  if (!user) return false;
  
  // Mapa de permisos por rol (sincronizado con backend)
  const permissions: Record<string, string[]> = {
    ADMIN: ['*'], // Todos los permisos
    AUDITOR: [
      'incapacidad.read',
      'incapacidad.update',
      'incapacidad.cambiar_estado',
      'incapacidad.observar',
      'empresa.read',
      'empleado.read',
      'empleado.create',
      'empleado.update',
      'empleado.delete',
    ],
    APROBADOR: [
      'incapacidad.read',
      'incapacidad.aprobar',
      'incapacidad.rechazar',
      'orden_pago.aprobar',
    ],
    READONLY: ['incapacidad.read'],
    EMPRESA: ['incapacidad.read', 'incapacidad.create'],
    EMPLEADO: ['incapacidad.read'],
    LIQUIDADOR: ['empresa.read', 'empleado.read'],
  };
  
  const userPermissions = permissions[user.rol] || [];
  
  // Si tiene permiso '*', puede todo
  if (userPermissions.includes('*')) return true;
  
  // Verificar si tiene el permiso específico
  return userPermissions.includes(action);
};
