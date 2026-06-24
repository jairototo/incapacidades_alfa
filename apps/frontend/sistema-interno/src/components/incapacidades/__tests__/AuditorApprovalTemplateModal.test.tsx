/**
 * Tests for AuditorApprovalTemplateModal
 *
 * Covers:
 *  - Pre-filling CIE-10 and medico from incapacidad
 *  - linea_autorizacion preview updates when dias/fechas change
 *  - Cancel button calls onCancel
 *  - Submit calls plantillaAuditoriaService.createOrUpdate + getTextoCopiable
 *  - Texto copiable textarea appears after successful submit
 *  - Copy-to-clipboard button is present
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditorApprovalTemplateModal } from '../AuditorApprovalTemplateModal';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';

// ---------------------------------------------------------------------------
// Mock the plantillaAuditoria service
// ---------------------------------------------------------------------------
vi.mock('@/services/plantillaAuditoria', () => ({
  plantillaAuditoriaService: {
    createOrUpdate: vi.fn().mockResolvedValue({ id: 'plantilla-1' }),
    getTextoCopiable: vi.fn().mockResolvedValue(
      'Se autoriza pago por 5 días desde 2024-01-15 hasta 2024-01-20\nCIE-10: M545\nCanal recepción: Portal',
    ),
  },
}));

// Mock use-toast to avoid Radix portal issues in jsdom
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// Mock the Select component so it renders a native <select> in tests,
// avoiding Radix portal/pointer-events issues in jsdom.
vi.mock('@/components/ui/select', () => ({
  Select: ({ onValueChange, children }: { onValueChange: (v: string) => void; children: React.ReactNode }) => (
    <div data-testid="select-root">
      <select
        data-testid="canal-select"
        onChange={(e) => onValueChange(e.target.value)}
      >
        <option value="">Seleccione el canal...</option>
        <option value="Portal">Portal</option>
        <option value="Imaginex">Imaginex</option>
        <option value="Onbase">Onbase</option>
      </select>
      {children}
    </div>
  ),
  SelectTrigger: () => null,
  SelectValue: () => null,
  SelectContent: () => null,
  SelectItem: () => null,
}));

// ---------------------------------------------------------------------------
// Shared mock incapacidad
// ---------------------------------------------------------------------------
const mockIncapacidad = {
  id: 'inc-test-001',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL',
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'M545',
  diagnostico_descripcion: 'Lumbago',
  valor_total: 500000,
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
};

const defaultProps = {
  incapacidad: mockIncapacidad,
  accion: 'LIQUIDACION' as const,
  open: true,
  onOpenChange: vi.fn(),
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
};

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
function renderModal(props = {}) {
  return render(<AuditorApprovalTemplateModal {...defaultProps} {...props} />);
}

async function selectCanal(user: ReturnType<typeof userEvent.setup>, value = 'Portal') {
  const select = screen.getByTestId('canal-select');
  await user.selectOptions(select, value);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('AuditorApprovalTemplateModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the modal with correct title when open', () => {
    renderModal();
    expect(screen.getByText(/Plantilla de Auditoría/i)).toBeInTheDocument();
    expect(screen.getByText(/Liquidación Completa/i)).toBeInTheDocument();
  });

  it('renders the correct title for LIQUIDACION_PARCIAL', () => {
    renderModal({ accion: 'LIQUIDACION_PARCIAL' });
    expect(screen.getByText(/Liquidación Parcial/i)).toBeInTheDocument();
  });

  it('pre-fills CIE-10 from incapacidad', () => {
    renderModal();
    expect(screen.getByDisplayValue('M545')).toBeInTheDocument();
  });

  it('pre-fills descripcion from incapacidad', () => {
    renderModal();
    expect(screen.getByDisplayValue('Lumbago')).toBeInTheDocument();
  });

  it('pre-fills dias_autorizados from incapacidad.dias_totales', () => {
    renderModal();
    const diasInput = screen.getByLabelText(/Días autorizados/i);
    expect(diasInput).toHaveValue(5);
  });

  it('pre-fills fecha_inicio from incapacidad', () => {
    renderModal();
    const fechaInicio = screen.getByLabelText(/Fecha inicio/i);
    expect(fechaInicio).toHaveValue('2024-01-15');
  });

  it('pre-fills fecha_fin from incapacidad', () => {
    renderModal();
    const fechaFin = screen.getByLabelText(/Fecha fin/i);
    expect(fechaFin).toHaveValue('2024-01-20');
  });

  it('shows linea_autorizacion preview based on pre-filled values', async () => {
    renderModal();
    await waitFor(() => {
      expect(
        screen.getByText(/Se autoriza pago por 5 días desde 2024-01-15 hasta 2024-01-20/i),
      ).toBeInTheDocument();
    });
  });

  it('updates linea_autorizacion when dias_autorizados changes', async () => {
    const user = userEvent.setup();
    renderModal();

    const diasInput = screen.getByLabelText(/Días autorizados/i);
    await user.clear(diasInput);
    await user.type(diasInput, '10');

    await waitFor(() => {
      expect(
        screen.getByText(/Se autoriza pago por 10 días/i),
      ).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    renderModal({ onCancel });

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i });
    await user.click(cancelBtn);

    expect(onCancel).toHaveBeenCalled();
  });

  it('shows validation error when canal_recepcion is not selected', async () => {
    const user = userEvent.setup();
    renderModal();

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Seleccione el canal de recepción/i)).toBeInTheDocument();
    });
  });

  it('calls createOrUpdate and getTextoCopiable on valid submit', async () => {
    const { plantillaAuditoriaService } = await import('@/services/plantillaAuditoria');
    const user = userEvent.setup();
    renderModal();

    await selectCanal(user);

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(plantillaAuditoriaService.createOrUpdate).toHaveBeenCalledWith(
        'inc-test-001',
        expect.objectContaining({
          canal_recepcion: 'Portal',
          dias_autorizados: 5,
          fecha_inicio_autorizada: '2024-01-15',
          fecha_fin_autorizada: '2024-01-20',
        }),
      );
      expect(plantillaAuditoriaService.getTextoCopiable).toHaveBeenCalledWith('inc-test-001');
    });
  });

  it('calls onConfirm with plantilla and observacion after successful submit', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ onConfirm });

    await selectCanal(user);

    const obsInput = screen.getByLabelText(/Observación adicional/i);
    await user.type(obsInput, 'Aprobado sin inconvenientes');

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ canal_recepcion: 'Portal' }),
        'Aprobado sin inconvenientes',
      );
    });
  });

  it('shows texto copiable textarea after successful submit', async () => {
    const user = userEvent.setup();
    renderModal();

    await selectCanal(user);

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByLabelText(/Texto copiable/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue(/Se autoriza pago por 5 días/i)).toBeInTheDocument();
    });
  });

  it('shows copy-to-clipboard button after successful submit', async () => {
    const user = userEvent.setup();
    renderModal();

    await selectCanal(user);

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Copiar/i })).toBeInTheDocument();
    });
  });

  it('shows "Listo — cerrar" button after successful submit', async () => {
    const user = userEvent.setup();
    renderModal();

    await selectCanal(user);

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Listo.*cerrar/i })).toBeInTheDocument();
    });
  });

  it('calls onConfirm without observacion when not filled', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderModal({ onConfirm });

    await selectCanal(user);

    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ canal_recepcion: 'Portal' }),
        '',
      );
    });
  });

  it('does not call createOrUpdate when form is invalid (missing canal)', async () => {
    const { plantillaAuditoriaService } = await import('@/services/plantillaAuditoria');
    const user = userEvent.setup();
    renderModal();

    // Do NOT select canal — just click submit
    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(plantillaAuditoriaService.createOrUpdate).not.toHaveBeenCalled();
    });
  });

  it('clears texto copiable when modal is re-opened', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();

    const { rerender } = renderModal({ onOpenChange });

    await selectCanal(user);
    const submitBtn = screen.getByRole('button', { name: /Generar plantilla/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByLabelText(/Texto copiable/i)).toBeInTheDocument();
    });

    // Simulate closing and re-opening
    await act(async () => {
      rerender(
        <AuditorApprovalTemplateModal
          {...defaultProps}
          open={false}
          onOpenChange={onOpenChange}
          onConfirm={vi.fn()}
          onCancel={vi.fn()}
        />,
      );
    });
    await act(async () => {
      rerender(
        <AuditorApprovalTemplateModal
          {...defaultProps}
          open={true}
          onOpenChange={onOpenChange}
          onConfirm={vi.fn()}
          onCancel={vi.fn()}
        />,
      );
    });

    // texto copiable should not be shown any more
    expect(screen.queryByLabelText(/Texto copiable/i)).not.toBeInTheDocument();
    // form should be visible again
    expect(screen.getByRole('button', { name: /Generar plantilla/i })).toBeInTheDocument();
  });
});
