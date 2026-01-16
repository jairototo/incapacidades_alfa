import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ResumenRadicacionForm } from '../ResumenRadicacionForm';
import type { WizardFormData } from '../RadicarIncapacidadWizard';

describe('ResumenRadicacionForm', () => {
  const mockWizardDataARL: WizardFormData = {
    tipo: 'ARL',
    datosPersonales: {
      tipo: 'ARL' as const,
      tipo_documento: 'CC',
      numero_documento: '1234567890',
      nombres: 'Juan',
      apellidos: 'Pérez García',
      email: 'juan@example.com',
      telefono: '3001234567',
      empresa_id: '123e4567-e89b-12d3-a456-426614174000',
      empresa_nombre: 'Empresa Test S.A.',
      cargo: 'Desarrollador',
      fecha_ingreso: new Date('2020-01-15'),
      id: '123e4567-e89b-12d3-a456-426614174001',
    },
    datosIncapacidad: {
      tipo: 'ARL' as const,
      fecha_inicio: new Date('2026-01-10'),
      fecha_fin: new Date('2026-01-15'),
      dias_totales: 5,
      diagnostico_cie10: 'A00.1',
      descripcion_diagnostico: 'Diagnóstico de prueba',
      valor_dia: 50000,
      ips: 'IPS Test',
      tipo_enfermedad: 'ACCIDENTE_TRABAJO',
    },
    documentos: {
      incapacidad_medica: [
        new File(['content'], 'incapacidad.pdf', { type: 'application/pdf' }),
      ],
      historia_clinica: [
        new File(['content'], 'historia-clinica.pdf', { type: 'application/pdf' }),
      ],
      soportes_adicionales: [],
    },
  };

  const mockWizardDataSalud: WizardFormData = {
    tipo: 'SALUD',
    datosPersonales: {
      tipo: 'SALUD' as const,
      tipo_documento: 'CC',
      numero_documento: '9876543210',
      nombres: 'María',
      apellidos: 'González López',
      email: 'maria@example.com',
      telefono: '3109876543',
      numero_poliza: 'POL-2026-001',
      tipo_poliza: 'INDIVIDUAL',
    },
    datosIncapacidad: {
      tipo: 'SALUD' as const,
      fecha_inicio: new Date('2026-01-12'),
      fecha_fin: new Date('2026-01-20'),
      dias_totales: 8,
      diagnostico_cie10: 'B00.2',
      descripcion_diagnostico: 'Enfermedad general',
      valor_dia: 40000,
      eps: 'EPS Test',
      subtipo: 'ENFERMEDAD_GENERAL',
    },
    documentos: {
      incapacidad_medica: [],
      historia_clinica: [],
      soportes_adicionales: [],
    },
  };

  describe('Renderizado - Datos ARL', () => {
    it('debe renderizar el título y descripción', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Resumen de Radicación')).toBeInTheDocument();
      expect(
        screen.getByText(/Revise los datos antes de confirmar/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar el tipo de incapacidad ARL', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Tipo de Incapacidad')).toBeInTheDocument();
      expect(
        screen.getByText(/ARL - Administradora de Riesgos Laborales/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar los datos personales del empleado', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Datos Personales')).toBeInTheDocument();
      expect(screen.getByText(/Juan Pérez García/i)).toBeInTheDocument();
      expect(screen.getByText(/1234567890/i)).toBeInTheDocument();
      expect(screen.getByText(/juan@example.com/i)).toBeInTheDocument();
      expect(screen.getByText(/3001234567/i)).toBeInTheDocument();
    });

    it('debe mostrar campos específicos de ARL (empresa, cargo)', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Empresa Test S.A.')).toBeInTheDocument();
      expect(screen.getByText('Desarrollador')).toBeInTheDocument();
      // Verificar que existe una fecha de ingreso formateada
      const dateElements = screen.getAllByText(/\d{2}\/\d{2}\/\d{4}/);
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it('debe mostrar los datos de la incapacidad con fechas formateadas', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Datos de la Incapacidad')).toBeInTheDocument();
      // Fechas formateadas en español: dd/MM/yyyy
      const dateElements = screen.getAllByText(/\d{2}\/\d{2}\/\d{4}/);
      expect(dateElements.length).toBeGreaterThan(0);
      expect(screen.getByText(/5 días/i)).toBeInTheDocument();
      expect(screen.getByText(/A00.1/i)).toBeInTheDocument();
    });

    it('debe formatear correctamente el valor por día', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText(/\$50\.000/i)).toBeInTheDocument();
    });

    it('debe mostrar los documentos adjuntos con tamaño', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('Documentos Adjuntos')).toBeInTheDocument();
      expect(screen.getByText(/incapacidad.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/historia-clinica.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/Incapacidad Médica/i)).toBeInTheDocument();
    });
  });

  describe('Renderizado - Datos SALUD', () => {
    it('debe mostrar el tipo de incapacidad SALUD', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataSalud}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(
        screen.getByText(/SALUD - Incapacidad de Salud/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar campos específicos de SALUD (póliza)', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataSalud}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText('POL-2026-001')).toBeInTheDocument();
      expect(screen.getByText('Individual')).toBeInTheDocument();
    });

    it('debe mostrar mensaje cuando no hay documentos', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataSalud}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      expect(screen.getByText(/No se adjuntaron documentos/i)).toBeInTheDocument();
    });
  });

  describe('Interacciones', () => {
    it('debe llamar a onBack cuando se hace click en Volver', async () => {
      const user = userEvent.setup();
      const onBackMock = vi.fn();

      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={onBackMock}
          onSubmit={vi.fn()}
        />
      );

      const backButton = screen.getByRole('button', { name: /Volver/i });
      await user.click(backButton);

      expect(onBackMock).toHaveBeenCalledTimes(1);
    });

    it('debe llamar a onSubmit cuando se hace click en Confirmar y Radicar', async () => {
      const user = userEvent.setup();
      const onSubmitMock = vi.fn();

      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={onSubmitMock}
        />
      );

      const submitButton = screen.getByRole('button', {
        name: /Confirmar y Radicar/i,
      });
      await user.click(submitButton);

      expect(onSubmitMock).toHaveBeenCalledTimes(1);
    });

    it('debe deshabilitar botones cuando isSubmitting=true', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={true}
        />
      );

      const backButton = screen.getByRole('button', { name: /Volver/i });
      const submitButton = screen.getByRole('button', { name: /Procesando/i });

      expect(backButton).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('debe mostrar texto "Procesando..." cuando isSubmitting=true', () => {
      render(
        <ResumenRadicacionForm
          wizardData={mockWizardDataARL}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={true}
        />
      );

      expect(screen.getByText(/Procesando.../i)).toBeInTheDocument();
    });
  });

  describe('Formateo de datos', () => {
    it('debe mostrar "N/A" para fechas undefined', () => {
      const dataWithoutDates: WizardFormData = {
        ...mockWizardDataARL,
        datosIncapacidad: {
          ...mockWizardDataARL.datosIncapacidad!,
          fecha_inicio: undefined as any,
          fecha_fin: undefined as any,
        },
      };

      render(
        <ResumenRadicacionForm
          wizardData={dataWithoutDates}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      const naTexts = screen.getAllByText('N/A');
      expect(naTexts.length).toBeGreaterThan(0);
    });

    it('debe mostrar "No especificado" para campos opcionales vacíos', () => {
      const dataWithoutOptionals: WizardFormData = {
        ...mockWizardDataARL,
        datosPersonales: {
          ...mockWizardDataARL.datosPersonales!,
          email: undefined,
          telefono: undefined,
        },
      };

      render(
        <ResumenRadicacionForm
          wizardData={dataWithoutOptionals}
          onBack={vi.fn()}
          onSubmit={vi.fn()}
        />
      );

      const noSpecifiedTexts = screen.getAllByText('No especificado');
      expect(noSpecifiedTexts.length).toBeGreaterThanOrEqual(2);
    });
  });
});
