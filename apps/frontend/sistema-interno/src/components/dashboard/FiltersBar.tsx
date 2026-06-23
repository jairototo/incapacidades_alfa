import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, X } from 'lucide-react';
import type { FilterState } from '@/types/dashboard';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types/enums';
import type { Empresa } from '@/types/incapacidad';
import { useDebounce } from '@/hooks/useDebounce';

interface FiltersBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  empresas: Empresa[];
}

export function FiltersBar({ filters, onFiltersChange, empresas }: FiltersBarProps) {
  const [searchLocal, setSearchLocal] = useState(filters.search);
  
  // Debounce de búsqueda (500ms)
  const debouncedSearch = useDebounce(searchLocal, 500);

  useEffect(() => {
    if (debouncedSearch !== filters.search) {
      onFiltersChange({ ...filters, search: debouncedSearch });
    }
  }, [debouncedSearch]);

  const handleTipoChange = (value: string) => {
    onFiltersChange({
      ...filters,
      tipo: value as TipoIncapacidad | 'TODAS',
    });
  };

  const handleEstadoChange = (value: string) => {
    onFiltersChange({
      ...filters,
      estado: value as EstadoIncapacidad | 'TODOS',
    });
  };

  const handleEmpresaChange = (value: string) => {
    onFiltersChange({
      ...filters,
      empresa_id: value === 'TODAS' ? null : value,
    });
  };

  const handleFechaDesdeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fecha = e.target.value ? new Date(e.target.value) : null;
    onFiltersChange({ ...filters, fecha_desde: fecha });
  };

  const handleFechaHastaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fecha = e.target.value ? new Date(e.target.value) : null;
    onFiltersChange({ ...filters, fecha_hasta: fecha });
  };

  const handleClearFilters = () => {
    setSearchLocal('');
    onFiltersChange({
      tipo: 'TODAS',
      estado: 'TODOS',
      fecha_desde: null,
      fecha_hasta: null,
      empresa_id: null,
      search: '',
    });
  };

  const hasActiveFilters =
    filters.tipo !== 'TODAS' ||
    filters.estado !== 'TODOS' ||
    filters.fecha_desde !== null ||
    filters.fecha_hasta !== null ||
    filters.empresa_id !== null ||
    filters.search !== '';

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {/* Tipo de Incapacidad */}
        <div className="space-y-2">
          <Label htmlFor="tipo">Tipo</Label>
          <Select value={filters.tipo} onValueChange={handleTipoChange}>
            <SelectTrigger id="tipo">
              <SelectValue placeholder="Seleccione tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODAS">Todas</SelectItem>
              <SelectItem value={TipoIncapacidad.ARL}>ARL</SelectItem>
              <SelectItem value={TipoIncapacidad.SALUD}>SALUD</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Estado */}
        <div className="space-y-2">
          <Label htmlFor="estado">Estado</Label>
          <Select value={filters.estado} onValueChange={handleEstadoChange}>
            <SelectTrigger id="estado">
              <SelectValue placeholder="Seleccione estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODOS">Todos</SelectItem>
              <SelectItem value={EstadoIncapacidad.RADICADA}>Radicada</SelectItem>
              <SelectItem value={EstadoIncapacidad.EN_AUDITORIA}>En Auditoría</SelectItem>
              <SelectItem value="PENDIENTE">Pendiente</SelectItem>
              <SelectItem value="LIQUIDACION">En Liquidación</SelectItem>
              <SelectItem value="LIQUIDACION_PARCIAL">Liquidación Parcial</SelectItem>
              <SelectItem value="GLOSADA">Glosada</SelectItem>
              <SelectItem value={EstadoIncapacidad.PAGADA}>Pagada</SelectItem>
              <SelectItem value="PAGADA_PARCIAL">Pagada Parcial</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Fecha Desde */}
        <div className="space-y-2">
          <Label htmlFor="fecha_desde">Fecha Desde</Label>
          <Input
            id="fecha_desde"
            type="date"
            value={filters.fecha_desde?.toISOString().split('T')[0] || ''}
            onChange={handleFechaDesdeChange}
            max={new Date().toISOString().split('T')[0]}
          />
        </div>

        {/* Fecha Hasta */}
        <div className="space-y-2">
          <Label htmlFor="fecha_hasta">Fecha Hasta</Label>
          <Input
            id="fecha_hasta"
            type="date"
            value={filters.fecha_hasta?.toISOString().split('T')[0] || ''}
            onChange={handleFechaHastaChange}
            max={new Date().toISOString().split('T')[0]}
            min={filters.fecha_desde?.toISOString().split('T')[0] || undefined}
          />
        </div>

        {/* Empresa */}
        <div className="space-y-2">
          <Label htmlFor="empresa">Empresa</Label>
          <Select
            value={filters.empresa_id || 'TODAS'}
            onValueChange={handleEmpresaChange}
          >
            <SelectTrigger id="empresa">
              <SelectValue placeholder="Seleccione empresa" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODAS">Todas</SelectItem>
              {empresas.map((empresa) => (
                <SelectItem key={empresa.id} value={empresa.id}>
                  {empresa.razon_social}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Búsqueda */}
        <div className="space-y-2">
          <Label htmlFor="search">Buscar</Label>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              id="search"
              placeholder="Número o documento..."
              value={searchLocal}
              onChange={(e) => setSearchLocal(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
      </div>

      {/* Botón Limpiar Filtros */}
      {hasActiveFilters && (
        <div className="mt-4 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearFilters}
            className="gap-2"
          >
            <X className="h-4 w-4" />
            Limpiar filtros
          </Button>
        </div>
      )}
    </div>
  );
}
