import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { RadicarIncapacidadWizard } from '../RadicarIncapacidadWizard';

// Mock del servicio de pre-incapacidades
vi.mock('@/services/preIncapacidadService', () => ({
  crearPreIncapacidad: vi.fn(),
  subirTodosLosDocumentos: vi.fn(),
  formatDateForApi: vi.fn((d: Date) => d.toISOString().split('T')[0]),
}));

// Mock de useToast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

const renderWizard = () =>
  render(
    <MemoryRouter>
      <RadicarIncapacidadWizard />
    </MemoryRouter>
  );

describe('RadicarIncapacidadWizard (2 pasos — ARL)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar el Paso 1 como primer paso', () => {
    renderWizard();

    // El wizard debe mostrar el primer paso con los datos del solicitante
    expect(screen.getByText(/información del solicitante/i)).toBeInTheDocument();
  });

  it('debe mostrar el stepper con 2 pasos', () => {
    const { container } = renderWizard();

    // Verificar que hay 2 círculos de paso en el stepper
    const stepNumbers = container.querySelectorAll('.rounded-full');
    expect(stepNumbers.length).toBeGreaterThanOrEqual(2);
  });

  it('debe mostrar los labels del wizard (Datos del Solicitante)', () => {
    renderWizard();
    expect(screen.getAllByText(/datos del solicitante/i).length).toBeGreaterThanOrEqual(1);
  });

  it('debe mostrar el label del paso 2 en el stepper', () => {
    renderWizard();
    expect(screen.getAllByText(/incapacidad y documentos/i).length).toBeGreaterThanOrEqual(1);
  });

  it('debe mostrar sección Solicitante con campo correo', () => {
    renderWizard();
    expect(screen.getByPlaceholderText(/ejemplo@correo/i)).toBeInTheDocument();
  });

  it('debe mostrar sección Empresa como opcional', () => {
    renderWizard();
    // Texto que indica que empresa es opcional
    expect(screen.getByText(/si no aplica/i)).toBeInTheDocument();
  });

  it('debe mostrar sección Empleado con selector de tipo de documento', () => {
    renderWizard();
    expect(screen.getByText(/cédula de ciudadanía/i)).toBeInTheDocument();
  });
});
