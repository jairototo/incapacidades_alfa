import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentosForm } from '../DocumentosForm';

describe('DocumentosForm', () => {
  const mockOnBack = vi.fn();
  const mockOnContinue = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderizado básico', () => {
    it('debe renderizar el formulario correctamente', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText('Documentos')).toBeInTheDocument();
      expect(screen.getByText(/Adjunte los documentos requeridos/)).toBeInTheDocument();
    });

    it('debe mostrar sección de incapacidad médica como requerida', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText(/Incapacidad Médica/)).toBeInTheDocument();
      expect(screen.getByText(/1 archivo requerido/)).toBeInTheDocument();
    });

    it('debe mostrar secciones opcionales', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText(/Historia Clínica/)).toBeInTheDocument();
      expect(screen.getAllByText(/Opcional/).length).toBeGreaterThan(0);
      expect(screen.getByText(/Soportes Adicionales/)).toBeInTheDocument();
    });

    it('debe mostrar descripción específica para ARL en soportes', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText(/siniestro, accidente laboral/)).toBeInTheDocument();
    });

    it('debe mostrar descripción específica para SALUD en soportes', () => {
      render(
        <DocumentosForm
          tipo="SALUD"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText(/Exámenes médicos, fórmulas/)).toBeInTheDocument();
    });
  });

  describe('Carga de archivos', () => {
    it('debe permitir cargar incapacidad médica', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const fileInputs = screen.getAllByLabelText('Seleccionar archivos');
      const file = new File(['content'], 'incapacidad.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInputs[0], { target: { files: [file] } });
      
      expect(screen.getByText('incapacidad.pdf')).toBeInTheDocument();
    });

    it('debe ocultar FileUpload después de cargar incapacidad médica', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const fileInputs = screen.getAllByLabelText('Seleccionar archivos');
      const initialCount = fileInputs.length;
      const file = new File(['content'], 'incapacidad.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInputs[0], { target: { files: [file] } });
      
      const updatedInputs = screen.getAllByLabelText('Seleccionar archivos');
      expect(updatedInputs.length).toBeLessThan(initialCount);
    });

    it('debe permitir eliminar archivo de incapacidad médica', async () => {
      const user = userEvent.setup();
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const fileInput = screen.getAllByLabelText('Seleccionar archivos')[0];
      const file = new File(['content'], 'incapacidad.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [file] } });
      
      const removeButton = screen.getByLabelText('Eliminar archivo');
      await user.click(removeButton);
      
      expect(screen.queryByText('incapacidad.pdf')).not.toBeInTheDocument();
    });
  });

  describe('Navegación', () => {
    it('debe tener botón Atrás', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByRole('button', { name: /Atrás/i })).toBeInTheDocument();
    });

    it('debe tener botón Continuar', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByRole('button', { name: /Continuar/i })).toBeInTheDocument();
    });

    it('debe llamar onBack al hacer click en Atrás', async () => {
      const user = userEvent.setup();
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const backButton = screen.getByRole('button', { name: /Atrás/i });
      await user.click(backButton);
      
      expect(mockOnBack).toHaveBeenCalledTimes(1);
    });

    it('debe deshabilitar botón Continuar si no hay incapacidad médica', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const continueButton = screen.getByRole('button', { name: /Continuar/i });
      expect(continueButton).toBeDisabled();
    });

    it('debe habilitar botón Continuar con incapacidad médica cargada', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      const fileInput = screen.getAllByLabelText('Seleccionar archivos')[0];
      const file = new File(['content'], 'incapacidad.pdf', { type: 'application/pdf' });
      
      fireEvent.change(fileInput, { target: { files: [file] } });
      
      const continueButton = screen.getByRole('button', { name: /Continuar/i });
      expect(continueButton).not.toBeDisabled();
    });
  });

  describe('Datos iniciales', () => {
    it('debe cargar archivos iniciales', () => {
      const initialData = {
        incapacidad_medica: [
          new File(['content'], 'inicial.pdf', { type: 'application/pdf' }),
        ],
        historia_clinica: [],
        soportes_adicionales: [],
      };
      
      render(
        <DocumentosForm
          tipo="ARL"
          initialData={initialData}
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      expect(screen.getByText('inicial.pdf')).toBeInTheDocument();
    });
  });

  describe('Múltiples archivos en secciones opcionales', () => {
    it('debe permitir cargar múltiples archivos en historia clínica', () => {
      render(
        <DocumentosForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );
      
      // Primero cargar incapacidad médica para habilitar otras secciones
      const fileInputs = screen.getAllByLabelText('Seleccionar archivos');
      const file1 = new File(['content1'], 'historia1.pdf', { type: 'application/pdf' });
      const file2 = new File(['content2'], 'historia2.pdf', { type: 'application/pdf' });
      
      // Cargar primer archivo en historia clínica (segundo input)
      fireEvent.change(fileInputs[1], { target: { files: [file1, file2] } });
      
      expect(screen.getByText('historia1.pdf')).toBeInTheDocument();
      expect(screen.getByText('historia2.pdf')).toBeInTheDocument();
    });
  });
});
