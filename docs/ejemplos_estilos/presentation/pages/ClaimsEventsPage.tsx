import { useState } from 'react';

import { useClaimEvents, useClaimEventsSummary } from '@/application/hooks/useClaims';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { ClaimEvent } from '@/infrastructure/api/claims';
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
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

const SEVERITY_VARIANT: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
  leve: 'info',
  moderado: 'warning',
  grave: 'error',
  mortal: 'error',
};

export function ClaimsEventsPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [eventType, setEventType] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useClaimEvents({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    event_type: eventType || undefined,
  });
  const summary = useClaimEventsSummary({ company_id: companyId || undefined });

  const columns: DataTableColumn<ClaimEvent>[] = [
    { key: 'type', header: 'Tipo', cell: (r) => r.event_type, width: 'w-28' },
    { key: 'event_date', header: 'Fecha evento', cell: (r) => r.event_date, width: 'w-32' },
    { key: 'notice_date', header: 'Fecha aviso', cell: (r) => r.notice_date, width: 'w-32' },
    {
      key: 'severity',
      header: 'Gravedad',
      cell: (r) => (
        <Badge variant={SEVERITY_VARIANT[r.severity] ?? 'neutral'}>{r.severity}</Badge>
      ),
      width: 'w-28',
    },
    { key: 'days_lost', header: 'Días perdidos', cell: (r) => r.days_lost, width: 'w-32' },
    {
      key: 'status',
      header: 'Estado',
      cell: (r) => <Badge variant="info">{r.status}</Badge>,
      width: 'w-32',
    },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader title="Eventos de siniestralidad" description="FURAT/FUREP consolidados." />

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader title="Total eventos" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">{summary.data?.total ?? 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Días perdidos" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">
              {summary.data?.total_days_lost ?? 0}
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Por gravedad" />
          <CardBody>
            <ul className="text-sm text-gray-700">
              {Object.entries(summary.data?.by_severity ?? {}).map(([k, v]) => (
                <li key={k} className="flex justify-between">
                  <span className="capitalize">{k}</span>
                  <span className="font-medium">{v}</span>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      </div>

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
        <FormField label="Tipo">
          <Select value={eventType} onChange={(e) => setEventType(e.target.value)}>
            <option value="">Todos</option>
            <option value="furat">FURAT</option>
            <option value="furep">FUREP</option>
          </Select>
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin eventos."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
