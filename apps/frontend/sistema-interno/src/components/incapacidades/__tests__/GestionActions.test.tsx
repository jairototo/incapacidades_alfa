import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GestionActions } from '../GestionActions';
import { EstadoIncapacidad, TipoIncapacidad } from '@/types';
import type { PlantillaAuditoriaCreate } from '@/services/plantillaAuditoria';

// ---------------------------------------------------------------------------
// Mock useHasRole so AUDITOR/ADMIN check returns true (enables Aprobar button)
// ---------------------------------------------------------------------------
vi.mock('@/store/authStore', () => ({
  useHasRole: vi.fn().mockReturnValue(true),
  useAuthStore: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock AuditorApprovalTemplateModal — prevents it from rendering in GestionActions tests.
// When open, it immediately calls onConfirm so the LIQUIDACION flow can be tested.
// ---------------------------------------------------------------------------
vi.mock(
  '@/components/incapacidades/AuditorApprovalTemplateModal',
  () => ({
    AuditorApprovalTemplateModal: ({
      open,
      onConfirm,
    }: {
      open: boolean;
      onConfirm: (p: PlantillaAuditoriaCreate, obs: string) => void;
    }) => {
      if (!open) return null;
      return (
        <div data-testid="mock-template-modal">
          <button
            type="button"
            onClick={() =>
              onConfirm(
                {
                  canal_recepcion: 'Portal',
                  dias_autorizados: 5,
                  fecha_inicio_autorizada: '2024-01-15',
                  fecha_fin_autorizada: '2024-01-20',
                },
                '',
              )
            }
          >
            ConfirmarPlantilla
          </button>
        </div>
      );
    },
  }),
);

const mockIncapacidad = {
  id: 'test-id',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL',
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'S06.0',
  diagnostico_descripcion: 'Conmoción cerebral',
  valor_total: 500000,
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
};

describe('GestionActions', () => {
  const mockOnAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar los 4 botones de acción (Liquidar, Liquidar Parcial, Poner en Pendiente, Glosar)', () => {
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    expect(screen.getByRole('button', { name: /Liquidar Pasar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Liquidar Parcial/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Poner en Pendiente/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Glosar/i })).toBeInTheDocument();
  });

  it('debe seleccionar una acción al hacer click', async () => {
    const user = userEvent.setup();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    const aprobarBtn = screen.getByRole('button', { name: /Liquidar Pasar/i });
    await user.click(aprobarBtn);

    // El botón debe cambiar de estilo (se verifica por la clase ring-2)
    expect(aprobarBtn).toHaveClass('ring-2');
  });

  it('debe mostrar formulario con textarea de observaciones al seleccionar una acción', async () => {
    const user = userEvent.setup();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    const pendienteBtn = screen.getByRole('button', { name: /Poner en Pendiente/i });
    await user.click(pendienteBtn);

    // Debe aparecer el textarea
    await waitFor(() => {
      expect(screen.getByLabelText(/Observaciones/i)).toBeInTheDocument();
    });

    // Debe aparecer el botón Confirmar
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeInTheDocument();
  });

  it('debe validar que se requiere observación para GLOSAR y PENDIENTE', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Glosar"
    const glosarBtn = screen.getByRole('button', { name: /Glosar/i });
    await user.click(glosarBtn);

    // El textarea debe aparecer
    const textarea = await screen.findByLabelText(/Observaciones/i);
    expect(textarea).toBeInTheDocument();

    // Debe mostrar texto indicando que es requerido
    expect(screen.getByText(/Requerido: Justifique las razones de la glosa/i)).toBeInTheDocument();
  });

  it('debe llamar a onAction con el objeto correcto { nuevoEstado, observacion }', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Poner en Pendiente"
    const pendienteBtn = screen.getByRole('button', { name: /Poner en Pendiente/i });
    await user.click(pendienteBtn);

    // Escribir observación
    const textarea = await screen.findByLabelText(/Observaciones/i);
    await user.type(textarea, 'Faltan documentos adicionales');

    // Confirmar
    const confirmarBtn = screen.getByRole('button', { name: /Confirmar/i });
    await user.click(confirmarBtn);

    // Verificar llamada con objeto
    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith({
        nuevoEstado: 'PENDIENTE',
        observacion: 'Faltan documentos adicionales',
      });
    });
  });

  it('debe abrir el modal de plantilla al seleccionar LIQUIDACION y pasar al Continuar', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Aprobar"
    const aprobarBtn = screen.getByRole('button', { name: /Liquidar Pasar/i });
    await user.click(aprobarBtn);

    // Debe aparecer el botón "Continuar con plantilla"
    const continuarBtn = await screen.findByRole('button', { name: /Continuar con plantilla/i });
    await user.click(continuarBtn);

    // El modal mock debe renderizarse
    await waitFor(() => {
      expect(screen.getByTestId('mock-template-modal')).toBeInTheDocument();
    });
  });

  it('debe llamar a onAction con nuevoEstado LIQUIDACION tras confirmar la plantilla', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    // Seleccionar "Aprobar"
    const aprobarBtn = screen.getByRole('button', { name: /Liquidar Pasar/i });
    await user.click(aprobarBtn);

    // Continuar con plantilla
    const continuarBtn = await screen.findByRole('button', { name: /Continuar con plantilla/i });
    await user.click(continuarBtn);

    // The mock modal has a "ConfirmarPlantilla" button that fires onConfirm
    const confirmarPlantillaBtn = await screen.findByRole('button', { name: /ConfirmarPlantilla/i });
    await user.click(confirmarPlantillaBtn);

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          nuevoEstado: 'LIQUIDACION',
        }),
      );
    });
  });

  it('debe deshabilitar los botones mientras procesa', async () => {
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} isLoading={true} />);

    const aprobarBtn = screen.getByRole('button', { name: /Liquidar Pasar/i });

    // Todos los botones deben estar deshabilitados cuando isLoading es true
    expect(aprobarBtn).toBeDisabled();
  });

  it('debe abrir el modal de plantilla al seleccionar LIQUIDACION_PARCIAL y confirmar', async () => {
    const user = userEvent.setup();
    const mockCallback = vi.fn();
    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockCallback} />);

    const parcialBtn = screen.getByRole('button', { name: /Liquidar Parcial/i });
    await user.click(parcialBtn);

    const continuarBtn = await screen.findByRole('button', { name: /Continuar con plantilla/i });
    await user.click(continuarBtn);

    await waitFor(() => {
      expect(screen.getByTestId('mock-template-modal')).toBeInTheDocument();
    });

    const confirmarPlantillaBtn = screen.getByRole('button', { name: /ConfirmarPlantilla/i });
    await user.click(confirmarPlantillaBtn);

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({ nuevoEstado: 'LIQUIDACION_PARCIAL' }),
      );
    });
  });

  it('no debe mostrar el botón Aprobar cuando el rol no es AUDITOR/ADMIN', async () => {
    const { useHasRole } = await import('@/store/authStore');
    (useHasRole as ReturnType<typeof vi.fn>).mockReturnValue(false);

    render(<GestionActions incapacidad={mockIncapacidad} onAction={mockOnAction} />);

    expect(screen.queryByRole('button', { name: /Liquidar Pasar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Liquidar Parcial/i })).not.toBeInTheDocument();
    // Other buttons are still visible
    expect(screen.getByRole('button', { name: /Poner en Pendiente/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Glosar/i })).toBeInTheDocument();
  });
});
