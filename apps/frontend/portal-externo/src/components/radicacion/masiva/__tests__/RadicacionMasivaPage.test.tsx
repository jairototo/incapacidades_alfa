import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicacionMasivaPage } from '@/components/radicacion/masiva/RadicacionMasivaPage';

const toastMock = vi.fn();
vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: toastMock }) }));

vi.mock('@/services/empresaEmpleadoService', () => ({ useEmpleadosDeMiEmpresa: () => ({ data: [], isLoading: false }) }));
vi.mock('@/services/bulkRadicacionService', () => ({
  descargarPlantilla: vi.fn(),
  mapearZip: vi.fn(),
  radicarMasiva: vi.fn(),
  validarExcel: vi.fn().mockResolvedValue({
    filas: [{ fila: 2, empleado_id: null, datos: { numero_documento: '1' },
              errores: [{ codigo: 'EMPTY_DIAGNOSTICO_CIE10', descripcion: 'CIE-10 requerido', severidad: 'ERROR' }],
              valida: false }],
    total: 1, validas: 0,
  }),
}));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><RadicacionMasivaPage /></MemoryRouter>
  </QueryClientProvider>,
);

describe('RadicacionMasivaPage', () => {
  it('renders the template download, the 3-step intro, and no submit button before rows', () => {
    wrap();
    expect(screen.getByRole('button', { name: /descargar plantilla/i })).toBeInTheDocument();
    // explanatory 3-step intro is shown before any upload
    expect(screen.getByText(/¿cómo funciona/i)).toBeInTheDocument();
    expect(screen.getByText(/diligencie la información/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /radicar incapacidades/i })).not.toBeInTheDocument();
  });

  it('documents the per-column field format with the authoritative values', () => {
    wrap();
    expect(screen.getByText(/ver formato de campos/i)).toBeInTheDocument();
    // date format matches what the backend actually parses
    expect(screen.getAllByText(/AAAA-MM-DD/).length).toBeGreaterThan(0);
    // tipo_enfermedad catalog + CIE-10 example surfaced
    expect(screen.getByText(/ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL o ACCIDENTE_TRAYECTO/)).toBeInTheDocument();
    expect(screen.getByText(/CIE-10 sin punto \(ej: A048, M545 o A09X\)/)).toBeInTheDocument();
  });

  it('shows a blocking banner when submitting with an invalid row', async () => {
    wrap();
    const excel = new File([new Uint8Array(10)], 'data.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    fireEvent.change(screen.getByLabelText(/subir excel/i), { target: { files: [excel] } });
    // after validation, the row + submit button appear
    const submit = await screen.findByRole('button', { name: /radicar incapacidades/i });
    // the intro is de-emphasized (hidden) once the user has uploaded a file
    expect(screen.queryByText(/¿cómo funciona/i)).not.toBeInTheDocument();
    fireEvent.click(submit);
    expect(await screen.findByRole('alert')).toHaveTextContent(/impiden radicar/i);
  });

  it('discards the previous file results when a new Excel is uploaded', async () => {
    const { validarExcel } = await import('@/services/bulkRadicacionService');
    const mk = (doc: string) => ({
      filas: [{ fila: 2, empleado_id: null, datos: { numero_documento: doc },
                errores: [{ codigo: 'X', descripcion: 'err', severidad: 'ERROR' }], valida: false }],
      total: 1, validas: 0,
    });
    (validarExcel as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mk('1')).mockResolvedValueOnce(mk('99'));
    wrap();
    const input = screen.getByLabelText(/subir excel/i);
    fireEvent.change(input, { target: { files: [new File([new Uint8Array(10)], 'a.xlsx')] } });
    expect(await screen.findByText(/Documento 1\b/)).toBeInTheDocument();
    fireEvent.change(input, { target: { files: [new File([new Uint8Array(10)], 'b.xlsx')] } });
    expect(await screen.findByText(/Documento 99/)).toBeInTheDocument();
    expect(screen.queryByText(/Documento 1\b/)).not.toBeInTheDocument();
  });

  it('clears previously valid rows when a re-upload fails validation', async () => {
    const { validarExcel } = await import('@/services/bulkRadicacionService');
    (validarExcel as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ filas: [{ fila: 2, empleado_id: 'e1',
        datos: { numero_documento: '1' }, errores: [], valida: true }], total: 1, validas: 1 })
      .mockRejectedValueOnce({ response: { data: { detail: 'Archivo inválido' } } });
    wrap();
    const input = screen.getByLabelText(/subir excel/i);
    fireEvent.change(input, { target: { files: [new File([new Uint8Array(10)], 'a.xlsx')] } });
    expect(await screen.findByRole('button', { name: /radicar incapacidades/i })).toBeInTheDocument();
    fireEvent.change(input, { target: { files: [new File([new Uint8Array(10)], 'b.xlsx')] } });
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /radicar incapacidades/i })).not.toBeInTheDocument());
  });

  it('shows an error toast when Excel validation fails', async () => {
    const { validarExcel } = await import('@/services/bulkRadicacionService');
    (validarExcel as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: { data: { detail: 'Archivo inválido' } },
    });
    wrap();
    fireEvent.change(screen.getByLabelText(/subir excel/i), {
      target: { files: [new File([new Uint8Array(10)], 'x.xlsx')] },
    });
    await waitFor(() =>
      expect(toastMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: expect.stringMatching(/no se pudo validar/i) }),
      ),
    );
    expect(screen.queryByRole('button', { name: /radicar incapacidades/i })).not.toBeInTheDocument();
  });
});
