import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CurrencyInput } from '../CurrencyInput';

describe('CurrencyInput', () => {
  it('debe renderizar correctamente con label', () => {
    render(<CurrencyInput label="Valor por Día" />);
    
    expect(screen.getByText('Valor por Día')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('debe mostrar asterisco cuando es requerido', () => {
    render(<CurrencyInput label="Campo requerido" required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('debe formatear valor como COP', () => {
    render(<CurrencyInput value={50000} />);
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input.value).toContain('50.000');
    expect(input.value).toContain('$');
  });

  it('debe formatear valores grandes correctamente', () => {
    render(<CurrencyInput value={1500000} />);
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input.value).toContain('1.500.000');
  });

  it('debe llamar onChange con valor numérico al escribir', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<CurrencyInput onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, '50000');
    
    expect(handleChange).toHaveBeenCalled();
    // El último call debe ser con 50000
    const lastCall = handleChange.mock.calls[handleChange.mock.calls.length - 1];
    expect(lastCall[0]).toBe(50000);
  });

  it('debe limpiar formato al hacer focus', async () => {
    const user = userEvent.setup();
    render(<CurrencyInput value={50000} />);
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input.value).toContain('$');
    
    await user.click(input);
    
    // Al hacer focus, debe mostrar solo el número
    expect(input.value).toBe('50000');
  });

  it('debe formatear al perder focus', async () => {
    const user = userEvent.setup();
    render(<CurrencyInput value={50000} />);
    
    const input = screen.getByRole('textbox');
    
    await user.click(input);
    await user.tab(); // Perder focus
    
    const inputElement = input as HTMLInputElement;
    expect(inputElement.value).toContain('$');
    expect(inputElement.value).toContain('50.000');
  });

  it('debe ignorar caracteres no numéricos', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<CurrencyInput onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'abc123xyz');
    
    // Debe haber llamado onChange solo con el valor numérico 123
    const lastCall = handleChange.mock.calls[handleChange.mock.calls.length - 1];
    expect(lastCall[0]).toBe(123);
  });

  it('debe manejar valor cero', () => {
    render(<CurrencyInput value={0} />);
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    // El formato COP puede variar ($ 0, $0, etc.)
    expect(input.value).toMatch(/\$\s*0/);
  });

  it('debe mostrar mensaje de error', () => {
    render(<CurrencyInput error="El valor es requerido" />);
    
    expect(screen.getByText('El valor es requerido')).toBeInTheDocument();
  });

  it('debe mostrar helperText cuando no hay error', () => {
    render(<CurrencyInput helperText="Ingrese el valor en pesos colombianos" />);
    
    expect(screen.getByText('Ingrese el valor en pesos colombianos')).toBeInTheDocument();
  });

  it('debe priorizar error sobre helperText', () => {
    render(
      <CurrencyInput 
        error="Error de validación" 
        helperText="Texto de ayuda"
      />
    );
    
    expect(screen.getByText('Error de validación')).toBeInTheDocument();
    expect(screen.queryByText('Texto de ayuda')).not.toBeInTheDocument();
  });

  it('debe aplicar clase de error cuando hay error', () => {
    render(<CurrencyInput error="Error" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });

  it('debe estar deshabilitado cuando disabled está establecido', () => {
    render(<CurrencyInput disabled />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('debe actualizar cuando cambia valor externo', () => {
    const { rerender } = render(<CurrencyInput value={50000} />);
    
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input.value).toContain('50.000');
    
    rerender(<CurrencyInput value={100000} />);
    
    expect(input.value).toContain('100.000');
  });

  it('debe manejar placeholder', () => {
    render(<CurrencyInput placeholder="$0" />);
    
    expect(screen.getByPlaceholderText('$0')).toBeInTheDocument();
  });
});
