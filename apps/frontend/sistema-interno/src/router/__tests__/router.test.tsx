import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { router } from '../index';
import * as authStoreModule from '@/store/authStore';
import { RolUsuario, EstadoUsuario, type Usuario } from '@/types/auth';

/**
 * Tests de integración para el router completo del sistema
 * Valida navegación, autenticación y control de acceso basado en roles
 */

// Mock del authStore
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockUserAdmin: Usuario = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  username: 'admin',
  email: 'admin@test.com',
  nombres: 'Admin',
  apellidos: 'Test',
  rol: RolUsuario.ADMIN,
  estado: EstadoUsuario.ACTIVO,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockUserAuditor: Usuario = {
  id: '223e4567-e89b-12d3-a456-426614174000',
  username: 'auditor',
  email: 'auditor@test.com',
  nombres: 'Auditor',
  apellidos: 'Test',
  rol: RolUsuario.AUDITOR,
  estado: EstadoUsuario.ACTIVO,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockUserEmpresa: Usuario = {
  id: '323e4567-e89b-12d3-a456-426614174000',
  username: 'empresa',
  email: 'empresa@test.com',
  nombres: 'Empresa',
  apellidos: 'Test',
  rol: RolUsuario.EMPRESA,
  estado: EstadoUsuario.ACTIVO,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('Router - Integración', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rutas públicas', () => {
    it('debe renderizar LoginPage en /login', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        refreshToken: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      render(<RouterProvider router={router} />);

      await waitFor(() => {
        expect(screen.getByText(/Iniciar Sesión/i)).toBeInTheDocument();
      });
    });

    it('debe renderizar UnauthorizedPage en /unauthorized', async () => {
      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/unauthorized'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Acceso Denegado/i)).toBeInTheDocument();
      });
    });
  });

  describe('Redirect raíz', () => {
    it('debe redirigir / a /dashboard cuando está autenticado', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAdmin,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Dashboard/i })).toBeInTheDocument();
      });
    });
  });

  describe('Rutas protegidas - Autenticación básica', () => {
    it('debe permitir acceso a /dashboard cuando está autenticado', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserEmpresa,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/dashboard'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Dashboard/i })).toBeInTheDocument();
        expect(screen.getByText(/Bienvenido, Empresa Test/i)).toBeInTheDocument();
      });
    });

    it('debe redirigir a /login cuando NO está autenticado', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: false,
        user: null,
        accessToken: null,
        refreshToken: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/dashboard'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Iniciar Sesión/i)).toBeInTheDocument();
      });
    });
  });

  describe('RBAC - Control de acceso por roles', () => {
    it('ADMIN debe acceder a /usuarios', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAdmin,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/usuarios'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Módulo Usuarios/i)).toBeInTheDocument();
      });
    });

    it('AUDITOR debe ser bloqueado de /usuarios', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAuditor,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/usuarios'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Acceso Denegado/i)).toBeInTheDocument();
      });
    });

    it('ADMIN y AUDITOR deben acceder a /incapacidades/pendientes', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAuditor,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/incapacidades/pendientes'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Pendientes de Auditoría/i)).toBeInTheDocument();
      });
    });

    it('EMPRESA debe ser bloqueado de /incapacidades/pendientes', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserEmpresa,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/incapacidades/pendientes'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Acceso Denegado/i)).toBeInTheDocument();
      });
    });
  });

  describe('404 - Rutas no encontradas', () => {
    it('debe renderizar NotFoundPage para rutas no existentes', async () => {
      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/ruta-que-no-existe'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Página No Encontrada/i)).toBeInTheDocument();
      });
    });
  });

  describe('Rutas específicas por rol', () => {
    it('ADMIN debe acceder a /empresas', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAdmin,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/empresas'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Módulo Empresas/i)).toBeInTheDocument();
      });
    });

    it('ADMIN debe acceder a /afiliados', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAdmin,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/afiliados'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Módulo Afiliados/i)).toBeInTheDocument();
      });
    });

    it('ADMIN debe acceder a /configuracion', async () => {
      vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
        isAuthenticated: true,
        user: mockUserAdmin,
        accessToken: 'token123',
        refreshToken: 'refresh123',
        login: vi.fn(),
        logout: vi.fn(),
        refreshAccessToken: vi.fn(),
      });

      const testRouter = createMemoryRouter(router.routes, {
        initialEntries: ['/configuracion'],
      });

      render(<RouterProvider router={testRouter} />);

      await waitFor(() => {
        expect(screen.getByText(/Módulo Configuración/i)).toBeInTheDocument();
      });
    });
  });
});
