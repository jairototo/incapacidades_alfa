import { describe, test, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TipoIncapacidadSelector } from '../TipoIncapacidadSelector';

describe('TipoIncapacidadSelector', () => {
  test('debe renderizar opciones ARL y SALUD', () => {
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Verificar que se muestran ambas opciones
    expect(screen.getByText('ARL - Riesgos Laborales')).toBeInTheDocument();
    expect(screen.getByText('SALUD - Enfermedad General')).toBeInTheDocument();
  });

  test('debe renderizar título y descripción', () => {
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    expect(screen.getByText('Seleccione el tipo de incapacidad')).toBeInTheDocument();
    expect(screen.getByText('Escoja el tipo de incapacidad que desea radicar')).toBeInTheDocument();
  });

  test('debe permitir seleccionar una opción', async () => {
    const user = userEvent.setup();
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Buscar y hacer click en la card de ARL
    const arlCard = screen.getByText('ARL - Riesgos Laborales').closest('div[class*="cursor-pointer"]');
    expect(arlCard).toBeInTheDocument();
    
    if (arlCard) {
      await user.click(arlCard);
      
      // Verificar que aparece el texto "Tipo seleccionado"
      await waitFor(() => {
        expect(screen.getByText('Tipo seleccionado')).toBeInTheDocument();
      });
    }
  });

  test('debe mostrar checkmark al seleccionar una opción', async () => {
    const user = userEvent.setup();
    const mockOnContinue = vi.fn();
    const { container } = render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Seleccionar SALUD
    const saludCard = screen.getByText('SALUD - Enfermedad General').closest('div[class*="cursor-pointer"]');
    
    if (saludCard) {
      await user.click(saludCard);
      
      // Verificar que aparece un checkmark
      await waitFor(() => {
        const checkIcons = container.querySelectorAll('svg');
        expect(checkIcons.length).toBeGreaterThan(0);
      });
    }
  });

  test('debe deshabilitar botón Continuar inicialmente', () => {
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    const continueButton = screen.getByRole('button', { name: /continuar/i });
    expect(continueButton).toBeDisabled();
  });

  test('debe habilitar botón Continuar al seleccionar un tipo', async () => {
    const user = userEvent.setup();
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Seleccionar ARL
    const arlCard = screen.getByText('ARL - Riesgos Laborales').closest('div[class*="cursor-pointer"]');
    
    if (arlCard) {
      await user.click(arlCard);
      
      // Verificar que el botón se habilita
      await waitFor(() => {
        const continueButton = screen.getByRole('button', { name: /continuar/i });
        expect(continueButton).not.toBeDisabled();
      });
    }
  });

  test('debe llamar onContinue con el tipo correcto al hacer submit', async () => {
    const user = userEvent.setup();
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Seleccionar SALUD
    const saludCard = screen.getByText('SALUD - Enfermedad General').closest('div[class*="cursor-pointer"]');
    
    if (saludCard) {
      await user.click(saludCard);
      
      // Click en botón Continuar
      const continueButton = screen.getByRole('button', { name: /continuar/i });
      await waitFor(() => expect(continueButton).not.toBeDisabled());
      
      await user.click(continueButton);
      
      // Verificar que se llamó con el tipo correcto
      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledWith('SALUD');
      });
    }
  });

  test('debe cambiar la selección si se hace click en otra opción', async () => {
    const user = userEvent.setup();
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    // Seleccionar ARL
    const arlCard = screen.getByText('ARL - Riesgos Laborales').closest('div[class*="cursor-pointer"]');
    if (arlCard) {
      await user.click(arlCard);
      await waitFor(() => {
        expect(screen.getByText('Tipo seleccionado')).toBeInTheDocument();
      });
    }
    
    // Cambiar a SALUD
    const saludCard = screen.getByText('SALUD - Enfermedad General').closest('div[class*="cursor-pointer"]');
    if (saludCard) {
      await user.click(saludCard);
      
      // Submit con SALUD
      const continueButton = screen.getByRole('button', { name: /continuar/i });
      await user.click(continueButton);
      
      await waitFor(() => {
        expect(mockOnContinue).toHaveBeenCalledWith('SALUD');
      });
    }
  });

  test('debe mostrar descripciones de cada tipo de incapacidad', () => {
    const mockOnContinue = vi.fn();
    render(<TipoIncapacidadSelector onContinue={mockOnContinue} />);
    
    expect(screen.getByText('Accidentes de trabajo o enfermedades laborales')).toBeInTheDocument();
    expect(screen.getByText('Incapacidades por enfermedad general o maternidad')).toBeInTheDocument();
  });
});
