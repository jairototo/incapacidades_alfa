import { useState } from 'react';

import { useAuditLogs } from '@/application/hooks/useAuditLogs';
import type { AuditLog } from '@/infrastructure/api/audit';
import {
  Badge,
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

const PAGE_SIZE = 20;

const RESULT_VARIANT: Record<string, 'success' | 'error' | 'warning'> = {
  ok: 'success',
  error: 'error',
  denied: 'warning',
};

export function AuditLogsPage() {
  const [offset, setOffset] = useState(0);
  const [moduleQ, setModuleQ] = useState('');
  const [actionQ, setActionQ] = useState('');

  const { data, isLoading, isError } = useAuditLogs({
    offset,
    limit: PAGE_SIZE,
    module: moduleQ || undefined,
    action: actionQ || undefined,
  });

  const columns: DataTableColumn<AuditLog>[] = [
    {
      key: 'occurred_at',
      header: 'Fecha',
      cell: (r) => (
        <span className="font-mono text-xs">
          {new Date(r.occurred_at).toLocaleString('es-CO')}
        </span>
      ),
      width: 'w-48',
    },
    { key: 'user', header: 'Usuario', cell: (r) => r.user_email || '—' },
    { key: 'module', header: 'Módulo', cell: (r) => r.module, width: 'w-32' },
    { key: 'action', header: 'Acción', cell: (r) => r.action, width: 'w-40' },
    { key: 'entity', header: 'Entidad', cell: (r) => r.entity_type, width: 'w-32' },
    {
      key: 'result',
      header: 'Resultado',
      cell: (r) => (
        <Badge variant={RESULT_VARIANT[r.result] ?? 'neutral'}>{r.result}</Badge>
      ),
      width: 'w-24',
    },
    { key: 'ip', header: 'IP', cell: (r) => r.ip_address || '—', width: 'w-32' },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Bitácora de auditoría"
        description="Trazas de acciones registradas en el portal."
      />

      <FilterBar columns={3}>
        <FormField label="Módulo">
          <Select value={moduleQ} onChange={(e) => setModuleQ(e.target.value)}>
            <option value="">Todos</option>
            <option value="auth">auth</option>
            <option value="companies">companies</option>
            <option value="workers">workers</option>
            <option value="affiliations">affiliations</option>
            <option value="claims">claims</option>
            <option value="absences">absences</option>
            <option value="contributions">contributions</option>
            <option value="portal_users">portal_users</option>
            <option value="admin">admin</option>
          </Select>
        </FormField>
        <FormField label="Acción">
          <Input value={actionQ} onChange={(e) => setActionQ(e.target.value)} placeholder="login, create, ..." />
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin registros de auditoría."
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
