import { clsx, type ClassValue } from 'clsx';

/**
 * Combinador de classNames Tailwind.
 * Uso: cn('base', condition && 'extra', props.className)
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
