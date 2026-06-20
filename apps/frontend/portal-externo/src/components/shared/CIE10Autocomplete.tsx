import { useState, useEffect, useRef } from 'react';
import { useSearchCIE10 } from '@/services/queries/useCatalogoCIE10';
import { useDebounce } from '@/hooks/useDebounce';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';
import { Input } from '@/components/ui/Input';
import { FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface CIE10AutocompleteProps {
  value: CatalogoCIE10 | null;
  onChange: (cie10: CatalogoCIE10 | null) => void;
  error?: string;
  id?: string;
}

/**
 * Componente de autocompletado para Catálogo CIE-10
 * Busca por código o descripción con debounce de 300ms
 */
export function CIE10Autocomplete({
  value,
  onChange,
  error,
  id,
}: CIE10AutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  
  const { data: catalogos, isLoading, isFetching } = useSearchCIE10(
    debouncedSearch,
    20
  );

  // Si hay un valor seleccionado, mostrar su código en el input
  useEffect(() => {
    if (value) {
      setSearchTerm(value.codigo);
    }
  }, [value]);

  const handleSelect = (cie10: CatalogoCIE10) => {
    onChange(cie10);
    setSearchTerm(cie10.codigo);
  };

  const loading = isLoading || isFetching;

  const inputRef = useRef<HTMLInputElement>(null);
  const [showResults, setShowResults] = useState(false);

  return (
    <div className="space-y-2">
      <div className="relative">
        <Input
          ref={inputRef}
          id={id}
          placeholder="Buscar por código (ej: A00) o descripción (ej: diabetes)..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setShowResults(true)}
          className={cn(error && "border-red-500")}
        />
        {showResults && debouncedSearch.length >= 2 && (
          <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-[300px] overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                <span className="ml-2 text-sm text-gray-600">Buscando en catálogo CIE-10...</span>
              </div>
            ) : catalogos && catalogos.length > 0 ? (
              <ul className="py-2">
                {catalogos.map((cie10) => (
                  <li
                    key={cie10.codigo}
                    onClick={() => {
                      handleSelect(cie10);
                      setShowResults(false);
                    }}
                    className="px-4 py-3 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-gray-400" />
                      <div className="flex flex-col flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-blue-600">
                            {cie10.codigo}
                          </span>
                          {value?.codigo === cie10.codigo && (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                        </div>
                        <span className="text-sm text-gray-900">
                          {cie10.descripcion}
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="py-6 text-center text-sm">
                <p className="font-medium text-gray-900">No se encontraron diagnósticos</p>
                <p className="mt-1 text-xs text-gray-500">
                  Verifique el código o descripción ingresada
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Badge de selección o error */}
      {value && !error && (
        <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-300 rounded-lg text-green-700">
          <CheckCircle2 className="h-4 w-4" />
          <span className="font-mono font-semibold">{value.codigo}</span>
          <span className="truncate">- {value.descripcion}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-300 rounded-lg text-red-700">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Texto de ayuda */}
      {!value && !error && debouncedSearch.length < 2 && (
        <p className="text-xs text-gray-500">
          Busque por código (ej: A00.1) o descripción (ej: cólera, diabetes). 
          El catálogo contiene ~22,000 códigos CIE-10.
        </p>
      )}
    </div>
  );
}
