import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilePreview, FileList } from '../FilePreview';

describe('FilePreview', () => {
  const mockOnRemove = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderizado básico', () => {
    it('debe renderizar información del archivo PDF', () => {
      const file = new File(['content'], 'documento.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} />);
      
      expect(screen.getByText('documento.pdf')).toBeInTheDocument();
    });

    it('debe renderizar información de archivo de imagen', () => {
      const file = new File(['content'], 'imagen.jpg', { type: 'image/jpeg' });
      render(<FilePreview file={file} />);
      
      expect(screen.getByText('imagen.jpg')).toBeInTheDocument();
    });

    it('debe formatear el tamaño del archivo', () => {
      const file = new File(['a'.repeat(1024)], 'test.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} />);
      
      expect(screen.getByText(/KB/)).toBeInTheDocument();
    });

    it('debe aplicar className personalizado', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const { container } = render(<FilePreview file={file} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Botón eliminar', () => {
    it('debe mostrar botón eliminar por defecto', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} onRemove={mockOnRemove} />);
      
      expect(screen.getByLabelText('Eliminar archivo')).toBeInTheDocument();
    });

    it('debe ocultar botón eliminar cuando showRemove=false', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} onRemove={mockOnRemove} showRemove={false} />);
      
      expect(screen.queryByLabelText('Eliminar archivo')).not.toBeInTheDocument();
    });

    it('debe llamar onRemove al hacer click en eliminar', async () => {
      const user = userEvent.setup();
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} onRemove={mockOnRemove} />);
      
      const removeButton = screen.getByLabelText('Eliminar archivo');
      await user.click(removeButton);
      
      expect(mockOnRemove).toHaveBeenCalledTimes(1);
    });

    it('no debe mostrar botón si no hay onRemove', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      render(<FilePreview file={file} />);
      
      expect(screen.queryByLabelText('Eliminar archivo')).not.toBeInTheDocument();
    });
  });

  describe('Iconos por tipo de archivo', () => {
    it('debe mostrar ícono de PDF para archivos PDF', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const { container } = render(<FilePreview file={file} />);
      
      const icon = container.querySelector('.bg-red-100');
      expect(icon).toBeInTheDocument();
    });

    it('debe mostrar ícono de imagen para archivos de imagen', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      const { container } = render(<FilePreview file={file} />);
      
      const icon = container.querySelector('.bg-blue-100');
      expect(icon).toBeInTheDocument();
    });
  });
});

describe('FileList', () => {
  const mockOnRemove = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderizado básico', () => {
    it('debe mostrar mensaje cuando no hay archivos', () => {
      render(<FileList files={[]} />);
      
      expect(screen.getByText('No hay archivos cargados')).toBeInTheDocument();
    });

    it('debe mostrar mensaje personalizado cuando está vacío', () => {
      render(<FileList files={[]} emptyMessage="Sin documentos" />);
      
      expect(screen.getByText('Sin documentos')).toBeInTheDocument();
    });

    it('debe renderizar lista de archivos', () => {
      const files = [
        new File(['content1'], 'archivo1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'archivo2.jpg', { type: 'image/jpeg' }),
      ];
      
      render(<FileList files={files} />);
      
      expect(screen.getByText('archivo1.pdf')).toBeInTheDocument();
      expect(screen.getByText('archivo2.jpg')).toBeInTheDocument();
    });

    it('debe aplicar className personalizado', () => {
      const files = [new File(['content'], 'test.pdf', { type: 'application/pdf' })];
      const { container } = render(<FileList files={files} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Eliminación de archivos', () => {
    it('debe llamar onRemove con índice correcto', async () => {
      const user = userEvent.setup();
      const files = [
        new File(['content1'], 'archivo1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'archivo2.jpg', { type: 'image/jpeg' }),
      ];
      
      render(<FileList files={files} onRemove={mockOnRemove} />);
      
      const removeButtons = screen.getAllByLabelText('Eliminar archivo');
      await user.click(removeButtons[1]);
      
      expect(mockOnRemove).toHaveBeenCalledWith(1);
    });

    it('debe ocultar botones eliminar cuando showRemove=false', () => {
      const files = [new File(['content'], 'test.pdf', { type: 'application/pdf' })];
      render(<FileList files={files} onRemove={mockOnRemove} showRemove={false} />);
      
      expect(screen.queryByLabelText('Eliminar archivo')).not.toBeInTheDocument();
    });
  });
});
