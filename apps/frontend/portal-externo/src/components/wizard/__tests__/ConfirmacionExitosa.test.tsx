import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ConfirmacionExitosa } from '../ConfirmacionExitosa';

describe('ConfirmacionExitosa', () => {
  const mockNumeroRadicacion = 'INC-ARL-2026-001234';

  describe('Renderizado', () => {
    it('debe renderizar el mensaje de éxito', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(
        screen.getByText(/¡Incapacidad radicada exitosamente!/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Su solicitud ha sido recibida/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar el icono de éxito (CheckCircle)', () => {
      const { container } = render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      // Verificar que existe un elemento con clase relacionada al icono
      const iconContainer = container.querySelector('.bg-green-100');
      expect(iconContainer).toBeInTheDocument();
    });

    it('debe mostrar el número de radicación destacado', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(screen.getByText(mockNumeroRadicacion)).toBeInTheDocument();
      const radicacionTexts = screen.getAllByText(/radicación/i);
      expect(radicacionTexts.length).toBeGreaterThan(0);
    });

    it('debe mostrar el timeline estimado del proceso', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(screen.getByText('Proceso estimado')).toBeInTheDocument();
      expect(screen.getByText('Radicada')).toBeInTheDocument();
      expect(screen.getByText('En auditoría')).toBeInTheDocument();
      expect(screen.getByText('Aprobación')).toBeInTheDocument();
      expect(screen.getByText('Pago')).toBeInTheDocument();

      // Verificar tiempos estimados
      expect(screen.getByText('Hoy')).toBeInTheDocument();
      expect(screen.getByText(/1-2 días hábiles/i)).toBeInTheDocument();
      expect(screen.getByText(/3-5 días hábiles/i)).toBeInTheDocument();
      expect(screen.getByText(/5-10 días hábiles/i)).toBeInTheDocument();
    });

    it('debe mostrar información importante', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(screen.getByText('Importante')).toBeInTheDocument();
      expect(
        screen.getByText(/Conserve el número de radicación/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Recibirá notificaciones por email/i)
      ).toBeInTheDocument();
    });

    it('debe mostrar botón "Radicar otra Incapacidad"', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(
        screen.getByRole('button', { name: /Radicar otra Incapacidad/i })
      ).toBeInTheDocument();
    });

    it('debe mostrar botón "Consultar Estado" si se proporciona callback', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
          onConsultarEstado={vi.fn()}
        />
      );

      expect(
        screen.getByRole('button', { name: /Consultar Estado/i })
      ).toBeInTheDocument();
    });

    it('NO debe mostrar botón "Consultar Estado" si no se proporciona callback', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(
        screen.queryByRole('button', { name: /Consultar Estado/i })
      ).not.toBeInTheDocument();
    });

    it('debe mostrar nota sobre descarga de comprobante (Fase 2)', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
        />
      );

      expect(
        screen.getByText(/comprobante PDF estará disponible próximamente/i)
      ).toBeInTheDocument();
    });
  });

  describe('Interacciones', () => {
    it('debe llamar a onRadicarOtra cuando se hace click en el botón', async () => {
      const user = userEvent.setup();
      const onRadicarOtraMock = vi.fn();

      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={onRadicarOtraMock}
        />
      );

      const button = screen.getByRole('button', {
        name: /Radicar otra Incapacidad/i,
      });
      await user.click(button);

      expect(onRadicarOtraMock).toHaveBeenCalledTimes(1);
    });

    it('debe llamar a onConsultarEstado cuando se hace click en el botón', async () => {
      const user = userEvent.setup();
      const onConsultarEstadoMock = vi.fn();

      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
          onConsultarEstado={onConsultarEstadoMock}
        />
      );

      const button = screen.getByRole('button', { name: /Consultar Estado/i });
      await user.click(button);

      expect(onConsultarEstadoMock).toHaveBeenCalledTimes(1);
    });
  });

  describe('Diferentes números de radicación', () => {
    it('debe renderizar correctamente con número ARL', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion="INC-ARL-2026-999999"
          onRadicarOtra={vi.fn()}
        />
      );

      expect(screen.getByText('INC-ARL-2026-999999')).toBeInTheDocument();
    });

    it('debe renderizar correctamente con número SALUD', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion="INC-SALUD-2026-123456"
          onRadicarOtra={vi.fn()}
        />
      );

      expect(screen.getByText('INC-SALUD-2026-123456')).toBeInTheDocument();
    });
  });

  describe('Accesibilidad', () => {
    it('debe tener botones accesibles con roles adecuados', () => {
      render(
        <ConfirmacionExitosa
          numeroRadicacion={mockNumeroRadicacion}
          onRadicarOtra={vi.fn()}
          onConsultarEstado={vi.fn()}
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBe(2);

      buttons.forEach((button) => {
        expect(button).toHaveAccessibleName();
      });
    });
  });
});
