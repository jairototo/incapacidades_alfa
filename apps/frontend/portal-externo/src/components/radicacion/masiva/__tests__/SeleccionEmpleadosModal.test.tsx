import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SeleccionEmpleadosModal } from '@/components/radicacion/masiva/SeleccionEmpleadosModal';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({ data: [
    { id: 'e1', numero_documento: '1', nombres: 'Ana', apellidos: 'G' },
    { id: 'e2', numero_documento: '2', nombres: 'Beto', apellidos: 'L' },
  ], isLoading: false }),
}));

describe('SeleccionEmpleadosModal', () => {
  it('downloads with selected employees', () => {
    const onDownload = vi.fn();
    render(<SeleccionEmpleadosModal open onClose={() => {}} onDownload={onDownload} />);
    fireEvent.click(screen.getByLabelText(/seleccionar Ana G/i));
    fireEvent.click(screen.getByRole('button', { name: /descargar/i }));
    expect(onDownload).toHaveBeenCalledWith(['e1']);
  });

  it('allows header-only download with no selection', () => {
    const onDownload = vi.fn();
    render(<SeleccionEmpleadosModal open onClose={() => {}} onDownload={onDownload} />);
    fireEvent.click(screen.getByRole('button', { name: /descargar/i }));
    expect(onDownload).toHaveBeenCalledWith([]);
  });
});
