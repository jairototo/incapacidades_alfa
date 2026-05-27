import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Textarea } from '../Textarea';

describe('Textarea', () => {
  it('debe renderizar correctamente con label', () => {
    render(<Textarea label="Descripción" />);
    
    expect(screen.getByText('Descripción')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('debe mostrar asterisco cuando es requerido', () => {
    render(<Textarea label="Campo requerido" required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('debe mostrar contador de caracteres cuando showCount y maxCount están establecidos', () => {
    render(<Textarea showCount maxCount={100} />);
    
    expect(screen.getByText('0/100')).toBeInTheDocument();
  });

  it('debe actualizar el contador al escribir', async () => {
    const user = userEvent.setup();
    render(<Textarea showCount maxCount={100} />);
    
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Hola mundo');
    
    expect(screen.getByText('10/100')).toBeInTheDocument();
  });

  it('debe cambiar color del contador cuando se excede el máximo', async () => {
    const user = userEvent.setup();
    render(<Textarea showCount maxCount={10} />);
    
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Esto tiene más de 10 caracteres');
    
    const counter = screen.getByText(/\/10/);
    expect(counter).toHaveClass('text-red-600');
  });

  it('debe mostrar mensaje de error', () => {
    render(<Textarea error="Este campo es requerido" />);
    
    expect(screen.getByText('Este campo es requerido')).toBeInTheDocument();
  });

  it('debe mostrar helperText cuando no hay error', () => {
    render(<Textarea helperText="Máximo 500 caracteres" />);
    
    expect(screen.getByText('Máximo 500 caracteres')).toBeInTheDocument();
  });

  it('debe priorizar error sobre helperText', () => {
    render(
      <Textarea 
        error="Error de validación" 
        helperText="Texto de ayuda"
      />
    );
    
    expect(screen.getByText('Error de validación')).toBeInTheDocument();
    expect(screen.queryByText('Texto de ayuda')).not.toBeInTheDocument();
  });

  it('debe aplicar clase de error cuando hay error', () => {
    render(<Textarea error="Error" />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('border-red-500');
  });

  it('debe llamar onChange cuando se escribe', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<Textarea onChange={handleChange} />);
    
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Test');
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('debe estar deshabilitado cuando disabled está establecido', () => {
    render(<Textarea disabled />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeDisabled();
  });

  it('debe permitir establecer número de filas', () => {
    render(<Textarea rows={10} />);
    
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '10');
  });

  it('debe aceptar placeholder', () => {
    render(<Textarea placeholder="Ingrese su descripción aquí..." />);
    
    expect(screen.getByPlaceholderText('Ingrese su descripción aquí...')).toBeInTheDocument();
  });
});
