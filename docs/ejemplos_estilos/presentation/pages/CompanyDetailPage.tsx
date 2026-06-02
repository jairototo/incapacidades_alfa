import { useParams } from 'react-router-dom';

import {
  useCompany,
  useCompanySites,
  useCompanyWorkCenters,
} from '@/application/hooks/useCompanies';
import type { CompanySite, WorkCenter } from '@/infrastructure/api/companies';
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  DataTable,
  PageHeader,
  PageLayout,
  Spinner,
  type DataTableColumn,
} from '@/presentation/components/ui';

const siteColumns: DataTableColumn<CompanySite>[] = [
  { key: 'name', header: 'Nombre', cell: (s) => s.name },
  { key: 'city', header: 'Ciudad', cell: (s) => s.city },
  { key: 'department', header: 'Departamento', cell: (s) => s.department },
  {
    key: 'status',
    header: 'Estado',
    cell: (s) => (
      <Badge variant={s.status === 'active' ? 'success' : 'neutral'}>{s.status}</Badge>
    ),
    width: 'w-28',
  },
];

const workCenterColumns: DataTableColumn<WorkCenter>[] = [
  {
    key: 'code',
    header: 'Código',
    cell: (w) => <span className="font-mono text-xs">{w.code}</span>,
    width: 'w-32',
  },
  { key: 'name', header: 'Nombre', cell: (w) => w.name },
  { key: 'risk_class', header: 'Clase riesgo', cell: (w) => w.risk_class, width: 'w-32' },
  {
    key: 'rate',
    header: 'Tarifa',
    cell: (w) => `${w.rate}%`,
    className: 'text-right font-mono text-xs',
    headerClassName: 'text-right',
    width: 'w-24',
  },
];

export function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const company = useCompany(id);
  const sites = useCompanySites(id);
  const workCenters = useCompanyWorkCenters(id);

  if (company.isLoading) {
    return (
      <PageLayout width="wide">
        <Spinner label="Cargando empresa..." />
      </PageLayout>
    );
  }
  if (company.isError || !company.data) {
    return (
      <PageLayout width="wide">
        <p className="text-red-600">No se pudo cargar la empresa.</p>
      </PageLayout>
    );
  }

  const c = company.data;

  return (
    <PageLayout width="wide">
      <PageHeader
        title={c.legal_name}
        description={`NIT ${c.nit}${c.commercial_name ? ` · ${c.commercial_name}` : ''}`}
        backTo="/companies"
        backLabel="Volver a empresas"
      />

      <Card className="mb-8">
        <CardHeader title="Información general" />
        <CardBody>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 md:grid-cols-2">
            <Field label="Tipo" value={c.company_type} />
            <Field label="Estado ARL" value={c.arl_status} />
            <Field label="Nivel de riesgo" value={c.risk_level} />
            <Field label="Actividad económica" value={c.economic_activity_code} />
            <Field label="Ciudad principal" value={c.main_city} />
            <Field label="Dirección" value={c.main_address} />
            <Field label="Representante legal" value={c.legal_representative} />
            <Field label="Source" value={c.source_system} />
          </dl>
        </CardBody>
      </Card>

      <section className="mb-8">
        <h2 className="mb-3 text-xl font-bold text-brand-900">Sitios</h2>
        <DataTable
          columns={siteColumns}
          data={sites.data}
          rowKey={(s) => s.id}
          isLoading={sites.isLoading}
          isError={sites.isError}
          emptyMessage="Sin sitios registrados."
        />
      </section>

      <section>
        <h2 className="mb-3 text-xl font-bold text-brand-900">Centros de trabajo</h2>
        <DataTable
          columns={workCenterColumns}
          data={workCenters.data}
          rowKey={(w) => w.id}
          isLoading={workCenters.isLoading}
          isError={workCenters.isError}
          emptyMessage="Sin centros de trabajo registrados."
        />
      </section>
    </PageLayout>
  );
}

function Field({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div className="text-sm">
      <dt className="text-xs uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-0.5 font-medium text-gray-900">{value || '—'}</dd>
    </div>
  );
}

