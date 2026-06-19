import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@/types/auth';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => void;
  updateAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      login: (tokens, user) => {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
      },
      updateAccessToken: (token) => {
        localStorage.setItem('access_token', token);
        set({ accessToken: token });
      },
    }),
    { name: 'portal-auth-storage' },
  ),
);

/** EMPRESA logged in AND linked to a company. */
export const useIsEmpresaHabilitada = () =>
  useAuthStore((s) => s.isAuthenticated && s.user?.rol === 'EMPRESA' && !!s.user?.empresa_id);
