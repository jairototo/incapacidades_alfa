# Patrones de Composición de Páginas

Fuente de verdad: [`docs/ejemplos_estilos/presentation/pages/`](../../../../docs/ejemplos_estilos/presentation/pages/)

---

## Patrón estándar — Lista con filtros y paginación

Toda página de listado sigue esta composición. Basada en `AbsencesPage.tsx` del style guide.

```tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { incapacidadService } from '@/services/incapacidadService';
import {
  PageLayout, PageHeader, FilterBar, FormField,
  Select, DataTable, Pagination, type DataTableColumn
} from '@/components/ui';
import type { Incapacidad } from '@/types/incapacidad';

const PAGE_SIZE = 15;

export function MiListaPage() {
  // Estado de filtros y paginación
  const [offset, setOffset] = useState(0);
  const [estado, setEstado] = useState('ALL');
  const [empresa, setEmpresa] = useState('');

  // Reset paginación al cambiar filtros
  const handleFiltroChange = (setter: (v: string) => void) => (val: string) => {
    setter(val);
    setOffset(0);
  };

  // React Query — query key incluye todos los filtros
  const { data, isLoading, isError } = useQuery({
    queryKey: ['mi-lista', { estado, empresa, offset }],
    queryFn: () => incapacidadService.list({
      estado: estado !== 'ALL' ? estado : undefined,
      empresa: empresa || undefined,
      offset,
      limit: PAGE_SIZE,
    }),
    staleTime: 5 * 60 * 1000,
  });

  const columns: DataTableColumn<Incapacidad>[] = [
    { key: 'radicado', header: 'Radicado', cell: (r) => r.numero_radicado, width: 'w-40', className: 'font-mono' },
    { key: 'nombre',   header: 'Empleado',  cell: (r) => `${r.primer_nombre} ${r.primer_apellido}` },
    { key: 'estado',   header: 'Estado',    cell: (r) => <BadgeEstado estado={r.estado} /> },
    { key: 'fecha',    header: 'Radicada',  cell: (r) => formatDate(r.fecha_radicacion), width: 'w-32' },
  ];

  return (
    <PageLayout width="wide">
      <PageHeader
        title="Incapacidades"
        description="Listado de solicitudes radicadas."
        actions={<Button size="sm" variant="secondary">Exportar CSV</Button>}
      />

      <FilterBar columns={3}>
        <FormField label="Estado">
          <Select value={estado} onChange={(e) => handleFiltroChange(setEstado)(e.target.value)}>
            <option value="ALL">Todos</option>
            <option value="RADICADA">Radicada</option>
            <option value="EN_AUDITORIA">En Auditoría</option>
          </Select>
        </FormField>
        <FormField label="Empresa">
          <SearchInput value={empresa} onChange={handleFiltroChange(setEmpresa)} placeholder="Buscar empresa..." />
        </FormField>
      </FilterBar>

      <DataTable
        columns={columns}
        data={data?.items}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sin incapacidades registradas."
        onRowClick={(r) => navigate(`/incapacidades/${r.id}`)}
      />

      <div className="mt-4">
        <Pagination total={data?.total ?? 0} offset={offset} limit={PAGE_SIZE} onChange={setOffset} />
      </div>
    </PageLayout>
  );
}
```

---

## Patrón — Página de detalle con pestañas

Basada en `GestionarPage.tsx` del proyecto.

```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

export function DetalleIncapacidadPage() {
  return (
    <PageLayout width="default">
      <PageHeader title="Gestionar Incapacidad" backTo="/incapacidades/pendientes" />

      <Tabs defaultValue="auditoria">
        <TabsList>
          <TabsTrigger value="auditoria">Auditoría</TabsTrigger>
          <TabsTrigger value="detalle">Detalle completo</TabsTrigger>
          <TabsTrigger value="historial">Historial</TabsTrigger>
        </TabsList>

        <TabsContent value="auditoria">
          <AuditoriaFormulario incapacidadId={id} />
        </TabsContent>
        <TabsContent value="detalle">
          <IncapacidadDetalle incapacidad={data} />
        </TabsContent>
        <TabsContent value="historial">
          <HistorialTimeline historial={historial} />
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}
```

---

## Patrón — Dashboard con métricas y gráficos

```tsx
export function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getStats,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <PageLayout width="wide">
      <PageHeader title="Dashboard" description="Visión general del sistema." />

      {/* Tarjetas KPI — grid de métricas */}
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader title="Pendientes" />
          <CardBody>
            <p className="text-3xl font-bold text-brand-900">{stats?.pendientes ?? 0}</p>
          </CardBody>
        </Card>
        {/* más cards... */}
      </div>

      {/* Gráficos — Recharts */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <TopEmpresasChart />
        <DistribucionEstadosPieChart />
      </div>
    </PageLayout>
  );
}
```

---

## Reglas de composición

1. **Siempre `PageLayout` como raíz** de la página (nunca `div` con márgenes manuales).
2. **`PageHeader` inmediatamente después** de `PageLayout` — nunca enterrado dentro de un Card.
3. **`FilterBar` antes de `DataTable`** — siempre separados, nunca dentro de la tabla.
4. **`Pagination` fuera de `DataTable`** con `mt-4`.
5. **Reset de `offset` al cambiar filtros** — obligatorio para no quedarse en una página que ya no existe.
6. **`value="ALL"` en Select vacío** — nunca `value=""` (incompatible con Shadcn/ui). Filtrar en `queryFn`.
7. **Gráficos en `grid grid-cols-1 md:grid-cols-2`** — siempre responsive, máximo 2 por fila.
