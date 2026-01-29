import { useState, useEffect, useRef } from 'react';
import { Search, Building2, Check } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { useSearchEmpresas } from '@/services/empresaService';
import { useDebounce } from '@/hooks/useDebounce';
import { cn } from '@/utils/cn';
import type { EmpresaResponse } from '@/types/api';

export interface AutocompleteEmpresaProps {
  value?: string; // empresa_id
  nombre?: string; // empresa_nombre para mostrar
  onSelect: (empresa: EmpresaResponse) => void;
  error?: string;
  disabled?: boolean;
  readOnly?: boolean; // Nuevo: modo solo lectura cuando se autocompleta
  helperText?: string; // Nuevo: texto de ayuda
}

/**
 * Componente de autocomplete para buscar y seleccionar empresas
 * Busca por NIT o razón social con debounce de 300ms
 */
export function AutocompleteEmpresa({
  value,
  nombre,
  onSelect,
  error,
  disabled,
  readOnly,
  helperText,
}: AutocompleteEmpresaProps) {
  const [query, setQuery] = useState(nombre || '');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedId, setSelectedId] = useState(value);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 300);
  const { data: empresas = [], isLoading } = useSearchEmpresas(debouncedQuery);


  // Actualizar query cuando cambia nombre (autocompletado desde empleado)
  useEffect(() => {
    if (nombre && nombre !== query) {
      setQuery(nombre);
      setSelectedId(value);
    }
  }, [nombre, value]);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (readOnly) return; // No permitir edición en modo solo lectura
    setQuery(e.target.value);
    setIsOpen(true);
    setSelectedId(undefined);
  };

  const handleSelect = (empresa: EmpresaResponse) => {
    setQuery(empresa.razon_social);
    setSelectedId(empresa.id);
    setIsOpen(false);
    onSelect(empresa);
  };

  const showDropdown = isOpen && query.length >= 2 && !selectedId && !readOnly;

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div className="relative">
        <Input
          value={query}
          onChange={handleInputChange}
          onFocus={() => !readOnly && setIsOpen(true)}
          placeholder="Buscar por NIT o razón social..."
          disabled={disabled}
          readOnly={readOnly}
          error={error}
          label="Empresa"
          required
          helperText={helperText || (readOnly ? 'Autocompletada desde empleado' : undefined)}
        />
        
        {/* Search/Check Icon */}
        <div className="pointer-events-none absolute right-3 top-[38px] flex items-center">
          {readOnly && selectedId ? (
            <Check className="h-4 w-4 text-green-600" />
          ) : (
            <Search className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
          {isLoading && (
            <div className="px-4 py-3 text-center text-sm text-gray-500">
              Buscando empresas...
            </div>
          )}

          {!isLoading && empresas.length === 0 && (
            <div className="px-4 py-3 text-center text-sm text-gray-500">
              No se encontraron empresas
            </div>
          )}

          {!isLoading && empresas.length > 0 && (
            <ul className="max-h-60 overflow-auto py-1">
              {empresas.map((empresa) => (
                <li key={empresa.id}>
                  <button
                    type="button"
                    onClick={() => handleSelect(empresa)}
                    className={cn(
                      'flex w-full items-center gap-3 px-4 py-2 text-left transition-colors',
                      'hover:bg-blue-50 focus:bg-blue-50 focus:outline-none'
                    )}
                  >
                    <Building2 className="h-5 w-5 flex-shrink-0 text-blue-600" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {empresa.razon_social}
                      </p>
                      <p className="text-xs text-gray-500">
                        NIT: {empresa.nit}
                      </p>
                    </div>
                    {selectedId === empresa.id && (
                      <Check className="h-4 w-4 text-blue-600" />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Selected empresa indicator */}
      {selectedId && query && (
        <div className="mt-2 flex items-center gap-2 text-sm text-green-600">
          <Check className="h-4 w-4" />
          <span>Empresa seleccionada</span>
        </div>
      )}
    </div>
  );
}
