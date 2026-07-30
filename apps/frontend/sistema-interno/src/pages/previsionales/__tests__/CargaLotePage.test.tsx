import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { CargaLotePage } from '../CargaLotePage';
import { previsionalesService } from '@/services/previsionales';
import type { LotePrevisional } from '@/types/previsional';

vi.mock('@/services/previsionales', () => ({
  previsionalesService: {
    cargarLote: vi.fn(),
  },
}));

function makeFile() {
  return new File(['contenido'], 'lote_afp.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

const mockLote: LotePrevisional = {
  id: 'lote-001',
  nombre_archivo: 'lote_afp.xlsx',
  estado: 'CARGADO',
  fecha_cargue: '2026-07-29T10:00:00Z',
  cargado_por_id: 'user-001',
  total_filas: 200,
  total_incapacidades: 195,
  observaciones: null,
  created_at: '2026-07-29T10:00:00Z',
  updated_at: '2026-07-29T10:00:00Z',
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/previsionales/carga']}>
        <Routes>
          <Route path="/previsionales/carga" element={<CargaLotePage />} />
          <Route path="/previsionales/lotes/:loteId" element={<div>Detalle de Lote</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('CargaLotePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the upload form', () => {
    renderPage();
    expect(screen.getByLabelText(/archivo \(\.xlsx\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña del archivo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/nombre de archivo/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cargar lote/i })).toBeInTheDocument();
  });

  it('shows a validation error and does not call the service when submitting without a file', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /cargar lote/i }));

    await waitFor(() => {
      expect(screen.getByText(/el archivo es obligatorio/i)).toBeInTheDocument();
    });
    expect(previsionalesService.cargarLote).not.toHaveBeenCalled();
  });

  it('calls cargarLote with the selected file, password and nombre_archivo, and shows the success summary', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.cargarLote).mockResolvedValue(mockLote);
    renderPage();

    await user.upload(screen.getByLabelText(/archivo \(\.xlsx\)/i), makeFile());
    await user.type(screen.getByLabelText(/contraseña del archivo/i), 'secreta123');
    await user.type(screen.getByLabelText(/nombre de archivo/i), 'lote-julio.xlsx');
    await user.click(screen.getByRole('button', { name: /cargar lote/i }));

    await waitFor(() => {
      expect(previsionalesService.cargarLote).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'lote_afp.xlsx' }),
        'secreta123',
        'lote-julio.xlsx'
      );
    });

    expect(await screen.findByText(/lote cargado correctamente/i)).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
    expect(screen.getByText('195')).toBeInTheDocument();
  });

  it('shows the error message extracted from the axios response when the upload fails', async () => {
    const user = userEvent.setup();
    vi.mocked(previsionalesService.cargarLote).mockRejectedValue({
      response: { data: { detail: 'Contraseña incorrecta para el archivo cifrado.' } },
    });
    renderPage();

    await user.upload(screen.getByLabelText(/archivo \(\.xlsx\)/i), makeFile());
    await user.click(screen.getByRole('button', { name: /cargar lote/i }));

    await waitFor(() => {
      expect(screen.getByText(/contraseña incorrecta para el archivo cifrado/i)).toBeInTheDocument();
    });
    // File selection is preserved so the user can retry without re-picking it.
    expect(screen.getByText(/seleccionado: lote_afp\.xlsx/i)).toBeInTheDocument();
  });
});
