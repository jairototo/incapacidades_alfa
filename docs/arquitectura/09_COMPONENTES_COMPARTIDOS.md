# Library de Componentes Compartidos

**Objetivo**: Biblioteca de componentes reutilizables entre Portal Externo y Sistema Interno para mantener consistencia y reducir duplicación de código.

---

## 🎯 Estrategia de Componentes Compartidos

### Enfoque

1. **Fase 1**: Componentes en cada proyecto (portal-externo, sistema-interno)
2. **Fase 2**: Identificar componentes duplicados
3. **Fase 3**: Extraer a library `@incapacidades/ui` (monorepo)

### Estructura Propuesta

```
shared-ui/
├── src/
│   ├── components/
│   │   ├── ui/              # Componentes base Shadcn/ui
│   │   ├── forms/           # Componentes de formularios
│   │   ├── data-display/    # Tablas, cards, listas
│   │   ├── feedback/        # Loading, alerts, toasts
│   │   ├── navigation/      # Breadcrumbs, pagination
│   │   └── media/           # File upload, preview
│   ├── hooks/               # Custom hooks
│   ├── utils/               # Utilidades
│   ├── types/               # TypeScript types compartidos
│   └── index.ts             # Exports principales
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── README.md
```

---

## 📦 Componentes UI Base (Shadcn/ui)

### Instalación y Configuración

```bash
# Instalar Shadcn/ui CLI
npx shadcn-ui@latest init

# Agregar componentes individuales
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add table
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add toast
```

### Componentes Base Utilizados

```typescript
// components/ui/button.tsx
import { cn } from '@/utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'destructive' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({ 
  variant = 'default', 
  size = 'md', 
  className, 
  children, 
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        {
          'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
          'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
          'bg-red-600 text-white hover:bg-red-700': variant === 'destructive',
          'border border-gray-300 bg-white hover:bg-gray-50': variant === 'outline',
          'hover:bg-gray-100': variant === 'ghost',
        },
        {
          'h-8 px-3 text-sm': size === 'sm',
          'h-10 px-4 text-base': size === 'md',
          'h-12 px-6 text-lg': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
```

```typescript
// components/ui/input.tsx
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, className, ...props }: InputProps) {
  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        className={cn(
          'w-full rounded-md border border-gray-300 px-3 py-2',
          'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20',
          'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
          className
        )}
        {...props}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      {hint && !error && <p className="text-sm text-gray-500">{hint}</p>}
    </div>
  );
}
```

```typescript
// components/ui/select.tsx
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: Array<{ value: string; label: string }>;
}

export function Select({ label, error, options, className, ...props }: SelectProps) {
  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <select
        className={cn(
          'w-full rounded-md border border-gray-300 px-3 py-2',
          'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20',
          'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
          error && 'border-red-500',
          className
        )}
        {...props}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

---

## 🎨 Componentes de Formularios

### FileUploader

```typescript
// components/forms/FileUploader.tsx
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, CheckCircle, AlertCircle } from 'lucide-react';

interface FileUploaderProps {
  maxSize?: number;  // en MB
  accept?: string[];
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  error?: string;
}

export function FileUploader({ 
  maxSize = 10, 
  accept = ['.pdf', '.jpg', '.jpeg', '.png'],
  onFileSelect,
  onFileRemove,
  error
}: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      setFile(selectedFile);
      setUploadStatus('success');
      onFileSelect(selectedFile);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.reduce((acc, ext) => ({ ...acc, [ext]: [] }), {}),
    maxSize: maxSize * 1024 * 1024,
    multiple: false,
  });

  const handleRemove = () => {
    setFile(null);
    setUploadStatus('idle');
    onFileRemove?.();
  };

  if (file) {
    return (
      <div className="border border-gray-300 rounded-md p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-blue-500" />
            <div>
              <p className="font-medium text-sm">{file.name}</p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="text-red-500 hover:text-red-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {uploadStatus === 'success' && (
          <div className="mt-2 flex items-center text-green-600 text-sm">
            <CheckCircle className="w-4 h-4 mr-1" />
            Archivo cargado correctamente
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition',
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
          error && 'border-red-500'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        {isDragActive ? (
          <p className="text-blue-600">Suelta el archivo aquí...</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium mb-1">
              Arrastra un archivo aquí o haz clic para seleccionar
            </p>
            <p className="text-sm text-gray-500">
              {accept.join(', ')} - Máximo {maxSize}MB
            </p>
          </>
        )}
      </div>
      {error && (
        <div className="mt-2 flex items-center text-red-600 text-sm">
          <AlertCircle className="w-4 h-4 mr-1" />
          {error}
        </div>
      )}
    </div>
  );
}
```

### AutocompleteInput

```typescript
// components/forms/AutocompleteInput.tsx
import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Loader2 } from 'lucide-react';

interface Option {
  value: string;
  label: string;
}

interface AutocompleteInputProps {
  label?: string;
  placeholder?: string;
  options: Option[];
  onSelect: (option: Option) => void;
  onSearch: (query: string) => void;
  isLoading?: boolean;
  error?: string;
}

