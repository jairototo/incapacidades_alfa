import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../DataTable';

interface Fila {
  id: string;
  nombre: string;
  alerta: boolean;
}

const columns: ColumnDef<Fila, unknown>[] = [
  { accessorKey: 'nombre', header: 'Nombre' },
];

const data: Fila[] = [
  { id: '1', nombre: 'Uno', alerta: true },
  { id: '2', nombre: 'Dos', alerta: false },
];

describe('DataTable', () => {
  it('renders rows with only the base TableRow styling when rowClassName is not passed (existing behavior unaffected)', () => {
    render(<DataTable columns={columns} data={data} />);
    const row = screen.getByText('Uno').closest('tr');
    expect(row).not.toBeNull();
    expect(row).toHaveClass('border-b', 'transition-colors');
    // No stray "undefined" leaking into the class list from an unset rowClassName.
    expect(row?.className).not.toMatch(/undefined/);
  });

  it('applies the class returned by rowClassName to each row using that row data', () => {
    const rowClassName = (row: Fila) => (row.alerta ? 'bg-red-100' : 'bg-white');
    render(<DataTable columns={columns} data={data} rowClassName={rowClassName} />);

    const filaUno = screen.getByText('Uno').closest('tr');
    const filaDos = screen.getByText('Dos').closest('tr');

    expect(filaUno).toHaveClass('bg-red-100');
    expect(filaDos).toHaveClass('bg-white');
  });
});
