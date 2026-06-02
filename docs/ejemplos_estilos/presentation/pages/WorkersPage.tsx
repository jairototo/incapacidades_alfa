import { useState } from 'react';

import { useCompanies } from '@/application/hooks/useCompanies';
import { useWorkers } from '@/application/hooks/useWorkers';
import type { Worker } from '@/infrastructure/api/workers';
import {
  Badge,
  DataTable,
  FilterBar,
  PageHeader,
  PageLayout,
  Pagination,
  SearchInput,
  Select,
  type DataTableColumn,
} from '@/presentation/components/ui';

const PAGE_SIZE = 15;

const columns: DataTableColumn<Worker>[] = [
  {
    key: 'document',
    header: 'Documento',
    cell: (w) => (
      <span className="font-mono text-xs">
        {w.document_type} {w.document_number}
      </span>
    ),
    width: 'w-40',
  },
  { key: 'full_name', header: 'Nombre', cell: (w) => w.full_name },
  {
    key: 'status',
    header: 'Estado',
    cell: (w) => (
      <Badge variant={w.status === 'active' ? 'success' : 'neutral'}>{w.status}</Badge>
    ),
    width: 'w-28',
  },
  {
    key: 'salary',
    header: 'Salario',
    cell: (w) => (
      <span className="font-mono text-xs">{Number(w.salary).toLocaleString('es-CO')}</span>
    ),
    className: 'text-right',
    headerClassName: 'text-right',
    width: 'w-36',
  },
];

export function WorkersPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useWorkers({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    status: status || undefined,
    q: q.trim() ? q.trim() : undefined,
  });

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Trabajadores"
        description="Listado de trabajadores afiliados (lectura)."
        backTo="/health"
      />

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
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">Todos los estados</option>
          <option value="active">Activo</option>
          <option value="inactive">Inactivo</option>
        </Select>
        <SearchInput
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
          placeholder="Buscar por nombre o documento"
        />
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(w) => w.id}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Error al cargar trabajadores."
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

