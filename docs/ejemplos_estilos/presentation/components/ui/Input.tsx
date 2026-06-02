import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from './cn';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...rest }, ref) => (
    <input
      ref={ref}
      className={cn(
        'block w-full rounded-md border border-gray-300 bg-white px-3 py-2',
        'text-sm font-normal text-gray-900 placeholder:text-gray-400',
        'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        'disabled:bg-gray-50 disabled:text-gray-500',
        'transition-colors duration-150',
        className,
      )}
      {...rest}
    />
  ),
);
Input.displayName = 'Input';
