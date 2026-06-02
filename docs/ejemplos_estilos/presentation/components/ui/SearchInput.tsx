import { forwardRef, type InputHTMLAttributes } from 'react';
import { Search } from 'lucide-react';
import { cn } from './cn';

/**
 * Input con ícono de búsqueda Alfa (outline, stroke fino).
 */
export const SearchInput = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, placeholder = 'Buscar...', ...rest }, ref) => (
    <div className="relative">
      <Search
        size={16}
        strokeWidth={1.75}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        aria-hidden
      />
      <input
        ref={ref}
        type="search"
        placeholder={placeholder}
        className={cn(
          'block w-full rounded-md border border-gray-300 bg-white pl-9 pr-3 py-2',
          'text-sm font-normal text-gray-900 placeholder:text-gray-400',
          'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
          'transition-colors duration-150',
          className,
        )}
        {...rest}
      />
    </div>
  ),
);
SearchInput.displayName = 'SearchInput';
