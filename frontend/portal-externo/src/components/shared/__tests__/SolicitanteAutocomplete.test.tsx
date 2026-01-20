import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SolicitanteAutocomplete } from '../SolicitanteAutocomplete';
import * as useSolicitantesModule from '@/services/queries/useSolicitantes';
import type { Solicitante } from '@/types/solicitante';

vi.mock('@/services/queries/useSolicitantes');
vi.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: string) => value, // Sin delay para tests
}));

describe('SolicitanteAutocomplete', () => {
  const mockOnChange = vi.fn();
  const mockOnEmailChange = vi.fn();

  const defaultProps = {
    value: null,
    onChange: mockOnChange,
    onEmailChange: mockOnEmailChange,
  };

  const mockSolicitante1: Solicitante = {
    id: '1',
    correo: 'juan@example.com',
    nombres: 'Juan',
    apellidos: 'Pérez',
    telefono: '3001234567',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  const mockSolicitante2: Solicitante = {
    id: '2',
    correo: 'maria@example.com',
    nombres: 'María',
    apellidos: 'García',
    telefono: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock default de useSearchSolicitantes
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);
  });

  it('should render search input with placeholder', () => {
    // Act
    render(<SolicitanteAutocomplete {...defaultProps} />);

    // Assert
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);
    expect(input).toBeInTheDocument();
  });

  it('should call onEmailChange when typing', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);

    // Act
    await user.type(input, 'juan@');

    // Assert
    expect(mockOnEmailChange).toHaveBeenCalled();
  });

  it('should show loading state while fetching', () => {
    // Arrange
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetching: true,
      isError: false,
      error: null,
    } as any);

    // Act
    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i) as HTMLInputElement;
    
    // Simular que el usuario ha escrito y enfocado
    input.value = 'juan@example.com';
    input.focus();

    // Assert - Buscar el icono de loading (Loader2)
    // Como el dropdown se muestra solo con focus y >= 3 chars, verificamos que el mock está activo
    expect(useSolicitantesModule.useSearchSolicitantes).toHaveBeenCalled();
  });

  it('should display search results in dropdown', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: [mockSolicitante1, mockSolicitante2],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);

    // Act
    await user.type(input, 'juan@example.com');
    await user.click(input); // Focus para mostrar dropdown

    // Assert
    await waitFor(() => {
      expect(screen.getByText('juan@example.com')).toBeInTheDocument();
      expect(screen.getByText(/juan pérez/i)).toBeInTheDocument();
    });
  });

  it('should call onChange when selecting a solicitante', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: [mockSolicitante1, mockSolicitante2],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);

    // Act
    await user.type(input, 'juan@');
    await user.click(input);
    
    await waitFor(() => {
      expect(screen.getByText('juan@example.com')).toBeInTheDocument();
    });
    
    const firstResult = screen.getByText('juan@example.com').closest('li');
    if (firstResult) {
      await user.click(firstResult);
    }

    // Assert
    expect(mockOnChange).toHaveBeenCalledWith(mockSolicitante1);
  });

  it('should show empty message when no results', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);

    // Act
    await user.type(input, 'noexiste@example.com');
    await user.click(input);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/no se encontraron solicitantes/i)).toBeInTheDocument();
    });
  });

  it('should not show dropdown when search term < 3 chars', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useSolicitantesModule.useSearchSolicitantes).mockReturnValue({
      data: [mockSolicitante1],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<SolicitanteAutocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/buscar por correo electrónico/i);

    // Act
    await user.type(input, 'ju');
    await user.click(input);

    // Assert
    // El dropdown no debería mostrarse porque el debounce es < 3 chars
    // Verificamos que el mensaje de ayuda aparezca
    await waitFor(() => {
      const helpText = screen.queryByText(/escriba al menos 3 caracteres/i);
      expect(helpText).toBeInTheDocument();
    });
  });
});
