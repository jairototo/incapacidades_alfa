import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from '../LoginForm';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';

// Mock authService
vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
  },
}));

// Mock authStore
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    login: vi.fn(),
  })),
}));

describe('LoginForm', () => {
  const mockOnSuccess = vi.fn();
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset authStore mock
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      login: mockLogin,
    });
  });

  describe('Renderizado inicial', () => {
    it('debe renderizar el formulario con todos los campos', () => {
      render(<LoginForm />);

      expect(screen.getByPlaceholderText('usuario@ejemplo.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument();
    });

    it('debe mostrar el link "¿Olvidaste tu contraseña?"', () => {
      render(<LoginForm />);

      expect(screen.getByText(/¿olvidaste tu contraseña\?/i)).toBeInTheDocument();
    });

    it('debe tener los campos con atributos de accesibilidad', () => {
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      const passwordInput = screen.getByPlaceholderText('••••••••');

      expect(usernameInput).toHaveAttribute('type', 'email');
      expect(usernameInput).toHaveAttribute('autoComplete', 'username');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('autoComplete', 'current-password');
    });

    it('debe marcar los campos como requeridos visualmente', () => {
      render(<LoginForm />);

      const requiredMarkers = screen.getAllByLabelText('requerido');
      expect(requiredMarkers).toHaveLength(2);
    });
  });

  describe('Validación de campos', () => {
    it('debe mostrar error cuando el usuario está vacío al hacer blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.click(usernameInput);
      await user.tab(); // Perder foco

      await waitFor(() => {
        expect(screen.getByText(/el usuario es requerido/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando la contraseña está vacía al hacer blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const passwordInput = screen.getByPlaceholderText('••••••••');
      
      await user.click(passwordInput);
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/la contraseña es requerida/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando el usuario tiene menos de 3 caracteres', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.type(usernameInput, 'ab');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/el usuario debe tener al menos 3 caracteres/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando el email no es válido', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.type(usernameInput, 'invalidemail');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/debe ser un email válido/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando la contraseña tiene menos de 6 caracteres', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const passwordInput = screen.getByPlaceholderText('••••••••');
      
      await user.type(passwordInput, '12345');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/la contraseña debe tener al menos 6 caracteres/i)).toBeInTheDocument();
      });
    });
  });

  describe('Toggle show/hide password', () => {
    it('debe cambiar el tipo de input al hacer clic en el botón de mostrar contraseña', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const passwordInput = screen.getByPlaceholderText('••••••••') as HTMLInputElement;
      const toggleButton = screen.getByLabelText(/mostrar contraseña/i);

      expect(passwordInput.type).toBe('password');

      await user.click(toggleButton);

      await waitFor(() => {
        expect(passwordInput.type).toBe('text');
      });
    });

    it('debe cambiar el aria-label del botón al toggle', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const toggleButton = screen.getByLabelText(/mostrar contraseña/i);

      await user.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/ocultar contraseña/i)).toBeInTheDocument();
      });
    });
  });

  describe('Autenticación exitosa', () => {
    it('debe llamar a authService.login con los datos del formulario', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: '123',
          email: 'test@example.com',
          nombres: 'Test',
          apellidos: 'User',
          rol: 'AUDITOR',
          estado: 'ACTIVO',
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      render(<LoginForm onSuccess={mockOnSuccess} />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith({
          username: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('debe guardar tokens en authStore después de login exitoso', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: '123',
          email: 'test@example.com',
          nombres: 'Test',
          apellidos: 'User',
          rol: 'AUDITOR',
          estado: 'ACTIVO',
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith(
          {
            access_token: 'mock-access-token',
            refresh_token: 'mock-refresh-token',
          },
          mockResponse.user
        );
      });
    });

    it('debe ejecutar el callback onSuccess después de login exitoso', async () => {
      const user = userEvent.setup();
      const mockResponse = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: '123',
          email: 'test@example.com',
          nombres: 'Test',
          apellidos: 'User',
          rol: 'AUDITOR',
          estado: 'ACTIVO',
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockResponse);

      render(<LoginForm onSuccess={mockOnSuccess} />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Loading state', () => {
    it('debe mostrar spinner y cambiar texto del botón durante autenticación', async () => {
      const user = userEvent.setup();
      
      // Mock que nunca se resuelve para mantener el loading state
      (authService.login as ReturnType<typeof vi.fn>).mockImplementationOnce(
        () => new Promise(() => {}) // Promise que nunca se resuelve
      );

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/iniciando sesión\.\.\./i)).toBeInTheDocument();
      });
    });

    it('debe deshabilitar el botón submit durante autenticación', async () => {
      const user = userEvent.setup();
      
      (authService.login as ReturnType<typeof vi.fn>).mockImplementationOnce(
        () => new Promise(() => {})
      );

      render(<LoginForm />);

      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i });

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('debe deshabilitar los inputs durante autenticación', async () => {
      const user = userEvent.setup();
      
      (authService.login as ReturnType<typeof vi.fn>).mockImplementationOnce(
        () => new Promise(() => {})
      );

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByPlaceholderText('usuario@ejemplo.com')).toBeDisabled();
        expect(screen.getByPlaceholderText('••••••••')).toBeDisabled();
      });
    });
  });

  describe('Manejo de errores', () => {
    it('debe mostrar error cuando las credenciales son inválidas (401)', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'wrong@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'wrongpass');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/usuario o contraseña incorrectos/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando la cuenta está bloqueada (403)', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          status: 403,
          data: { detail: 'Account blocked' },
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'blocked@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/tu cuenta ha sido bloqueada/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando hay un error de red', async () => {
      const user = userEvent.setup();
      const error = {
        code: 'ERR_NETWORK',
        message: 'Network Error',
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/no se pudo conectar al servidor/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error cuando el usuario está inactivo', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          status: 403,
          data: { detail: 'Usuario inactivo' },
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'inactive@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/tu cuenta está inactiva/i)).toBeInTheDocument();
      });
    });

    it('debe mostrar error genérico para errores del servidor (500)', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal Server Error' },
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'test@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'password123');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/error del servidor/i)).toBeInTheDocument();
      });
    });

    it('NO debe ejecutar onSuccess cuando hay error', async () => {
      const user = userEvent.setup();
      const error = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      (authService.login as ReturnType<typeof vi.fn>).mockRejectedValueOnce(error);

      render(<LoginForm onSuccess={mockOnSuccess} />);

      await user.type(screen.getByPlaceholderText('usuario@ejemplo.com'), 'wrong@example.com');
      await user.type(screen.getByPlaceholderText('••••••••'), 'wrongpass');
      await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

      await waitFor(() => {
        expect(screen.getByText(/usuario o contraseña incorrectos/i)).toBeInTheDocument();
      });

      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  describe('Accesibilidad (ARIA)', () => {
    it('debe tener aria-invalid en inputs con errores', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.click(usernameInput);
      await user.tab();

      await waitFor(() => {
        expect(usernameInput).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('debe tener aria-describedby apuntando al mensaje de error', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.click(usernameInput);
      await user.tab();

      await waitFor(() => {
        expect(usernameInput).toHaveAttribute('aria-describedby', 'username-error');
      });
    });

    it('debe tener role="alert" en mensajes de error', async () => {
      const user = userEvent.setup();
      render(<LoginForm />);

      const usernameInput = screen.getByPlaceholderText('usuario@ejemplo.com');
      
      await user.click(usernameInput);
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.getByRole('alert');
        expect(errorMessage).toHaveTextContent(/el usuario es requerido/i);
      });
    });
  });
});