export function AutocompleteInput({
  label,
  placeholder,
  options,
  onSelect,
  onSearch,
  isLoading,
  error
}: AutocompleteInputProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setIsOpen(true);
    onSearch(value);
  };

  const handleSelect = (option: Option) => {
    setQuery(option.label);
    setIsOpen(false);
    onSelect(option);
  };

  return (
    <div ref={wrapperRef} className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className={cn(
            'w-full rounded-md border border-gray-300 px-3 py-2 pr-10',
            'focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20',
            error && 'border-red-500'
          )}
        />
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {isOpen && options.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {options.map(option => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSelect(option)}
              className="w-full px-3 py-2 text-left hover:bg-blue-50 focus:bg-blue-50 focus:outline-none"
            >
              {option.label}
            </button>
          ))}
        </div>
      )}

      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

### DateRangePicker

```typescript
// components/forms/DateRangePicker.tsx
import { useState } from 'react';
import { Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  label?: string;
}

export function DateRangePicker({ value, onChange, label }: DateRangePickerProps) {
  const formatDate = (date: Date | null) => {
    return date ? format(date, 'dd/MM/yyyy', { locale: es }) : '';
  };

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <input
            type="date"
            value={value.from ? format(value.from, 'yyyy-MM-dd') : ''}
            onChange={e => onChange({ ...value, from: e.target.value ? new Date(e.target.value) : null })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 pr-10"
          />
          <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
        <span className="text-gray-500">-</span>
        <div className="relative flex-1">
          <input
            type="date"
            value={value.to ? format(value.to, 'yyyy-MM-dd') : ''}
            onChange={e => onChange({ ...value, to: e.target.value ? new Date(e.target.value) : null })}
            className="w-full rounded-md border border-gray-300 px-3 py-2 pr-10"
          />
          <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>
    </div>
  );
}
```

---

## 📊 Componentes de Visualización de Datos

### DataTable (Genérico y Reutilizable)

```typescript
// components/data-display/DataTable.tsx
import { useState } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

export function DataTable<T extends { id: string | number }>({ 
  data, 
  columns, 
  onRowClick,
  emptyMessage = 'No hay datos disponibles'
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: keyof T | string;
    direction: 'asc' | 'desc';
  } | null>(null);

  const handleSort = (key: keyof T | string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig?.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortConfig) return 0;

    const aValue = a[sortConfig.key as keyof T];
    const bValue = b[sortConfig.key as keyof T];

    if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const getSortIcon = (columnKey: string) => {
    if (sortConfig?.key !== columnKey) {
      return <ChevronsUpDown className="w-4 h-4 text-gray-400" />;
    }
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4 text-blue-600" />
    ) : (
      <ChevronDown className="w-4 h-4 text-blue-600" />
    );
  };

  if (data.length === 0) {
    return (
      <div className="border border-gray-200 rounded-md p-8 text-center text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-md">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map(column => (
              <th
                key={String(column.key)}
                className={cn(
                  'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                  column.sortable && 'cursor-pointer hover:bg-gray-100'
                )}
                style={{ width: column.width }}
                onClick={() => column.sortable && handleSort(column.key)}
              >
                <div className="flex items-center space-x-1">
                  <span>{column.header}</span>
                  {column.sortable && getSortIcon(String(column.key))}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map(row => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className={cn(
                'hover:bg-gray-50 transition',
                onRowClick && 'cursor-pointer'
              )}
            >
              {columns.map(column => (
                <td key={String(column.key)} className="px-4 py-3 text-sm text-gray-900">
                  {column.render 
                    ? column.render(row) 
                    : String(row[column.key as keyof T] ?? '-')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Pagination

```typescript
// components/navigation/Pagination.tsx
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  itemsPerPage?: number;
  totalItems?: number;
}

