import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DetalleModal } from '../DetalleModal';
import { incapacidadService } from '@/services/incapacidadService';
import { TipoIncapacidad, EstadoIncapacidad, Prioridad } from '@/types/enums';

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getById: vi.fn(),
    getHistorial: vi.fn(),
    getDocumentos: vi.fn(),
    descargarDocumento: vi.fn(),
  },
}));

const mockIncapacidad = {
  id: 'inc-1',
  numero: 'ARL-0001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: Prioridad.NORMAL,
  fecha_inicio: '2026-01-01',
  fecha_fin: '2026-01-05',
  dias_totales: 5,
  diagnostico_cie10: 'M545',
  diagnostico_descripcion: 'Lumbago',
  valor_total: 100000,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

function renderModal() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <DetalleModal open={true} onClose={vi.fn()} incapacidadId="inc-1" />
    </QueryClientProvider>
  );
}

describe('DetalleModal — tab Timeline', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(incapacidadService.getById).mockResolvedValue(mockIncapacidad as any);
    vi.mocked(incapacidadService.getDocumentos).mockResolvedValue([]);
  });

  it('debe mostrar el nombre del responsable con su etiqueta cuando el cambio tiene usuario', async () => {
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([
      {
        id: 'hist-1',
        estado_anterior: 'RADICADA',
        estado_nuevo: 'EN_AUDITORIA',
        observacion: 'Pasando a auditoría',
        cambiado_por_id: 'user-1',
        cambiado_por_nombre: 'Admin Usuario',
        created_at: '2026-01-02T00:00:00Z',
      },
    ] as any);

    const user = userEvent.setup();
    renderModal();

    await waitFor(() => screen.getByRole('tab', { name: 'Timeline' }));
    await user.click(screen.getByRole('tab', { name: 'Timeline' }));

    expect(await screen.findByText('Responsable:')).toBeInTheDocument();
    expect(screen.getByText('Admin Usuario')).toBeInTheDocument();
    // El id técnico nunca debe mostrarse como texto visible.
    expect(screen.queryByText('user-1')).not.toBeInTheDocument();
  });

  it('no debe romper ni mostrar la sección de responsable cuando el cambio fue automático (sin usuario)', async () => {
    vi.mocked(incapacidadService.getHistorial).mockResolvedValue([
      {
        id: 'hist-auto',
        estado_anterior: null,
        estado_nuevo: 'RADICADA',
        observacion: 'Transición automática por job de auditoría',
        cambiado_por_id: null,
        cambiado_por_nombre: null,
        created_at: '2026-01-01T00:05:00Z',
      },
    ] as any);

    const user = userEvent.setup();
    renderModal();

    await waitFor(() => screen.getByRole('tab', { name: 'Timeline' }));
    await user.click(screen.getByRole('tab', { name: 'Timeline' }));

    expect(await screen.findByText(/Transición automática por job de auditoría/)).toBeInTheDocument();
    expect(screen.queryByText('Responsable:')).not.toBeInTheDocument();
  });
});
