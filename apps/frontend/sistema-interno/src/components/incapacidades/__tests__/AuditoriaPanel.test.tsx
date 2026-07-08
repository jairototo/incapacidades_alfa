/**
 * Tests for AuditoriaPanel
 *
 * Covers:
 * 1. El formulario de aprobación precarga nombre_ips, nombre_medico y canal_recepcion
 *    ("Portal IT") desde la incapacidad, y resuelve la descripción CIE-10 del
 *    código original consultando el catálogo (GET /catalogos/cie10/{codigo}).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

import { AuditoriaPanel } from '../AuditoriaPanel';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';
import type { Incapacidad } from '@/types/incapacidad';
import api from '@/lib/api';

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    aprobarEnAuditoria: vi.fn(),
    glosar: vi.fn(),
    ponerPendiente: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => ({
  default: { get: vi.fn() },
}));

const mockIncapacidad: Incapacidad = {
  id: 'inc-1',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL' as any,
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 6,
  diagnostico_cie10: 'M545',
  diagnostico_descripcion: 'Lumbago',
  ips: 'Clínica San Rafael',
  nombre_medico: 'Dr. Carlos Pérez',
  valor_total: 500000,
  numero_siniestro: 'SIN-001',
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
} as any;

function renderPanel(incapacidad: Incapacidad = mockIncapacidad) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AuditoriaPanel incapacidad={incapacidad} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AuditoriaPanel — precarga de plantilla en formulario de aprobación', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/catalogos/cie10/M545') {
        return Promise.resolve({ data: { codigo: 'M545', descripcion: 'Lumbago' } });
      }
      if (url === '/catalogos/cie10') {
        return Promise.resolve({ data: [] });
      }
      return Promise.reject(new Error(`unexpected url ${url}`));
    });
  });

  it('precarga nombre_ips, nombre_medico y canal_recepcion ("Portal IT") y resuelve la descripción CIE-10 desde el catálogo', async () => {
    const user = userEvent.setup();
    renderPanel();

    await user.click(screen.getByRole('button', { name: /Aprobar para pago/i }));

    const ipsInput = await screen.findByLabelText(/Nombre IPS/i);
    expect(ipsInput).toHaveValue('Clínica San Rafael');

    const medicoInput = screen.getByLabelText(/Nombre médico/i);
    expect(medicoInput).toHaveValue('Dr. Carlos Pérez');

    const canalInput = screen.getByLabelText(/Canal de recepción/i);
    expect(canalInput).toHaveValue('Portal IT');

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/catalogos/cie10/M545');
    });

    const descripcionInput = screen.getByLabelText(/Descripción diagnóstico/i);
    await waitFor(() => {
      expect(descripcionInput).toHaveValue('Lumbago');
    });
  });

  it('deja el campo IPS vacío y editable cuando la incapacidad no trae valor', async () => {
    const user = userEvent.setup();
    renderPanel({ ...mockIncapacidad, ips: null, nombre_medico: null } as any);

    await user.click(screen.getByRole('button', { name: /Aprobar para pago/i }));

    const ipsInput = await screen.findByLabelText(/Nombre IPS/i);
    expect(ipsInput).toHaveValue('');
    expect(ipsInput).not.toHaveAttribute('readonly');
  });
});
