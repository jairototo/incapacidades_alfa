import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { TablePagination } from '@/components/shared/TablePagination';
import { empleadoService } from '@/services/empleadoService';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';

const PAGE_SIZE = 20;
const ALL_EMPRESAS = 'ALL';

export function EmpleadosPage() {
  const [searchParams] = useSearchParams();
  const canCreate = useCanPerform('empleado.create');
  const canUpdate = useCanPerform('empleado.update');

  const [skip, setSkip] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [empresaId, setEmpresaId] = useState(searchParams.get('empresa_id') ?? ALL_EMPRESAS);

  const { data: empresas = [] } = useQuery({
    queryKey: ['empresas-para-filtro'],
    queryFn: () => empresaService.list({ limit: 1000 }),
  });

  const { data: empleados = [], isLoading } = useQuery({
    queryKey: ['empleados-admin', skip, appliedSearch, empresaId],
    queryFn: () =>
      empleadoService.list({
        skip,
        limit: PAGE_SIZE,
        search: appliedSearch || undefined,
        empresa_id: empresaId === ALL_EMPRESAS ? undefined : empresaId,
      }),
  });

  const handleSearch = () => {
    setSkip(0);
    setAppliedSearch(searchTerm);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Empleados</h1>
          <p className="text-slate-500 mt-1">Empleados por empresa o de todas las empresas afiliadas.</p>
        </div>
        {canCreate && (
          <div className="space-x-2">
            <Button variant="outline">Cargar masivo</Button>
            <Button>Crear empleado</Button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="empresa-filter">Empresa</Label>
          <Select value={empresaId} onValueChange={(v) => { setEmpresaId(v); setSkip(0); }}>
            <SelectTrigger id="empresa-filter" className="w-56">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_EMPRESAS}>Todas las empresas</SelectItem>
              {empresas.map((e) => (
                <SelectItem key={e.id} value={e.id}>{e.razon_social}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="search-filter">Nombres, apellidos o documento</Label>
          <Input id="search-filter" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-64" />
        </div>
        <Button onClick={handleSearch}>Buscar</Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Documento</TableHead>
              <TableHead>Nombres</TableHead>
              <TableHead>Apellidos</TableHead>
              <TableHead>Cargo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && empleados.map((empleado) => (
              <TableRow key={empleado.id}>
                <TableCell>{empleado.tipo_documento} {empleado.numero_documento}</TableCell>
                <TableCell className="font-medium">{empleado.nombres}</TableCell>
                <TableCell>{empleado.apellidos}</TableCell>
                <TableCell>{empleado.cargo ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>
                  <Badge variant={empleado.estado === 'ACTIVO' ? 'default' : 'secondary'}>{empleado.estado}</Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  {canUpdate && <Button variant="outline" size="sm">Editar</Button>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="p-4">
          <TablePagination
            skip={skip}
            limit={PAGE_SIZE}
            resultCount={empleados.length}
            onPrev={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
            onNext={() => setSkip(skip + PAGE_SIZE)}
          />
        </div>
      </div>
    </div>
  );
}
