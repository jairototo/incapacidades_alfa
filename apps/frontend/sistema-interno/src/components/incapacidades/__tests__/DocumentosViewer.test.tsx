import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentosViewer } from '../DocumentosViewer';
import { incapacidadService } from '@/services/incapacidadService';

// Mock del servicio
vi.mock('@/services/incapacidadService', () => ({
  incapacidadService: {
    getDownloadUrl: vi.fn((id) => `/api/documentos/${id}/download`),
  },
}));

const mockDocumentos = [
  {
    id: 'doc-1',
    nombre_original: 'incapacidad_medica.pdf',
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano_bytes: 102400,
    ruta_archivo: '/documentos/incapacidad_medica.pdf',
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
    ruta_archivo: '/documentos/historia_clinica.pdf',
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
    ruta_archivo: '/documentos/radiografia.jpg',
    uploaded_by: 'user-123',
    created_at: '2024-01-10T12:00:00Z',
    extension: 'jpg',
  },
];

describe('DocumentosViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debe renderizar mensaje de "Sin documentos" cuando el array está vacío', () => {
    render(<DocumentosViewer documentos={[]} />);

    expect(
      screen.getByText(/No hay documentos adjuntos a esta incapacidad/)
    ).toBeInTheDocument();
  });

  it('debe renderizar tabs horizontales con todos los documentos', () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Debe mostrar los nombres de todos los documentos en los tabs (aparecen múltiples veces)
    expect(screen.getAllByText('incapacidad_medica.pdf').length).toBeGreaterThan(0);
    expect(screen.getAllByText('historia_clinica.pdf').length).toBeGreaterThan(0);
    expect(screen.getAllByText('radiografia.jpg').length).toBeGreaterThan(0);
  });

  it('debe auto-seleccionar el primer documento al montar', () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // El primer documento debe estar seleccionado (mostrar su tipo de documento)
    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();
    // El nombre debe aparecer al menos en el tab
    expect(screen.getAllByText('incapacidad_medica.pdf').length).toBeGreaterThan(0);
  });

  it('debe cambiar la vista al seleccionar un tab diferente', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Inicialmente debe mostrar el primer documento
    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();

    // Click en el tab del segundo documento (PDF)
    const historiaTab = screen.getByText('historia_clinica.pdf');
    await user.click(historiaTab);

    // Debe mostrar información del segundo documento
    expect(screen.getByText('HISTORIA_CLINICA')).toBeInTheDocument();
  });

  it('debe cambiar a vista de imagen al seleccionar un documento de imagen', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en el tab de la imagen
    const radiografiaTab = screen.getByText('radiografia.jpg');
    await user.click(radiografiaTab);

    // Debe mostrar información del documento de imagen
    expect(screen.getByText('SOPORTE_MEDICO')).toBeInTheDocument();
  });

  it('debe manejar documentos sin nombre_original correctamente', () => {
    const documentoSinNombre = {
      id: 'doc-no-name',
      nombre_original: undefined,
      tipo_documento: 'OTRO',
      mime_type: 'application/octet-stream',
      tamano_bytes: 1024,
      ruta_archivo: '/documentos/archivo_sin_nombre',
      uploaded_by: 'user-123',
      created_at: '2024-01-10T10:00:00Z',
      extension: '',
    };

    render(<DocumentosViewer documentos={[documentoSinNombre] as any} />);

    // Debe mostrar "Sin nombre" como fallback (aparece en tab + info header)
    expect(screen.getAllByText('Sin nombre').length).toBeGreaterThan(0);

    // Debe mostrar el tipo de documento
    expect(screen.getByText('OTRO')).toBeInTheDocument();
  });

  it('debe mostrar iframe para PDF en el inline viewer', async () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // El primer documento es PDF, debe mostrar iframe
    const iframe = screen.getByTitle(/Vista previa de incapacidad_medica.pdf/);
    expect(iframe).toBeInTheDocument();
  });

  it('debe mostrar imagen para archivos JPG en el inline viewer', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en el tab de la imagen
    const radiografiaTab = screen.getByText('radiografia.jpg');
    await user.click(radiografiaTab);

    // Debe haber una etiqueta <img>
    const img = screen.getByAltText('radiografia.jpg');
    expect(img).toBeInTheDocument();
  });

  it('debe llamar a getDownloadUrl al hacer click en "Descargar"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Mockear window.open
    const originalWindowOpen = window.open;
    window.open = vi.fn();

    // Click en botón "Descargar"
    const descargarBtn = screen.getByRole('button', { name: /Descargar/ });
    await user.click(descargarBtn);

    // Verificar que se llamó a getDownloadUrl
    expect(incapacidadService.getDownloadUrl).toHaveBeenCalledWith('doc-1');

    // Verificar que se intentó abrir la URL
    expect(window.open).toHaveBeenCalledWith('/api/documentos/doc-1/download', '_blank');

    // Restaurar window.open
    window.open = originalWindowOpen;
  });

  it('debe mostrar fechas de subida para cada documento', () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Debe mostrar fechas de subida (formato: DD/MM/YYYY)
    const fechasSubida = screen.getAllByText(/Subido:/);
    expect(fechasSubida.length).toBeGreaterThan(0);
  });

  it('debe desabilitar botón de descarga mientras se está descargando', async () => {
    const user = userEvent.setup();

    // Mock getDownloadUrl para que se demore
    (incapacidadService.getDownloadUrl as any).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve('/download-url'), 100))
    );

    render(<DocumentosViewer documentos={mockDocumentos} />);

    const descargarBtn = screen.getByRole('button', { name: /Descargar/ });

    // Click en botón
    await user.click(descargarBtn);

    // Debe estar deshabilitado mientras se descarga
    expect(descargarBtn).toBeDisabled();
  });
});
