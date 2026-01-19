import { useState, useEffect, useRef } from 'react';
import { useSearchSolicitantes } from '@/services/queries/useSolicitantes';
import { useDebounce } from '@/hooks/useDebounce';
import type { Solicitante } from '@/types/solicitante';
import { Input } from '@/components/ui/Input';
import { User, Loader2 } from 'lucide-react';

interface SolicitanteAutocompleteProps {
  value: Solicitante | null;
  onChange: (solicitante: Solicitante | null) => void;
  onEmailChange: (email: string) => void;
}

/**
 * Componente de autocompletado para solicitantes
 * Busca por correo electrónico con debounce de 300ms
 */
export function SolicitanteAutocomplete({
  value,
  onChange,
  onEmailChange,
}: SolicitanteAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  
  const { data: solicitantes, isLoading, isFetching } = useSearchSolicitantes(
    { correo: debouncedSearch, limit: 10 },
    debouncedSearch.length >= 3
  );

  // Notificar cambios de email al padre
  useEffect(() => {
    onEmailChange(searchTerm);
  }, [searchTerm, onEmailChange]);

  // Si hay un valor seleccionado, mostrar su correo en el input
  useEffect(() => {
    if (value) {
      setSearchTerm(value.correo);
    }
  }, [value]);

  const handleSelect = (solicitante: Solicitante) => {
    onChange(solicitante);
    setSearchTerm(solicitante.correo);
  };

  const loading = isLoading || isFetching;

  const inputRef = useRef<HTMLInputElement>(null);
  const [showResults, setShowResults] = useState(false);

  return (
    <div className="relative">
      <Input
        ref={inputRef}
        placeholder="Buscar por correo electrónico..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        onFocus={() => setShowResults(true)}
      />
      {showResults && debouncedSearch.length >= 3 && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-sm text-gray-600">Buscando...</span>
            </div>
          ) : solicitantes && solicitantes.length > 0 ? (
            <ul className="py-2">
              {solicitantes.map((solicitante) => (
                <li
                  key={solicitante.id}
                  onClick={() => {
                    handleSelect(solicitante);
                    setShowResults(false);
                  }}
                  className="px-4 py-3 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400" />
                    <div className="flex flex-col">
                      <span className="font-medium text-gray-900">{solicitante.correo}</span>
                      <span className="text-sm text-gray-600">
                        {solicitante.nombres} {solicitante.apellidos}
                      </span>
                      {solicitante.telefono && (
                        <span className="text-xs text-gray-500">Tel: {solicitante.telefono}</span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-sm">
              <p className="font-medium text-gray-900">No se encontraron solicitantes</p>
              <p className="mt-1 text-xs text-gray-500">Registre un nuevo solicitante a continuación</p>
            </div>
          )}
        </div>
      )}
      {debouncedSearch.length > 0 && debouncedSearch.length < 3 && (
        <p className="text-xs text-gray-500 mt-1">Escriba al menos 3 caracteres para buscar</p>
      )}
    </div>
  );
}
