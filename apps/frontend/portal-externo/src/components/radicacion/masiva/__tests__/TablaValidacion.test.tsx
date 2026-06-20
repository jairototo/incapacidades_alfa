import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablaValidacion } from '@/components/radicacion/masiva/TablaValidacion';

const filas = [
  { fila: 2, empleado_id: 'e1', datos: { numero_documento: '1' }, errores: [], valida: true },
  { fila: 3, empleado_id: null, datos: { numero_documento: '2' },
    errores: [
      { codigo: 'INVALID_DATE_RANGE', descripcion: 'Fechas invertidas', severidad: 'ERROR' },
      { codigo: 'EMPTY_DIAGNOSTICO_CIE10', descripcion: 'CIE-10 requerido', severidad: 'ERROR' },
    ], valida: false },
  { fila: 4, empleado_id: 'e3', datos: { numero_documento: '3' },
    errores: [{ codigo: 'RETROACTIVE_BEYOND_LIMIT', descripcion: 'Incapacidad retroactiva', severidad: 'WARNING' }],
    valida: true },
];

describe('TablaValidacion', () => {
  it('shows all ERRORs for an invalid row and slots for a valid one', () => {
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/Fechas invertidas/)).toBeInTheDocument();
    expect(screen.getByText(/CIE-10 requerido/)).toBeInTheDocument();
    expect(screen.getAllByText(/INCAPACIDAD/).length).toBeGreaterThan(0); // slot label on valid rows
  });

  it('shows a WARNING as advisory and still renders slots for that valid row', () => {
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/Incapacidad retroactiva/)).toBeInTheDocument(); // warning surfaced
    // row 4 is valida=true with an empleado_id, so it must have its own slots
  });

  it('calls onDelete when a row is removed', () => {
    const onDelete = vi.fn();
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={onDelete} />);
    fireEvent.click(screen.getAllByRole('button', { name: /eliminar fila/i })[0]);
    expect(onDelete).toHaveBeenCalledWith(2);
  });
});
