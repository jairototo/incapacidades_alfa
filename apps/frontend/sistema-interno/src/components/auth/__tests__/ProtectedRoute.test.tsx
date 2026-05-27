import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { useAuthStore } from '@/store/authStore';
import type { User } from '@/types/auth';
import { RolUsuario } from '@/types/auth';

// Mock del store de autenticación
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Componente de prueba para renderizar dentro de ProtectedRoute
  const ProtectedContent = () => <div>Protected Content</div>;
  const LoginPage = () => <div>Login Page</div>;
  const UnauthorizedPage = () => <div>Unauthorized Page</div>;

  const renderProtectedRoute = (
    allowedRoles?: RolUsuario[],
    initialRoute = '/'
  ) => {
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route element={<ProtectedRoute allowedRoles={allowedRoles} />}>
            <Route path="/" element={<ProtectedContent />} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
  };

  describe('Autenticación', () => {
    it('debe redirigir a /login cuando el usuario NO está autenticado', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        refreshToken: null,
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute();

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('debe renderizar el contenido protegido cuando el usuario ESTÁ autenticado', () => {
      const mockUser: User = {
        id: '123',
        username: 'admin@test.com',
        email: 'admin@test.com',
        nombres: 'Admin',
        apellidos: 'Test',
        rol: RolUsuario.ADMIN,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute();

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
    });
  });

  describe('RBAC (Control de acceso basado en roles)', () => {
    it('debe permitir acceso cuando el usuario tiene un rol permitido (ADMIN)', () => {
      const mockUser: User = {
        id: '123',
        username: 'admin@test.com',
        email: 'admin@test.com',
        nombres: 'Admin',
        apellidos: 'Test',
        rol: RolUsuario.ADMIN,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute([RolUsuario.ADMIN, RolUsuario.AUDITOR]);

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByText('Unauthorized Page')).not.toBeInTheDocument();
    });

    it('debe permitir acceso cuando el usuario tiene un rol permitido (AUDITOR)', () => {
      const mockUser: User = {
        id: '123',
        username: 'auditor@test.com',
        email: 'auditor@test.com',
        nombres: 'Auditor',
        apellidos: 'Test',
        rol: RolUsuario.AUDITOR,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute([RolUsuario.ADMIN, RolUsuario.AUDITOR]);

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByText('Unauthorized Page')).not.toBeInTheDocument();
    });

    it('debe redirigir a /unauthorized cuando el usuario NO tiene un rol permitido', () => {
      const mockUser: User = {
        id: '123',
        username: 'empresa@test.com',
        email: 'empresa@test.com',
        nombres: 'Empresa',
        apellidos: 'Test',
        rol: RolUsuario.EMPRESA,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      // Ruta solo para ADMIN y AUDITOR
      renderProtectedRoute([RolUsuario.ADMIN, RolUsuario.AUDITOR]);

      expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('debe permitir acceso a cualquier usuario autenticado cuando NO se especifican roles', () => {
      const mockUser: User = {
        id: '123',
        username: 'empleado@test.com',
        email: 'empleado@test.com',
        nombres: 'Empleado',
        apellidos: 'Test',
        rol: RolUsuario.EMPLEADO,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      // Sin allowedRoles = cualquier usuario autenticado puede acceder
      renderProtectedRoute();

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByText('Unauthorized Page')).not.toBeInTheDocument();
    });
  });

  describe('Múltiples roles permitidos', () => {
    it('debe permitir acceso a APROBADOR cuando está en la lista', () => {
      const mockUser: User = {
        id: '123',
        username: 'aprobador@test.com',
        email: 'aprobador@test.com',
        nombres: 'Aprobador',
        apellidos: 'Test',
        rol: RolUsuario.APROBADOR,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute([RolUsuario.ADMIN, RolUsuario.APROBADOR]);

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('debe bloquear acceso a READONLY cuando NO está en la lista', () => {
      const mockUser: User = {
        id: '123',
        username: 'readonly@test.com',
        email: 'readonly@test.com',
        nombres: 'ReadOnly',
        apellidos: 'Test',
        rol: RolUsuario.READONLY,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute([RolUsuario.ADMIN, RolUsuario.AUDITOR]);

      expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Edge cases', () => {
    it('debe redirigir a /login cuando isAuthenticated es false pero user existe', () => {
      const mockUser: User = {
        id: '123',
        username: 'user@test.com',
        email: 'user@test.com',
        nombres: 'User',
        apellidos: 'Test',
        rol: RolUsuario.ADMIN,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: mockUser, // Usuario existe pero no autenticado
        accessToken: null,
        refreshToken: null,
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute();

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('debe redirigir a /login cuando user es null', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        refreshToken: null,
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute([RolUsuario.ADMIN]);

      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  });

  describe('Renderizado de Outlet', () => {
    it('debe renderizar Outlet cuando el acceso está permitido', () => {
      const mockUser: User = {
        id: '123',
        username: 'admin@test.com',
        email: 'admin@test.com',
        nombres: 'Admin',
        apellidos: 'Test',
        rol: RolUsuario.ADMIN,
        estado: 'ACTIVO' as any,
        created_at: '2026-01-23T00:00:00Z',
        updated_at: '2026-01-23T00:00:00Z',
      };

      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        accessToken: 'mock-token',
        refreshToken: 'mock-refresh-token',
        login: vi.fn(),
        logout: vi.fn(),
        updateAccessToken: vi.fn(),
        updateUser: vi.fn(),
      });

      renderProtectedRoute();

      // Outlet renderiza el contenido hijo
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });
});
