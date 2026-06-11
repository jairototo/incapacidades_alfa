import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentosViewer } from '../DocumentosViewer';
import { incapacidadService } from '@/services/incapacidadService';
import api from '@/lib/api';

// ── Stubs for browser APIs not in jsdom ────────────────────────────────────
URL.createObjectURL = vi.fn(() => 'blob:mock-preview-url');
URL.revokeObjectURL = vi.fn();

// ── Module mocks ───────────────────────────────────────────────────────────

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getDownloadUrl: vi.fn(),
  },
}));

// ── Fixtures ───────────────────────────────────────────────────────────────

const mockDocumentos = [
  {
    id: 'doc-1',
    nombre_original: 'incapacidad_medica.pdf',
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano_bytes: 102400,
    ruta_arquivo: '/documentos/incapacidad_medica.pdf',
    uploaded_by: 'user-123',
    created_at: '2024-01-10T10:30:00Z',
    extension: 'pdf',
  },
  {
    id: 'doc-2',
    nombre_original: 'historia_clinica.pdf',
    tipo_documento: 'HISTORIA_CLINICA',
    mime_type: 'application/pdf',
    tamano_bytes: 204800,
    ruta_arquivo: '/documentos/historia_clinica.pdf',
    uploaded_by: 'user-123',
    created_at: '2024-01-10T11:00:00Z',
    extension: 'pdf',
  },
  {
    id: 'doc-3',
    nombre_original: 'radiografia.jpg',
    tipo_documento: 'SOPORTE_MEDICO',
    mime_type: 'image/jpeg',
    tamano_bytes: 512000,
    ruta_arquivo: '/documentos/radiografia.jpg',
    uploaded_by: 'user-123',
    created_at: '2024-01-10T12:00:00Z',
    extension: 'jpg',
  },
];

