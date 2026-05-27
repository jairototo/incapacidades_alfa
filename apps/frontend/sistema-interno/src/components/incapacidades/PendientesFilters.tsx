import { useForm } from 'react-hook-form';
import { Search, X } from 'lucide-react';
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
import { Card, CardContent } from '@/components/ui/card';
import type { FiltrosPendientes } from '@/types/incapacidad';
import { TipoIncapacidad, Prioridad } from '@/types/enums';

interface PendientesFiltersProps {
  onSearch: (filtros: FiltrosPendientes) => void;
  isLoading?: boolean;
}

export function PendientesFilters({ onSearch, isLoading }: PendientesFiltersProps) {
  const { register, handleSubmit, reset, setValue, watch } = useForm<FiltrosPendientes>();

  const onSubmit = (data: FiltrosPendientes) => {
    // Filtrar valores vacíos, NaN, y valores "ALL"
    const filtrosFiltrados = Object.fromEntries(
      Object.entries(data).filter(([_, value]) => {
        // Excluir valores vacíos, undefined, "ALL", y NaN
        if (value === '' || value === undefined || value === 'ALL') {
          return false;
        }
        // Excluir NaN (específicamente para números)
        if (typeof value === 'number' && isNaN(value)) {
          return false;
        }
        return true;
      })
    );
    onSearch(filtrosFiltrados);
  };

  const handleReset = () => {
    reset();
    onSearch({});
  };

  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Tipo */}
            <div className="space-y-2">
              <Label htmlFor="tipo">Tipo</Label>
              <Select
                onValueChange={(value) => setValue('tipo', value as TipoIncapacidad)}
                defaultValue={watch('tipo')}
              >
                <SelectTrigger id="tipo">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos</SelectItem>
                  <SelectItem value={TipoIncapacidad.ARL}>ARL</SelectItem>
                  <SelectItem value={TipoIncapacidad.SALUD}>SALUD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Prioridad */}
            <div className="space-y-2">
              <Label htmlFor="prioridad">Prioridad</Label>
              <Select
                onValueChange={(value) => setValue('prioridad', value as Prioridad)}
                defaultValue={watch('prioridad')}
              >
                <SelectTrigger id="prioridad">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todas</SelectItem>
                  <SelectItem value={Prioridad.ALTA}>Alta</SelectItem>
                  <SelectItem value={Prioridad.NORMAL}>Normal</SelectItem>
                  <SelectItem value={Prioridad.BAJA}>Baja</SelectItem>
                  <SelectItem value={Prioridad.URGENTE}>Urgente</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* NIT Empresa */}
            <div className="space-y-2">
              <Label htmlFor="empresa_nit">NIT Empresa</Label>
              <Input
                id="empresa_nit"
                type="text"
                placeholder="900123456"
                {...register('empresa_nit')}
              />
            </div>

            {/* Antigüedad mínima */}
            <div className="space-y-2">
              <Label htmlFor="dias_antiguedad_min">Antigüedad mínima (días)</Label>
              <Input
                id="dias_antiguedad_min"
                type="number"
                min="0"
                placeholder="Ej: 3"
                {...register('dias_antiguedad_min', { valueAsNumber: true })}
              />
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex gap-2">
            <Button type="submit" disabled={isLoading}>
              <Search className="mr-2 h-4 w-4" />
              Buscar
            </Button>
            <Button type="button" variant="outline" onClick={handleReset} disabled={isLoading}>
              <X className="mr-2 h-4 w-4" />
              Limpiar
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
