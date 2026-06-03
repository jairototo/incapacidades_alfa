# Catálogo de Componentes UI — Sistema Interno

Fuente de verdad: [`docs/ejemplos_estilos/presentation/components/ui/`](../../../../docs/ejemplos_estilos/presentation/components/ui/)

Todos los componentes usan el helper `cn()` (`clsx + tailwind-merge`) de `src/lib/utils.ts`.
Importación: `import { Button, DataTable, ... } from '@/components/ui';`

---

## Button

```tsx
<Button
  variant="primary"   // 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent'
  size="md"           // 'sm' | 'md' | 'lg'
  loading={false}     // muestra Loader2 animado, deshabilita el botón
  leftIcon={<Icon />} // ícono antes del texto (se oculta si loading)
  rightIcon={<Icon />}
>
  Texto
</Button>
```

**Variantes de color:**
- `primary` → `brand-600` (azul institucional)
- `secondary` → borde `brand-600`, fondo blanco
- `ghost` → transparente, texto `brand-900`
- `danger` → `red-600`
- `accent` → `lime` (verde limón)

**Tamaños:** `sm=h-8`, `md=h-10`, `lg=h-12`

---

## DataTable

Wrapper tipado genérico sobre `<table>` nativo. Maneja loading, error y empty states automáticamente.

```tsx
const columns: DataTableColumn<Incapacidad>[] = [
  {
    key: 'radicado',
    header: 'Radicado',
    cell: (row) => row.numero_radicado,
    width: 'w-40',          // opcional — ancho fijo Tailwind
    className: 'font-mono', // opcional — clases extra para la celda
  },
];

<DataTable
  columns={columns}
  data={data?.items}
  rowKey={(row) => row.id}
  isLoading={isLoading}
  isError={isError}
  errorMessage="Error al cargar incapacidades."
  emptyMessage="Sin resultados."
  onRowClick={(row) => navigate(`/incapacidades/${row.id}`)} // opcional
/>
```

**Comportamiento de filas:**
- Sin `onRowClick`: hover gris suave (`gray-50`)
- Con `onRowClick`: cursor pointer, hover `brand-50`

---

## FilterBar

Cuadrícula responsive para agrupar filtros. Mobile: 1 columna. Desktop: 2, 3 o 4 columnas.

```tsx
<FilterBar columns={3}>   {/* 2 | 3 | 4 */}
  <FormField label="Estado">
    <Select value={estado} onChange={(e) => setEstado(e.target.value)}>
      <option value="ALL">Todos</option>
      <option value="RADICADA">Radicada</option>
    </Select>
  </FormField>
  <FormField label="Empresa">
    <SearchInput value={empresa} onChange={setEmpresa} placeholder="Buscar empresa..." />
  </FormField>
  <FormField label="Fecha desde">
    <Input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
  </FormField>
</FilterBar>
```

---

## PageLayout

Contenedor estándar de página con padding y max-width.

```tsx
<PageLayout width="wide">   {/* 'narrow'=max-w-3xl | 'default'=max-w-6xl | 'wide'=max-w-7xl | 'full' */}
  {/* contenido */}
</PageLayout>
```

---

## PageHeader

Encabezado de página. Título h1 bold en `brand-900`. Slot de acciones a la derecha.

```tsx
<PageHeader
  title="Incapacidades Pendientes"
  description="Solicitudes sin asignar auditor."
  backTo="/dashboard"         // opcional — link con ArrowLeft
  backLabel="Volver"
  actions={<Button size="sm">Exportar CSV</Button>}  // opcional
/>
```

---

## Badge

Etiqueta de estado con variante semántica.

```tsx
<Badge variant="success">Aprobada</Badge>
<Badge variant="warning">Observada</Badge>
<Badge variant="error">Rechazada</Badge>
<Badge variant="info">En Auditoría</Badge>
<Badge variant="neutral">Radicada</Badge>
<Badge variant="accent">En Pago</Badge>
```

**Mapa recomendado de estados de incapacidad:**
| Estado | Variante |
|---|---|
| `RADICADA` | `neutral` |
| `EN_AUDITORIA` | `info` |
| `OBSERVADA` | `warning` |
| `APROBADA` / `APROBADA_PARCIALMENTE` | `success` |
| `RECHAZADA` | `error` |
| `EN_PAGO` | `accent` |
| `PAGADA` | `success` |

---

## Card

Contenedor de sección con borde suave y sombra mínima.

```tsx
<Card>
  <CardHeader title="Resumen" />
  <CardBody>
    <p className="text-3xl font-bold text-brand-900">127</p>
  </CardBody>
  <CardFooter>
    <p className="text-xs text-gray-500">Actualizado hace 2 min</p>
  </CardFooter>
</Card>
```

---

## FormField

Envuelve un input con label y mensaje de error.

```tsx
<FormField label="Número de documento" error={errors.documento?.message}>
  <Input {...register('documento')} placeholder="123456789" />
</FormField>
```

---

## Pagination

Prev/Next con contador de página. Controlado externamente con `offset`.

```tsx
<Pagination
  total={data?.total ?? 0}
  offset={offset}
  limit={PAGE_SIZE}          // ej: 15
  onChange={setOffset}       // recibe el nuevo offset
/>
```

---

## Componentes restantes

| Componente | Props clave | Notas |
|---|---|---|
| `Input` | `placeholder`, `type`, `disabled` | Styled nativo — alineado a `form-input` del brand book |
| `Select` | `value`, `onChange`, `children` | Styled nativo — NO usar `<SelectItem value="">`, usar `value="ALL"` |
| `SearchInput` | `value`, `onChange`, `placeholder`, `debounceMs=300` | Incluye ícono lupa + debounce interno |
| `TextArea` | `value`, `onChange`, `maxLength`, `showCount` | Contador de caracteres opcional |
| `Spinner` | `size` | Anillo animado Tailwind — para loading de toda la página |
| `EmptyState` | `title`, `description`, `action` | Ilustración + botón opcional de acción |
