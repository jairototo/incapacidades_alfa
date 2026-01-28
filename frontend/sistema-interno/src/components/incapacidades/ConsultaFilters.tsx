/**
 * ConsultaFilters - Filtros para búsqueda de incapacidades
 */
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

export interface ConsultaFiltros {
  numero?: string;
  tipo?: 'ARL' | 'SALUD' | 'ALL' | '';
  estado?: string;
  empleado_documento?: string;
  empresa_nit?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
}

interface ConsultaFiltersProps {
  onSearch: (filtros: ConsultaFiltros) => void;
  isLoading?: boolean;
}

export function ConsultaFilters({ onSearch, isLoading }: ConsultaFiltersProps) {
  const { register, handleSubmit, reset, setValue } = useForm<ConsultaFiltros>();

  const onSubmit = (data: ConsultaFiltros) => {
    // Filtrar campos vacíos y valores 'ALL'
    const filtros = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== '' && value !== undefined && value !== null && value !== 'ALL') {
        acc[key as keyof ConsultaFiltros] = value;
      }
      return acc;
    }, {} as ConsultaFiltros);

    onSearch(filtros);
  };

  const handleReset = () => {
    reset();
    onSearch({});
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Número de Radicación */}
            <div className="space-y-2">
              <Label htmlFor="numero">Número de Radicación</Label>
              <Input
                id="numero"
                {...register('numero')}
                placeholder="INC-ARL-20260123-0001"
                disabled={isLoading}
              />
            </div>

            {/* Tipo */}
            <div className="space-y-2">
              <Label htmlFor="tipo">Tipo</Label>
              <Select 
                onValueChange={(value: string) => setValue('tipo', value as 'ARL' | 'SALUD' | 'ALL' | '')}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos</SelectItem>
                  <SelectItem value="ARL">ARL</SelectItem>
                  <SelectItem value="SALUD">SALUD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Estado */}
            <div className="space-y-2">
              <Label htmlFor="estado">Estado</Label>
              <Select 
                onValueChange={(value: string) => setValue('estado', value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos</SelectItem>
                  <SelectItem value="RADICADA">Radicada</SelectItem>
                  <SelectItem value="EN_AUDITORIA">En Auditoría</SelectItem>
                  <SelectItem value="OBSERVADA">Observada</SelectItem>
                  <SelectItem value="APROBADA">Aprobada</SelectItem>
                  <SelectItem value="RECHAZADA">Rechazada</SelectItem>
                  <SelectItem value="EN_PAGO">En Pago</SelectItem>
                  <SelectItem value="PAGADA">Pagada</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Documento Empleado */}
            <div className="space-y-2">
              <Label htmlFor="empleado_documento">Documento Empleado</Label>
              <Input
                id="empleado_documento"
                {...register('empleado_documento')}
                placeholder="1234567890"
                disabled={isLoading}
              />
            </div>

            {/* NIT Empresa */}
            <div className="space-y-2">
              <Label htmlFor="empresa_nit">NIT Empresa</Label>
              <Input
                id="empresa_nit"
                {...register('empresa_nit')}
                placeholder="900123456"
                disabled={isLoading}
              />
            </div>

            {/* Fecha Inicio */}
            <div className="space-y-2">
              <Label htmlFor="fecha_inicio">Fecha Inicio</Label>
              <Input
                id="fecha_inicio"
                type="date"
                {...register('fecha_inicio')}
                disabled={isLoading}
              />
            </div>

            {/* Fecha Fin */}
            <div className="space-y-2">
              <Label htmlFor="fecha_fin">Fecha Fin</Label>
              <Input
                id="fecha_fin"
                type="date"
                {...register('fecha_fin')}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleReset}
              disabled={isLoading}
            >
              <X className="mr-2 h-4 w-4" />
              Limpiar
            </Button>
            <Button type="submit" disabled={isLoading}>
              <Search className="mr-2 h-4 w-4" />
              Buscar
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
