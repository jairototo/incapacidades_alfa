import { useEffect, useState } from 'react';

/**
 * Hook para debounce de valores
 * Útil para reducir llamadas a API durante escritura
 * 
 * @param value - Valor a debounce
 * @param delay - Delay en milisegundos (default: 300ms)
 * @returns Valor debounced
 * 
 * @example
 * const searchQuery = useDebounce(inputValue, 300);
 * // searchQuery solo se actualiza 300ms después de que el usuario deja de escribir
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
