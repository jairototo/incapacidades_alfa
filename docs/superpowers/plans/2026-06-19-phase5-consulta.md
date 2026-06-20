# Phase 5 — Consulta de Incapacidades (acotada a la empresa) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Depends on:** Phase 1 (auth, `require_empresa`, ProtectedRoute, `/auth/me` empresa).

**Goal:** An authenticated EMPRESA user sees a filterable table of *only their company's* incapacidades and can open a detail+timeline view per row.

**Architecture:** A new backend endpoint `GET /incapacidades/mi-empresa` forces `empresa_id` from the authenticated user's token (never a client param), reusing the existing list/repository logic. The frontend adds a `/consulta` page: a filter bar (estado, tipo, date range, document/numero search), a results table, and a row → detail drawer reusing the existing `DetalleIncapacidad` + `TimelineEstados` components.

**Tech Stack:** FastAPI, React 19, React Query, vitest.

---

## File Structure

**Backend:**
- Modify: `app/api/v1/endpoints/incapacidades.py` — add `GET /incapacidades/mi-empresa`.
- Test: `tests/test_consulta_mi_empresa.py`.

**Frontend:**
- Create: `src/services/consultaEmpresaService.ts` — company-scoped list query.
- Create: `src/components/consulta/FiltrosConsultaEmpresa.tsx` — filter bar.
- Create: `src/components/consulta/TablaIncapacidades.tsx` — results table.
- Create: `src/pages/ConsultaEmpresa.tsx` — page (filters + table + detail drawer).
- Modify: `src/App.tsx` — `/consulta`.

---

## Task 1: Backend — company-scoped list endpoint

**Files:**
- Modify: `app/api/v1/endpoints/incapacidades.py`
- Test: `tests/test_consulta_mi_empresa.py`

