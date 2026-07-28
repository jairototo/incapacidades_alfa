import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { TablePagination } from '@/components/shared/TablePagination';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';
import type { Empresa } from '@/types/empresa';

const PAGE_SIZE = 20;

export function EmpresasPage() {
  const navigate = useNavigate();
  const canCreate = useCanPerform('empresa.create');
  const canUpdate = useCanPerform('empresa.update');

  const [skip, setSkip] = useState(0);
  const [nitFilter, setNitFilter] = useState('');
  const [ciudadFilter, setCiudadFilter] = useState('');
  const [departamentoFilter, setDepartamentoFilter] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ nit: '', ciudad: '', departamento: '' });

  const { data: empresas = [], isLoading } = useQuery({
    queryKey: ['empresas-admin', skip, appliedFilters],
    queryFn: () =>
      empresaService.list({
        skip,
        limit: PAGE_SIZE,
        nit: appliedFilters.nit || undefined,
        ciudad: appliedFilters.ciudad || undefined,
        departamento: appliedFilters.departamento || undefined,
      }),
  });

  const handleSearch = () => {
    setSkip(0);
    setAppliedFilters({ nit: nitFilter, ciudad: ciudadFilter, departamento: departamentoFilter });
  };

  const handleVerEmpleados = (empresa: Empresa) => {
    navigate(`/empleados?empresa_id=${empresa.id}`);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Empresas</h1>
          <p className="text-slate-500 mt-1">Empresas afiliadas y sus usuarios de acceso.</p>
        </div>
        {canCreate && <Button>Crear empresa</Button>}
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="nit-filter">NIT o razón social</Label>
          <Input id="nit-filter" value={nitFilter} onChange={(e) => setNitFilter(e.target.value)} className="w-56" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ciudad-filter">Ciudad</Label>
          <Input id="ciudad-filter" value={ciudadFilter} onChange={(e) => setCiudadFilter(e.target.value)} className="w-40" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="departamento-filter">Departamento</Label>
          <Input id="departamento-filter" value={departamentoFilter} onChange={(e) => setDepartamentoFilter(e.target.value)} className="w-40" />
        </div>
        <Button onClick={handleSearch}>Buscar</Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>NIT</TableHead>
              <TableHead>Razón social</TableHead>
              <TableHead>Ciudad</TableHead>
              <TableHead>Departamento</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && empresas.map((empresa) => (
              <TableRow key={empresa.id}>
                <TableCell>{empresa.nit}</TableCell>
                <TableCell className="font-medium">{empresa.razon_social}</TableCell>
                <TableCell>{empresa.ciudad ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>{empresa.departamento ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>
                  <Badge variant={empresa.estado === 'ACTIVA' ? 'default' : 'secondary'}>{empresa.estado}</Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  <Button variant="outline" size="sm" onClick={() => handleVerEmpleados(empresa)}>
                    Ver empleados
                  </Button>
                  {canUpdate && (
                    <>
                      <Button variant="outline" size="sm">Editar</Button>
                      <Button variant="outline" size="sm">Regenerar contraseña</Button>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="p-4">
          <TablePagination
            skip={skip}
            limit={PAGE_SIZE}
            resultCount={empresas.length}
            onPrev={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
            onNext={() => setSkip(skip + PAGE_SIZE)}
          />
        </div>
      </div>
    </div>
  );
}
