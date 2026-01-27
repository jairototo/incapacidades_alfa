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
    nombre_archivo: 'incapacidad_medica.pdf',
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano: 102400, // 100 KB
    ruta_archivo: '/documentos/incapacidad_medica.pdf',
    uploaded_by_id: 'user-123',
    created_at: '2024-01-10T10:30:00Z',
  },
  {
    id: 'doc-2',
    nombre_archivo: 'historia_clinica.pdf',
    tipo_documento: 'HISTORIA_CLINICA',
    mime_type: 'application/pdf',
    tamano: 204800, // 200 KB
    ruta_archivo: '/documentos/historia_clinica.pdf',
    uploaded_by_id: 'user-123',
    created_at: '2024-01-10T11:00:00Z',
  },
  {
    id: 'doc-3',
    nombre_archivo: 'radiografia.jpg',
    tipo_documento: 'SOPORTE_MEDICO',
    mime_type: 'image/jpeg',
    tamano: 512000, // 500 KB
    ruta_archivo: '/documentos/radiografia.jpg',
    uploaded_by_id: 'user-123',
    created_at: '2024-01-10T12:00:00Z',
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

  it('debe renderizar grid de documentos con información correcta', () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Título
    expect(screen.getByText('Documentos Adjuntos')).toBeInTheDocument();
    expect(screen.getByText('3 archivos')).toBeInTheDocument();

    // Debe mostrar todos los documentos
    expect(screen.getByText('incapacidad_medica.pdf')).toBeInTheDocument();
    expect(screen.getByText('historia_clinica.pdf')).toBeInTheDocument();
    expect(screen.getByText('radiografia.jpg')).toBeInTheDocument();

    // Debe mostrar tamaños formateados
    expect(screen.getByText('100.00 KB')).toBeInTheDocument();
    expect(screen.getByText('200.00 KB')).toBeInTheDocument();
    expect(screen.getByText('500.00 KB')).toBeInTheDocument();

    // Debe mostrar tipos de documento
    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();
    expect(screen.getByText('HISTORIA_CLINICA')).toBeInTheDocument();
    expect(screen.getByText('SOPORTE_MEDICO')).toBeInTheDocument();
  });

  it('debe manejar documentos sin nombre_archivo correctamente', () => {
    const documentoSinNombre = {
      id: 'doc-no-name',
      nombre_archivo: undefined,
      tipo_documento: 'OTRO',
      mime_type: 'application/octet-stream',
      tamano: 1024,
      ruta_archivo: '/documentos/archivo_sin_nombre',
      uploaded_by_id: 'user-123',
      created_at: '2024-01-10T10:00:00Z',
    };

    render(<DocumentosViewer documentos={[documentoSinNombre]} />);

    // Debe mostrar "Sin nombre" como fallback
    expect(screen.getByText('Sin nombre')).toBeInTheDocument();

    // No debe romper el componente
    expect(screen.getByText('Documentos Adjuntos')).toBeInTheDocument();
  });

  it('debe abrir modal de vista previa al hacer click en "Ver"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en botón "Ver" del primer documento (PDF)
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[0]);

    // Debe abrir modal con el título del documento
    expect(screen.getByText(/Vista Previa/)).toBeInTheDocument();
    expect(screen.getByText('incapacidad_medica.pdf')).toBeInTheDocument();

    // Debe haber un iframe para PDF
    const iframe = document.querySelector('iframe');
    expect(iframe).toBeInTheDocument();
    expect(iframe?.src).toContain('/api/documentos/doc-1/download');
  });

  it('debe mostrar vista previa de imagen en el modal', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en botón "Ver" del tercer documento (imagen)
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[2]);

    // Debe abrir modal con imagen
    expect(screen.getByText('radiografia.jpg')).toBeInTheDocument();

    // Debe haber una etiqueta <img>
    const img = document.querySelector('img[alt*="Documento"]');
    expect(img).toBeInTheDocument();
    expect(img?.src).toContain('/api/documentos/doc-3/download');
  });

  it('debe cerrar el modal al hacer click en "Cerrar"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Abrir modal
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[0]);

    // Verificar que el modal está abierto
    expect(screen.getByText(/Vista Previa/)).toBeInTheDocument();

    // Click en botón "Cerrar"
    const cerrarBtn = screen.getByRole('button', { name: /Cerrar/i });
    await user.click(cerrarBtn);

    // El modal debe desaparecer
    expect(screen.queryByText(/Vista Previa/)).not.toBeInTheDocument();
  });

  it('debe llamar a getDownloadUrl al hacer click en "Descargar"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Simular click en "Descargar"
    const descargarButtons = screen.getAllByText('Descargar');
    
    // Mockear window.open
    const originalWindowOpen = window.open;
    window.open = vi.fn();

    await user.click(descargarButtons[0]);

    // Verificar que se llamó a getDownloadUrl
    expect(incapacidadService.getDownloadUrl).toHaveBeenCalledWith('doc-1');

    // Verificar que se intentó abrir la URL
    expect(window.open).toHaveBeenCalledWith('/api/documentos/doc-1/download', '_blank');

    // Restaurar window.open
    window.open = originalWindowOpen;
  });

  it('debe mostrar iconos diferentes según el tipo de archivo', () => {
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Debe haber iconos de archivo (no vamos a verificar el ícono exacto, pero sí que se renderice)
    const cards = screen.getAllByRole('article'); // Las Cards suelen tener role="article"
    expect(cards.length).toBe(3);
  });
});
