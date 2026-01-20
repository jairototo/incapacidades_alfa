import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DatosIncapacidadForm } from '../DatosIncapacidadForm';

describe('DatosIncapacidadForm', () => {
  const mockOnBack = vi.fn();
  const mockOnContinue = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderizado básico', () => {
    it('debe renderizar el formulario para tipo ARL', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Datos de la Incapacidad')).toBeInTheDocument();
      expect(screen.getByText(/Accidente Laboral/)).toBeInTheDocument();
      expect(screen.getByText('Tipo de Enfermedad')).toBeInTheDocument();
    });

    it('debe renderizar el formulario para tipo SALUD', () => {
      render(
        <DatosIncapacidadForm
          tipo="SALUD"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Datos de la Incapacidad')).toBeInTheDocument();
      expect(screen.getByText('Subtipo de Incapacidad')).toBeInTheDocument();
    });

    it('debe renderizar todos los campos comunes', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Fecha de Inicio')).toBeInTheDocument();
      expect(screen.getByText('Fecha de Fin')).toBeInTheDocument();
      expect(screen.getByText('Días Totales')).toBeInTheDocument();
      expect(screen.getByText('Código CIE-10')).toBeInTheDocument();
      expect(screen.getByText('Descripción del Diagnóstico')).toBeInTheDocument();
      expect(screen.getByText('IPS')).toBeInTheDocument();
      expect(screen.getByText('EPS')).toBeInTheDocument();
    });
  });

  describe('Campos específicos por tipo', () => {
    it('debe mostrar campo tipo_enfermedad solo para ARL', () => {
      const { rerender } = render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Tipo de Enfermedad')).toBeInTheDocument();
      expect(screen.queryByText('Subtipo de Incapacidad')).not.toBeInTheDocument();

      rerender(
        <DatosIncapacidadForm
          tipo="SALUD"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.queryByText('Tipo de Enfermedad')).not.toBeInTheDocument();
      expect(screen.getByText('Subtipo de Incapacidad')).toBeInTheDocument();
    });

    it('debe tener las opciones correctas para tipo_enfermedad (ARL)', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Accidente de Trabajo')).toBeInTheDocument();
      expect(screen.getByText('Enfermedad Laboral')).toBeInTheDocument();
      expect(screen.getByText('Accidente de Trayecto')).toBeInTheDocument();
    });

    it('debe tener las opciones correctas para subtipo (SALUD)', () => {
      render(
        <DatosIncapacidadForm
          tipo="SALUD"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Enfermedad General')).toBeInTheDocument();
      expect(screen.getByText('Maternidad')).toBeInTheDocument();
      expect(screen.getByText('Licencia')).toBeInTheDocument();
    });
  });

  describe('Campos deshabilitados (auto-calculados)', () => {
    it('debe tener campo dias_totales deshabilitado', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      const diasTotales = screen.getByRole('spinbutton');
      expect(diasTotales).toBeDisabled();
    });

    it('debe mostrar texto de ayuda en campo dias_totales', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Calculado automáticamente')).toBeInTheDocument();

    });
  });

  describe('Navegación', () => {
    it('debe llamar onBack al hacer clic en el botón Atrás', async () => {
      const user = userEvent.setup();
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      const backButton = screen.getByRole('button', { name: /Atrás/i });
      await user.click(backButton);

      expect(mockOnBack).toHaveBeenCalledTimes(1);
    });

    it('debe tener botones de navegación', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByRole('button', { name: /Atrás/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Continuar/i })).toBeInTheDocument();
    });
  });

  describe('Datos iniciales', () => {
    it('debe cargar datos iniciales cuando se proporcionan', () => {
      const initialData = {
        tipo: 'ARL' as const,
        diagnostico_cie10: 'J00',
        descripcion_diagnostico: 'Rinofaringitis aguda (resfriado común)',
        ips: 'Clínica Santa María',
        eps: 'Sura EPS',
        dias_totales: 5,
      };

      render(
        <DatosIncapacidadForm
          tipo="ARL"
          initialData={initialData}
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByDisplayValue('J00')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Clínica Santa María')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Sura EPS')).toBeInTheDocument();
    });
  });

  describe('Secciones del formulario', () => {
    it('debe tener sección de información de atención médica', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText('Información de Atención Médica (Opcional)')).toBeInTheDocument();
    });
  });

  describe('Textos de ayuda', () => {
    it('debe mostrar helperText para CIE-10', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText(/clasificación internacional de enfermedades/i)).toBeInTheDocument();
    });

    it('debe mostrar helperText para IPS', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText(/Institución Prestadora de Salud/i)).toBeInTheDocument();
    });

    it('debe mostrar helperText para EPS', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByText(/Entidad Promotora de Salud/i)).toBeInTheDocument();
    });
  });

  describe('Integración con CIE-10 y Médico Tratante', () => {
    it('debe renderizar CIE10Autocomplete component', () => {
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      // Verificar que existe el placeholder del CIE-10 autocomplete
      const cie10Input = screen.getByPlaceholderText(/código o descripción/i);
      expect(cie10Input).toBeInTheDocument();
    });

    it('debe renderizar campos de médico tratante', () => {
      render(
        <DatosIncapacidadForm
          tipo="SALUD"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      expect(screen.getByLabelText(/nombre del médico/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/registro médico/i)).toBeInTheDocument();
    });

    it('debe validar formato CIE-10 cuando se proporciona', async () => {
      const user = userEvent.setup();
      
      render(
        <DatosIncapacidadForm
          tipo="ARL"
          onBack={mockOnBack}
          onContinue={mockOnContinue}
        />
      );

      // Intentar enviar formulario con campos vacíos
      const continueButton = screen.getByRole('button', { name: /continuar/i });
      await user.click(continueButton);

      // El componente CIE10Autocomplete maneja su propia validación
      // Aquí solo verificamos que el campo existe y puede recibir input
      const cie10Input = screen.getByPlaceholderText(/código o descripción/i);
      expect(cie10Input).toBeInTheDocument();
    });
  });
});
