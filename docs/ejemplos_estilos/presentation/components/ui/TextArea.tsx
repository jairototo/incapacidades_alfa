import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from './cn';

export const TextArea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, rows = 4, ...rest }, ref) => (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(
        'block w-full rounded-md border border-gray-300 bg-white px-3 py-2',
        'text-sm font-normal text-gray-900 placeholder:text-gray-400',
        'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
        'disabled:bg-gray-50 disabled:text-gray-500',
        'transition-colors duration-150 resize-y',
        className,
      )}
      {...rest}
    />
  ),
);
TextArea.displayName = 'TextArea';
