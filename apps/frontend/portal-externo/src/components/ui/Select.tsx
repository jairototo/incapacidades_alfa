import type { SelectHTMLAttributes } from 'react';
import { forwardRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

/**
 * Select component siguiendo el patrón Shadcn/ui
 * Componente nativo de HTML con estilos personalizados
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, children, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={props.id}
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative">
          <select
            ref={ref}
            className={cn(
              'w-full appearance-none rounded-lg border border-gray-300 bg-white px-4 py-2.5 pr-10',
              'text-sm text-gray-900 placeholder:text-gray-400',
              'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200',
              'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
              'transition-colors duration-200',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-200',
              className
            )}
            {...props}
          >
            {children}
          </select>
          
          {/* Icon */}
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </div>
        </div>

        {/* Error or Helper Text */}
        {error && (
          <p className="mt-1 text-sm text-red-600">{error}</p>
        )}
        {!error && helperText && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
