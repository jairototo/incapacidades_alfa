import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stepper } from '../Stepper';

describe('Stepper', () => {
  test('debe renderizar el número correcto de pasos (2 pasos)', () => {
    render(<Stepper currentStep={1} totalSteps={2} />);

    // Verificar que se renderizan 2 círculos de paso
    const stepCircles = screen.getAllByText(/[12]/);
    expect(stepCircles.length).toBeGreaterThanOrEqual(2);
  });

  test('debe mostrar el paso actual correctamente', () => {
    render(<Stepper currentStep={2} totalSteps={2} />);

    // El paso 2 debe ser visible
    const step2 = screen.getByText('2');
    expect(step2).toBeInTheDocument();
  });

  test('debe mostrar checkmark en pasos completados', () => {
    const { container } = render(<Stepper currentStep={2} totalSteps={2} />);

    // El paso 1 debe tener checkmark (completado)
    const checkIcons = container.querySelectorAll('svg');
    expect(checkIcons.length).toBeGreaterThan(0);
  });

  test('debe aplicar estilos correctos al paso actual', () => {
    const { container } = render(<Stepper currentStep={1} totalSteps={2} />);

    // Verificar que hay elementos con las clases de paso actual
    const activeElements = container.querySelectorAll('.bg-blue-600');
    expect(activeElements.length).toBeGreaterThan(0);
  });

  test('debe renderizar labels personalizados si se proporcionan', () => {
    const customSteps = ['Inicio', 'Final'];
    render(<Stepper currentStep={1} totalSteps={2} steps={customSteps} />);

    const inicioLabels = screen.getAllByText('Inicio');
    expect(inicioLabels.length).toBeGreaterThanOrEqual(1);
  });

  test('debe renderizar labels por defecto si no se proporcionan', () => {
    render(<Stepper currentStep={1} totalSteps={2} />);

    // Los labels por defecto del wizard son 2 ahora
    const label = screen.getAllByText('Datos del Solicitante');
    expect(label.length).toBeGreaterThanOrEqual(1);
  });
});
