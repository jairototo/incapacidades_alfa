import { useState } from 'react';

import { useAbsences, useAbsencesSummary } from '@/application/hooks/useAbsences';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { Absence } from '@/infrastructure/api/absences';
import {
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

export function AbsencesPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [absenceType, setAbsenceType] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useAbsences({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    absence_type: absenceType || undefined,
  });
  const summary = useAbsencesSummary({ company_id: companyId || undefined });

  const columns: DataTableColumn<Absence>[] = [
    { key: 'type', header: 'Tipo', cell: (r) => r.absence_type, width: 'w-32' },
    { key: 'start', header: 'Desde', cell: (r) => r.start_date, width: 'w-32' },
    { key: 'end', header: 'Hasta', cell: (r) => r.end_date, width: 'w-32' },
    { key: 'days', header: 'Días hábiles', cell: (r) => r.business_days, width: 'w-28' },
    { key: 'hours', header: 'Horas', cell: (r) => r.hours_lost, width: 'w-24' },
    { key: 'diag', header: 'Diagnóstico', cell: (r) => `${r.diagnosis_code} ${r.diagnosis_name}` },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader title="Ausencias laborales" description="Incapacidades y otros tipos de ausencia." />

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader title="Total ausencias" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">{summary.data?.total ?? 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Días hábiles" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">
              {summary.data?.total_business_days ?? 0}
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Horas perdidas" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">
              {summary.data?.total_hours_lost ?? 0}
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
        <FormField label="Tipo">
          <Select value={absenceType} onChange={(e) => setAbsenceType(e.target.value)}>
            <option value="">Todos</option>
            <option value="incapacidad_comun">Incapacidad común</option>
            <option value="incapacidad_laboral">Incapacidad laboral</option>
            <option value="licencia_maternidad">Lic. maternidad</option>
            <option value="licencia_paternidad">Lic. paternidad</option>
            <option value="luto">Luto</option>
          </Select>
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin ausencias registradas."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
