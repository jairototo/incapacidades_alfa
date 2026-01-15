import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Select } from '../../ui/Select';

describe('Select', () => {
  test('debe renderizar correctamente', () => {
    render(
      <Select>
        <option value="1">Opción 1</option>
        <option value="2">Opción 2</option>
      </Select>
    );

    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  test('debe mostrar label si se proporciona', () => {
    render(
      <Select label="Mi Select">
        <option value="1">Opción 1</option>
      </Select>
    );

    expect(screen.getByText('Mi Select')).toBeInTheDocument();
  });

  test('debe mostrar indicador de required con asterisco', () => {
    render(
      <Select label="Campo Requerido" required>
        <option value="1">Opción 1</option>
      </Select>
    );

    expect(screen.getByText('*')).toBeInTheDocument();
  });

  test('debe mostrar mensaje de error', () => {
    const errorMessage = 'Este campo es requerido';
    render(
      <Select error={errorMessage}>
        <option value="1">Opción 1</option>
      </Select>
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('debe mostrar helper text si no hay error', () => {
    const helperText = 'Texto de ayuda';
    render(
      <Select helperText={helperText}>
        <option value="1">Opción 1</option>
      </Select>
    );

    expect(screen.getByText(helperText)).toBeInTheDocument();
  });

  test('debe permitir seleccionar una opción', async () => {
    const user = userEvent.setup();
    render(
      <Select>
        <option value="">Seleccione...</option>
        <option value="1">Opción 1</option>
        <option value="2">Opción 2</option>
      </Select>
    );

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '2');

    expect(select).toHaveValue('2');
  });

  test('debe estar deshabilitado si disabled es true', () => {
    render(
      <Select disabled>
        <option value="1">Opción 1</option>
      </Select>
    );

    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  test('debe aplicar className personalizado', () => {
    const { container } = render(
      <Select className="custom-class">
        <option value="1">Opción 1</option>
      </Select>
    );

    const select = container.querySelector('select');
    expect(select).toHaveClass('custom-class');
  });
});
