import { useState } from 'react';
import { Download } from 'lucide-react';

import { useFurepList } from '@/application/hooks/useClaims';
import { useDownloadFurepPdf } from '@/application/hooks/useDownloadDocuments';
import { useCompanies } from '@/application/hooks/useCompanies';
import type { Furep } from '@/infrastructure/api/claims';
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

export function FurepPage() {
  const [offset, setOffset] = useState(0);
  const [companyId, setCompanyId] = useState('');
  const [status, setStatus] = useState('');

  const companies = useCompanies({ limit: 100 });
  const { data, isLoading, isError } = useFurepList({
    offset,
    limit: PAGE_SIZE,
    company_id: companyId || undefined,
    status: status || undefined,
  });

  const downloadMut = useDownloadFurepPdf();

  const columns: DataTableColumn<Furep>[] = [
    { key: 'disease', header: 'Enfermedad sospechada', cell: (r) => r.disease_suspected },
    {
      key: 'start',
      header: 'Inicio síntomas',
      cell: (r) => r.symptoms_start_date ?? '—',
      width: 'w-36',
    },
    { key: 'eps', header: 'EPS', cell: (r) => r.eps, width: 'w-40' },
    {
      key: 'status',
      header: 'Estado',
      cell: (r) => <Badge variant="info">{r.status}</Badge>,
      width: 'w-32',
    },
    {
      key: 'actions',
      header: 'Acciones',
      cell: (r) => (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => downloadMut.mutate(r.id)}
          loading={downloadMut.isPending}
          leftIcon={<Download size={12} strokeWidth={1.75} aria-hidden />}
        >
          PDF
        </Button>
      ),
      width: 'w-32',
    },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="FUREP — Enfermedades laborales"
        description="Formato Único de Reporte de Enfermedad Profesional."
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
            <option value="draft">Borrador</option>
            <option value="submitted">Radicada</option>
            <option value="accepted">Aceptada</option>
            <option value="rejected">Rechazada</option>
          </Select>
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin FUREP registrados."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
