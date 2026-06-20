import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FiltrosConsultaEmpresa } from '@/components/consulta/FiltrosConsultaEmpresa';

describe('FiltrosConsultaEmpresa', () => {
  it('emits filter changes', () => {
    const onChange = vi.fn();
    render(<FiltrosConsultaEmpresa value={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/documento/i), { target: { value: '123' } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ empleado_documento: '123' }));
  });

  it('emits estado changes', () => {
    const onChange = vi.fn();
    render(<FiltrosConsultaEmpresa value={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/estado/i), { target: { value: 'RADICADA' } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ estado: 'RADICADA' }));
  });
});
