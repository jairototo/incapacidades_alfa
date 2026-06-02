import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useCompanies } from '@/application/hooks/useCompanies';
import type { Company } from '@/infrastructure/api/companies';
import {
  Badge,
  DataTable,
  FilterBar,
  PageHeader,
  PageLayout,
  Pagination,
  SearchInput,
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 10;

const columns: DataTableColumn<Company>[] = [
  {
    key: 'nit',
    header: 'NIT',
    cell: (c) => <span className="font-mono text-xs">{c.nit}</span>,
    width: 'w-32',
  },
  { key: 'legal_name', header: 'Razón social', cell: (c) => c.legal_name },
  { key: 'main_city', header: 'Ciudad', cell: (c) => c.main_city },
  { key: 'risk_level', header: 'Riesgo', cell: (c) => c.risk_level },
  {
    key: 'arl_status',
    header: 'ARL',
    cell: (c) => <Badge variant="success">{c.arl_status}</Badge>,
  },
  {
    key: 'actions',
    header: '',
    cell: (c) => (
      <Link
        to={`/companies/${c.id}`}
        className="text-sm font-medium text-brand-600 hover:text-brand-700"
      >
        Ver detalle
      </Link>
    ),
    className: 'text-right',
  },
];

export function CompaniesPage() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const { data, isLoading, isError } = useCompanies({
    offset,
    limit: PAGE_SIZE,
    search: search.trim() ? search.trim() : undefined,
  });

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Empresas"
        description="Catálogo de empresas afiliadas (lectura)."
        backTo="/health"
      />

      <FilterBar columns={3}>
        <div className="md:col-span-3">
          <SearchInput
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
            placeholder="Buscar por razón social, NIT o nombre comercial"
          />
        </div>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(c) => c.id}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Error al cargar empresas."
        emptyMessage="Sin empresas registradas."
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

