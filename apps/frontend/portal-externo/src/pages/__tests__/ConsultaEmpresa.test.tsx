import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConsultaEmpresa } from '@/pages/ConsultaEmpresa';

// ── List hook: factory returns a vi.fn() so each test can override ──────────
const mockUseIncapacidadesDeMiEmpresa = vi.fn();
vi.mock('@/services/consultaEmpresaService', () => ({
  useIncapacidadesDeMiEmpresa: (...args: unknown[]) =>
    mockUseIncapacidadesDeMiEmpresa(...args),
}));

// ── Detail hook: always returns isLoading:true to avoid partial-data render ─
vi.mock('@/hooks/useConsultaIncapacidad', () => ({
  useConsultarPorNumero: () => ({ data: undefined, isLoading: true, isError: false }),
}));

// ── Default list: empty, no loading, no error (smoke test baseline) ─────────
beforeEach(() => {
  mockUseIncapacidadesDeMiEmpresa.mockReturnValue({
    data: [],
    isLoading: false,
    isError: false,
  });
});

const wrap = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <ConsultaEmpresa />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe('ConsultaEmpresa', () => {
  it('renders heading, filters and empty table', () => {
    wrap();
    expect(screen.getByText(/consulta de incapacidades/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/estado/i)).toBeInTheDocument();
    expect(screen.getByText(/no hay incapacidades/i)).toBeInTheDocument();
  });

  it('opens the detail drawer on row click and closes on Escape', () => {
    mockUseIncapacidadesDeMiEmpresa.mockReturnValue({
      data: [
        {
          id: 'i1',
          numero: 'ARL-1',
          estado: 'RADICADA',
          tipo: 'ARL',
          fecha_inicio: '2026-06-01',
          fecha_fin: '2026-06-05',
          dias_totales: 5,
          diagnostico_cie10: 'S00.0',
          empleado: { nombres: 'Ana', apellidos: 'G', numero_documento: '1' },
        },
      ],
      isLoading: false,
      isError: false,
    });

    wrap();

    // Click the "ARL-1" cell — bubbles up to the <tr> onClick handler
    act(() => {
      fireEvent.click(screen.getByRole('cell', { name: 'ARL-1' }));
    });
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Escape should close the drawer — wrap in act to flush state update
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