// ── Helper ─────────────────────────────────────────────────────────────────
function setupDefaultMocks() {
  (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
    data: new Blob(['mock-content'], { type: 'application/pdf' }),
  });
  (incapacidadService.getDownloadUrl as ReturnType<typeof vi.fn>).mockResolvedValue(
    '/api/v1/storage/files/documentos/test.pdf'
  );
  URL.createObjectURL = vi.fn(() => 'blob:mock-preview-url');
  URL.revokeObjectURL = vi.fn();
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe('DocumentosViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  it('debe renderizar mensaje de "Sin documentos" cuando el array está vacío', () => {
    render(<DocumentosViewer documentos={[]} />);
    expect(
      screen.getByText(/No hay documentos adjuntos a esta incapacidad/)
    ).toBeInTheDocument();
  });

  it('debe renderizar tabs horizontales con todos los documentos', async () => {
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    expect(screen.getAllByText('incapacidad_medica.pdf').length).toBeGreaterThan(0);
    expect(screen.getAllByText('historia_clinica.pdf').length).toBeGreaterThan(0);
    expect(screen.getAllByText('radiografia.jpg').length).toBeGreaterThan(0);
  });

  it('debe auto-seleccionar el primer documento al montar', async () => {
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();
    expect(screen.getAllByText('incapacidad_medica.pdf').length).toBeGreaterThan(0);
  });

  it('debe cambiar la vista al seleccionar un tab diferente', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();

    const historiaTab = screen.getByText('historia_clinica.pdf');
    await user.click(historiaTab);

    expect(screen.getByText('HISTORIA_CLINICA')).toBeInTheDocument();
  });

  it('debe cambiar a vista de imagen al seleccionar un documento de imagen', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    const radiografiaTab = screen.getByText('radiografia.jpg');
    await user.click(radiografiaTab);

    expect(screen.getByText('SOPORTE_MEDICO')).toBeInTheDocument();
  });

  it('debe manejar documentos sin nombre_original correctamente', async () => {
    const documentoSinNombre = {
      id: 'doc-no-name',
      nombre_original: undefined,
      tipo_documento: 'OTRO',
      mime_type: 'application/octet-stream',
      tamano_bytes: 1024,
      ruta_arquivo: '/documentos/archivo_sin_nombre',
      uploaded_by: 'user-123',
      created_at: '2024-01-10T10:00:00Z',
      extension: '',
    };

    await act(async () => {
      render(<DocumentosViewer documentos={[documentoSinNombre] as any} />);
    });

    expect(screen.getAllByText('Sin nombre').length).toBeGreaterThan(0);
    expect(screen.getByText('OTRO')).toBeInTheDocument();
  });

  it('debe cargar vista previa via blob fetch autenticado para PDF', async () => {
    await act(async () => {
      render(<DocumentosViewer documentos={[mockDocumentos[0]]} />);
    });

    // After async preview loading, api.get is called with responseType: blob
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining('/view'),
        expect.objectContaining({ responseType: 'blob' })
      );
    });

    // Object URL is created from the blob
    await waitFor(() => {
      expect(URL.createObjectURL).toHaveBeenCalled();
    });
  });

  it('debe mostrar iframe para PDF en el inline viewer después de cargar preview', async () => {
    await act(async () => {
      render(<DocumentosViewer documentos={[mockDocumentos[0]]} />);
    });

    await waitFor(() => {
      const iframe = screen.queryByTitle(/Vista previa de incapacidad_medica.pdf/);
      expect(iframe).toBeInTheDocument();
    });
  });

  it('debe mostrar imagen para archivos JPG en el inline viewer', async () => {
    const user = userEvent.setup();
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    const radiografiaTab = screen.getByText('radiografia.jpg');
    await user.click(radiografiaTab);

    expect(screen.getByText('SOPORTE_MEDICO')).toBeInTheDocument();
  });

  it('debe usar blob fetch autenticado al descargar un documento con URL relativa', async () => {
    const user = userEvent.setup();

    // Simulate filesystem backend URL
    (incapacidadService.getDownloadUrl as ReturnType<typeof vi.fn>).mockResolvedValue(
      '/api/v1/storage/files/documentos/test.pdf'
    );

    await act(async () => {
      render(<DocumentosViewer documentos={[mockDocumentos[0]]} />);
    });

    const descargarBtn = screen.getByRole('button', { name: /Descargar/ });
    await user.click(descargarBtn);

    // api.get must be called with the storage URL and responseType: blob
    await waitFor(() => {
      const blobDownloadCalls = (api.get as ReturnType<typeof vi.fn>).mock.calls.filter(
        (call: any[]) =>
          typeof call[0] === 'string' &&
          call[0].includes('storage/files') &&
          call[1]?.responseType === 'blob'
      );
      expect(blobDownloadCalls.length).toBeGreaterThan(0);
    });
  });

  it('debe llamar a window.open para URLs presigned (MinIO)', async () => {
    const user = userEvent.setup();

    // Simulate MinIO presigned URL (absolute HTTPS — not a relative /api/ path)
    (incapacidadService.getDownloadUrl as ReturnType<typeof vi.fn>).mockResolvedValue(
      'https://minio.example.com/bucket/file.pdf?X-Amz-Signature=abc123'
    );

    const originalWindowOpen = window.open;
    window.open = vi.fn();

    await act(async () => {
      render(<DocumentosViewer documentos={[mockDocumentos[0]]} />);
    });

    const descargarBtn = screen.getByRole('button', { name: /Descargar/ });
    await user.click(descargarBtn);

    await waitFor(() => {
      expect(window.open).toHaveBeenCalledWith(
        'https://minio.example.com/bucket/file.pdf?X-Amz-Signature=abc123',
        '_blank'
      );
    });

    window.open = originalWindowOpen;
  });

  it('debe mostrar fechas de subida para cada documento', async () => {
    await act(async () => {
      render(<DocumentosViewer documentos={mockDocumentos} />);
    });

    const fechasSubida = screen.getAllByText(/Subido:/);
    expect(fechasSubida.length).toBeGreaterThan(0);
  });

  it('debe desabilitar botón de descarga mientras se está descargando', async () => {
    const user = userEvent.setup();

    // Make getDownloadUrl resolve slowly so we can observe the disabled state
    (incapacidadService.getDownloadUrl as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(resolve =>
        setTimeout(() => resolve('/api/v1/storage/files/test.pdf'), 300)
      )
    );

    await act(async () => {
      render(<DocumentosViewer documentos={[mockDocumentos[0]]} />);
    });

    const descargarBtn = screen.getByRole('button', { name: /Descargar/ });

    // Fire without awaiting so the button goes into loading state
    act(() => {
      user.click(descargarBtn);
    });

    await waitFor(() => {
      expect(descargarBtn).toBeDisabled();
    });
  });
});
