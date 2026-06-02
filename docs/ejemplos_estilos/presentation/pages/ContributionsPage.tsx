import { useState } from 'react';

import { useContributions, useContributionsSummary } from '@/application/hooks/useContributions';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { Contribution } from '@/infrastructure/api/contributions';
import {
  Badge,
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
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 15;

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
  paid: 'success',
  pending: 'warning',
  overdue: 'error',
  partial: 'info',
};

function fmt(amount: string | number): string {
  const n = typeof amount === 'string' ? Number(amount) : amount;
  if (!isFinite(n)) return '—';
  return n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
}

export function ContributionsPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [period, setPeriod] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useContributions({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    period: period || undefined,
  });
  const summary = useContributionsSummary({
    company_id: companyId || undefined,
    period: period || undefined,
  });

  const columns: DataTableColumn<Contribution>[] = [
    { key: 'period', header: 'Periodo', cell: (r) => r.period, width: 'w-28' },
    { key: 'base', header: 'Base salario', cell: (r) => fmt(r.base_salary), width: 'w-36' },
    { key: 'ibc', header: 'IBC', cell: (r) => fmt(r.ibc), width: 'w-36' },
    { key: 'rate', header: 'Tarifa', cell: (r) => `${(Number(r.rate) * 100).toFixed(3)}%`, width: 'w-24' },
    { key: 'amount', header: 'Monto', cell: (r) => fmt(r.amount), width: 'w-36' },
    {
      key: 'status',
      header: 'Estado',
      cell: (r) => (
        <Badge variant={STATUS_VARIANT[r.payment_status] ?? 'neutral'}>{r.payment_status}</Badge>
      ),
      width: 'w-28',
    },
    { key: 'op', header: 'Operador', cell: (r) => r.operator, width: 'w-28' },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader title="Aportes SGRL" description="Pagos PILA y conciliación de aportes." />

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader title="Monto total" />
          <CardBody>
            <p className="text-2xl font-bold text-brand-900">{fmt(summary.data?.total_amount ?? 0)}</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Registros" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">{summary.data?.count ?? 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Inconsistencias" />
          <CardBody>
            <p className="text-3xl font-bold text-red-600">
              {summary.data?.inconsistencies ?? 0}
            </p>
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
        <FormField label="Periodo (YYYY-MM)">
          <Input
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2025-01"
          />
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin aportes registrados."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
