import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablaIncapacidades } from '@/components/consulta/TablaIncapacidades';

const items = [{
  id: 'i1', numero: 'ARL-20260601-0001', estado: 'RADICADA', tipo: 'ARL',
  fecha_inicio: '2026-06-01', fecha_fin: '2026-06-05', dias_totales: 5, diagnostico_cie10: 'S00.0',
  empleado: { nombres: 'Ana', apellidos: 'Gómez', numero_documento: '123' },
}];

describe('TablaIncapacidades', () => {
  it('renders rows and emits row click', () => {
    const onSelect = vi.fn();
    render(<TablaIncapacidades items={items as any} isLoading={false} onSelect={onSelect} />);
    expect(screen.getByText('ARL-20260601-0001')).toBeInTheDocument();
    fireEvent.click(screen.getByText('ARL-20260601-0001'));
    expect(onSelect).toHaveBeenCalledWith('i1');
  });

  it('shows empty state', () => {
    render(<TablaIncapacidades items={[]} isLoading={false} onSelect={() => {}} />);
    expect(screen.getByText(/no hay incapacidades/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<TablaIncapacidades items={[]} isLoading={true} onSelect={() => {}} />);
    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });
});
