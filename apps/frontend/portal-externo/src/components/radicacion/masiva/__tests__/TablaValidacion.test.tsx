import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablaValidacion } from '@/components/radicacion/masiva/TablaValidacion';

const datosOk = {
  numero_documento: '1', empleado_nombres: 'Ana', empleado_apellidos: 'Gómez',
  tipo_enfermedad: 'ACCIDENTE_TRABAJO', fecha_inicio: '2026-06-01', fecha_fin: '2026-06-05',
  dias_totales: 5, diagnostico_cie10: 'M545', prorroga: false, nombre_medico: 'Dr X', ips: 'IPS Salud',
};

const filas = [
  { fila: 2, empleado_id: 'e1', datos: datosOk, errores: [], valida: true },
  { fila: 3, empleado_id: null, datos: { numero_documento: '2' },
    errores: [
      { codigo: 'INVALID_DATE_RANGE', descripcion: 'Fechas invertidas', severidad: 'ERROR' },
      { codigo: 'EMPTY_DIAGNOSTICO_CIE10', descripcion: 'CIE-10 requerido', severidad: 'ERROR' },
    ], valida: false },
  { fila: 4, empleado_id: 'e3', datos: { ...datosOk, numero_documento: '3' },
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
  });

  it('renders the parsed Excel data for the row (employee, dates, CIE-10, prorroga)', () => {
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getAllByText(/Ana Gómez/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('ACCIDENTE_TRABAJO').length).toBeGreaterThan(0);
    expect(screen.getAllByText('M545').length).toBeGreaterThan(0);
    expect(screen.getAllByText('01/06/2026').length).toBeGreaterThan(0); // ISO formatted to DD/MM/YYYY
    expect(screen.getAllByText('No').length).toBeGreaterThan(0); // prorroga false
  });

  it('marks a required doc as missing and shows the filename once attached', () => {
    const conDoc = { e1: { INCAPACIDAD: new File(['x'], 'incap_ana.pdf') } } as any;
    const { rerender } = render(
      <TablaValidacion filas={[filas[0]] as any} documentos={{}} onAddDoc={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByText(/Falta \(requerido\)/)).toBeInTheDocument();
    rerender(<TablaValidacion filas={[filas[0]] as any} documentos={conDoc} onAddDoc={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText('incap_ana.pdf')).toBeInTheDocument();
    expect(screen.queryByText(/Falta \(requerido\)/)).not.toBeInTheDocument();
  });

  it('calls onDelete when a row is removed', () => {
    const onDelete = vi.fn();
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={onDelete} />);
    fireEvent.click(screen.getAllByRole('button', { name: /eliminar fila/i })[0]);
    expect(onDelete).toHaveBeenCalledWith(2);
  });
});
