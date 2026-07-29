import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '@/components/ui/dialog';
import { TablePagination } from '@/components/shared/TablePagination';
import { CargaMasivaWizard } from '@/components/empleados/CargaMasivaWizard';
import { empleadoService } from '@/services/empleadoService';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';
import type { EmpleadoListItem } from '@/types/empleado';

const PAGE_SIZE = 20;
const ALL_EMPRESAS = 'ALL';

function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

interface EmpleadoFormState {
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string;
  fecha_nacimiento: string;
  genero: string;
  cargo: string;
  area: string;
  fecha_ingreso: string;
  salario_base: string;
}

const emptyEmpleadoForm: EmpleadoFormState = {
  numero_documento: '', tipo_documento: 'CC', nombres: '', apellidos: '', email: '', telefono: '',
  fecha_nacimiento: '', genero: '', cargo: '', area: '', fecha_ingreso: '', salario_base: '',
};

export function EmpleadosPage() {
  const [searchParams] = useSearchParams();
  const canCreate = useCanPerform('empleado.create');
  const canUpdate = useCanPerform('empleado.update');

  const queryClient = useQueryClient();
  const [skip, setSkip] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [empresaId, setEmpresaId] = useState(searchParams.get('empresa_id') ?? ALL_EMPRESAS);

  const [wizardOpen, setWizardOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<EmpleadoListItem | null>(null);
  const [form, setForm] = useState<EmpleadoFormState>(emptyEmpleadoForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  const createMutation = useMutation({
    mutationFn: () => {
      if (empresaId === ALL_EMPRESAS) throw new Error('Selecciona una empresa antes de crear un empleado');
      return empleadoService.create({
        empresa_id: empresaId,
        numero_documento: form.numero_documento,
        tipo_documento: form.tipo_documento,
        nombres: form.nombres,
        apellidos: form.apellidos,
        email: form.email || undefined,
        telefono: form.telefono || undefined,
        fecha_nacimiento: form.fecha_nacimiento || undefined,
        genero: form.genero || undefined,
        cargo: form.cargo || undefined,
        area: form.area || undefined,
        fecha_ingreso: form.fecha_ingreso,
        salario_base: form.salario_base ? Number(form.salario_base) : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
      setDialogOpen(false);
      setForm(emptyEmpleadoForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo crear el empleado')),
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay empleado en edición');
      return empleadoService.update(editing.id, {
        nombres: form.nombres,
        apellidos: form.apellidos,
        email: form.email || undefined,
        telefono: form.telefono || undefined,
        fecha_nacimiento: form.fecha_nacimiento || undefined,
        genero: form.genero || undefined,
        cargo: form.cargo || undefined,
        area: form.area || undefined,
        fecha_ingreso: form.fecha_ingreso || undefined,
        salario_base: form.salario_base ? Number(form.salario_base) : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyEmpleadoForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo actualizar el empleado')),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyEmpleadoForm);
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const openEdit = (empleado: EmpleadoListItem) => {
    setEditing(empleado);
    setForm({
      ...emptyEmpleadoForm,
      numero_documento: empleado.numero_documento,
      tipo_documento: empleado.tipo_documento,
      nombres: empleado.nombres,
      apellidos: empleado.apellidos,
      cargo: empleado.cargo ?? '',
    });
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
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
            <Button variant="outline" onClick={() => setWizardOpen(true)}>Cargar masivo</Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={openCreate}>Crear empleado</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{editing ? 'Editar Empleado' : 'Crear Empleado'}</DialogTitle>
                </DialogHeader>
                <div className="space-y-3">
                  {!editing && (
                    <div className="space-y-2">
                      <Label htmlFor="numero_documento">Número de documento</Label>
                      <Input id="numero_documento" value={form.numero_documento} onChange={(e) => setForm({ ...form, numero_documento: e.target.value })} />
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="nombres">Nombres</Label>
                    <Input id="nombres" value={form.nombres} onChange={(e) => setForm({ ...form, nombres: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="apellidos">Apellidos</Label>
                    <Input id="apellidos" value={form.apellidos} onChange={(e) => setForm({ ...form, apellidos: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cargo">Cargo</Label>
                    <Input id="cargo" value={form.cargo} onChange={(e) => setForm({ ...form, cargo: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fecha_ingreso">Fecha de ingreso</Label>
                    <Input id="fecha_ingreso" type="date" value={form.fecha_ingreso} onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })} />
                  </div>
                </div>
                {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
                <DialogFooter>
                  <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                    Guardar
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
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
                  {canUpdate && <Button variant="outline" size="sm" onClick={() => openEdit(empleado)}>Editar</Button>}
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

      <CargaMasivaWizard
        open={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
        }}
      />
    </div>
  );
}
