import { useState } from 'react';
import { Plus, X, KeyRound, Trash2 } from 'lucide-react';

import {
  useCreatePortalUser,
  useDeletePortalUser,
  usePortalUsers,
  useResetPortalUserPassword,
  useUpdatePortalUser,
} from '@/application/hooks/usePortalUsers';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { PortalUser } from '@/infrastructure/api/portal_users';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  DataTable,
  FilterBar,
  FormField,
  Input,
  PageHeader,
  PageLayout,
  Pagination,
  SearchInput,
  Select,
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 15;

const ROLE_VARIANT: Record<string, 'info' | 'accent' | 'success' | 'neutral'> = {
  admin: 'accent',
  asesor: 'info',
  empresa: 'success',
  trabajador: 'neutral',
};

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'error'> = {
  active: 'success',
  disabled: 'warning',
  locked: 'error',
};

interface FormState {
  email: string;
  full_name: string;
  role: 'admin' | 'asesor' | 'empresa' | 'trabajador';
  password: string;
  company_id: string;
}

const EMPTY_FORM: FormState = {
  email: '',
  full_name: '',
  role: 'asesor',
  password: '',
  company_id: '',
};

export function PortalUsersPage() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = usePortalUsers({
    offset,
    limit: PAGE_SIZE,
    search: search || undefined,
    role: role || undefined,
    status: status || undefined,
  });

  const createMut = useCreatePortalUser();
  const updateMut = useUpdatePortalUser();
  const deleteMut = useDeletePortalUser();
  const resetMut = useResetPortalUserPassword();

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!form.email || !form.password || form.password.length < 8) {
      setFormError('Email y contraseña (≥8 caracteres) son obligatorios.');
      return;
    }
    try {
      await createMut.mutateAsync({
        email: form.email,
        full_name: form.full_name,
        role: form.role,
        password: form.password,
        company_id: form.company_id || null,
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Error al crear usuario');
    }
  }

  function handleToggleStatus(u: PortalUser) {
    const next = u.status === 'active' ? 'disabled' : 'active';
    updateMut.mutate({ id: u.id, input: { status: next as 'active' | 'disabled' } });
  }

  function handleReset(u: PortalUser) {
    const pw = window.prompt(`Nueva contraseña para ${u.email} (mín. 8 caracteres):`);
    if (!pw || pw.length < 8) return;
    resetMut.mutate({ id: u.id, password: pw });
  }

  function handleDelete(u: PortalUser) {
    if (!window.confirm(`¿Eliminar usuario ${u.email}?`)) return;
    deleteMut.mutate(u.id);
  }

  const columns: DataTableColumn<PortalUser>[] = [
    { key: 'email', header: 'Email', cell: (u) => <span className="font-mono text-xs">{u.email}</span> },
    { key: 'name', header: 'Nombre', cell: (u) => u.full_name },
    {
      key: 'role',
      header: 'Rol',
      cell: (u) => <Badge variant={ROLE_VARIANT[u.role] ?? 'neutral'}>{u.role}</Badge>,
      width: 'w-28',
    },
    {
      key: 'status',
      header: 'Estado',
      cell: (u) => <Badge variant={STATUS_VARIANT[u.status] ?? 'neutral'}>{u.status}</Badge>,
      width: 'w-28',
    },
    {
      key: 'actions',
      header: 'Acciones',
      cell: (u) => (
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleToggleStatus(u)}>
            {u.status === 'active' ? 'Deshabilitar' : 'Habilitar'}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleReset(u)}
            leftIcon={<KeyRound size={12} strokeWidth={1.75} aria-hidden />}
          >
            Reset
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleDelete(u)}
            leftIcon={<Trash2 size={12} strokeWidth={1.75} aria-hidden />}
          >
            Eliminar
          </Button>
        </div>
      ),
      width: 'w-72',
    },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Usuarios del portal"
        description="Administración de usuarios y permisos."
        actions={
          <Button
            variant={showForm ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => setShowForm((v) => !v)}
            leftIcon={
              showForm ? <X size={14} strokeWidth={1.75} aria-hidden /> : <Plus size={14} strokeWidth={1.75} aria-hidden />
            }
          >
            {showForm ? 'Cancelar' : 'Nuevo usuario'}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <CardHeader title="Crear usuario" />
          <CardBody>
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField label="Email" required>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  required
                />
              </FormField>
              <FormField label="Nombre completo" required>
                <Input
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  required
                />
              </FormField>
              <FormField label="Rol" required>
                <Select
                  value={form.role}
                  onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as FormState['role'] }))}
                >
                  <option value="admin">admin</option>
                  <option value="asesor">asesor</option>
                  <option value="empresa">empresa</option>
                  <option value="trabajador">trabajador</option>
                </Select>
              </FormField>
              <FormField label="Empresa (opcional)">
                <Select
                  value={form.company_id}
                  onChange={(e) => setForm((f) => ({ ...f, company_id: e.target.value }))}
                >
                  <option value="">—</option>
                  {companies.data?.items.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.legal_name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Contraseña (≥8)" required>
                <Input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  required
                  minLength={8}
                />
              </FormField>
              <div className="md:col-span-2 flex justify-end gap-2">
                {formError && <p className="text-sm text-red-600">{formError}</p>}
                <Button type="submit" loading={createMut.isPending}>
                  Crear
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      <FilterBar columns={3}>
        <FormField label="Buscar">
          <SearchInput value={search} onChange={(e) => setSearch(e.target.value)} placeholder="email o nombre" />
        </FormField>
        <FormField label="Rol">
          <Select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="">Todos</option>
            <option value="admin">admin</option>
            <option value="asesor">asesor</option>
            <option value="empresa">empresa</option>
            <option value="trabajador">trabajador</option>
          </Select>
        </FormField>
        <FormField label="Estado">
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option>
            <option value="active">active</option>
            <option value="disabled">disabled</option>
            <option value="locked">locked</option>
          </Select>
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(u) => u.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin usuarios."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
