import { useMemo, useState } from 'react';
import { Plus, Send, X } from 'lucide-react';

import { useCompanies } from '@/application/hooks/useCompanies';
import {
  useCreateWorkerNovelty,
  useWorkerNovelties,
} from '@/application/hooks/useWorkerNovelties';
import { useWorkers } from '@/application/hooks/useWorkers';
import {
  NOVELTY_TYPES,
  type NoveltyType,
  type WorkerNovelty,
} from '@/infrastructure/api/worker_novelties';
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
  Select,
  TextArea,
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 15;

interface FormState {
  company_id: string;
  worker_id: string;
  novelty_type: NoveltyType;
  effective_date: string;
  previous_value: string;
  new_value: string;
  description: string;
}

const EMPTY_FORM: FormState = {
  company_id: '',
  worker_id: '',
  novelty_type: 'WORK_CENTER_CHANGE',
  effective_date: new Date().toISOString().slice(0, 10),
  previous_value: '',
  new_value: '',
  description: '',
};

type BadgeVariant = 'success' | 'warning' | 'info' | 'error' | 'neutral' | 'accent';

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  draft: 'neutral',
  submitted: 'info',
  accepted: 'success',
  rejected: 'error',
  synced: 'accent',
};

export function WorkerNoveltiesPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [status, setStatus] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const companies = useCompanies({ limit: 100 });
  const formCompanyId = form.company_id || companyId;
  const workersForForm = useWorkers({
    limit: 200,
    company_id: formCompanyId || undefined,
  });

  const { data, isLoading, isError } = useWorkerNovelties({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    status: status || undefined,
    novelty_type: typeFilter || undefined,
  });

  const createMutation = useCreateWorkerNovelty();

  const companyMap = useMemo(
    () => new Map(companies.data?.items.map((c) => [c.id, c.legal_name]) ?? []),
    [companies.data],
  );

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!form.company_id || !form.worker_id) {
      setFormError('Selecciona empresa y trabajador.');
      return;
    }
    try {
      await createMutation.mutateAsync({
        company_id: form.company_id,
        worker_id: form.worker_id,
        novelty_type: form.novelty_type,
        effective_date: form.effective_date,
        previous_value: form.previous_value,
        new_value: form.new_value,
        description: form.description,
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Error al crear la novedad');
    }
  }

  const columns: DataTableColumn<WorkerNovelty>[] = [
    {
      key: 'company',
      header: 'Empresa',
      cell: (n) => companyMap.get(n.company_id) ?? n.company_id,
    },
    {
      key: 'novelty_type',
      header: 'Tipo',
      cell: (n) => <span className="font-mono text-xs">{n.novelty_type}</span>,
      width: 'w-48',
    },
    {
      key: 'effective_date',
      header: 'Fecha efectiva',
      cell: (n) => n.effective_date,
      width: 'w-36',
    },
    {
      key: 'status',
      header: 'Estado',
      cell: (n) => (
        <Badge variant={STATUS_VARIANT[n.status] ?? 'neutral'}>{n.status}</Badge>
      ),
      width: 'w-28',
    },
    {
      key: 'description',
      header: 'Descripción',
      cell: (n) => <span className="text-gray-600">{n.description}</span>,
    },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Novedades SGRL"
        description="Novedades laborales reportadas para la ARL."
        backTo="/health"
        actions={
          <Button
            variant={showForm ? 'secondary' : 'primary'}
            size="sm"
            onClick={() => setShowForm((v) => !v)}
            leftIcon={
              showForm ? (
                <X size={14} strokeWidth={1.75} aria-hidden />
              ) : (
                <Plus size={14} strokeWidth={1.75} aria-hidden />
              )
            }
          >
            {showForm ? 'Cancelar' : 'Nueva novedad'}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <CardHeader title="Registrar nueva novedad" />
          <CardBody>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <FormField label="Empresa" required>
                <Select
                  value={form.company_id}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, company_id: e.target.value, worker_id: '' }))
                  }
                  required
                >
                  <option value="">Seleccionar empresa...</option>
                  {companies.data?.items.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.legal_name}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Trabajador" required>
                <Select
                  value={form.worker_id}
                  onChange={(e) => setForm((f) => ({ ...f, worker_id: e.target.value }))}
                  required
                  disabled={!form.company_id}
                >
                  <option value="">Seleccionar trabajador...</option>
                  {workersForForm.data?.items.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.full_name} ({w.document_number})
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Tipo de novedad" required>
                <Select
                  value={form.novelty_type}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, novelty_type: e.target.value as NoveltyType }))
                  }
                >
                  {NOVELTY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Fecha efectiva" required>
                <Input
                  type="date"
                  value={form.effective_date}
                  onChange={(e) => setForm((f) => ({ ...f, effective_date: e.target.value }))}
                  required
                />
              </FormField>

              <FormField label="Valor anterior">
                <Input
                  type="text"
                  value={form.previous_value}
                  onChange={(e) => setForm((f) => ({ ...f, previous_value: e.target.value }))}
                />
              </FormField>

              <FormField label="Valor nuevo">
                <Input
                  type="text"
                  value={form.new_value}
                  onChange={(e) => setForm((f) => ({ ...f, new_value: e.target.value }))}
                />
              </FormField>

              <FormField label="Descripción" className="md:col-span-3">
                <TextArea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                />
              </FormField>

              <div className="md:col-span-3 flex items-center justify-between">
                {formError && <span className="text-sm text-red-600">{formError}</span>}
                <Button
                  type="submit"
                  loading={createMutation.isPending}
                  leftIcon={<Send size={14} strokeWidth={1.75} aria-hidden />}
                  className="ml-auto"
                >
                  Radicar novedad
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      <FilterBar columns={3}>
        <Select
          value={companyId}
          onChange={(e) => {
            setCompanyId(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todas las empresas</option>
          {companies.data?.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.legal_name}
            </option>
          ))}
        </Select>
        <Select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todos los tipos</option>
          {NOVELTY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todos los estados</option>
          <option value="draft">Borrador</option>
          <option value="submitted">Radicada</option>
          <option value="accepted">Aceptada</option>
          <option value="rejected">Rechazada</option>
          <option value="synced">Sincronizada</option>
        </Select>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(n) => n.id}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Error al cargar novedades."
      />

      <div className="mt-4">
        <Pagination
          total={data?.total ?? 0}
          offset={offset}
          limit={PAGE_SIZE}
          onChange={setOffset}
        />
      </div>
    </PageLayout>
  );
}
