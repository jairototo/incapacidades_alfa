import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DatosSolicitanteForm } from '../DatosSolicitanteForm';
import * as useSolicitantesModule from '@/services/queries/useSolicitantes';
import type { Solicitante } from '@/types/solicitante';

vi.mock('@/services/queries/useSolicitantes');

describe('DatosSolicitanteForm', () => {
  const mockOnNext = vi.fn();
  const mockOnBack = vi.fn();

  const defaultProps = {
    onNext: mockOnNext,
    onBack: mockOnBack,
  };

  const mockSolicitante: Solicitante = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    correo: 'juan.perez@example.com',
    nombres: 'Juan',
    apellidos: 'Pérez García',
    telefono: '3001234567',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  const mockMutate = vi.fn();

  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock default de useCreateSolicitante
    vi.mocked(useSolicitantesModule.useCreateSolicitante).mockReturnValue({
      mutateAsync: mockMutate,
      isPending: false,
      isError: false,
      error: null,
    } as any);

    // Mock default de useSearchSolicitantes
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);
  });

  it('should render form with SolicitanteAutocomplete', () => {
    // Act
    const { container } = render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByPlaceholderText(/correo electrónico/i)).toBeInTheDocument();
    expect(container).toBeTruthy();
  });

  it('should show editable fields for new solicitante', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act - Ingresar correo que no existe
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    await user.type(emailInput, 'nuevo@example.com');

    // Assert - Badge "Nuevo solicitante"
    await waitFor(() => {
      expect(screen.getByText(/nuevo solicitante/i)).toBeInTheDocument();
    });

    // Campos editables
    expect(screen.getByLabelText(/nombres/i)).not.toBeDisabled();
    expect(screen.getByLabelText(/apellidos/i)).not.toBeDisabled();
    expect(screen.getByLabelText(/teléfono/i)).not.toBeDisabled();
  });

  it('should show readonly fields for existing solicitante', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: [mockSolicitante],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act - Buscar y seleccionar solicitante existente
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    await user.type(emailInput, 'juan.perez@example.com');
    
    await waitFor(() => {
      const dropdown = screen.getByText('Juan Pérez García');
      expect(dropdown).toBeInTheDocument();
    });

    const solicitanteOption = screen.getByText('Juan Pérez García');
    await user.click(solicitanteOption);

    // Assert - Badge "Solicitante registrado"
    await waitFor(() => {
      expect(screen.getByText(/solicitante registrado/i)).toBeInTheDocument();
    });

    // Campos readonly (disabled)
    expect(screen.getByLabelText(/nombres/i)).toBeDisabled();
    expect(screen.getByLabelText(/apellidos/i)).toBeDisabled();
    expect(screen.getByLabelText(/teléfono/i)).toBeDisabled();
  });

  it('should validate email format', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act - Ingresar email inválido y enviar formulario
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    await user.type(emailInput, 'correo-invalido');
    
    const submitButton = screen.getByRole('button', { name: /continuar/i });
    await user.click(submitButton);

    // Assert - Mensaje de error
    await waitFor(() => {
      expect(screen.getByText(/correo electrónico inválido/i)).toBeInTheDocument();
    });
  });

  it('should validate nombres field', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act - Ingresar correo válido
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    await user.type(emailInput, 'nuevo@example.com');

    // Ingresar nombre inválido (1 caracter)
    const nombresInput = screen.getByLabelText(/nombres/i);
    await user.type(nombresInput, 'A');

    const submitButton = screen.getByRole('button', { name: /continuar/i });
    await user.click(submitButton);

    // Assert - Mensaje de error (min 2 caracteres)
    await waitFor(() => {
      expect(screen.getByText(/mínimo 2 caracteres/i)).toBeInTheDocument();
    });
  });

  it('should create new solicitante on submit', async () => {
    // Arrange
    const user = userEvent.setup();
    mockMutate.mockResolvedValue(mockSolicitante);

    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act - Llenar formulario
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    await user.type(emailInput, 'nuevo@example.com');

    const nombresInput = screen.getByLabelText(/nombres/i);
    await user.type(nombresInput, 'Juan');

    const apellidosInput = screen.getByLabelText(/apellidos/i);
    await user.type(apellidosInput, 'Pérez');

    const telefonoInput = screen.getByLabelText(/teléfono/i);
    await user.type(telefonoInput, '3001234567');

    const submitButton = screen.getByRole('button', { name: /crear y continuar/i });
    await user.click(submitButton);

    // Assert - mutateAsync llamado con datos correctos
    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith({
        correo: 'nuevo@example.com',
        nombres: 'Juan',
        apellidos: 'Pérez',
        telefono: '3001234567',
      });
    });

    // onNext llamado con solicitante creado
    expect(mockOnNext).toHaveBeenCalledWith(mockSolicitante);
  });

  it('should show loading state during creation', async () => {
    // Arrange
    const user = userEvent.setup();
    const emailInput = screen.getByPlaceholderText(/correo electrónico/i);
    
    // Primero renderizar con pending = false para tener el formulario visible
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Ingresar correo para activar modo "nuevo solicitante"
    await user.type(emailInput, 'nuevo@example.com');

    // Luego actualizar el mock para simular loading
    vi.mocked(useSolicitantesModule.useCreateSolicitante).mockReturnValue({
      mutateAsync: mockMutate,
      isPending: true,
      isError: false,
      error: null,
    } as any);

    // Re-render con nuevo estado
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Assert - Botón disabled durante carga
    const buttons = screen.getAllByRole('button');
    const submitButton = buttons.find(btn => btn.textContent?.includes('Procesando') || btn.textContent?.includes('Creando'));
    expect(submitButton).toBeDisabled();
  });

  it('should call onBack when clicking Cancelar', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<DatosSolicitanteForm {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    // Act
    const backButton = screen.getByRole('button', { name: /cancelar/i });
    await user.click(backButton);

    // Assert
    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });
});
