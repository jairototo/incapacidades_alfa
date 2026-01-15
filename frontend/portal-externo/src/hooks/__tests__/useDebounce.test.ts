import { describe, test, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce } from '../useDebounce';
import { act } from 'react';

describe('useDebounce', () => {
  test('debe retornar el valor inicial inmediatamente', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    
    expect(result.current).toBe('initial');
  });

  test('debe debounce el valor con delay de 300ms', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    expect(result.current).toBe('initial');

    // Cambiar valor
    rerender({ value: 'updated' });

    // No debe cambiar inmediatamente
    expect(result.current).toBe('initial');

    // Debe cambiar después del delay
    await waitFor(
      () => {
        expect(result.current).toBe('updated');
      },
      { timeout: 500 }
    );
  });

  test('debe cancelar el timeout anterior si cambia el valor antes del delay', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'initial' } }
    );

    // Primer cambio
    rerender({ value: 'first' });
    
    // Segundo cambio antes de que termine el delay
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100));
    });
    rerender({ value: 'second' });

    // Debe actualizar con el último valor después del delay completo
    await waitFor(
      () => {
        expect(result.current).toBe('second');
      },
      { timeout: 500 }
    );
  });

  test('debe funcionar con diferentes tipos de datos', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 100),
      { initialProps: { value: 123 } }
    );

    expect(result.current).toBe(123);

    rerender({ value: 456 });

    await waitFor(
      () => {
        expect(result.current).toBe(456);
      },
      { timeout: 200 }
    );
  });

  test('debe usar delay personalizado', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );

    rerender({ value: 'updated', delay: 500 });

    // No debe cambiar antes del delay
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 300));
    });
    expect(result.current).toBe('initial');

    // Debe cambiar después del delay
    await waitFor(
      () => {
        expect(result.current).toBe('updated');
      },
      { timeout: 700 }
    );
  });
});
