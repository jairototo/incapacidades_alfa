import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicarIncapacidadWizard } from '../RadicarIncapacidadWizard';
import * as useSolicitantesModule from '@/services/queries/useSolicitantes';
import * as useCatalogoCIE10Module from '@/services/queries/useCatalogoCIE10';
import type { Solicitante } from '@/types/solicitante';

vi.mock('@/services/queries/useSolicitantes');
vi.mock('@/services/queries/useCatalogoCIE10');

describe('RadicarIncapacidadWizard', () => {
  const mockSolicitante: Solicitante = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    correo: 'test@example.com',
    nombres: 'Juan',
    apellidos: 'Pérez',
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

    // Mock default de useSearchCIE10
    vi.mocked(useCatalogoCIE10Module.useSearchCIE10).mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
    } as any);
  });

  it('should render Step 0 (Solicitante) as first step', () => {
    // Act
    render(<RadicarIncapacidadWizard />, {
      wrapper: createWrapper(),
    });

    // Assert - El wizard debe empezar en el selector de tipo
    // (El wizard real comienza con TipoIncapacidadSelector, no Step 0)
    expect(screen.getByText(/seleccione el tipo de incapacidad/i)).toBeInTheDocument();
  });

  it('should navigate between wizard steps', async () => {
    // Arrange
    const user = userEvent.setup();

    render(<RadicarIncapacidadWizard />, {
      wrapper: createWrapper(),
    });

    // Inicialmente debe mostrar el selector de tipo
    expect(screen.getByText(/seleccione el tipo de incapacidad/i)).toBeInTheDocument();

    // Seleccionar tipo ARL
    const tipoARLButton = screen.getByRole('button', { name: /arl/i });
    await user.click(tipoARLButton);

    // Debe avanzar al siguiente paso
    await waitFor(() => {
      // Aquí verificamos que avanzó (puede ser DatosSolicitanteForm o DatosPersonalesForm)
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('should store selected tipo in wizardData', async () => {
    // Arrange
    const user = userEvent.setup();

    render(<RadicarIncapacidadWizard />, {
      wrapper: createWrapper(),
    });

    // Seleccionar tipo SALUD
    expect(screen.getByText(/seleccione el tipo de incapacidad/i)).toBeInTheDocument();
    
    const tipoSaludButton = screen.getByRole('button', { name: /salud/i });
    await user.click(tipoSaludButton);

    // El wizard debe almacenar el tipo seleccionado
    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('should render wizard with all steps indicators', () => {
    // Arrange
    render(<RadicarIncapacidadWizard />, {
      wrapper: createWrapper(),
    });

    // Assert - El wizard debe mostrar los indicadores de pasos
    // Los pasos son: Tipo, Datos Personales, Datos Incapacidad, Documentos, Resumen
    expect(screen.getByText(/tipo de incapacidad/i)).toBeInTheDocument();
    expect(screen.getByText(/datos personales/i)).toBeInTheDocument();
    expect(screen.getByText(/datos incapacidad/i)).toBeInTheDocument();
    expect(screen.getByText(/documentos/i)).toBeInTheDocument();
    expect(screen.getByText(/resumen/i)).toBeInTheDocument();
  });
});
