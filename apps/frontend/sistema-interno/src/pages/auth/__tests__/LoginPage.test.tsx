import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../LoginPage';
import { useAuthStore } from '@/store/authStore';
import type { User } from '@/types/auth';

// Mock del store de autenticación
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

// Mock del LoginForm component
vi.mock('@/components/auth/LoginForm', () => ({
  LoginForm: ({ onSuccess }: { onSuccess?: () => void }) => (
    <div data-testid="mock-login-form">
      <button onClick={onSuccess}>Mock Login Form</button>
    </div>
  ),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLoginPage = () => {
    return render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );
  };

  describe('Renderizado inicial', () => {
    it('debe renderizar el logo', () => {
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

      renderLoginPage();

      const logo = screen.getByLabelText('Logo Sistema Interno');
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveTextContent('SI');
    });

    it('debe renderizar el título del sistema', () => {
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

      renderLoginPage();

      expect(screen.getByText('Sistema Interno de Incapacidades')).toBeInTheDocument();
    });

    it('debe renderizar la descripción', () => {
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

      renderLoginPage();

      expect(screen.getByText('Ingrese sus credenciales para acceder')).toBeInTheDocument();
    });

    it('debe renderizar el componente LoginForm', () => {
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

      renderLoginPage();

      expect(screen.getByTestId('mock-login-form')).toBeInTheDocument();
    });

    it('debe renderizar el footer con copyright', () => {
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

      renderLoginPage();

      const currentYear = new Date().getFullYear();
      expect(screen.getByText(`© ${currentYear} Sistema de Incapacidades`)).toBeInTheDocument();
      expect(screen.getByText('Todos los derechos reservados')).toBeInTheDocument();
    });
  });

  describe('Auto-redirect cuando ya está autenticado', () => {
    it('debe redirigir a /dashboard para rol ADMIN', async () => {
      const mockUser: User = {
        id: '123',
        username: 'admin@test.com',
        email: 'admin@test.com',
        nombres: 'Admin',
        apellidos: 'Test',
        rol: 'ADMIN' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
      });
    });

    it('debe redirigir a /dashboard para rol AUDITOR', async () => {
      const mockUser: User = {
        id: '123',
        username: 'auditor@test.com',
        email: 'auditor@test.com',
        nombres: 'Auditor',
        apellidos: 'Test',
        rol: 'AUDITOR' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
      });
    });

    it('debe redirigir a /ordenes-pago para rol APROBADOR', async () => {
      const mockUser: User = {
        id: '123',
        username: 'aprobador@test.com',
        email: 'aprobador@test.com',
        nombres: 'Aprobador',
        apellidos: 'Test',
        rol: 'APROBADOR' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/ordenes-pago', { replace: true });
      });
    });

    it('debe redirigir a /incapacidades/consulta para rol EMPRESA', async () => {
      const mockUser: User = {
        id: '123',
        username: 'empresa@test.com',
        email: 'empresa@test.com',
        nombres: 'Empresa',
        apellidos: 'Test',
        rol: 'EMPRESA' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/incapacidades/consulta', { replace: true });
      });
    });

    it('debe redirigir a /incapacidades/mis-incapacidades para rol EMPLEADO', async () => {
      const mockUser: User = {
        id: '123',
        username: 'empleado@test.com',
        email: 'empleado@test.com',
        nombres: 'Empleado',
        apellidos: 'Test',
        rol: 'EMPLEADO' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/incapacidades/mis-incapacidades', { replace: true });
      });
    });

    it('debe redirigir a /dashboard para rol desconocido (default)', async () => {
      const mockUser: User = {
        id: '123',
        username: 'unknown@test.com',
        email: 'unknown@test.com',
        nombres: 'Unknown',
        apellidos: 'Test',
        rol: 'UNKNOWN_ROLE' as any,
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

      renderLoginPage();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
      });
    });

    it('NO debe redirigir si no está autenticado', () => {
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

      renderLoginPage();

      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Estilos y diseño', () => {
    it('debe tener un gradiente de fondo (from-slate-50 to-slate-100)', () => {
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

      const { container } = renderLoginPage();

      const mainDiv = container.querySelector('.bg-gradient-to-br');
      expect(mainDiv).toBeInTheDocument();
      expect(mainDiv).toHaveClass('from-slate-50', 'to-slate-100');
    });

    it('debe estar centrado vertical y horizontalmente', () => {
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

      const { container } = renderLoginPage();

      const mainDiv = container.querySelector('.min-h-screen');
      expect(mainDiv).toHaveClass('flex', 'items-center', 'justify-center');
    });

    it('debe tener un Card con max-width-md', () => {
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

      const { container } = renderLoginPage();

      // El Card debe tener clase max-w-md
      const card = container.querySelector('.max-w-md');
      expect(card).toBeInTheDocument();
    });
  });
});
