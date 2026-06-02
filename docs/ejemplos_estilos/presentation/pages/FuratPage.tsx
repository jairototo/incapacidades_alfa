import { useState } from 'react';
import { Send, Trash2, Download } from 'lucide-react';

import {
  useDiscardFurat,
  useFuratList,
  useSubmitFurat,
} from '@/application/hooks/useClaims';
import { useDownloadFuratPdf } from '@/application/hooks/useDownloadDocuments';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { Furat } from '@/infrastructure/api/claims';
import {
  Badge,
  Button,
  DataTable,
  FilterBar,
  FormField,
  PageHeader,
  PageLayout,
  Pagination,
  Select,
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 15;

const STATUS_LABEL: Record<string, string> = {
  draft: 'Borrador',
  submitted: 'Radicada',
  accepted: 'Aceptada',
  rejected: 'Rechazada',
  synced: 'Sincronizada',
  discarded: 'Descartada',
};

type V = 'success' | 'warning' | 'info' | 'error' | 'neutral' | 'accent';
const STATUS_VARIANT: Record<string, V> = {
  draft: 'neutral',
  submitted: 'info',
  accepted: 'success',
  rejected: 'error',
  synced: 'accent',
  discarded: 'neutral',
};

export function FuratPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [status, setStatus] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useFuratList({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    status: status || undefined,
  });

  const submitMut = useSubmitFurat();
  const discardMut = useDiscardFurat();
  const downloadMut = useDownloadFuratPdf();

  const columns: DataTableColumn<Furat>[] = [
    {
      key: 'radicado',
      header: 'Radicado',
      cell: (r) => <span className="font-mono text-xs">{r.radicado || '—'}</span>,
      width: 'w-40',
    },
    { key: 'date', header: 'Fecha accidente', cell: (r) => r.accident_date, width: 'w-32' },
    { key: 'city', header: 'Ciudad', cell: (r) => r.accident_city, width: 'w-32' },
    {
      key: 'desc',
      header: 'Descripción',
      cell: (r) => <span className="line-clamp-2">{r.accident_description}</span>,
    },
    {
      key: 'status',
      header: 'Estado',
      cell: (r) => (
        <Badge variant={STATUS_VARIANT[r.status] ?? 'neutral'}>
          {STATUS_LABEL[r.status] ?? r.status}
        </Badge>
      ),
      width: 'w-32',
    },
    {
      key: 'actions',
      header: 'Acciones',
      cell: (r) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => downloadMut.mutate(r.id)}
            loading={downloadMut.isPending}
            leftIcon={<Download size={12} strokeWidth={1.75} aria-hidden />}
          >
            PDF
          </Button>
          {r.status === 'draft' && (
            <>
              <Button
                size="sm"
                onClick={() => submitMut.mutate(r.id)}
                loading={submitMut.isPending}
                leftIcon={<Send size={12} strokeWidth={1.75} aria-hidden />}
              >
                Radicar
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => discardMut.mutate(r.id)}
                loading={discardMut.isPending}
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
        title="FURAT — Accidentes de trabajo"
        description="Formato Único de Reporte de Accidente de Trabajo."
      />

      <FilterBar columns={3}>
        <FormField label="Empresa">
          <Select value={companyId} onChange={(e) => setCompanyId(e.target.value)}>
            <option value="">Todas</option>
            {companies.data?.items.map((c) => (
              <option key={c.id} value={c.id}>
                {c.legal_name}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Estado">
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option>
            {Object.entries(STATUS_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin FURAT registrados."
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
