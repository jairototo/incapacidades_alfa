import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '@/components/ui/dialog';
import { TablePagination } from '@/components/shared/TablePagination';
import { PasswordRevealDialog } from '@/components/empresas/PasswordRevealDialog';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';
import { useToast } from '@/hooks/use-toast';
import type { Empresa, UsuarioGenerado } from '@/types/empresa';

const PAGE_SIZE = 20;

function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

interface EmpresaFormState {
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono: string;
  direccion: string;
  ciudad: string;
  departamento: string;
}

const emptyEmpresaForm: EmpresaFormState = {
  nit: '', razon_social: '', email_contacto: '', telefono: '', direccion: '', ciudad: '', departamento: '',
};

export function EmpresasPage() {
  const navigate = useNavigate();
  const canCreate = useCanPerform('empresa.create');
  const canUpdate = useCanPerform('empresa.update');
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [skip, setSkip] = useState(0);
  const [nitFilter, setNitFilter] = useState('');
  const [ciudadFilter, setCiudadFilter] = useState('');
  const [departamentoFilter, setDepartamentoFilter] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ nit: '', ciudad: '', departamento: '' });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Empresa | null>(null);
  const [form, setForm] = useState<EmpresaFormState>(emptyEmpresaForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [credenciales, setCredenciales] = useState<UsuarioGenerado | null>(null);

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

  const createMutation = useMutation({
    mutationFn: () => empresaService.create({
      nit: form.nit,
      razon_social: form.razon_social,
      email_contacto: form.email_contacto,
      telefono: form.telefono || undefined,
      direccion: form.direccion || undefined,
      ciudad: form.ciudad || undefined,
      departamento: form.departamento || undefined,
    }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['empresas-admin'] });
      setDialogOpen(false);
      setForm(emptyEmpresaForm);
      setErrorMessage(null);
      setCredenciales(data.usuario_generado);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo crear la empresa')),
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay empresa en edición');
      return empresaService.update(editing.id, {
        razon_social: form.razon_social,
        email_contacto: form.email_contacto,
        telefono: form.telefono || undefined,
        direccion: form.direccion || undefined,
        ciudad: form.ciudad || undefined,
        departamento: form.departamento || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyEmpresaForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo actualizar la empresa')),
  });

  const regenerarPasswordMutation = useMutation({
    mutationFn: (id: string) => empresaService.regenerarPassword(id),
    onSuccess: (data) => setCredenciales({ username: data.username, password: data.password }),
    onError: (error: unknown) => {
      const message = extractErrorMessage(error, 'No se pudo regenerar la contraseña');
      setErrorMessage(message);
      toast({ title: 'Error', description: message, variant: 'destructive' });
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyEmpresaForm);
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const openEdit = (empresa: Empresa) => {
    setEditing(empresa);
    setForm({
      nit: empresa.nit,
      razon_social: empresa.razon_social,
      email_contacto: empresa.email_contacto ?? '',
      telefono: empresa.telefono ?? '',
      direccion: empresa.direccion ?? '',
      ciudad: empresa.ciudad ?? '',
      departamento: empresa.departamento ?? '',
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
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          {canCreate && (
            <DialogTrigger asChild>
              <Button onClick={openCreate}>Crear empresa</Button>
            </DialogTrigger>
          )}
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editing ? 'Editar Empresa' : 'Crear Empresa'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="nit">NIT</Label>
                  <Input id="nit" value={form.nit} onChange={(e) => setForm({ ...form, nit: e.target.value })} />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="razon_social">Razón social</Label>
                <Input id="razon_social" value={form.razon_social} onChange={(e) => setForm({ ...form, razon_social: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email_contacto">Correo de contacto</Label>
                <Input id="email_contacto" type="email" value={form.email_contacto} onChange={(e) => setForm({ ...form, email_contacto: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telefono">Teléfono</Label>
                <Input id="telefono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="direccion">Dirección</Label>
                <Input id="direccion" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ciudad">Ciudad</Label>
                <Input id="ciudad" value={form.ciudad} onChange={(e) => setForm({ ...form, ciudad: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="departamento">Departamento</Label>
                <Input id="departamento" value={form.departamento} onChange={(e) => setForm({ ...form, departamento: e.target.value })} />
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

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="nit-filter">Buscar por NIT</Label>
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
                      <Button variant="outline" size="sm" onClick={() => openEdit(empresa)}>Editar</Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => regenerarPasswordMutation.mutate(empresa.id)}
                        disabled={regenerarPasswordMutation.isPending}
                      >
                        Regenerar contraseña
                      </Button>
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

      {credenciales && (
        <PasswordRevealDialog
          open
          username={credenciales.username}
          password={credenciales.password}
          onClose={() => setCredenciales(null)}
        />
      )}
    </div>
  );
}
