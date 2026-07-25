import { useState } from 'react';
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
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { auditorService, type AuditorOption } from '@/services/auditorService';

const SUCURSALES = ['Cali', 'Medellín', 'Cartagena', 'Bogotá'];

interface FormState {
  username: string;
  nombre_completo: string;
  email: string;
  password: string;
  sucursal: string;
}

const emptyForm: FormState = { username: '', nombre_completo: '', email: '', password: '', sucursal: '' };

function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

export function AuditoresPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AuditorOption | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: auditores = [], isLoading } = useQuery({
    queryKey: ['auditores-admin'],
    queryFn: () => auditorService.reporte(),
  });

  const createMutation = useMutation({
    mutationFn: () => auditorService.create({
      username: form.username,
      email: form.email,
      nombre_completo: form.nombre_completo,
      password: form.password,
      sucursal: form.sucursal || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditores-admin'] });
      setDialogOpen(false);
      setForm(emptyForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => {
      setErrorMessage(extractErrorMessage(error, 'No se pudo crear el auditor'));
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay auditor en edición');
      return auditorService.update(editing.id, {
        nombre_completo: form.nombre_completo,
        email: form.email,
        sucursal: form.sucursal || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditores-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => {
      setErrorMessage(extractErrorMessage(error, 'No se pudo actualizar el auditor'));
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => auditorService.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditores-admin'] });
      setErrorMessage(null);
    },
    onError: (error: unknown) => {
      setErrorMessage(extractErrorMessage(error, 'No se pudo desactivar el auditor'));
    },
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const openEdit = (auditor: AuditorOption) => {
    setEditing(auditor);
    setForm({
      username: auditor.username,
      nombre_completo: auditor.nombre_completo,
      email: auditor.email,
      password: '',
      sucursal: auditor.sucursal ?? '',
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

  const handleDeactivate = (auditor: AuditorOption) => {
    const confirmed = window.confirm(
      `¿Seguro que deseas desactivar a ${auditor.nombre_completo}? Esto puede afectar la asignación automática de auditoría si es el auditor por defecto.`
    );
    if (confirmed) {
      deactivateMutation.mutate(auditor.id);
    }
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Auditores</h1>
          <p className="text-slate-500 mt-1">
            Auditores asignados por sucursal y su carga activa de incapacidades.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openCreate}>Nuevo Auditor</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editing ? 'Editar Auditor' : 'Nuevo Auditor'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="nombre_completo">Nombre completo</Label>
                <Input
                  id="nombre_completo"
                  value={form.nombre_completo}
                  onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña temporal</Label>
                  <Input
                    id="password"
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="sucursal">Sucursal</Label>
                <Select
                  value={form.sucursal || 'NONE'}
                  onValueChange={(value) => setForm({ ...form, sucursal: value === 'NONE' ? '' : value })}
                >
                  <SelectTrigger id="sucursal">
                    <SelectValue placeholder="Sin sucursal (auditor por defecto)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">Sin sucursal</SelectItem>
                    {SUCURSALES.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {errorMessage && (
              <p className="text-sm text-red-600">{errorMessage}</p>
            )}
            <DialogFooter>
              <Button
                onClick={handleSubmit}
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Sucursal</TableHead>
              <TableHead>Carga Activa</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && auditores.map((auditor) => (
              <TableRow key={auditor.id}>
                <TableCell className="font-medium">{auditor.nombre_completo}</TableCell>
                <TableCell>{auditor.email}</TableCell>
                <TableCell>{auditor.sucursal ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>{auditor.incapacidades_asignadas_activas}</TableCell>
                <TableCell>
                  <Badge variant={auditor.estado === 'ACTIVO' ? 'default' : 'secondary'}>
                    {auditor.estado}
                  </Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  <Button variant="outline" size="sm" onClick={() => openEdit(auditor)}>Editar</Button>
                  {auditor.estado === 'ACTIVO' && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeactivate(auditor)}
                    >
                      Desactivar
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <strong>Pendiente:</strong> el módulo de reasignación de incapacidades entre auditores
        no está implementado en esta iteración.
      </div>
    </div>
  );
}