export function Pagination({ 
  currentPage, 
  totalPages, 
  onPageChange,
  itemsPerPage,
  totalItems
}: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  const visiblePages = pages.filter(page => {
    if (totalPages <= 7) return true;
    if (page === 1 || page === totalPages) return true;
    if (Math.abs(page - currentPage) <= 1) return true;
    return false;
  });

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
      <div className="flex-1 flex justify-between sm:hidden">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="btn btn-secondary"
        >
          Anterior
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="btn btn-secondary"
        >
          Siguiente
        </button>
      </div>

      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-700">
            Mostrando{' '}
            <span className="font-medium">
              {(currentPage - 1) * (itemsPerPage || 0) + 1}
            </span>{' '}
            a{' '}
            <span className="font-medium">
              {Math.min(currentPage * (itemsPerPage || 0), totalItems || 0)}
            </span>{' '}
            de <span className="font-medium">{totalItems}</span> resultados
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          {visiblePages.map((page, index) => {
            const prevPage = visiblePages[index - 1];
            const showEllipsis = prevPage && page - prevPage > 1;

            return (
              <React.Fragment key={page}>
                {showEllipsis && (
                  <span className="px-2 text-gray-500">...</span>
                )}
                <button
                  onClick={() => onPageChange(page)}
                  className={cn(
                    'px-3 py-1 rounded text-sm',
                    page === currentPage
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100'
                  )}
                >
                  {page}
                </button>
              </React.Fragment>
            );
          })}

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

### StatsCard

```typescript
// components/data-display/StatsCard.tsx
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
}

export function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  trend,
  color = 'blue'
}: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
          {trend && (
            <p className={cn(
              'mt-2 text-sm',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        <div className={cn('p-3 rounded-full', colorClasses[color])}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}
```

---

## 🔔 Componentes de Feedback

### LoadingSpinner

```typescript
// components/feedback/LoadingSpinner.tsx
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

export function LoadingSpinner({ 
  size = 'md', 
  text,
  fullScreen = false
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center space-y-2">
      <Loader2 className={cn('animate-spin text-blue-600', sizeClasses[size])} />
      {text && <p className="text-sm text-gray-600">{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}
```

### EmptyState

```typescript
// components/feedback/EmptyState.tsx
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 text-center max-w-sm mb-4">
          {description}
        </p>
      )}
      {action && (
        <button onClick={action.onClick} className="btn btn-primary">
          {action.label}
        </button>
      )}
    </div>
  );
}
```

---

## 🛠️ Custom Hooks

### useDebounce

```typescript
// hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number = 500): T {
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
```

### usePagination

```typescript
// hooks/usePagination.ts
import { useState, useMemo } from 'react';

interface UsePaginationProps<T> {
  data: T[];
  itemsPerPage?: number;
}

export function usePagination<T>({ data, itemsPerPage = 10 }: UsePaginationProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(data.length / itemsPerPage);

  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return data.slice(startIndex, endIndex);
  }, [data, currentPage, itemsPerPage]);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  return {
    currentPage,
    totalPages,
    paginatedData,
    goToPage,
    nextPage: () => goToPage(currentPage + 1),
    prevPage: () => goToPage(currentPage - 1),
  };
}
```

### useLocalStorage

```typescript
// hooks/useLocalStorage.ts
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue] as const;
}
```

---

## 🎨 Utilidades

### cn (classnames utility)

```typescript
// utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### formatters

```typescript
// utils/formatters.ts
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export const formatDate = (date: Date | string, formatStr = 'dd/MM/yyyy') => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return format(dateObj, formatStr, { locale: es });
};

export const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
  }).format(amount);
};

export const formatFileSize = (bytes: number) => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};
```

---

## 📝 Documentación de Uso

### Instalación en Proyecto

```bash
# Opción 1: NPM Package (Fase 3)
npm install @incapacidades/ui

# Opción 2: Copiar componentes (Fase 1-2)
# Copiar carpetas components/, hooks/, utils/ al proyecto
```

### Ejemplo de Uso

```typescript
// App.tsx
import { DataTable, Pagination, usePagination } from '@/components';

function IncapacidadesPage() {
  const [data, setData] = useState([]);
  const { paginatedData, currentPage, totalPages, goToPage } = usePagination({
    data,
    itemsPerPage: 10
  });

  const columns = [
    { key: 'numero', header: 'Número', sortable: true },
    { key: 'solicitante', header: 'Solicitante', sortable: true },
    { 
      key: 'estado', 
      header: 'Estado',
      render: (row) => <Badge variant={row.estado}>{row.estado}</Badge>
    },
  ];

  return (
    <div>
      <DataTable 
        data={paginatedData} 
        columns={columns}
        onRowClick={(row) => navigate(`/incapacidades/${row.id}`)}
      />
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={goToPage}
      />
    </div>
  );
}
```

---

## 📚 Storybook

### Configuración

```bash
npx sb init
```

```typescript
// .storybook/main.ts
export default {
  stories: ['../src/**/*.stories.@(ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
  ],
  framework: '@storybook/react-vite',
};
```

### Ejemplo de Story

```typescript
// components/ui/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Botón Primario',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Botón Secundario',
  },
};
```

---

## 🎯 Checklist de Componentes

### Componentes Base (Shadcn/ui)
- [x] Button
- [x] Input
- [x] Select
- [x] Textarea
- [x] Checkbox
- [x] Radio
- [x] Card
- [x] Dialog/Modal
- [x] Dropdown Menu
- [x] Table
- [x] Badge
- [x] Alert
- [x] Toast

### Componentes Personalizados
- [x] FileUploader
- [x] AutocompleteInput
- [x] DateRangePicker
- [x] DataTable
- [x] Pagination
- [x] StatsCard
- [x] LoadingSpinner
- [x] EmptyState
- [ ] TimelineEstados
- [ ] FilePreview
- [ ] BreadcrumbNavigation
- [ ] SearchInput
- [ ] FilterPanel

### Hooks
- [x] useDebounce
- [x] usePagination
- [x] useLocalStorage
- [ ] useMediaQuery
- [ ] useClickOutside
- [ ] useKeyPress

### Utilidades
- [x] cn (classnames)
- [x] formatters (date, currency, fileSize)
- [ ] validators
- [ ] exporters (Excel, PDF)
