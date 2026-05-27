import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '../FileUpload';

describe('FileUpload', () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderizado básico', () => {
    it('debe renderizar el componente correctamente', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      
      expect(screen.getByText(/Selecciona archivos/)).toBeInTheDocument();
      expect(screen.getByText(/o arrástralos aquí/)).toBeInTheDocument();
    });

    it('debe mostrar el tamaño máximo permitido', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} maxSize={5 * 1024 * 1024} />);
      
      expect(screen.getByText(/5 MB/)).toBeInTheDocument();
    });

    it('debe tener input file oculto', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      
      const input = screen.getByLabelText('Seleccionar archivos');
      expect(input).toHaveClass('hidden');
      expect(input).toHaveAttribute('type', 'file');
    });

    it('debe aplicar className personalizado', () => {
      const { container } = render(
        <FileUpload onFileSelect={mockOnFileSelect} className="custom-class" />
      );
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Interacción con archivos', () => {
    it('debe abrir selector de archivos al hacer click', async () => {
      const user = userEvent.setup();
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      
      const dropzone = screen.getByText(/Selecciona archivos/).closest('div');
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      
      const clickSpy = vi.spyOn(input, 'click');
      
      if (dropzone) {
        await user.click(dropzone);
      }
      
      expect(clickSpy).toHaveBeenCalled();
    });

    it('debe aceptar archivos válidos', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      
      fireEvent.change(input, { target: { files: [file] } });
      
      expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
    });

    it('debe aceptar múltiples archivos cuando multiple=true', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} multiple={true} />);
      
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      const files = [
        new File(['content1'], 'test1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'test2.jpg', { type: 'image/jpeg' }),
      ];
      
      fireEvent.change(input, { target: { files } });
      
      expect(mockOnFileSelect).toHaveBeenCalledWith(files);
    });
  });

  describe('Validaciones', () => {
    it('debe rechazar archivos con tipo inválido', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      const file = new File(['content'], 'test.doc', { type: 'application/msword' });
      
      fireEvent.change(input, { target: { files: [file] } });
      
      expect(mockOnFileSelect).not.toHaveBeenCalled();
      expect(screen.getByText(/Tipo de archivo no permitido/)).toBeInTheDocument();
    });

    it('debe rechazar archivos que exceden tamaño máximo', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} maxSize={1000} />);
      
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      const content = 'a'.repeat(2000);
      const file = new File([content], 'test.pdf', { type: 'application/pdf' });
      
      fireEvent.change(input, { target: { files: [file] } });
      
      expect(mockOnFileSelect).not.toHaveBeenCalled();
      expect(screen.getByText(/excede el tamaño máximo/)).toBeInTheDocument();
    });

    it('debe rechazar más archivos que maxFiles', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} maxFiles={2} />);
      
      const input = screen.getByLabelText('Seleccionar archivos') as HTMLInputElement;
      const files = [
        new File(['1'], 'test1.pdf', { type: 'application/pdf' }),
        new File(['2'], 'test2.pdf', { type: 'application/pdf' }),
        new File(['3'], 'test3.pdf', { type: 'application/pdf' }),
      ];
      
      fireEvent.change(input, { target: { files } });
      
      expect(mockOnFileSelect).not.toHaveBeenCalled();
      expect(screen.getByText(/Solo se permiten hasta 2 archivos/)).toBeInTheDocument();
    });

    it('debe mostrar error prop si se proporciona', () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} error="Error personalizado" />);
      
      expect(screen.getByText('Error personalizado')).toBeInTheDocument();
    });
  });

  describe('Drag & Drop', () => {
    it('debe cambiar estilo al arrastrar archivos', () => {
      const { container } = render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const dropzone = container.querySelector('.border-dashed');
      
      if (dropzone) {
        fireEvent.dragEnter(dropzone);
        expect(dropzone).toHaveClass('border-blue-500');
        
        fireEvent.dragLeave(dropzone);
        expect(dropzone).not.toHaveClass('border-blue-500');
      }
    });

    it('debe aceptar archivos al soltar', () => {
      const { container } = render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const dropzone = container.querySelector('.border-dashed');
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      
      if (dropzone) {
        const dataTransfer = {
          files: [file],
        };
        
        fireEvent.drop(dropzone, { dataTransfer });
        
        expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
      }
    });
  });

  describe('Estado deshabilitado', () => {
    it('debe deshabilitar interacciones cuando disabled=true', async () => {
      const user = userEvent.setup();
      render(<FileUpload onFileSelect={mockOnFileSelect} disabled={true} />);
      
      const dropzone = screen.getByText(/Selecciona archivos/).closest('div');
      
      if (dropzone) {
        await user.click(dropzone);
      }
      
      expect(mockOnFileSelect).not.toHaveBeenCalled();
    });

    it('debe aplicar estilos de deshabilitado', () => {
      const { container } = render(<FileUpload onFileSelect={mockOnFileSelect} disabled={true} />);
      const dropzone = container.querySelector('.border-dashed');
      
      expect(dropzone).toHaveClass('opacity-50');
      expect(dropzone).toHaveClass('cursor-not-allowed');
    });
  });
});
