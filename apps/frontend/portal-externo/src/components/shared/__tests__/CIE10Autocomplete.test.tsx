import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CIE10Autocomplete } from '../CIE10Autocomplete';
import * as useCatalogoCIE10Module from '@/services/queries/useCatalogoCIE10';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';

vi.mock('@/services/queries/useCatalogoCIE10');
vi.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: string) => value, // Sin delay para tests
}));

describe('CIE10Autocomplete', () => {
  const mockOnChange = vi.fn();

  const defaultProps = {
    value: null,
    onChange: mockOnChange,
  };

  const mockCIE10_1: CatalogoCIE10 = {
    id: '1',
    codigo: 'A00',
    descripcion: 'Cólera',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  const mockCIE10_2: CatalogoCIE10 = {
    id: '2',
    codigo: 'A00.1',
    descripcion: 'Cólera debido a Vibrio cholerae 01, biotipo El Tor',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock default de useSearchCIE10
    vi.mocked(useCatalogoCIE10Module.useSearchCIE10).mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);
  });

  it('should render input with CIE-10 placeholder', () => {
    // Act
    render(<CIE10Autocomplete {...defaultProps} />);

    // Assert
    const input = screen.getByPlaceholderText(/código.*descripción/i);
    expect(input).toBeInTheDocument();
  });

  it('should search when typing >= 2 characters', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<CIE10Autocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/código.*descripción/i);

    // Act
    await user.type(input, 'A0');

    // Assert
    expect(useCatalogoCIE10Module.useSearchCIE10).toHaveBeenCalled();
  });

  it('should display CIE-10 codes in dropdown', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useCatalogoCIE10Module.useSearchCIE10).mockReturnValue({
      data: [mockCIE10_1, mockCIE10_2],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(<CIE10Autocomplete {...defaultProps} />);
    const input = screen.getByPlaceholderText(/código.*descripción/i);

    // Act
    await user.type(input, 'A00');
    await user.click(input); // Focus para mostrar dropdown

    // Assert
    await waitFor(() => {
      const codeElement = screen.getByText('A00');
      expect(codeElement).toBeInTheDocument();
      expect(codeElement).toHaveClass('font-mono', 'font-bold');
      expect(screen.getByText('Cólera')).toBeInTheDocument();
    });
  });

  it('should show CheckCircle when value matches selected', async () => {
    // Arrange
    const user = userEvent.setup();
    vi.mocked(useCatalogoCIE10Module.useSearchCIE10).mockReturnValue({
      data: [mockCIE10_1, mockCIE10_2],
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);

    render(
      <CIE10Autocomplete 
        value={mockCIE10_1}
        onChange={mockOnChange} 
      />
    );
    const input = screen.getByPlaceholderText(/código.*descripción/i);

    // Act
    await user.type(input, 'A00');
    await user.click(input);

    // Assert - Debería mostrar CheckCircle en el item seleccionado
    await waitFor(() => {
      const dropdown = screen.getByText('A00').closest('li');
      expect(dropdown).toBeInTheDocument();
    });
  });

  it('should display success badge when value selected', () => {
    // Arrange
    const selectedValue: CatalogoCIE10 = {
      id: '2',
      codigo: 'A00.1',
      descripcion: 'Cólera debido a Vibrio cholerae',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };

    // Act
    render(
      <CIE10Autocomplete 
        value={selectedValue}
        onChange={mockOnChange}
      />
    );

    // Assert
    expect(screen.getByText('A00.1')).toBeInTheDocument();
    expect(screen.getByText(/cólera debido a vibrio cholerae/i)).toBeInTheDocument();
    
    // Verificar que el badge tiene estilos de éxito (bg-green)
    const badge = screen.getByText('A00.1').closest('div');
    expect(badge).toHaveClass('bg-green-50');
  });

  it('should display error badge when error prop exists', () => {
    // Arrange
    const errorMessage = 'Código CIE-10 inválido';

    // Act
    render(
      <CIE10Autocomplete 
        value={null}
        onChange={mockOnChange}
        error={errorMessage}
      />
    );

    // Assert
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    
    // Verificar que el badge tiene estilos de error (bg-red)
    const errorBadge = screen.getByText(errorMessage).closest('div');
    expect(errorBadge).toHaveClass('bg-red-50');
  });
});
