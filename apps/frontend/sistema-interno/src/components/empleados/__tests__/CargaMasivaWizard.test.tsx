import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CargaMasivaWizard } from '../CargaMasivaWizard';
import { empleadoService } from '@/services/empleadoService';

vi.mock('@/services/empleadoService');

function makeFile() {
  return new File(['contenido'], 'empleados.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

describe('CargaMasivaWizard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('step 1 → validar → step 2 shows the error summary', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 2, validas: 1, con_error: 1,
      errores: [{ fila: 2, columna: 'numero_documento', mensaje: 'Campo obligatorio' }],
    });
    const onClose = vi.fn();
    render(<CargaMasivaWizard open onClose={onClose} />);

    const fileInput = screen.getByLabelText(/archivo/i) as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));

    await waitFor(() => expect(screen.getByText(/campo obligatorio/i)).toBeInTheDocument());
    expect(screen.getByText(/1 válidas/i)).toBeInTheDocument();
    expect(screen.getByText(/1 con error/i)).toBeInTheDocument();
  });

  it('step 2 → confirmar disabled when validas=0', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 0, con_error: 1,
      errores: [{ fila: 2, mensaje: 'Campo obligatorio', columna: 'nombres' }],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));

    await waitFor(() => expect(screen.getByRole('button', { name: /confirmar carga/i })).toBeDisabled());
  });

  it('step 2 → confirmar → step 3 shows insertadas/con_error summary', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 1, con_error: 0, errores: [],
    });
    vi.mocked(empleadoService.confirmarCargaMasiva).mockResolvedValue({
      total_filas: 1, insertadas: 1, con_error: 0, errores: [],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /confirmar carga/i })).not.toBeDisabled());

    fireEvent.click(screen.getByRole('button', { name: /confirmar carga/i }));

    await waitFor(() => expect(screen.getByText(/1 insertadas/i)).toBeInTheDocument());
  });

  it('"Volver" returns from step 2 to step 1', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 1, con_error: 0, errores: [],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /volver/i })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /volver/i }));
    expect(screen.getByRole('button', { name: /^validar$/i })).toBeInTheDocument();
  });

  it('"Descargar plantilla" calls empleadoService.getPlantilla', async () => {
    vi.mocked(empleadoService.getPlantilla).mockResolvedValue(new Blob(['x']));
    // jsdom has no real URL.createObjectURL; stub it for this assertion-only test.
    window.URL.createObjectURL = vi.fn(() => 'blob:mock');
    window.URL.revokeObjectURL = vi.fn();
    render(<CargaMasivaWizard open onClose={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /descargar plantilla/i }));

    await waitFor(() => expect(empleadoService.getPlantilla).toHaveBeenCalled());
  });
});
