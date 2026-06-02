import { useMemo, useState } from 'react';
import { Plus, Send, Trash2, X, Download } from 'lucide-react';

import {
  useAffiliations,
  useCreateAffiliationDraft,
  useDiscardAffiliation,
  useSubmitAffiliation,
} from '@/application/hooks/useAffiliations';
import { useDownloadAffiliationPdf } from '@/application/hooks/useDownloadDocuments';
import { useCompanies } from '@/application/hooks/useCompanies';
import { useWorkers } from '@/application/hooks/useWorkers';
import type { Affiliation } from '@/infrastructure/api/affiliations';
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
  request_type: 'affiliation' | 'novelty';
  contributor_type_code: string;
  affiliate_type_code: string;
  observaciones: string;
}

const EMPTY_FORM: FormState = {
  company_id: '',
  worker_id: '',
  request_type: 'affiliation',
  contributor_type_code: '01',
  affiliate_type_code: '01',
  observaciones: '',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  submitted: 'Radicada',
  under_review: 'En revisión',
  accepted: 'Aceptada',
  rejected: 'Rechazada',
  synced: 'Sincronizada',
  discarded: 'Descartada',
};

type BadgeVariant = 'success' | 'warning' | 'info' | 'error' | 'neutral' | 'accent';

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  draft: 'neutral',
  submitted: 'info',
  under_review: 'warning',
  accepted: 'success',
  rejected: 'error',
  synced: 'accent',
  discarded: 'neutral',
};

export function AffiliationsPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [status, setStatus] = useState('');
  const [requestType, setRequestType] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const companies = useCompanies({ limit: 100 });
  const workersForForm = useWorkers({
    limit: 200,
    company_id: form.company_id || undefined,
  });

  const { data, isLoading, isError } = useAffiliations({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    status: status || undefined,
    request_type: requestType || undefined,
  });

  const createMutation = useCreateAffiliationDraft();
  const submitMutation = useSubmitAffiliation();
  const discardMutation = useDiscardAffiliation();
  const downloadMutation = useDownloadAffiliationPdf();

  const companyMap = useMemo(
    () => new Map(companies.data?.items.map((c) => [c.id, c.legal_name]) ?? []),
    [companies.data],
  );

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!form.company_id) {
      setFormError('Selecciona empresa.');
      return;
    }
    try {
      await createMutation.mutateAsync({
        company_id: form.company_id,
        request_type: form.request_type,
        worker_id: form.worker_id || null,
        contributor_type_code: form.contributor_type_code,
        affiliate_type_code: form.affiliate_type_code,
        payload: form.observaciones ? { observaciones: form.observaciones } : {},
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Error al crear el borrador');
    }
  }

  const columns: DataTableColumn<Affiliation>[] = [
    {
      key: 'radicado',
      header: 'Radicado',
      cell: (a) => <span className="font-mono text-xs">{a.radicado || '—'}</span>,
      width: 'w-40',
    },
    {
      key: 'company',
      header: 'Empresa',
      cell: (a) => companyMap.get(a.company_id) ?? a.company_id,
    },
    {
      key: 'request_type',
      header: 'Tipo',
      cell: (a) => <span className="capitalize">{a.request_type}</span>,
      width: 'w-32',
    },
    {
      key: 'status',
      header: 'Estado',
      cell: (a) => (
        <Badge variant={STATUS_VARIANT[a.status] ?? 'neutral'}>
          {STATUS_LABELS[a.status] ?? a.status}
        </Badge>
      ),
      width: 'w-32',
    },
    {
      key: 'coverage',
      header: 'Cobertura',
      cell: (a) => a.coverage_start_date ?? '—',
      width: 'w-32',
    },
    {
      key: 'actions',
      header: 'Acciones',
      cell: (a) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => downloadMutation.mutate(a.id)}
            loading={downloadMutation.isPending}
            leftIcon={<Download size={12} strokeWidth={1.75} aria-hidden />}
          >
            PDF
          </Button>
          {a.status === 'draft' && (
            <>
              <Button
                size="sm"
                onClick={() => submitMutation.mutate(a.id)}
                loading={submitMutation.isPending}
                leftIcon={<Send size={12} strokeWidth={1.75} aria-hidden />}
              >
                Radicar
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => discardMutation.mutate(a.id)}
                loading={discardMutation.isPending}
                leftIcon={<Trash2 size={12} strokeWidth={1.75} aria-hidden />}
              >
                Descartar
              </Button>
            </>
          )}
        </div>
      ),
      width: 'w-72',
    },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Afiliaciones SGRL"
        description="Solicitudes de afiliación y novedades formales radicadas ante la ARL."
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
            {showForm ? 'Cancelar' : 'Nuevo borrador'}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <CardHeader title="Crear borrador de afiliación" />
          <CardBody>
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 md:grid-cols-3">
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

              <FormField label="Tipo de solicitud" required>
                <Select
                  value={form.request_type}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      request_type: e.target.value as 'affiliation' | 'novelty',
                    }))
                  }
                >
                  <option value="affiliation">Afiliación</option>
                  <option value="novelty">Novedad formal</option>
                </Select>
              </FormField>

              <FormField label="Trabajador" hint="Opcional">
                <Select
                  value={form.worker_id}
                  onChange={(e) => setForm((f) => ({ ...f, worker_id: e.target.value }))}
                  disabled={!form.company_id}
                >
                  <option value="">(Sin trabajador asociado)</option>
                  {workersForForm.data?.items.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.full_name} ({w.document_number})
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Cód. tipo cotizante">
                <Input
                  type="text"
                  value={form.contributor_type_code}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, contributor_type_code: e.target.value }))
                  }
                />
              </FormField>

              <FormField label="Cód. tipo afiliado">
                <Input
                  type="text"
                  value={form.affiliate_type_code}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, affiliate_type_code: e.target.value }))
                  }
                />
              </FormField>

              <FormField label="Observaciones" className="md:col-span-3">
                <TextArea
                  value={form.observaciones}
                  onChange={(e) => setForm((f) => ({ ...f, observaciones: e.target.value }))}
                  rows={2}
                />
              </FormField>

              <div className="md:col-span-3 flex items-center justify-between">
                {formError && <span className="text-sm text-red-600">{formError}</span>}
                <Button
                  type="submit"
                  loading={createMutation.isPending}
                  leftIcon={<Plus size={14} strokeWidth={1.75} aria-hidden />}
                  className="ml-auto"
                >
                  Crear borrador
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
          value={requestType}
          onChange={(e) => {
            setRequestType(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todos los tipos</option>
          <option value="affiliation">Afiliación</option>
          <option value="novelty">Novedad formal</option>
        </Select>
        <Select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(a) => a.id}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Error al cargar afiliaciones."
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

