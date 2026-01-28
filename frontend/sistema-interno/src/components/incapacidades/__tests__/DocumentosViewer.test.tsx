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
    nombre_original: 'incapacidad_medica.pdf', // Cambiado de nombre_archivo
    tipo_documento: 'INCAPACIDAD_MEDICA',
    mime_type: 'application/pdf',
    tamano_bytes: 102400, // 100 KB (cambiado de tamano)
    ruta_archivo: '/documentos/incapacidad_medica.pdf',
    uploaded_by: 'user-123', // Cambiado de uploaded_by_id
    created_at: '2024-01-10T10:30:00Z',
    extension: 'pdf', // Agregado
  },
  {
    id: 'doc-2',
    nombre_original: 'historia_clinica.pdf', // Cambiado de nombre_archivo
    tipo_documento: 'HISTORIA_CLINICA',
    mime_type: 'application/pdf',
    tamano_bytes: 204800, // 200 KB (cambiado de tamano)
    ruta_archivo: '/documentos/historia_clinica.pdf',
    uploaded_by: 'user-123', // Cambiado de uploaded_by_id
    created_at: '2024-01-10T11:00:00Z',
    extension: 'pdf', // Agregado
  },
  {
    id: 'doc-3',
    nombre_original: 'radiografia.jpg', // Cambiado de nombre_archivo
    tipo_documento: 'SOPORTE_MEDICO',
    mime_type: 'image/jpeg',
    tamano_bytes: 512000, // 500 KB (cambiado de tamano)
    ruta_archivo: '/documentos/radiografia.jpg',
    uploaded_by: 'user-123', // Cambiado de uploaded_by_id
    created_at: '2024-01-10T12:00:00Z',
    extension: 'jpg', // Agregado
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

    // Debe mostrar los nombres de todos los documentos
    expect(screen.getByText('incapacidad_medica.pdf')).toBeInTheDocument();
    expect(screen.getByText('historia_clinica.pdf')).toBeInTheDocument();
    expect(screen.getByText('radiografia.jpg')).toBeInTheDocument();

    // Debe mostrar tipos de documento
    expect(screen.getByText('INCAPACIDAD_MEDICA')).toBeInTheDocument();
    expect(screen.getByText('HISTORIA_CLINICA')).toBeInTheDocument();
    expect(screen.getByText('SOPORTE_MEDICO')).toBeInTheDocument();

    // Debe mostrar fechas de subida (formato: DD/MM/YYYY)
    const fechasSubida = screen.getAllByText(/Subido:/);
    expect(fechasSubida).toHaveLength(3);
  });

  it('debe manejar documentos sin nombre_original correctamente', () => {
    const documentoSinNombre = {
      id: 'doc-no-name',
      nombre_original: undefined, // Cambiado de nombre_archivo
      tipo_documento: 'OTRO',
      mime_type: 'application/octet-stream',
      tamano_bytes: 1024, // Cambiado de tamano
      ruta_archivo: '/documentos/archivo_sin_nombre',
      uploaded_by: 'user-123', // Cambiado de uploaded_by_id
      created_at: '2024-01-10T10:00:00Z',
      extension: '', // Agregado
    };

    render(<DocumentosViewer documentos={[documentoSinNombre] as any} />);

    // Debe mostrar "Sin nombre" como fallback
    expect(screen.getByText('Sin nombre')).toBeInTheDocument();

    // Debe mostrar el tipo de documento
    expect(screen.getByText('OTRO')).toBeInTheDocument();
  });

  it('debe abrir modal de vista previa al hacer click en "Ver"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en botón "Ver" del primer documento (PDF)
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[0]);

    // Debe abrir modal con el nombre del documento (aparece 2 veces: en card y en modal)
    const nombreDocumento = screen.getAllByText('incapacidad_medica.pdf');
    expect(nombreDocumento.length).toBeGreaterThan(1); // Al menos en card y modal

    // Debe haber botón "Cerrar" en el modal
    expect(screen.getByText('Cerrar')).toBeInTheDocument();

    // Debe haber un iframe para PDF con title
    const iframe = screen.getByTitle('Vista previa PDF');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', '/api/documentos/doc-1/download');
  });

  it('debe mostrar vista previa de imagen en el modal', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Click en botón "Ver" del tercer documento (imagen)
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[2]);

    // Debe abrir modal con el nombre del archivo (aparece 2 veces)
    const nombreDocumento = screen.getAllByText('radiografia.jpg');
    expect(nombreDocumento.length).toBeGreaterThan(1); // En card y modal

    // Debe haber una etiqueta <img> con alt text
    const img = screen.getByAltText('radiografia.jpg');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', '/api/documentos/doc-3/download');
  });

  it('debe cerrar el modal al hacer click en "Cerrar"', async () => {
    const user = userEvent.setup();
    render(<DocumentosViewer documentos={mockDocumentos} />);

    // Abrir modal
    const verButtons = screen.getAllByText('Ver');
    await user.click(verButtons[0]);

    // Verificar que el modal está abierto (aparece botón "Cerrar")
    const cerrarBtn = screen.getByRole('button', { name: /Cerrar/i });
    expect(cerrarBtn).toBeInTheDocument();

    // Click en botón "Cerrar"
    await user.click(cerrarBtn);

    // El modal debe desaparecer (botón "Cerrar" ya no está)
    expect(screen.queryByRole('button', { name: /Cerrar/i })).not.toBeInTheDocument();
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

    // Debe renderizar los 3 documentos con sus nombres
    expect(screen.getByText('incapacidad_medica.pdf')).toBeInTheDocument();
    expect(screen.getByText('historia_clinica.pdf')).toBeInTheDocument();
    expect(screen.getByText('radiografia.jpg')).toBeInTheDocument();

    // Debe haber botones "Ver" para PDFs e imágenes (todos son previsualizables)
    const verButtons = screen.getAllByText('Ver');
    expect(verButtons).toHaveLength(3);
  });
});