> Reuses the existing list service but injects `empresa_id = current_user.empresa_id`, ignoring any
> client-supplied empresa filter. This guarantees a company can only ever see its own records.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_consulta_mi_empresa.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mi_empresa_only_returns_own_records(client: AsyncClient, empresa_user_token,
                                                   incapacidad_de_mi_empresa, incapacidad_de_otra_empresa):
    resp = await client.get("/api/v1/incapacidades/mi-empresa",
                            headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200
    numeros = {item["numero"] for item in resp.json()}
    assert incapacidad_de_mi_empresa.numero in numeros
    assert incapacidad_de_otra_empresa.numero not in numeros


@pytest.mark.asyncio
async def test_mi_empresa_filters_by_estado(client: AsyncClient, empresa_user_token, incapacidad_de_mi_empresa):
    resp = await client.get("/api/v1/incapacidades/mi-empresa",
                            params={"estado": "RADICADA"},
                            headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200
    assert all(i["estado"] == "RADICADA" for i in resp.json())
```

> Add fixtures `incapacidad_de_mi_empresa` and `incapacidad_de_otra_empresa` to conftest (two ARL
> incapacidades under different empresas; the token belongs to the first empresa).

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_consulta_mi_empresa.py -v --no-cov`
Expected: FAIL — route missing (404).

- [ ] **Step 3: Implement the endpoint**

```python
# app/api/v1/endpoints/incapacidades.py  (add a new route ABOVE the dynamic /{id} route to avoid path clash)
@router.get("/mi-empresa", response_model=List[IncapacidadInDB],
            summary="Listar incapacidades de mi empresa (EMPRESA)")
async def list_incapacidades_mi_empresa(
    estado: Optional[EstadoIncapacidad] = Query(None),
    numero: Optional[str] = Query(None),
    empleado_documento: Optional[str] = Query(None),
    fecha_inicio_desde: Optional[date] = Query(None),
    fecha_inicio_hasta: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    if not current_user.empresa_id:
        raise HTTPException(status_code=403, detail="Usuario no vinculado a una empresa")
    service = IncapacidadService()  # use the same service the existing list endpoint uses
    result = await service.list_incapacidades(
        db,
        tipo=TipoIncapacidad.ARL,
        estado=estado,
        numero=numero,
        empleado_documento=empleado_documento,
        empresa_id=current_user.empresa_id,   # forced from token, never from client
        fecha_inicio_desde=fecha_inicio_desde,
        fecha_inicio_hasta=fecha_inicio_hasta,
        skip=skip,
        limit=limit,
    )
    return result
```

> **Verify before coding:** match the exact `IncapacidadService.list_incapacidades` signature used by
> the existing `list_incapacidades` endpoint (parameter names, how it's instantiated, and the response
> serialization helper `_serialize` if one is used in that file). Mirror that endpoint's serialization
> so the response shape matches `IncapacidadInDB`.
>
> **Route ordering:** register `/mi-empresa` before any `/{incapacidad_id}` route so FastAPI doesn't
> treat "mi-empresa" as an id.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_consulta_mi_empresa.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_consulta_mi_empresa.py
git commit -m "feat(consulta): add company-scoped incapacidades listing endpoint"
```

---

## Task 2: Frontend — company-scoped list service

**Files:**
- Create: `apps/frontend/portal-externo/src/services/consultaEmpresaService.ts`

- [ ] **Step 1: Create the service + types**

```typescript
// src/services/consultaEmpresaService.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface FiltrosConsulta {
  estado?: string;
  numero?: string;
  empleado_documento?: string;
  fecha_inicio_desde?: string;
  fecha_inicio_hasta?: string;
}

export interface IncapacidadListItem {
  id: string;
  numero: string;
  estado: string;
  tipo: string;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10?: string;
  empleado?: { nombres?: string; apellidos?: string; numero_documento?: string } | null;
}

export function useIncapacidadesDeMiEmpresa(filtros: FiltrosConsulta) {
  return useQuery({
    queryKey: ['incapacidades', 'mi-empresa', filtros],
    queryFn: async () => {
      const params: Record<string, string> = {};
      Object.entries(filtros).forEach(([k, v]) => { if (v) params[k] = v; });
      const { data } = await api.get<IncapacidadListItem[]>('/incapacidades/mi-empresa', { params });
      return data;
    },
    staleTime: 60 * 1000,
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add src/services/consultaEmpresaService.ts
git commit -m "feat(consulta): add company-scoped incapacidades query hook"
```

---

## Task 3: Frontend — filter bar

**Files:**
- Create: `src/components/consulta/FiltrosConsultaEmpresa.tsx`
- Test: `src/components/consulta/__tests__/FiltrosConsultaEmpresa.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// __tests__/FiltrosConsultaEmpresa.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FiltrosConsultaEmpresa } from '@/components/consulta/FiltrosConsultaEmpresa';

describe('FiltrosConsultaEmpresa', () => {
  it('emits filter changes', () => {
    const onChange = vi.fn();
    render(<FiltrosConsultaEmpresa value={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/documento/i), { target: { value: '123' } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ empleado_documento: '123' }));
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- FiltrosConsultaEmpresa`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the filter bar**

```tsx
// src/components/consulta/FiltrosConsultaEmpresa.tsx
import type { FiltrosConsulta } from '@/services/consultaEmpresaService';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

const ESTADOS = ['', 'RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 'RECHAZADA', 'EN_PAGO', 'PAGADA'];

interface Props { value: FiltrosConsulta; onChange: (f: FiltrosConsulta) => void; }

export function FiltrosConsultaEmpresa({ value, onChange }: Props) {
  const set = (patch: Partial<FiltrosConsulta>) => onChange({ ...value, ...patch });
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 bg-white rounded-lg shadow-sm border border-border p-4">
      <div className="space-y-1">
        <Label htmlFor="f-estado">Estado</Label>
        <select id="f-estado" className="w-full rounded-md border border-input p-2 text-sm"
          value={value.estado ?? ''} onChange={(e) => set({ estado: e.target.value || undefined })}>
          {ESTADOS.map((s) => <option key={s} value={s}>{s || 'Todos'}</option>)}
        </select>
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-doc">Documento empleado</Label>
        <Input id="f-doc" value={value.empleado_documento ?? ''}
          onChange={(e) => set({ empleado_documento: e.target.value || undefined })} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-desde">Inicio desde</Label>
        <Input id="f-desde" type="date" value={value.fecha_inicio_desde ?? ''}
          onChange={(e) => set({ fecha_inicio_desde: e.target.value || undefined })} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="f-hasta">Inicio hasta</Label>
        <Input id="f-hasta" type="date" value={value.fecha_inicio_hasta ?? ''}
          onChange={(e) => set({ fecha_inicio_hasta: e.target.value || undefined })} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- FiltrosConsultaEmpresa`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/consulta/FiltrosConsultaEmpresa.tsx src/components/consulta/__tests__/FiltrosConsultaEmpresa.test.tsx
git commit -m "feat(consulta): add company inquiry filter bar"
```

---

## Task 4: Frontend — results table

**Files:**
- Create: `src/components/consulta/TablaIncapacidades.tsx`
- Test: `src/components/consulta/__tests__/TablaIncapacidades.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// __tests__/TablaIncapacidades.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablaIncapacidades } from '@/components/consulta/TablaIncapacidades';

const items = [{
  id: 'i1', numero: 'ARL-20260601-0001', estado: 'RADICADA', tipo: 'ARL',
  fecha_inicio: '2026-06-01', fecha_fin: '2026-06-05', dias_totales: 5, diagnostico_cie10: 'S00.0',
  empleado: { nombres: 'Ana', apellidos: 'Gómez', numero_documento: '123' },
}];

describe('TablaIncapacidades', () => {
  it('renders rows and emits row click', () => {
    const onSelect = vi.fn();
    render(<TablaIncapacidades items={items as any} isLoading={false} onSelect={onSelect} />);
    expect(screen.getByText('ARL-20260601-0001')).toBeInTheDocument();
    fireEvent.click(screen.getByText('ARL-20260601-0001'));
    expect(onSelect).toHaveBeenCalledWith('i1');
  });

  it('shows empty state', () => {
    render(<TablaIncapacidades items={[]} isLoading={false} onSelect={() => {}} />);
    expect(screen.getByText(/no hay incapacidades/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- TablaIncapacidades`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the table**

```tsx
// src/components/consulta/TablaIncapacidades.tsx
import type { IncapacidadListItem } from '@/services/consultaEmpresaService';

const ESTADO_COLOR: Record<string, string> = {
  RADICADA: 'bg-[#0094B3]/10 text-[#0094B3]',
  EN_AUDITORIA: 'bg-[#FECB00]/15 text-[#8a6d00]',
  APROBADA: 'bg-[#009B76]/10 text-[#009B76]',
  RECHAZADA: 'bg-[#D92D20]/10 text-[#D92D20]',
};

interface Props {
  items: IncapacidadListItem[];
  isLoading: boolean;
  onSelect: (id: string) => void;
}

export function TablaIncapacidades({ items, isLoading, onSelect }: Props) {
  if (isLoading) return <p className="p-6 text-sm text-muted-foreground">Cargando…</p>;
  if (items.length === 0) return <p className="p-6 text-sm text-muted-foreground">No hay incapacidades para los filtros seleccionados.</p>;

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-white">
      <table className="w-full text-sm">
        <thead className="bg-muted text-left">
          <tr>
            <th className="p-3 font-medium">Número</th>
            <th className="p-3 font-medium">Empleado</th>
            <th className="p-3 font-medium">CIE-10</th>
            <th className="p-3 font-medium">Periodo</th>
            <th className="p-3 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-t border-border hover:bg-muted/50 cursor-pointer"
              onClick={() => onSelect(it.id)}>
              <td className="p-3 font-medium text-primary">{it.numero}</td>
              <td className="p-3">{it.empleado ? `${it.empleado.nombres ?? ''} ${it.empleado.apellidos ?? ''}` : '—'}<br />
                <span className="text-xs text-muted-foreground">{it.empleado?.numero_documento}</span></td>
              <td className="p-3">{it.diagnostico_cie10 ?? '—'}</td>
              <td className="p-3">{it.fecha_inicio} → {it.fecha_fin} <span className="text-xs text-muted-foreground">({it.dias_totales}d)</span></td>
              <td className="p-3">
                <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_COLOR[it.estado] ?? 'bg-muted text-foreground'}`}>{it.estado}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- TablaIncapacidades`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/consulta/TablaIncapacidades.tsx src/components/consulta/__tests__/TablaIncapacidades.test.tsx
git commit -m "feat(consulta): add incapacidades results table"
```

---

## Task 5: Frontend — inquiry page with detail drawer + route

**Files:**
- Create: `src/pages/ConsultaEmpresa.tsx`
- Modify: `src/App.tsx`
- Test: `src/pages/__tests__/ConsultaEmpresa.test.tsx`

> Combines filters + table; clicking a row fetches the full incapacidad (reuse the existing
> single-record fetch in `consultaService`/`incapacidadService` by `numero` or `id`) and shows it in a
> drawer/panel using the existing `DetalleIncapacidad` + `TimelineEstados` components.

- [ ] **Step 1: Write the failing test (smoke)**

```tsx
// src/pages/__tests__/ConsultaEmpresa.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConsultaEmpresa } from '@/pages/ConsultaEmpresa';

vi.mock('@/services/consultaEmpresaService', () => ({
  useIncapacidadesDeMiEmpresa: () => ({ data: [], isLoading: false }),
}));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><ConsultaEmpresa /></MemoryRouter>
  </QueryClientProvider>,
);

describe('ConsultaEmpresa', () => {
  it('renders the heading, filters and empty table', () => {
    wrap();
    expect(screen.getByText(/consulta de incapacidades/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/estado/i)).toBeInTheDocument();
    expect(screen.getByText(/no hay incapacidades/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- ConsultaEmpresa`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the page**

```tsx
// src/pages/ConsultaEmpresa.tsx
import { useState } from 'react';
import { FiltrosConsultaEmpresa } from '@/components/consulta/FiltrosConsultaEmpresa';
import { TablaIncapacidades } from '@/components/consulta/TablaIncapacidades';
import { useIncapacidadesDeMiEmpresa, type FiltrosConsulta } from '@/services/consultaEmpresaService';

export function ConsultaEmpresa() {
  const [filtros, setFiltros] = useState<FiltrosConsulta>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: items = [], isLoading } = useIncapacidadesDeMiEmpresa(filtros);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">Consulta de Incapacidades</h1>
      <FiltrosConsultaEmpresa value={filtros} onChange={setFiltros} />
      <TablaIncapacidades items={items} isLoading={isLoading} onSelect={setSelectedId} />

      {selectedId && (
        <DetalleDrawer id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  );
}

// Drawer that loads the full record and reuses existing detail + timeline components.
function DetalleDrawer({ id, onClose }: { id: string; onClose: () => void }) {
  // Reuse the existing single-record fetch. If consultaService exposes a by-id/by-numero query,
  // call it here (React Query). Then render <DetalleIncapacidad incapacidad={data} /> and
  // <TimelineEstados ... /> from src/components/consulta/.
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex justify-end" onClick={onClose}>
      <aside className="w-full max-w-2xl h-full bg-white shadow-xl overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="text-sm text-muted-foreground mb-4">Cerrar ✕</button>
        {/* <DetalleIncapacidad incapacidad={data} /> */}
        {/* <TimelineEstados historial={data.historial} /> */}
        <p className="text-sm text-muted-foreground">Detalle de la incapacidad {id}.</p>
      </aside>
    </div>
  );
}
```

> **Wire the drawer to real data:** read `src/services/consultaService.ts` and `DetalleIncapacidad.tsx`
> /`TimelineEstados.tsx` props, then fetch the full record by id (add a query to
> `consultaEmpresaService` calling `GET /incapacidades/{id}` if needed) and render those components.
> Keep the drawer scoped to the company (the id came from the company-scoped table).

- [ ] **Step 4: Add the route**

```tsx
// src/App.tsx — inside <ProtectedRoute />
import { ConsultaEmpresa } from '@/pages/ConsultaEmpresa';
<Route path="/consulta" element={<ConsultaEmpresa />} />
```

Also confirm the Phase 1 redirect `/consultar → /consulta` now resolves to a real page.

- [ ] **Step 5: Run tests + build**

Run: `npm test -- consulta && npm run build`
Expected: PASS + build OK.

- [ ] **Step 6: Commit**

```bash
git add src/pages/ConsultaEmpresa.tsx src/App.tsx src/pages/__tests__/ConsultaEmpresa.test.tsx
git commit -m "feat(consulta): add company inquiry page with detail drawer"
```

---

## Self-Review Notes (coverage vs spec Phase 5)

- Filterable table scoped to company, `empresa_id` from token not query param (D6) → Tasks 1, 2. ✅
- Filters estado/tipo(ARL fixed)/date range/document search → Tasks 1, 3. ✅
- Columns numero, employee, CIE-10, period, estado → Task 4. ✅
- Row → detail + timeline reusing existing components → Task 5. ✅
- Company can only see its own records (hardened) → Task 1 forces token empresa_id + test asserts isolation. ✅

**Manual verification:** log in as EMPRESA, open `/consulta`, confirm only this company's incapacidades
appear; filter by estado RADICADA; open a row and confirm the detail + timeline render. Attempt to view
another company's record id → backend returns nothing/forbidden.
