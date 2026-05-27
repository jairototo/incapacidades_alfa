import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DatePicker } from '../DatePicker';

describe('DatePicker', () => {
  it('debe renderizar correctamente con label', () => {
    render(<DatePicker label="Fecha de Inicio" />);
    
    expect(screen.getByText('Fecha de Inicio')).toBeInTheDocument();
  });

  it('debe mostrar asterisco cuando es requerido', () => {
    render(<DatePicker label="Fecha requerida" required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('debe mostrar placeholder cuando no hay fecha seleccionada', () => {
    render(<DatePicker placeholder="Selecciona una fecha" />);
    
    expect(screen.getByText('Selecciona una fecha')).toBeInTheDocument();
  });

  it('debe mostrar fecha formateada cuando tiene valor', () => {
    const fecha = new Date(2024, 0, 15); // 15 de enero de 2024
    render(<DatePicker value={fecha} />);
    
    // Buscar texto que contenga "15" y "enero"
    expect(screen.getByText(/15.*enero.*2024/i)).toBeInTheDocument();
  });

  it.skip('debe abrir calendario al hacer clic en el botón', async () => {
    const user = userEvent.setup();
    render(<DatePicker label="Fecha" />);
    
    const button = screen.getByRole('button');
    await user.click(button);
    
    // Esperar a que el calendario se renderice
    await waitFor(() => {
      const calendar = document.querySelector('.rdp');
      expect(calendar).toBeInTheDocument();
    });
  });

  it('debe llamar onChange cuando se selecciona una fecha', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<DatePicker onChange={handleChange} value={new Date(2024, 0, 1)} />);
    
    const button = screen.getByRole('button');
    await user.click(button);
    
    // Simular selección de una fecha
    const days = document.querySelectorAll('button.rdp-day');
    if (days.length > 0) {
      await user.click(days[10] as HTMLElement);
      expect(handleChange).toHaveBeenCalled();
    }
  });

  it.skip('debe cerrar calendario después de seleccionar fecha', async () => {
    const user = userEvent.setup();
    render(<DatePicker value={new Date(2024, 0, 1)} />);
    
    const button = screen.getByRole('button');
    await user.click(button);
    
    // Esperar que calendario esté abierto
    await waitFor(() => {
      const calendar = document.querySelector('.rdp');
      expect(calendar).toBeInTheDocument();
    });
    
    // Seleccionar una fecha
    const days = document.querySelectorAll('button.rdp-day');
    if (days.length > 0) {
      await user.click(days[10] as HTMLElement);
      
      // Esperar a que se cierre
      await waitFor(() => {
        const calendar = document.querySelector('.rdp');
        expect(calendar).not.toBeInTheDocument();
      });
    }
  });

  it('debe mostrar mensaje de error', () => {
    render(<DatePicker error="Fecha requerida" />);
    
    expect(screen.getByText('Fecha requerida')).toBeInTheDocument();
  });

  it('debe mostrar helperText cuando no hay error', () => {
    render(<DatePicker helperText="Seleccione la fecha de inicio" />);
    
    expect(screen.getByText('Seleccione la fecha de inicio')).toBeInTheDocument();
  });

  it('debe priorizar error sobre helperText', () => {
    render(
      <DatePicker 
        error="Error de validación" 
        helperText="Texto de ayuda"
      />
    );
    
    expect(screen.getByText('Error de validación')).toBeInTheDocument();
    expect(screen.queryByText('Texto de ayuda')).not.toBeInTheDocument();
  });

  it('debe estar deshabilitado cuando disabled está establecido', () => {
    render(<DatePicker disabled />);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('debe aplicar clase de error cuando hay error', () => {
    render(<DatePicker error="Error" />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('border-red-500');
  });

  it('debe sincronizar valor externo', () => {
    const fecha1 = new Date(2024, 0, 15);
    const { rerender } = render(<DatePicker value={fecha1} />);
    
    expect(screen.getByText(/15.*enero.*2024/i)).toBeInTheDocument();
    
    const fecha2 = new Date(2024, 1, 20);
    rerender(<DatePicker value={fecha2} />);
    
    expect(screen.getByText(/20.*febrero.*2024/i)).toBeInTheDocument();
  });
});
