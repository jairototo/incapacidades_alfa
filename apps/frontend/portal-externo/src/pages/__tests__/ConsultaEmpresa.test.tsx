import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConsultaEmpresa } from '@/pages/ConsultaEmpresa';

vi.mock('@/services/consultaEmpresaService', () => ({
  useIncapacidadesDeMiEmpresa: () => ({ data: [], isLoading: false }),
}));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><ConsultaEmpresa /></MemoryRouter>
  </QueryClientProvider>,
);

describe('ConsultaEmpresa', () => {
  it('renders heading, filters and empty table', () => {
    wrap();
    expect(screen.getByText(/consulta de incapacidades/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/estado/i)).toBeInTheDocument();
    expect(screen.getByText(/no hay incapacidades/i)).toBeInTheDocument();
  });
});
