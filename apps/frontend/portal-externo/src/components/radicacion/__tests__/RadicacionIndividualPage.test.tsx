import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicacionIndividualPage } from '@/components/radicacion/RadicacionIndividualPage';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({ data: [], isLoading: false }),
}));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><RadicacionIndividualPage /></MemoryRouter>
  </QueryClientProvider>,
);

describe('RadicacionIndividualPage', () => {
  it('renders the form heading and the prorroga switch', () => {
    wrap();
    expect(screen.getByText(/radicación individual/i)).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });
});
