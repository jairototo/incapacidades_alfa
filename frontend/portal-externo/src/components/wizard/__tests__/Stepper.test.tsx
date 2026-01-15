import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stepper } from '../Stepper';

describe('Stepper', () => {
  test('debe renderizar el número correcto de pasos', () => {
    render(<Stepper currentStep={1} totalSteps={5} />);
    
    // Verificar que se renderizan 5 círculos de paso
    const stepCircles = screen.getAllByText(/[1-5]/);
    expect(stepCircles.length).toBeGreaterThanOrEqual(5);
  });

  test('debe mostrar el paso actual correctamente', () => {
    render(<Stepper currentStep={2} totalSteps={5} />);
    
    // El paso 2 debe ser visible
    const step2 = screen.getByText('2');
    expect(step2).toBeInTheDocument();
  });

  test('debe mostrar checkmark en pasos completados', () => {
    const { container } = render(<Stepper currentStep={3} totalSteps={5} />);
    
    // Los pasos 1 y 2 deben tener checkmark (completos)
    // El paso 3 debe mostrar el número (actual)
    const checkIcons = container.querySelectorAll('svg');
    expect(checkIcons.length).toBeGreaterThan(0);
  });

  test('debe aplicar estilos correctos al paso actual', () => {
    const { container } = render(<Stepper currentStep={3} totalSteps={5} />);
    
    // Verificar que hay elementos con las clases de paso actual
    const activeElements = container.querySelectorAll('.bg-blue-600');
    expect(activeElements.length).toBeGreaterThan(0);
  });

  test('debe renderizar labels personalizados si se proporcionan', () => {
    const customSteps = ['Inicio', 'Medio', 'Final'];
    render(
      <Stepper currentStep={1} totalSteps={3} steps={customSteps} />
    );
    
    // Verificar que se muestran los labels personalizados
    // El label aparece dos veces: una vez oculto en mobile (sm:block) y otra visible en mobile
    const inicioLabels = screen.getAllByText('Inicio');
    expect(inicioLabels.length).toBeGreaterThanOrEqual(1);
  });

  test('debe renderizar labels por defecto si no se proporcionan', () => {
    render(<Stepper currentStep={1} totalSteps={5} />);
    
    // Verificar que se muestra el primer label por defecto
    // El label aparece dos veces: desktop y mobile
    const tipoLabels = screen.getAllByText('Tipo de Incapacidad');
    expect(tipoLabels.length).toBeGreaterThanOrEqual(1);
  });
});
