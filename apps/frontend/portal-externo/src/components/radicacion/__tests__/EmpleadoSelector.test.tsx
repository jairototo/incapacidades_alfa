import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpleadoSelector } from '@/components/radicacion/EmpleadoSelector';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({
    data: [{ id: 'e1', numero_documento: '123', nombres: 'Ana', apellidos: 'Gómez' }],
    isLoading: false,
  }),
}));

const wrap = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>);

describe('EmpleadoSelector', () => {
  it('renders the help tooltip text and selects an employee', () => {
    const onChange = vi.fn();
    wrap(<EmpleadoSelector value={undefined} onChange={onChange} />);
    expect(screen.getByLabelText(/ayuda/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Ana Gómez/));
    expect(onChange).toHaveBeenCalledWith('e1');
  });
});
