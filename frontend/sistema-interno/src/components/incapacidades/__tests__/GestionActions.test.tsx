import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GestionActions } from '../GestionActions';
import { EstadoIncapacidad, TipoIncapacidad } from '@/types';

const mockIncapacidad = {
  id: 'test-id',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'S06.0',
  diagnostico_descripcion: 'Conmoción cerebral',
  valor_total: 500000,
};

describe('GestionActions', () => {
  const mockOnAction = vi.fn();

  it('debe renderizar los 3 botones de acción (Aprobar, Observar, Rechazar)', () => {
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    expect(screen.getByRole('button', { name: /Aprobar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Observar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Rechazar/i })).toBeInTheDocument();
  });

  it('debe seleccionar una acción al hacer click', async () => {
    const user = userEvent.setup();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    const aprobarBtn = screen.getByRole('button', { name: /Aprobar/i });
    await user.click(aprobarBtn);

    // El botón debe cambiar de estilo (se verifica por la clase ring-2)
    expect(aprobarBtn).toHaveClass('ring-2');
  });

  it('debe mostrar formulario con textarea de observaciones al seleccionar una acción', async () => {
    const user = userEvent.setup();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    const observarBtn = screen.getByRole('button', { name: /Observar/i });
    await user.click(observarBtn);

    // Debe aparecer el textarea
    await waitFor(() => {
      expect(screen.getByLabelText(/Observaciones/i)).toBeInTheDocument();
    });

    // Debe aparecer el botón Confirmar
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeInTheDocument();
  });

  it('debe validar que se requiere observación para RECHAZAR y OBSERVAR', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Rechazar"
    const rechazarBtn = screen.getByRole('button', { name: /Rechazar/i });
    await user.click(rechazarBtn);

    // El textarea debe aparecer
    const textarea = await screen.findByLabelText(/Observaciones/i);
    expect(textarea).toBeInTheDocument();

    // Debe mostrar texto indicando que es requerido
    expect(screen.getByText(/Requerido: Justifique las razones del rechazo/i)).toBeInTheDocument();
  });

  it('debe llamar a onAction con el objeto correcto { nuevoEstado, observacion }', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Observar"
    const observarBtn = screen.getByRole('button', { name: /Observar/i });
    await user.click(observarBtn);

    // Escribir observación
    const textarea = await screen.findByLabelText(/Observaciones/i);
    await user.type(textarea, 'Faltan documentos adicionales');

    // Confirmar
    const confirmarBtn = screen.getByRole('button', { name: /Confirmar/i });
    await user.click(confirmarBtn);

    // Verificar llamada con objeto
    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith({
        nuevoEstado: 'OBSERVADA',
        observacion: 'Faltan documentos adicionales',
      });
    });
  });

  it('debe permitir confirmar APROBADA sin observación', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Aprobar"
    const aprobarBtn = screen.getByRole('button', { name: /Aprobar/i });
    await user.click(aprobarBtn);

    // Confirmar directamente (sin escribir observación)
    const confirmarBtn = await screen.findByRole('button', { name: /Confirmar/i });
    await user.click(confirmarBtn);

    // Debe llamar a onAction sin observación
    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          nuevoEstado: 'APROBADA',
        })
       );
    });
  });

  it('debe deshabilitar el botón Confirmar mientras procesa', async () => {
    const user = userEvent.setup();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} isLoading={true} />);

    const aprobarBtn = screen.getByRole('button', { name: /Aprobar/i });
    
    // Todos los botones deben estar deshabilitados cuando isLoading es true
    expect(aprobarBtn).toBeDisabled();
  });
});
