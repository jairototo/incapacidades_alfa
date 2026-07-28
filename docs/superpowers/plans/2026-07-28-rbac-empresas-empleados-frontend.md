# RBAC + Empresa/Empleado Admin Module (Frontend) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the sistema-interno admin UI for Empresas and Empleados — role-gated CRUD, an analytics panel with two charts, and a 3-step bulk-upload wizard — wired to the backend contract shipped in `docs/superpowers/plans/2026-07-27-rbac-empresas-empleados-backend.md`.

**Architecture:** React + TypeScript + Vite, React Query for server state, Zustand (`authStore`) for auth/permissions, shadcn/ui components, recharts for charts. Every page/component follows the existing `AuditoresPage.tsx`/`auditorService.ts` pattern (local `useState` form + one `useMutation` per action, inline error text, `window.confirm()` for destructive actions) rather than introducing a new state-management or notification pattern.

**Tech Stack:** React 18, TypeScript, `@tanstack/react-query`, `@tanstack/react-table`, `recharts@^3.7.0`, `axios`, `zustand`, shadcn/ui, vitest + `@testing-library/react`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-28-rbac-empresas-empleados-frontend-design.md` — every task implements one section of that spec.
- **No style/typography/token changes.** Reuse existing shadcn components, Tailwind classes, and color/spacing conventions exactly as `AuditoresPage.tsx` and `components/dashboard/charts/*.tsx` already use them. No new design system.
- `GET /empresas` and `GET /empleados` return a **flat array** (`EmpresaListItem[]`/`EmpleadoListItem[]`), with **no total count**. Pagination never shows "de N"; "Siguiente" is enabled only when the current page came back full (`results.length === limit`).
- `EmpleadoListItem` (the list-row shape returned by `GET /empleados`) has **no `empresa_id`/company field at all** — `{id, numero_documento, tipo_documento, nombres, apellidos, cargo, estado, created_at}` only. The Empleados table never renders an "Empresa" column; users rely on the empresa filter/selector to scope results.
- Run frontend tests via `npm test` from `apps/frontend/sistema-interno/` (vitest). Only run the test file(s) touched by the current task, not the full suite, unless a task says otherwise.
- `RolUsuario` in `src/types/enums.ts` is a `const` object + derived type (`as const` pattern), not a TypeScript `enum` — follow that exact pattern for `LIQUIDADOR`, never introduce a real `enum`.
- New backend action strings for the `authStore.ts` permission map: `'empresa.read'`, `'empresa.create'`, `'empresa.update'`, `'empresa.delete'`, `'empleado.read'`, `'empleado.create'`, `'empleado.update'`, `'empleado.delete'`. `ADMIN` stays `['*']`. `READONLY` gets none of these (matches the backend, which removed READONLY's Empresas/Empleados access entirely).

---

### Task 1: `LIQUIDADOR` role + permission map sync

**Files:**
- Modify: `src/types/enums.ts`
- Modify: `src/store/authStore.ts`
- Test: `src/store/__tests__/authStore.test.ts` (new)

**Interfaces:**
- Produces: `RolUsuario.LIQUIDADOR` (value `"LIQUIDADOR"`) and `useCanPerform` returning correct booleans for the 8 new action strings per role — consumed by every later task's role-gated button rendering.

- [ ] **Step 1: Write the failing test**

```typescript
// src/store/__tests__/authStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore, useCanPerform } from '../authStore';
import { renderHook } from '@testing-library/react';
import { RolUsuario } from '@/types/enums';
import type { User } from '@/types/auth';

function setUser(rol: RolUsuario) {
  const user: User = {
    id: '1',
    username: 'test',
    email: 'test@test.com',
    nombres: 'Test',
    apellidos: 'User',
    rol,
    estado: 'ACTIVO' as any,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
  useAuthStore.setState({ isAuthenticated: true, user, accessToken: 't', refreshToken: 'r' });
}

describe('useCanPerform — Empresas/Empleados matrix', () => {
  beforeEach(() => {
    useAuthStore.setState({ isAuthenticated: false, user: null, accessToken: null, refreshToken: null });
  });

  it('LIQUIDADOR can read but not write Empresas/Empleados', () => {
    setUser(RolUsuario.LIQUIDADOR);
    const { result: read1 } = renderHook(() => useCanPerform('empresa.read'));
    const { result: read2 } = renderHook(() => useCanPerform('empleado.read'));
    const { result: write1 } = renderHook(() => useCanPerform('empresa.create'));
    const { result: write2 } = renderHook(() => useCanPerform('empleado.create'));
    expect(read1.current).toBe(true);
    expect(read2.current).toBe(true);
    expect(write1.current).toBe(false);
    expect(write2.current).toBe(false);
  });

  it('AUDITOR can read Empresas and read+write Empleados, but not write Empresas', () => {
    setUser(RolUsuario.AUDITOR);
    const { result: empresaRead } = renderHook(() => useCanPerform('empresa.read'));
    const { result: empresaCreate } = renderHook(() => useCanPerform('empresa.create'));
    const { result: empleadoCreate } = renderHook(() => useCanPerform('empleado.create'));
    const { result: empleadoDelete } = renderHook(() => useCanPerform('empleado.delete'));
    expect(empresaRead.current).toBe(true);
    expect(empresaCreate.current).toBe(false);
    expect(empleadoCreate.current).toBe(true);
    expect(empleadoDelete.current).toBe(true);
  });

  it('READONLY has no Empresas/Empleados access at all', () => {
    setUser(RolUsuario.READONLY);
    const { result: empresaRead } = renderHook(() => useCanPerform('empresa.read'));
    const { result: empleadoRead } = renderHook(() => useCanPerform('empleado.read'));
    expect(empresaRead.current).toBe(false);
    expect(empleadoRead.current).toBe(false);
  });

  it('ADMIN can do everything via the wildcard', () => {
    setUser(RolUsuario.ADMIN);
    const { result } = renderHook(() => useCanPerform('empresa.delete'));
    expect(result.current).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `apps/frontend/sistema-interno/`): `npm test -- src/store/__tests__/authStore.test.ts`
Expected: FAIL — `RolUsuario.LIQUIDADOR` is `undefined` (TypeScript would also fail to compile this file once the test references it), and `useCanPerform('empresa.read')` returns `false` for every role since the action string doesn't exist in the map yet.

- [ ] **Step 3: Add the enum value and permission entries**

In `src/types/enums.ts`, add `LIQUIDADOR` to the `RolUsuario` const object:

```typescript
export const RolUsuario = {
  ADMIN: 'ADMIN',
  AUDITOR: 'AUDITOR',
  APROBADOR: 'APROBADOR',
  EMPRESA: 'EMPRESA',
  EMPLEADO: 'EMPLEADO',
  READONLY: 'READONLY',
  LIQUIDADOR: 'LIQUIDADOR',
} as const;
```

In `src/store/authStore.ts`, update the `permissions` map inside `useCanPerform`:

```typescript
  const permissions: Record<string, string[]> = {
    ADMIN: ['*'], // Todos los permisos
    AUDITOR: [
      'incapacidad.read',
      'incapacidad.update',
      'incapacidad.cambiar_estado',
      'incapacidad.observar',
      'empresa.read',
      'empleado.read',
      'empleado.create',
      'empleado.update',
      'empleado.delete',
    ],
    APROBADOR: [
      'incapacidad.read',
      'incapacidad.aprobar',
      'incapacidad.rechazar',
      'orden_pago.aprobar',
    ],
    READONLY: ['incapacidad.read'],
    EMPRESA: ['incapacidad.read', 'incapacidad.create'],
    EMPLEADO: ['incapacidad.read'],
    LIQUIDADOR: ['empresa.read', 'empleado.read'],
  };
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/store/__tests__/authStore.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/types/enums.ts src/store/authStore.ts src/store/__tests__/authStore.test.ts
git commit -m "feat: add LIQUIDADOR role and sync Empresas/Empleados permission matrix"
```

---

### Task 2: Fix `Empresa` type + extend `empresaService`

**Files:**
- Modify: `src/types/empresa.ts`
- Modify: `src/services/empresaService.ts`
- Test: `src/services/__tests__/empresaService.test.ts` (new)

**Interfaces:**
- Produces: `Empresa` type matching the real backend `EmpresaResponse`/`EmpresaListItem` shape; `empresaService.list(params) -> EmpresaListItem[]` (flat array, replacing the old `{items, total, ...}` wrapper — **breaking change to this service's return type**, consumed by Task 5); `empresaService.create/update/regenerarPassword/getAnalitica` — consumed by Tasks 6/7.

- [ ] **Step 1: Write the failing test**

```typescript
// src/services/__tests__/empresaService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/lib/api';
import { empresaService } from '../empresaService';

vi.mock('@/lib/api');

describe('empresaService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('list() returns the flat array from the backend, not a wrapper object', async () => {
    const mockItems = [
      { id: '1', nit: '900123456', razon_social: 'Empresa Test', estado: 'ACTIVA', ciudad: 'Bogotá', created_at: '2026-01-01T00:00:00Z' },
    ];
    vi.mocked(api.get).mockResolvedValue({ data: mockItems });

    const result = await empresaService.list({ skip: 0, limit: 100 });

    expect(result).toEqual(mockItems);
    expect(api.get).toHaveBeenCalledWith('/empresas/', { params: { skip: 0, limit: 100 } });
  });

  it('create() posts to /empresas/ and returns the credentials-included response', async () => {
    const mockResponse = {
      id: '1', nit: '900999999', razon_social: 'Nueva SAS', estado: 'ACTIVA',
      email_contacto: 'nueva@empresa.com', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
      usuario_generado: { username: '900999999', password: 'Abc12345xyz9' },
    };
    vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

    const result = await empresaService.create({
      nit: '900999999', razon_social: 'Nueva SAS', email_contacto: 'nueva@empresa.com',
    });

    expect(result.usuario_generado.password).toBe('Abc12345xyz9');
    expect(api.post).toHaveBeenCalledWith('/empresas/', {
      nit: '900999999', razon_social: 'Nueva SAS', email_contacto: 'nueva@empresa.com',
    });
  });

  it('regenerarPassword() posts to the regenerar-password endpoint', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { message: 'ok', username: '900999999', password: 'NewTemp123x' },
    });

    const result = await empresaService.regenerarPassword('1');

    expect(result.password).toBe('NewTemp123x');
    expect(api.post).toHaveBeenCalledWith('/empresas/1/regenerar-password');
  });

  it('getAnalitica() fetches the combined analytics payload', async () => {
    const mockData = { top_empresas: [], tendencia_mensual: [] };
    vi.mocked(api.get).mockResolvedValue({ data: mockData });

    const result = await empresaService.getAnalitica();

    expect(result).toEqual(mockData);
    expect(api.get).toHaveBeenCalledWith('/empresas/analitica');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/services/__tests__/empresaService.test.ts`
Expected: FAIL — `empresaService.create`/`regenerarPassword`/`getAnalitica` don't exist yet; `list()`'s current implementation returns `data.items`... actually returns the whole `data` object (the wrapper), so `result` won't equal `mockItems` (a flat array) since `list()` currently just returns whatever `api.get` resolves to unwrapped — the test's `expect(result).toEqual(mockItems)` will fail because current code passes the mock array straight through already (re-examine: since the mock now returns the array directly as `data`, `list()`'s current body `const { data } = await api.get(...); return data;`-equivalent actually already matches — the REAL failure is that `create`/`regenerarPassword`/`getAnalitica` are undefined, causing a TypeError). Confirm the actual failure reason in the test run output rather than assuming.

- [ ] **Step 3: Fix the type and extend the service**

Replace `src/types/empresa.ts` entirely:

```typescript
export interface UsuarioGenerado {
  username: string;
  password: string;
}

export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  estado: string;
  email_contacto?: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
  created_at: string;
  updated_at?: string;
}

export interface EmpresaCreatePayload {
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
}

export interface EmpresaCreateResponse extends Empresa {
  usuario_generado: UsuarioGenerado;
}

export interface EmpresaUpdatePayload {
  razon_social?: string;
  email_contacto?: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  departamento?: string;
  tipo_empresa?: string;
  nro_contrato?: string;
  estado?: string;
}

export interface RegenerarPasswordResponse {
  message: string;
  username: string;
  password: string;
}

export interface EmpresaTopItem {
  empresa_id: string;
  razon_social: string;
  nit: string;
  total_radicadas: number;
}

export interface TendenciaMensualItem {
  periodo: string;
  total: number;
}

export interface AnaliticaEmpresasResponse {
  top_empresas: EmpresaTopItem[];
  tendencia_mensual: TendenciaMensualItem[];
}
```

Replace `src/services/empresaService.ts` entirely:

```typescript
import api from '@/lib/api';
import type {
  Empresa,
  EmpresaCreatePayload,
  EmpresaCreateResponse,
  EmpresaUpdatePayload,
  RegenerarPasswordResponse,
  AnaliticaEmpresasResponse,
} from '@/types/empresa';

interface ListEmpresasParams {
  skip?: number;
  limit?: number;
  nit?: string;
  ciudad?: string;
  departamento?: string;
  search?: string;
}

/**
 * Servicio para gestión de empresas
 */
class EmpresaService {
  private readonly baseUrl = '/empresas/';

  async list(params: ListEmpresasParams): Promise<Empresa[]> {
    const { data } = await api.get<Empresa[]>(this.baseUrl, { params });
    return data;
  }

  async getById(id: string): Promise<Empresa> {
    const { data } = await api.get<Empresa>(`${this.baseUrl}${id}`);
    return data;
  }

  async create(payload: EmpresaCreatePayload): Promise<EmpresaCreateResponse> {
    const { data } = await api.post<EmpresaCreateResponse>(this.baseUrl, payload);
    return data;
  }

  async update(id: string, payload: EmpresaUpdatePayload): Promise<Empresa> {
    const { data } = await api.put<Empresa>(`${this.baseUrl}${id}`, payload);
    return data;
  }

  async regenerarPassword(id: string): Promise<RegenerarPasswordResponse> {
    const { data } = await api.post<RegenerarPasswordResponse>(`${this.baseUrl}${id}/regenerar-password`);
    return data;
  }

  async getAnalitica(): Promise<AnaliticaEmpresasResponse> {
    const { data } = await api.get<AnaliticaEmpresasResponse>(`${this.baseUrl}analitica`);
    return data;
  }
}

export const empresaService = new EmpresaService();
export default empresaService;
```

Note: `search()` (used previously for autocomplete-style lookups elsewhere, if any) is dropped since the backend's `search` query param is now folded into `list()`'s params — if any existing caller of `empresaService.search()` is found during this step, grep for it (`grep -rn "empresaService.search" src`) and update the call site to use `list({ search: query, limit: 10 })` instead; report what you find in your task report even if there are no callers.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/services/__tests__/empresaService.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/types/empresa.ts src/services/empresaService.ts src/services/__tests__/empresaService.test.ts
git commit -m "fix: correct Empresa type to match backend contract, extend empresaService for create/update/password/analitica"
```

---

### Task 3: `Empleado` type + `empleadoService`

**Files:**
- Create: `src/types/empleado.ts`
- Create: `src/services/empleadoService.ts`
- Test: `src/services/__tests__/empleadoService.test.ts`

**Interfaces:**
- Produces: `Empleado`, `EmpleadoCreatePayload`, `EmpleadoUpdatePayload` types; `empleadoService.{list,getById,create,update,deactivate,getPlantilla,validarCargaMasiva,confirmarCargaMasiva}` — consumed by Tasks 8, 9, 10.

- [ ] **Step 1: Write the failing test**

```typescript
// src/services/__tests__/empleadoService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/lib/api';
import { empleadoService } from '../empleadoService';

vi.mock('@/lib/api');

describe('empleadoService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('list() returns the flat array, forwards filters as params', async () => {
    const mockItems = [
      { id: '1', numero_documento: '123', tipo_documento: 'CC', nombres: 'Ana', apellidos: 'Gómez', cargo: 'Analista', estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' },
    ];
    vi.mocked(api.get).mockResolvedValue({ data: mockItems });

    const result = await empleadoService.list({ empresa_id: 'e1', skip: 0, limit: 100 });

    expect(result).toEqual(mockItems);
    expect(api.get).toHaveBeenCalledWith('/empleados/', { params: { empresa_id: 'e1', skip: 0, limit: 100 } });
  });

  it('create() posts to /empleados/', async () => {
    const payload = {
      empresa_id: 'e1', numero_documento: '999', tipo_documento: 'CC',
      nombres: 'Luis', apellidos: 'Pérez', fecha_ingreso: '2024-01-01',
    };
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'x', ...payload, estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' } });

    await empleadoService.create(payload);

    expect(api.post).toHaveBeenCalledWith('/empleados/', payload);
  });

  it('getPlantilla() requests a blob', async () => {
    const mockBlob = new Blob(['xlsx-bytes']);
    vi.mocked(api.get).mockResolvedValue({ data: mockBlob });

    const result = await empleadoService.getPlantilla();

    expect(result).toBe(mockBlob);
    expect(api.get).toHaveBeenCalledWith('/empleados/plantilla', { responseType: 'blob' });
  });

  it('validarCargaMasiva() posts multipart form data with the file', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { total_filas: 2, validas: 1, con_error: 1, errores: [{ fila: 2, columna: 'numero_documento', mensaje: 'Campo obligatorio' }] },
    });
    const file = new File(['content'], 'empleados.xlsx');

    const result = await empleadoService.validarCargaMasiva(file);

    expect(result.validas).toBe(1);
    const callArgs = vi.mocked(api.post).mock.calls[0];
    expect(callArgs[0]).toBe('/empleados/carga-masiva/validar');
    expect(callArgs[1]).toBeInstanceOf(FormData);
    expect(callArgs[2]?.headers).toEqual({ 'Content-Type': 'multipart/form-data' });
  });

  it('confirmarCargaMasiva() posts multipart form data with the file', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { total_filas: 2, insertadas: 1, con_error: 1, errores: [] },
    });
    const file = new File(['content'], 'empleados.xlsx');

    const result = await empleadoService.confirmarCargaMasiva(file);

    expect(result.insertadas).toBe(1);
    const callArgs = vi.mocked(api.post).mock.calls[0];
    expect(callArgs[0]).toBe('/empleados/carga-masiva/confirmar');
    expect(callArgs[1]).toBeInstanceOf(FormData);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/services/__tests__/empleadoService.test.ts`
Expected: FAIL — module `../empleadoService` doesn't exist.

- [ ] **Step 3: Create the type and service files**

`src/types/empleado.ts`:

```typescript
export interface Empleado {
  id: string;
  empresa_id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso: string;
  fecha_retiro?: string;
  salario_base?: number;
  estado: string;
  created_at: string;
  updated_at?: string;
}

/** Shape actually returned by GET /empleados (list) — no empresa reference, see plan's Global Constraints. */
export interface EmpleadoListItem {
  id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  cargo?: string;
  estado: string;
  created_at: string;
}

export interface EmpleadoCreatePayload {
  empresa_id: string;
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso: string;
  salario_base?: number;
}

export interface EmpleadoUpdatePayload {
  nombres?: string;
  apellidos?: string;
  email?: string;
  telefono?: string;
  fecha_nacimiento?: string;
  genero?: string;
  cargo?: string;
  area?: string;
  fecha_ingreso?: string;
  salario_base?: number;
  estado?: string;
}

export interface FilaError {
  fila: number;
  columna?: string;
  mensaje: string;
}

export interface ValidacionMasivaResponse {
  total_filas: number;
  validas: number;
  con_error: number;
  errores: FilaError[];
}

export interface ConfirmacionMasivaResponse {
  total_filas: number;
  insertadas: number;
  con_error: number;
  errores: FilaError[];
}
```

`src/services/empleadoService.ts`:

```typescript
import api from '@/lib/api';
import type {
  EmpleadoListItem,
  Empleado,
  EmpleadoCreatePayload,
  EmpleadoUpdatePayload,
  ValidacionMasivaResponse,
  ConfirmacionMasivaResponse,
} from '@/types/empleado';

interface ListEmpleadosParams {
  empresa_id?: string;
  estado?: string;
  documento?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

class EmpleadoService {
  private readonly baseUrl = '/empleados/';

  async list(params: ListEmpleadosParams): Promise<EmpleadoListItem[]> {
    const { data } = await api.get<EmpleadoListItem[]>(this.baseUrl, { params });
    return data;
  }

  async getById(id: string): Promise<Empleado> {
    const { data } = await api.get<Empleado>(`${this.baseUrl}${id}`);
    return data;
  }

  async create(payload: EmpleadoCreatePayload): Promise<Empleado> {
    const { data } = await api.post<Empleado>(this.baseUrl, payload);
    return data;
  }

  async update(id: string, payload: EmpleadoUpdatePayload): Promise<Empleado> {
    const { data } = await api.put<Empleado>(`${this.baseUrl}${id}`, payload);
    return data;
  }

  async deactivate(id: string): Promise<Empleado> {
    const { data } = await api.post<Empleado>(`${this.baseUrl}${id}/deactivate`);
    return data;
  }

  async getPlantilla(): Promise<Blob> {
    const { data } = await api.get<Blob>(`${this.baseUrl}plantilla`, { responseType: 'blob' });
    return data;
  }

  async validarCargaMasiva(file: File): Promise<ValidacionMasivaResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ValidacionMasivaResponse>(
      `${this.baseUrl}carga-masiva/validar`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }

  async confirmarCargaMasiva(file: File): Promise<ConfirmacionMasivaResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ConfirmacionMasivaResponse>(
      `${this.baseUrl}carga-masiva/confirmar`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }
}

export const empleadoService = new EmpleadoService();
export default empleadoService;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/services/__tests__/empleadoService.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/types/empleado.ts src/services/empleadoService.ts src/services/__tests__/empleadoService.test.ts
git commit -m "feat: add Empleado type and empleadoService (CRUD + bulk upload)"
```

---

### Task 4: `TablePagination` shared component

**Files:**
- Create: `src/components/shared/TablePagination.tsx`
- Test: `src/components/shared/__tests__/TablePagination.test.tsx`

**Interfaces:**
- Produces: `<TablePagination skip limit resultCount onPrev onNext />` — consumed by Tasks 5 and 8.

- [ ] **Step 1: Write the failing test**

```typescript
// src/components/shared/__tests__/TablePagination.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablePagination } from '../TablePagination';

describe('TablePagination', () => {
  it('disables "Anterior" on the first page (skip=0)', () => {
    render(<TablePagination skip={0} limit={100} resultCount={100} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /anterior/i })).toBeDisabled();
  });

  it('enables "Anterior" when skip > 0', () => {
    render(<TablePagination skip={100} limit={100} resultCount={50} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /anterior/i })).not.toBeDisabled();
  });

  it('disables "Siguiente" when the page came back incomplete', () => {
    render(<TablePagination skip={0} limit={100} resultCount={42} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /siguiente/i })).toBeDisabled();
  });

  it('enables "Siguiente" when the page came back full', () => {
    render(<TablePagination skip={0} limit={100} resultCount={100} onPrev={vi.fn()} onNext={vi.fn()} />);
    expect(screen.getByRole('button', { name: /siguiente/i })).not.toBeDisabled();
  });

  it('calls onNext/onPrev when clicked', () => {
    const onNext = vi.fn();
    const onPrev = vi.fn();
    render(<TablePagination skip={100} limit={100} resultCount={100} onPrev={onPrev} onNext={onNext} />);
    fireEvent.click(screen.getByRole('button', { name: /siguiente/i }));
    fireEvent.click(screen.getByRole('button', { name: /anterior/i }));
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onPrev).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/shared/__tests__/TablePagination.test.tsx`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement the component**

```typescript
// src/components/shared/TablePagination.tsx
import { Button } from '@/components/ui/button';

interface TablePaginationProps {
  skip: number;
  limit: number;
  resultCount: number;
  onPrev: () => void;
  onNext: () => void;
}

export function TablePagination({ skip, limit, resultCount, onPrev, onNext }: TablePaginationProps) {
  const hasPrev = skip > 0;
  const hasNext = resultCount === limit;

  return (
    <div className="flex items-center justify-between pt-2">
      <span className="text-sm text-slate-500">
        Mostrando {resultCount === 0 ? 0 : skip + 1}–{skip + resultCount}
      </span>
      <div className="space-x-2">
        <Button variant="outline" size="sm" onClick={onPrev} disabled={!hasPrev}>
          Anterior
        </Button>
        <Button variant="outline" size="sm" onClick={onNext} disabled={!hasNext}>
          Siguiente
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/shared/__tests__/TablePagination.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/components/shared/TablePagination.tsx src/components/shared/__tests__/TablePagination.test.tsx
git commit -m "feat: add TablePagination shared component (no total-count dependency)"
```

---

### Task 5: Router wiring for `/empresas` and `/empleados`

**Files:**
- Modify: `src/router/index.tsx`
- Test: `src/router/__tests__/router.test.tsx` (extend existing file — read it first to match its conventions before adding cases)

**Interfaces:**
- Consumes: `RolUsuario.LIQUIDADOR` (Task 1).
- Produces: `/empresas` and `/empleados` routes rendering `<EmpresasPage />`/`<EmpleadosPage />` behind `ProtectedRoute allowedRoles={[ADMIN, AUDITOR, LIQUIDADOR]}` — consumed by Tasks 6 and 8, which create those page components. **This task creates placeholder page components first** (`EmpresasPage`/`EmpleadosPage` returning a simple `<div>`) so the route wiring is testable in isolation; Tasks 6/8 replace the placeholder bodies with real implementations in the same files.

- [ ] **Step 1: Write the failing test**

First read `src/router/__tests__/router.test.tsx` in full to see its existing rendering/assertion helpers, then add (adapting to match whatever helper pattern that file already uses for asserting a route renders for a given role):

```typescript
// addition to src/router/__tests__/router.test.tsx
it('renders EmpresasPage at /empresas for ADMIN, AUDITOR, and LIQUIDADOR', () => {
  // Use this file's existing render-at-route helper for each of the three roles.
  // Assert the placeholder/real EmpresasPage content is present and there is no
  // redirect to /unauthorized.
});

it('renders EmpleadosPage at /empleados for ADMIN, AUDITOR, and LIQUIDADOR', () => {
  // Same shape as above, targeting /empleados.
});
```

(Match the exact rendering helper — `MemoryRouter`+`RouterProvider`, or whatever this file already sets up — rather than inventing a new one; read the file before writing these two cases.)

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/router/__tests__/router.test.tsx`
Expected: FAIL — `/empresas` still renders the placeholder text "Módulo Empresas (Placeholder)" with only ADMIN allowed, `/empleados` doesn't exist as a route at all.

- [ ] **Step 3: Wire the routes**

Create minimal placeholder pages (Tasks 6/8 will replace their bodies):

```typescript
// src/pages/admin/EmpresasPage.tsx
export function EmpresasPage() {
  return <div className="p-6">Cargando módulo de Empresas…</div>;
}
```

```typescript
// src/pages/admin/EmpleadosPage.tsx
export function EmpleadosPage() {
  return <div className="p-6">Cargando módulo de Empleados…</div>;
}
```

In `src/router/index.tsx`, add the import and replace the `/empresas` block (lines 128-138), and add a new `/empleados` block right after it:

```typescript
import { EmpresasPage } from '@/pages/admin/EmpresasPage';
import { EmpleadosPage } from '@/pages/admin/EmpleadosPage';
```

```typescript
          // Empresas - ADMIN, AUDITOR, LIQUIDADOR (lectura); escritura gateada por botón
          {
            path: '/empresas',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR]} />,
            children: [
              {
                index: true,
                element: <EmpresasPage />,
              },
            ],
          },

          // Empleados - ADMIN, AUDITOR, LIQUIDADOR (lectura); escritura gateada por botón
          {
            path: '/empleados',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR]} />,
            children: [
              {
                index: true,
                element: <EmpleadosPage />,
              },
            ],
          },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/router/__tests__/router.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/router/index.tsx src/pages/admin/EmpresasPage.tsx src/pages/admin/EmpleadosPage.tsx src/router/__tests__/router.test.tsx
git commit -m "feat: wire /empresas and /empleados routes for ADMIN/AUDITOR/LIQUIDADOR"
```

---

### Task 6: `EmpresasPage` — list, filters, pagination

**Files:**
- Modify: `src/pages/admin/EmpresasPage.tsx` (replace placeholder body)
- Test: `src/pages/admin/__tests__/EmpresasPage.test.tsx`

**Interfaces:**
- Consumes: `empresaService.list` (Task 2), `TablePagination` (Task 4), `useCanPerform` (Task 1).
- Produces: the page shell that Task 7 (create/edit/password modals) and Task 9 (analytics panel) slot into — this task builds list+filters+pagination+navigation-to-empleados only, no create/edit yet (those buttons render but are inert placeholders wired up in Task 7).

- [ ] **Step 1: Write the failing test**

```typescript
// src/pages/admin/__tests__/EmpresasPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpresasPage } from '../EmpresasPage';
import { empresaService } from '@/services/empresaService';
import { useAuthStore } from '@/store/authStore';
import { RolUsuario } from '@/types/enums';

vi.mock('@/services/empresaService');

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <EmpresasPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function setUser(rol: RolUsuario) {
  useAuthStore.setState({
    isAuthenticated: true,
    user: { id: '1', username: 'u', email: 'u@u.com', nombres: 'U', apellidos: 'U', rol, estado: 'ACTIVO' as any, created_at: '', updated_at: '' },
    accessToken: 't', refreshToken: 'r',
  });
}

describe('EmpresasPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(empresaService.list).mockResolvedValue([
      { id: '1', nit: '900123456', razon_social: 'Empresa Uno', estado: 'ACTIVA', ciudad: 'Bogotá', created_at: '2026-01-01T00:00:00Z' },
    ]);
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
  });

  it('renders the list of empresas', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
  });

  it('shows "Crear empresa" for ADMIN but not for AUDITOR/LIQUIDADOR', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /crear empresa/i })).toBeInTheDocument();
  });

  it('does not show "Crear empresa" for AUDITOR', async () => {
    setUser(RolUsuario.AUDITOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /crear empresa/i })).not.toBeInTheDocument();
  });

  it('filters by NIT and re-fetches', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage();
    await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/nit o razón social/i), { target: { value: '900123456' } });
    fireEvent.click(screen.getByRole('button', { name: /buscar/i }));

    await waitFor(() =>
      expect(empresaService.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ nit: '900123456' })
      )
    );
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/admin/__tests__/EmpresasPage.test.tsx`
Expected: FAIL — placeholder page has none of this content.

- [ ] **Step 3: Implement `EmpresasPage`**

```typescript
// src/pages/admin/EmpresasPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { TablePagination } from '@/components/shared/TablePagination';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';
import type { Empresa } from '@/types/empresa';

const PAGE_SIZE = 20;

export function EmpresasPage() {
  const navigate = useNavigate();
  const canCreate = useCanPerform('empresa.create');
  const canUpdate = useCanPerform('empresa.update');

  const [skip, setSkip] = useState(0);
  const [nitFilter, setNitFilter] = useState('');
  const [ciudadFilter, setCiudadFilter] = useState('');
  const [departamentoFilter, setDepartamentoFilter] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ nit: '', ciudad: '', departamento: '' });

  const { data: empresas = [], isLoading } = useQuery({
    queryKey: ['empresas-admin', skip, appliedFilters],
    queryFn: () =>
      empresaService.list({
        skip,
        limit: PAGE_SIZE,
        nit: appliedFilters.nit || undefined,
        ciudad: appliedFilters.ciudad || undefined,
        departamento: appliedFilters.departamento || undefined,
      }),
  });

  const handleSearch = () => {
    setSkip(0);
    setAppliedFilters({ nit: nitFilter, ciudad: ciudadFilter, departamento: departamentoFilter });
  };

  const handleVerEmpleados = (empresa: Empresa) => {
    navigate(`/empleados?empresa_id=${empresa.id}`);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Empresas</h1>
          <p className="text-slate-500 mt-1">Empresas afiliadas y sus usuarios de acceso.</p>
        </div>
        {canCreate && <Button>Crear empresa</Button>}
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="nit-filter">NIT o razón social</Label>
          <Input id="nit-filter" value={nitFilter} onChange={(e) => setNitFilter(e.target.value)} className="w-56" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="ciudad-filter">Ciudad</Label>
          <Input id="ciudad-filter" value={ciudadFilter} onChange={(e) => setCiudadFilter(e.target.value)} className="w-40" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="departamento-filter">Departamento</Label>
          <Input id="departamento-filter" value={departamentoFilter} onChange={(e) => setDepartamentoFilter(e.target.value)} className="w-40" />
        </div>
        <Button onClick={handleSearch}>Buscar</Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>NIT</TableHead>
              <TableHead>Razón social</TableHead>
              <TableHead>Ciudad</TableHead>
              <TableHead>Departamento</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && empresas.map((empresa) => (
              <TableRow key={empresa.id}>
                <TableCell>{empresa.nit}</TableCell>
                <TableCell className="font-medium">{empresa.razon_social}</TableCell>
                <TableCell>{empresa.ciudad ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>{empresa.departamento ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>
                  <Badge variant={empresa.estado === 'ACTIVA' ? 'default' : 'secondary'}>{empresa.estado}</Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  <Button variant="outline" size="sm" onClick={() => handleVerEmpleados(empresa)}>
                    Ver empleados
                  </Button>
                  {canUpdate && (
                    <>
                      <Button variant="outline" size="sm">Editar</Button>
                      <Button variant="outline" size="sm">Regenerar contraseña</Button>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="p-4">
          <TablePagination
            skip={skip}
            limit={PAGE_SIZE}
            resultCount={empresas.length}
            onPrev={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
            onNext={() => setSkip(skip + PAGE_SIZE)}
          />
        </div>
      </div>
    </div>
  );
}
```

(The "Crear empresa", "Editar", and "Regenerar contraseña" buttons are visually present per the role check but not yet wired to a `Dialog` — Task 7 replaces them with working modals, matching this task's exact button labels/`data-testid`-free selectors so Task 7's diff only adds behavior, not new markup to find.)

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/admin/__tests__/EmpresasPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pages/admin/EmpresasPage.tsx src/pages/admin/__tests__/EmpresasPage.test.tsx
git commit -m "feat: implement EmpresasPage list, filters, and pagination"
```

---

### Task 7: Empresa create/edit modal + password reveal modal

**Files:**
- Modify: `src/pages/admin/EmpresasPage.tsx`
- Create: `src/components/empresas/PasswordRevealDialog.tsx`
- Test: extend `src/pages/admin/__tests__/EmpresasPage.test.tsx`; new `src/components/empresas/__tests__/PasswordRevealDialog.test.tsx`

**Interfaces:**
- Consumes: `empresaService.create/update/regenerarPassword` (Task 2).
- Produces: `<PasswordRevealDialog open username password onClose />` — a standalone component so it can be reused identically by both "Crear empresa" and "Regenerar contraseña" flows within `EmpresasPage`.

- [ ] **Step 1: Write the failing tests**

```typescript
// src/components/empresas/__tests__/PasswordRevealDialog.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PasswordRevealDialog } from '../PasswordRevealDialog';

describe('PasswordRevealDialog', () => {
  it('shows username and password', () => {
    render(<PasswordRevealDialog open username="900123456" password="Abc12345xyz" onClose={vi.fn()} />);
    expect(screen.getByText('900123456')).toBeInTheDocument();
    expect(screen.getByText('Abc12345xyz')).toBeInTheDocument();
  });

  it('keeps "Cerrar" disabled until the confirmation checkbox is checked', () => {
    render(<PasswordRevealDialog open username="u" password="p" onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /cerrar/i })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(screen.getByRole('button', { name: /cerrar/i })).not.toBeDisabled();
  });

  it('calls onClose only after the checkbox is checked and Cerrar is clicked', () => {
    const onClose = vi.fn();
    render(<PasswordRevealDialog open username="u" password="p" onClose={onClose} />);
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: /cerrar/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
```

Add to `src/pages/admin/__tests__/EmpresasPage.test.tsx`:

```typescript
it('creating an empresa shows the password reveal dialog with the generated credentials', async () => {
  setUser(RolUsuario.ADMIN);
  vi.mocked(empresaService.create).mockResolvedValue({
    id: '2', nit: '900555555', razon_social: 'Nueva SAS', estado: 'ACTIVA',
    email_contacto: 'nueva@empresa.com', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
    usuario_generado: { username: '900555555', password: 'GenPass123x' },
  });
  renderPage();
  await waitFor(() => expect(screen.getByText('Empresa Uno')).toBeInTheDocument());

  fireEvent.click(screen.getByRole('button', { name: /^crear empresa$/i }));
  fireEvent.change(screen.getByLabelText(/^nit$/i), { target: { value: '900555555' } });
  fireEvent.change(screen.getByLabelText(/razón social/i), { target: { value: 'Nueva SAS' } });
  fireEvent.change(screen.getByLabelText(/correo/i), { target: { value: 'nueva@empresa.com' } });
  fireEvent.click(screen.getByRole('button', { name: /^guardar$/i }));

  await waitFor(() => expect(screen.getByText('GenPass123x')).toBeInTheDocument());
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/empresas/__tests__/PasswordRevealDialog.test.tsx src/pages/admin/__tests__/EmpresasPage.test.tsx`
Expected: FAIL — `PasswordRevealDialog` doesn't exist; `EmpresasPage`'s create button has no form/dialog behind it yet.

- [ ] **Step 3: Implement**

```typescript
// src/components/empresas/PasswordRevealDialog.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from '@/components/ui/use-toast';

interface PasswordRevealDialogProps {
  open: boolean;
  username: string;
  password: string;
  onClose: () => void;
}

export function PasswordRevealDialog({ open, username, password, onClose }: PasswordRevealDialogProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: 'Error al copiar', description: 'No se pudo copiar al portapapeles', variant: 'destructive' });
    }
  };

  const handleClose = () => {
    if (!confirmed) return;
    setConfirmed(false);
    onClose();
  };

  return (
    <Dialog open={open}>
      <DialogContent onInteractOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>Credenciales generadas</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3">
            Esta contraseña no se volverá a mostrar. Cópiala ahora y compártela de forma segura.
          </p>
          <div className="space-y-1">
            <span className="text-sm text-slate-500">Usuario</span>
            <p className="font-mono text-sm bg-slate-100 rounded px-2 py-1 select-all">{username}</p>
          </div>
          <div className="space-y-1">
            <span className="text-sm text-slate-500">Contraseña</span>
            <div className="flex items-center gap-2">
              <p className="font-mono text-sm bg-slate-100 rounded px-2 py-1 select-all flex-1">{password}</p>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? 'Copiado' : 'Copiar'}
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-2">
            <Checkbox id="confirm-copied" checked={confirmed} onCheckedChange={(v) => setConfirmed(v === true)} />
            <label htmlFor="confirm-copied" className="text-sm">Copié la contraseña</label>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleClose} disabled={!confirmed}>Cerrar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

In `src/pages/admin/EmpresasPage.tsx`, add state, mutations, and the create/edit `Dialog` (following `AuditoresPage`'s exact pattern), plus wire the `PasswordRevealDialog`:

```typescript
// additions to imports
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '@/components/ui/dialog';
import { PasswordRevealDialog } from '@/components/empresas/PasswordRevealDialog';
import type { UsuarioGenerado } from '@/types/empresa';

function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

interface EmpresaFormState {
  nit: string;
  razon_social: string;
  email_contacto: string;
  telefono: string;
  direccion: string;
  ciudad: string;
  departamento: string;
}

const emptyEmpresaForm: EmpresaFormState = {
  nit: '', razon_social: '', email_contacto: '', telefono: '', direccion: '', ciudad: '', departamento: '',
};
```

Inside the component, add:

```typescript
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Empresa | null>(null);
  const [form, setForm] = useState<EmpresaFormState>(emptyEmpresaForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [credenciales, setCredenciales] = useState<UsuarioGenerado | null>(null);

  const createMutation = useMutation({
    mutationFn: () => empresaService.create({
      nit: form.nit,
      razon_social: form.razon_social,
      email_contacto: form.email_contacto,
      telefono: form.telefono || undefined,
      direccion: form.direccion || undefined,
      ciudad: form.ciudad || undefined,
      departamento: form.departamento || undefined,
    }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['empresas-admin'] });
      setDialogOpen(false);
      setForm(emptyEmpresaForm);
      setErrorMessage(null);
      setCredenciales(data.usuario_generado);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo crear la empresa')),
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay empresa en edición');
      return empresaService.update(editing.id, {
        razon_social: form.razon_social,
        email_contacto: form.email_contacto,
        telefono: form.telefono || undefined,
        direccion: form.direccion || undefined,
        ciudad: form.ciudad || undefined,
        departamento: form.departamento || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyEmpresaForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo actualizar la empresa')),
  });

  const regenerarPasswordMutation = useMutation({
    mutationFn: (id: string) => empresaService.regenerarPassword(id),
    onSuccess: (data) => setCredenciales({ username: data.username, password: data.password }),
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo regenerar la contraseña')),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyEmpresaForm);
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const openEdit = (empresa: Empresa) => {
    setEditing(empresa);
    setForm({
      nit: empresa.nit,
      razon_social: empresa.razon_social,
      email_contacto: empresa.email_contacto ?? '',
      telefono: empresa.telefono ?? '',
      direccion: empresa.direccion ?? '',
      ciudad: empresa.ciudad ?? '',
      departamento: empresa.departamento ?? '',
    });
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };
```

Replace the `{canCreate && <Button>Crear empresa</Button>}` line with the full `Dialog`:

```tsx
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          {canCreate && (
            <DialogTrigger asChild>
              <Button onClick={openCreate}>Crear empresa</Button>
            </DialogTrigger>
          )}
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editing ? 'Editar Empresa' : 'Crear Empresa'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="nit">NIT</Label>
                  <Input id="nit" value={form.nit} onChange={(e) => setForm({ ...form, nit: e.target.value })} />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="razon_social">Razón social</Label>
                <Input id="razon_social" value={form.razon_social} onChange={(e) => setForm({ ...form, razon_social: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email_contacto">Correo de contacto</Label>
                <Input id="email_contacto" type="email" value={form.email_contacto} onChange={(e) => setForm({ ...form, email_contacto: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telefono">Teléfono</Label>
                <Input id="telefono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="direccion">Dirección</Label>
                <Input id="direccion" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ciudad">Ciudad</Label>
                <Input id="ciudad" value={form.ciudad} onChange={(e) => setForm({ ...form, ciudad: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="departamento">Departamento</Label>
                <Input id="departamento" value={form.departamento} onChange={(e) => setForm({ ...form, departamento: e.target.value })} />
              </div>
            </div>
            {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            <DialogFooter>
              <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
```

Replace the row-action buttons with wired versions:

```tsx
                  {canUpdate && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => openEdit(empresa)}>Editar</Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => regenerarPasswordMutation.mutate(empresa.id)}
                        disabled={regenerarPasswordMutation.isPending}
                      >
                        Regenerar contraseña
                      </Button>
                    </>
                  )}
```

Add `<PasswordRevealDialog>` right before the component's closing `</div>`:

```tsx
      {credenciales && (
        <PasswordRevealDialog
          open
          username={credenciales.username}
          password={credenciales.password}
          onClose={() => setCredenciales(null)}
        />
      )}
```

Note: `Checkbox` (`@/components/ui/checkbox`) and `toast`/`use-toast` (`@/components/ui/use-toast`) must already exist in this project (confirmed during planning research — `toast` is used by `AuditorApprovalTemplateModal.tsx`); if `Checkbox` specifically isn't present, install it via the project's existing shadcn CLI convention (check how other `ui/*.tsx` files were added, e.g. a `components.json` + `npx shadcn add checkbox`) rather than hand-rolling one.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/empresas/__tests__/PasswordRevealDialog.test.tsx src/pages/admin/__tests__/EmpresasPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pages/admin/EmpresasPage.tsx src/components/empresas/PasswordRevealDialog.tsx src/components/empresas/__tests__/PasswordRevealDialog.test.tsx src/pages/admin/__tests__/EmpresasPage.test.tsx
git commit -m "feat: add empresa create/edit modal and password reveal/regenerate flow"
```

---

### Task 8: Analytics panel — `AnaliticaPanel`, `TopEmpresasChart`, `TendenciaRadicacionesChart`

**Files:**
- Create: `src/components/empresas/AnaliticaPanel.tsx`
- Create: `src/components/empresas/TopEmpresasChart.tsx`
- Create: `src/components/empresas/TendenciaRadicacionesChart.tsx`
- Modify: `src/pages/admin/EmpresasPage.tsx` (mount the panel)
- Test: `src/components/empresas/__tests__/AnaliticaPanel.test.tsx`

**Interfaces:**
- Consumes: `empresaService.getAnalitica` (Task 2).
- Produces: `<AnaliticaPanel />` mounted at the top of `EmpresasPage` — self-contained, no props needed (fetches its own data).

- [ ] **Step 1: Write the failing test**

```typescript
// src/components/empresas/__tests__/AnaliticaPanel.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnaliticaPanel } from '../AnaliticaPanel';
import { empresaService } from '@/services/empresaService';

vi.mock('@/services/empresaService');

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AnaliticaPanel />
    </QueryClientProvider>
  );
}

describe('AnaliticaPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shows "No hay datos para mostrar" when both datasets are empty', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
    renderPanel();
    await waitFor(() => expect(screen.getAllByText(/no hay datos/i).length).toBeGreaterThan(0));
  });

  it('renders empresa names from the top_empresas payload', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({
      top_empresas: [{ empresa_id: '1', razon_social: 'Empresa Líder SAS', nit: '900111222', total_radicadas: 42 }],
      tendencia_mensual: [{ periodo: '2026-07', total: 10 }],
    });
    renderPanel();
    await waitFor(() => expect(screen.getByText('Empresa Líder SAS')).toBeInTheDocument());
  });

  it('shows a retry button on error and refetches on click', async () => {
    vi.mocked(empresaService.getAnalitica).mockRejectedValueOnce(new Error('network error'));
    renderPanel();
    await waitFor(() => expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument());

    vi.mocked(empresaService.getAnalitica).mockResolvedValueOnce({ top_empresas: [], tendencia_mensual: [] });
    fireEvent.click(screen.getByRole('button', { name: /reintentar/i }));
    await waitFor(() => expect(empresaService.getAnalitica).toHaveBeenCalledTimes(2));
  });

  it('toggles collapsed state and persists it to localStorage', async () => {
    vi.mocked(empresaService.getAnalitica).mockResolvedValue({ top_empresas: [], tendencia_mensual: [] });
    renderPanel();
    await waitFor(() => expect(screen.getAllByText(/no hay datos/i).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole('button', { name: /analítica de empresas/i }));
    expect(localStorage.getItem('analitica-empresas-collapsed')).toBe('true');
    expect(screen.queryByText(/no hay datos/i)).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/empresas/__tests__/AnaliticaPanel.test.tsx`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement**

```typescript
// src/components/empresas/TopEmpresasChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { EmpresaTopItem } from '@/types/empresa';

interface TopEmpresasChartProps {
  data: EmpresaTopItem[];
}

function truncar(nombre: string, max = 22): string {
  return nombre.length > max ? `${nombre.slice(0, max - 1)}…` : nombre;
}

export function TopEmpresasChart({ data }: TopEmpresasChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Top 10 empresas por radicadas</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos para mostrar
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => ({ ...item, nombreCorto: truncar(item.razon_social) }));

  return (
    <Card>
      <CardHeader><CardTitle>Top 10 empresas por radicadas</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis type="number" className="text-xs" tickFormatter={(v) => v.toLocaleString('es-CO')} />
            <YAxis type="category" dataKey="nombreCorto" width={140} className="text-xs" />
            <Tooltip
              contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '6px' }}
              formatter={(value: number) => [value.toLocaleString('es-CO'), 'Radicadas']}
              labelFormatter={(_, payload) => {
                const item = payload?.[0]?.payload as EmpresaTopItem | undefined;
                return item ? `${item.razon_social} (NIT ${item.nit})` : '';
              }}
            />
            <Bar dataKey="total_radicadas" fill="#9333ea" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

```typescript
// src/components/empresas/TendenciaRadicacionesChart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TendenciaMensualItem } from '@/types/empresa';

interface TendenciaRadicacionesChartProps {
  data: TendenciaMensualItem[];
}

const MESES: Record<string, string> = {
  '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun',
  '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic',
};

export function TendenciaRadicacionesChart({ data }: TendenciaRadicacionesChartProps) {
  const hasData = data && data.some((d) => d.total > 0);
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Tendencia mensual de radicaciones</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos para mostrar
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => {
    const [anio, mes] = item.periodo.split('-');
    return { periodo: `${MESES[mes]} ${anio}`, total: item.total };
  });

  return (
    <Card>
      <CardHeader><CardTitle>Tendencia mensual de radicaciones</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="periodo" className="text-xs" />
            <YAxis className="text-xs" allowDecimals={false} />
            <Tooltip
              contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '6px' }}
              formatter={(value: number) => [value.toLocaleString('es-CO'), 'Radicaciones']}
            />
            <Line type="monotone" dataKey="total" stroke="#9333ea" strokeWidth={2} dot={{ fill: '#9333ea', r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
        {!hasData && (
          <p className="text-xs text-muted-foreground text-center mt-2">Sin radicaciones en los últimos 12 meses</p>
        )}
      </CardContent>
    </Card>
  );
}
```

```typescript
// src/components/empresas/AnaliticaPanel.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { empresaService } from '@/services/empresaService';
import { TopEmpresasChart } from './TopEmpresasChart';
import { TendenciaRadicacionesChart } from './TendenciaRadicacionesChart';

const STORAGE_KEY = 'analitica-empresas-collapsed';

export function AnaliticaPanel() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(STORAGE_KEY) === 'true');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['empresas-analitica'],
    queryFn: () => empresaService.getAnalitica(),
  });

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem(STORAGE_KEY, String(next));
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <button
        type="button"
        onClick={toggle}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Analítica de empresas</h2>
          <p className="text-sm text-slate-500">Top 10 y tendencia de los últimos 12 meses</p>
        </div>
        {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
      </button>

      {!collapsed && (
        <div className="p-4 pt-0">
          {isLoading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Skeleton className="h-[300px] w-full" />
              <Skeleton className="h-[300px] w-full" />
            </div>
          )}
          {isError && !isLoading && (
            <div className="flex flex-col items-center justify-center h-[200px] gap-3 text-muted-foreground">
              <p>No se pudo cargar la analítica.</p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>Reintentar</Button>
            </div>
          )}
          {!isLoading && !isError && data && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TopEmpresasChart data={data.top_empresas} />
              <TendenciaRadicacionesChart data={data.tendencia_mensual} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

In `src/pages/admin/EmpresasPage.tsx`, add the import and mount it as the first child inside the outer `<div className="space-y-4 p-6">`:

```typescript
import { AnaliticaPanel } from '@/components/empresas/AnaliticaPanel';
```

```tsx
    <div className="space-y-4 p-6">
      <AnaliticaPanel />
      <div className="flex items-center justify-between">
```

Note: `Skeleton` (`@/components/ui/skeleton`) and `lucide-react`'s `ChevronDown`/`ChevronRight` were both confirmed present in this project during planning research (used by `Sidebar.tsx`) — no new dependency.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/empresas/__tests__/AnaliticaPanel.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/components/empresas/AnaliticaPanel.tsx src/components/empresas/TopEmpresasChart.tsx src/components/empresas/TendenciaRadicacionesChart.tsx src/pages/admin/EmpresasPage.tsx src/components/empresas/__tests__/AnaliticaPanel.test.tsx
git commit -m "feat: add collapsible analytics panel with top-10 and trend charts"
```

---

### Task 9: `EmpleadosPage` — list, filters, pagination, cross-navigation

**Files:**
- Modify: `src/pages/admin/EmpleadosPage.tsx` (replace placeholder body)
- Test: `src/pages/admin/__tests__/EmpleadosPage.test.tsx`

**Interfaces:**
- Consumes: `empleadoService.list` (Task 3), `TablePagination` (Task 4), `useCanPerform` (Task 1).
- Produces: page shell that Task 10 (create/edit modal) and Task 11 (bulk-upload wizard button) slot into.

- [ ] **Step 1: Write the failing test**

```typescript
// src/pages/admin/__tests__/EmpleadosPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpleadosPage } from '../EmpleadosPage';
import { empleadoService } from '@/services/empleadoService';
import { empresaService } from '@/services/empresaService';
import { useAuthStore } from '@/store/authStore';
import { RolUsuario } from '@/types/enums';

vi.mock('@/services/empleadoService');
vi.mock('@/services/empresaService');

function renderPage(initialRoute = '/empleados') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <EmpleadosPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function setUser(rol: RolUsuario) {
  useAuthStore.setState({
    isAuthenticated: true,
    user: { id: '1', username: 'u', email: 'u@u.com', nombres: 'U', apellidos: 'U', rol, estado: 'ACTIVO' as any, created_at: '', updated_at: '' },
    accessToken: 't', refreshToken: 'r',
  });
}

describe('EmpleadosPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(empleadoService.list).mockResolvedValue([
      { id: '1', numero_documento: '123', tipo_documento: 'CC', nombres: 'Ana', apellidos: 'Gómez', cargo: 'Analista', estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' },
    ]);
    vi.mocked(empresaService.list).mockResolvedValue([
      { id: 'e1', nit: '900111', razon_social: 'Empresa A', estado: 'ACTIVA', created_at: '2026-01-01T00:00:00Z' },
    ]);
  });

  it('renders the employee list', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
  });

  it('pre-fills the empresa filter from ?empresa_id= query param', async () => {
    setUser(RolUsuario.ADMIN);
    renderPage('/empleados?empresa_id=e1');
    await waitFor(() =>
      expect(empleadoService.list).toHaveBeenCalledWith(
        expect.objectContaining({ empresa_id: 'e1' })
      )
    );
  });

  it('shows "Crear empleado" and "Cargar masivo" for AUDITOR but not LIQUIDADOR', async () => {
    setUser(RolUsuario.AUDITOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /crear empleado/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cargar masivo/i })).toBeInTheDocument();
  });

  it('hides "Crear empleado" and "Cargar masivo" for LIQUIDADOR', async () => {
    setUser(RolUsuario.LIQUIDADOR);
    renderPage();
    await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /crear empleado/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cargar masivo/i })).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/admin/__tests__/EmpleadosPage.test.tsx`
Expected: FAIL — placeholder page has none of this content.

- [ ] **Step 3: Implement `EmpleadosPage`**

```typescript
// src/pages/admin/EmpleadosPage.tsx
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { TablePagination } from '@/components/shared/TablePagination';
import { empleadoService } from '@/services/empleadoService';
import { empresaService } from '@/services/empresaService';
import { useCanPerform } from '@/store/authStore';

const PAGE_SIZE = 20;
const ALL_EMPRESAS = 'ALL';

export function EmpleadosPage() {
  const [searchParams] = useSearchParams();
  const canCreate = useCanPerform('empleado.create');
  const canUpdate = useCanPerform('empleado.update');

  const [skip, setSkip] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [empresaId, setEmpresaId] = useState(searchParams.get('empresa_id') ?? ALL_EMPRESAS);

  const { data: empresas = [] } = useQuery({
    queryKey: ['empresas-para-filtro'],
    queryFn: () => empresaService.list({ limit: 1000 }),
  });

  const { data: empleados = [], isLoading } = useQuery({
    queryKey: ['empleados-admin', skip, appliedSearch, empresaId],
    queryFn: () =>
      empleadoService.list({
        skip,
        limit: PAGE_SIZE,
        search: appliedSearch || undefined,
        empresa_id: empresaId === ALL_EMPRESAS ? undefined : empresaId,
      }),
  });

  const handleSearch = () => {
    setSkip(0);
    setAppliedSearch(searchTerm);
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Empleados</h1>
          <p className="text-slate-500 mt-1">Empleados por empresa o de todas las empresas afiliadas.</p>
        </div>
        {canCreate && (
          <div className="space-x-2">
            <Button variant="outline">Cargar masivo</Button>
            <Button>Crear empleado</Button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="empresa-filter">Empresa</Label>
          <Select value={empresaId} onValueChange={(v) => { setEmpresaId(v); setSkip(0); }}>
            <SelectTrigger id="empresa-filter" className="w-56">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_EMPRESAS}>Todas las empresas</SelectItem>
              {empresas.map((e) => (
                <SelectItem key={e.id} value={e.id}>{e.razon_social}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="search-filter">Nombres, apellidos o documento</Label>
          <Input id="search-filter" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-64" />
        </div>
        <Button onClick={handleSearch}>Buscar</Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Documento</TableHead>
              <TableHead>Nombres</TableHead>
              <TableHead>Apellidos</TableHead>
              <TableHead>Cargo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && empleados.map((empleado) => (
              <TableRow key={empleado.id}>
                <TableCell>{empleado.tipo_documento} {empleado.numero_documento}</TableCell>
                <TableCell className="font-medium">{empleado.nombres}</TableCell>
                <TableCell>{empleado.apellidos}</TableCell>
                <TableCell>{empleado.cargo ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>
                  <Badge variant={empleado.estado === 'ACTIVO' ? 'default' : 'secondary'}>{empleado.estado}</Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  {canUpdate && <Button variant="outline" size="sm">Editar</Button>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="p-4">
          <TablePagination
            skip={skip}
            limit={PAGE_SIZE}
            resultCount={empleados.length}
            onPrev={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
            onNext={() => setSkip(skip + PAGE_SIZE)}
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/admin/__tests__/EmpleadosPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pages/admin/EmpleadosPage.tsx src/pages/admin/__tests__/EmpleadosPage.test.tsx
git commit -m "feat: implement EmpleadosPage list, filters, pagination, cross-navigation prefill"
```

---

### Task 10: Empleado create/edit modal

**Files:**
- Modify: `src/pages/admin/EmpleadosPage.tsx`
- Test: extend `src/pages/admin/__tests__/EmpleadosPage.test.tsx`

**Interfaces:**
- Consumes: `empleadoService.create/update` (Task 3).

- [ ] **Step 1: Write the failing test**

Add to `src/pages/admin/__tests__/EmpleadosPage.test.tsx`:

```typescript
it('creates an employee via the modal form', async () => {
  setUser(RolUsuario.ADMIN);
  vi.mocked(empleadoService.create).mockResolvedValue({
    id: '2', empresa_id: 'e1', numero_documento: '999', tipo_documento: 'CC',
    nombres: 'Luis', apellidos: 'Ramírez', fecha_ingreso: '2024-01-01', estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z',
  });
  renderPage('/empleados?empresa_id=e1');
  await waitFor(() => expect(screen.getByText('Ana')).toBeInTheDocument());

  fireEvent.click(screen.getByRole('button', { name: /^crear empleado$/i }));
  fireEvent.change(screen.getByLabelText(/número de documento/i), { target: { value: '999' } });
  fireEvent.change(screen.getByLabelText(/^nombres$/i), { target: { value: 'Luis' } });
  fireEvent.change(screen.getByLabelText(/^apellidos$/i), { target: { value: 'Ramírez' } });
  fireEvent.change(screen.getByLabelText(/fecha de ingreso/i), { target: { value: '2024-01-01' } });
  fireEvent.click(screen.getByRole('button', { name: /^guardar$/i }));

  await waitFor(() => expect(empleadoService.create).toHaveBeenCalledWith(
    expect.objectContaining({ numero_documento: '999', nombres: 'Luis', apellidos: 'Ramírez', empresa_id: 'e1' })
  ));
});
```

(`fireEvent.change` for `<Input type="date">` needs a matching `<Label htmlFor>` pairing in the implementation, per this test's `getByLabelText` calls — implement accordingly.)

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/admin/__tests__/EmpleadosPage.test.tsx`
Expected: FAIL — "Crear empleado" button doesn't open a form yet.

- [ ] **Step 3: Implement the modal**

Add to `src/pages/admin/EmpleadosPage.tsx` imports:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '@/components/ui/dialog';
import type { EmpleadoListItem } from '@/types/empleado';

function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

interface EmpleadoFormState {
  numero_documento: string;
  tipo_documento: string;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string;
  fecha_nacimiento: string;
  genero: string;
  cargo: string;
  area: string;
  fecha_ingreso: string;
  salario_base: string;
}

const emptyEmpleadoForm: EmpleadoFormState = {
  numero_documento: '', tipo_documento: 'CC', nombres: '', apellidos: '', email: '', telefono: '',
  fecha_nacimiento: '', genero: '', cargo: '', area: '', fecha_ingreso: '', salario_base: '',
};
```

Inside the component:

```typescript
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<EmpleadoListItem | null>(null);
  const [form, setForm] = useState<EmpleadoFormState>(emptyEmpleadoForm);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => {
      if (empresaId === ALL_EMPRESAS) throw new Error('Selecciona una empresa antes de crear un empleado');
      return empleadoService.create({
        empresa_id: empresaId,
        numero_documento: form.numero_documento,
        tipo_documento: form.tipo_documento,
        nombres: form.nombres,
        apellidos: form.apellidos,
        email: form.email || undefined,
        telefono: form.telefono || undefined,
        fecha_nacimiento: form.fecha_nacimiento || undefined,
        genero: form.genero || undefined,
        cargo: form.cargo || undefined,
        area: form.area || undefined,
        fecha_ingreso: form.fecha_ingreso,
        salario_base: form.salario_base ? Number(form.salario_base) : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
      setDialogOpen(false);
      setForm(emptyEmpleadoForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo crear el empleado')),
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay empleado en edición');
      return empleadoService.update(editing.id, {
        nombres: form.nombres,
        apellidos: form.apellidos,
        email: form.email || undefined,
        telefono: form.telefono || undefined,
        fecha_nacimiento: form.fecha_nacimiento || undefined,
        genero: form.genero || undefined,
        cargo: form.cargo || undefined,
        area: form.area || undefined,
        fecha_ingreso: form.fecha_ingreso || undefined,
        salario_base: form.salario_base ? Number(form.salario_base) : undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyEmpleadoForm);
      setErrorMessage(null);
    },
    onError: (error: unknown) => setErrorMessage(extractErrorMessage(error, 'No se pudo actualizar el empleado')),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyEmpleadoForm);
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const openEdit = (empleado: EmpleadoListItem) => {
    setEditing(empleado);
    setForm({
      ...emptyEmpleadoForm,
      numero_documento: empleado.numero_documento,
      tipo_documento: empleado.tipo_documento,
      nombres: empleado.nombres,
      apellidos: empleado.apellidos,
      cargo: empleado.cargo ?? '',
    });
    setErrorMessage(null);
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };
```

Replace the `{canCreate && (<div className="space-x-2">...<Button>Crear empleado</Button></div>)}` block with:

```tsx
        {canCreate && (
          <div className="space-x-2">
            <Button variant="outline">Cargar masivo</Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={openCreate}>Crear empleado</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{editing ? 'Editar Empleado' : 'Crear Empleado'}</DialogTitle>
                </DialogHeader>
                <div className="space-y-3">
                  {!editing && (
                    <div className="space-y-2">
                      <Label htmlFor="numero_documento">Número de documento</Label>
                      <Input id="numero_documento" value={form.numero_documento} onChange={(e) => setForm({ ...form, numero_documento: e.target.value })} />
                    </div>
                  )}
                  <div className="space-y-2">
                    <Label htmlFor="nombres">Nombres</Label>
                    <Input id="nombres" value={form.nombres} onChange={(e) => setForm({ ...form, nombres: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="apellidos">Apellidos</Label>
                    <Input id="apellidos" value={form.apellidos} onChange={(e) => setForm({ ...form, apellidos: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cargo">Cargo</Label>
                    <Input id="cargo" value={form.cargo} onChange={(e) => setForm({ ...form, cargo: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="fecha_ingreso">Fecha de ingreso</Label>
                    <Input id="fecha_ingreso" type="date" value={form.fecha_ingreso} onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })} />
                  </div>
                </div>
                {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
                <DialogFooter>
                  <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
                    Guardar
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        )}
```

And wire the row "Editar" button: `<Button variant="outline" size="sm" onClick={() => openEdit(empleado)}>Editar</Button>`.

(Banking fields `cuenta_bancaria`/`banco`/`tipo_cuenta` are intentionally absent from this form, matching the backend decision that they're never collected at creation.)

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/admin/__tests__/EmpleadosPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pages/admin/EmpleadosPage.tsx src/pages/admin/__tests__/EmpleadosPage.test.tsx
git commit -m "feat: add empleado create/edit modal"
```

---

### Task 11: `CargaMasivaWizard` — 3-step bulk upload

**Files:**
- Create: `src/components/empleados/CargaMasivaWizard.tsx`
- Modify: `src/pages/admin/EmpleadosPage.tsx` (wire the "Cargar masivo" button)
- Test: `src/components/empleados/__tests__/CargaMasivaWizard.test.tsx`

**Interfaces:**
- Consumes: `empleadoService.getPlantilla/validarCargaMasiva/confirmarCargaMasiva` (Task 3).

- [ ] **Step 1: Write the failing test**

```typescript
// src/components/empleados/__tests__/CargaMasivaWizard.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CargaMasivaWizard } from '../CargaMasivaWizard';
import { empleadoService } from '@/services/empleadoService';

vi.mock('@/services/empleadoService');

function makeFile() {
  return new File(['contenido'], 'empleados.xlsx', {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

describe('CargaMasivaWizard', () => {
  beforeEach(() => vi.clearAllMocks());

  it('step 1 → validar → step 2 shows the error summary', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 2, validas: 1, con_error: 1,
      errores: [{ fila: 2, columna: 'numero_documento', mensaje: 'Campo obligatorio' }],
    });
    const onClose = vi.fn();
    render(<CargaMasivaWizard open onClose={onClose} />);

    const fileInput = screen.getByLabelText(/archivo/i) as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));

    await waitFor(() => expect(screen.getByText(/campo obligatorio/i)).toBeInTheDocument());
    expect(screen.getByText(/1 válidas/i)).toBeInTheDocument();
    expect(screen.getByText(/1 con error/i)).toBeInTheDocument();
  });

  it('step 2 → confirmar disabled when validas=0', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 0, con_error: 1,
      errores: [{ fila: 2, mensaje: 'Campo obligatorio', columna: 'nombres' }],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));

    await waitFor(() => expect(screen.getByRole('button', { name: /confirmar carga/i })).toBeDisabled());
  });

  it('step 2 → confirmar → step 3 shows insertadas/con_error summary', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 1, con_error: 0, errores: [],
    });
    vi.mocked(empleadoService.confirmarCargaMasiva).mockResolvedValue({
      total_filas: 1, insertadas: 1, con_error: 0, errores: [],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /confirmar carga/i })).not.toBeDisabled());

    fireEvent.click(screen.getByRole('button', { name: /confirmar carga/i }));

    await waitFor(() => expect(screen.getByText(/1 insertadas/i)).toBeInTheDocument());
  });

  it('"Volver" returns from step 2 to step 1', async () => {
    vi.mocked(empleadoService.validarCargaMasiva).mockResolvedValue({
      total_filas: 1, validas: 1, con_error: 0, errores: [],
    });
    render(<CargaMasivaWizard open onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/archivo/i), { target: { files: [makeFile()] } });
    fireEvent.click(screen.getByRole('button', { name: /validar/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /volver/i })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /volver/i }));
    expect(screen.getByRole('button', { name: /^validar$/i })).toBeInTheDocument();
  });

  it('"Descargar plantilla" calls empleadoService.getPlantilla', async () => {
    vi.mocked(empleadoService.getPlantilla).mockResolvedValue(new Blob(['x']));
    // jsdom has no real URL.createObjectURL; stub it for this assertion-only test.
    global.URL.createObjectURL = vi.fn(() => 'blob:mock');
    global.URL.revokeObjectURL = vi.fn();
    render(<CargaMasivaWizard open onClose={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /descargar plantilla/i }));

    await waitFor(() => expect(empleadoService.getPlantilla).toHaveBeenCalled());
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/empleados/__tests__/CargaMasivaWizard.test.tsx`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Implement**

```typescript
// src/components/empleados/CargaMasivaWizard.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { empleadoService } from '@/services/empleadoService';
import type { ValidacionMasivaResponse, ConfirmacionMasivaResponse } from '@/types/empleado';

interface CargaMasivaWizardProps {
  open: boolean;
  onClose: () => void;
}

type Step = 1 | 2 | 3;

export function CargaMasivaWizard({ open, onClose }: CargaMasivaWizardProps) {
  const [step, setStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [validando, setValidando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [validacion, setValidacion] = useState<ValidacionMasivaResponse | null>(null);
  const [confirmacion, setConfirmacion] = useState<ConfirmacionMasivaResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDescargarPlantilla = async () => {
    const blob = await empleadoService.getPlantilla();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'plantilla_empleados.xlsx';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleValidar = async () => {
    if (!file) return;
    setValidando(true);
    setErrorMessage(null);
    try {
      const result = await empleadoService.validarCargaMasiva(file);
      setValidacion(result);
      setStep(2);
    } catch {
      setErrorMessage('No se pudo validar el archivo. Verifica el formato e inténtalo de nuevo.');
    } finally {
      setValidando(false);
    }
  };

  const handleConfirmar = async () => {
    if (!file) return;
    setConfirmando(true);
    setErrorMessage(null);
    try {
      const result = await empleadoService.confirmarCargaMasiva(file);
      setConfirmacion(result);
      setStep(3);
    } catch {
      setErrorMessage('No se pudo confirmar la carga. Inténtalo de nuevo.');
    } finally {
      setConfirmando(false);
    }
  };

  const handleClose = () => {
    setStep(1);
    setFile(null);
    setValidacion(null);
    setConfirmacion(null);
    setErrorMessage(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Carga masiva de empleados — Paso {step} de 3</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4">
            <Button variant="outline" onClick={handleDescargarPlantilla}>Descargar plantilla</Button>
            <div className="space-y-2">
              <Label htmlFor="carga-masiva-archivo">Archivo (.xlsx)</Label>
              <input
                id="carga-masiva-archivo"
                type="file"
                accept=".xlsx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full text-sm"
              />
            </div>
            {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            <DialogFooter>
              <Button onClick={handleValidar} disabled={!file || validando}>Validar</Button>
            </DialogFooter>
          </div>
        )}

        {step === 2 && validacion && (
          <div className="space-y-4">
            <p className="text-sm">
              {validacion.total_filas} filas totales · {validacion.validas} válidas · {validacion.con_error} con error
            </p>
            {validacion.errores.length > 0 && (
              <div className="max-h-64 overflow-auto border rounded">
                <Table>
                  <TableHeader>
                    <TableRow><TableHead>Fila</TableHead><TableHead>Columna</TableHead><TableHead>Mensaje</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {validacion.errores.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell>{e.fila}</TableCell>
                        <TableCell>{e.columna ?? '—'}</TableCell>
                        <TableCell>{e.mensaje}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
            <DialogFooter className="justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>Volver</Button>
              <Button onClick={handleConfirmar} disabled={validacion.validas === 0 || confirmando}>
                Confirmar carga
              </Button>
            </DialogFooter>
          </div>
        )}

        {step === 3 && confirmacion && (
          <div className="space-y-4">
            <p className="text-sm">
              {confirmacion.insertadas} insertadas · {confirmacion.con_error} con error
            </p>
            {confirmacion.errores.length > 0 && (
              <div className="max-h-64 overflow-auto border rounded">
                <Table>
                  <TableHeader>
                    <TableRow><TableHead>Fila</TableHead><TableHead>Columna</TableHead><TableHead>Mensaje</TableHead></TableRow>
                  </TableHeader>
                  <TableBody>
                    {confirmacion.errores.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell>{e.fila}</TableCell>
                        <TableCell>{e.columna ?? '—'}</TableCell>
                        <TableCell>{e.mensaje}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            <DialogFooter>
              <Button onClick={handleClose}>Cerrar</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

In `src/pages/admin/EmpleadosPage.tsx`, wire the "Cargar masivo" button:

```typescript
import { CargaMasivaWizard } from '@/components/empleados/CargaMasivaWizard';
```

```typescript
  const [wizardOpen, setWizardOpen] = useState(false);
```

Replace `<Button variant="outline">Cargar masivo</Button>` with:

```tsx
            <Button variant="outline" onClick={() => setWizardOpen(true)}>Cargar masivo</Button>
```

And mount it near the end of the returned JSX, before the closing `</div>`:

```tsx
      <CargaMasivaWizard
        open={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          queryClient.invalidateQueries({ queryKey: ['empleados-admin'] });
        }}
      />
```

(`queryClient` here is the same instance already introduced in Task 10 for the create/edit mutations — no new import needed beyond what Task 10 added.)

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/empleados/__tests__/CargaMasivaWizard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/components/empleados/CargaMasivaWizard.tsx src/pages/admin/EmpleadosPage.tsx src/components/empleados/__tests__/CargaMasivaWizard.test.tsx
git commit -m "feat: add 3-step bulk-upload wizard for empleados"
```

---

## Post-plan checklist (not a task — do after Task 11 lands)

- Run the full modified-file test sweep: `npm test -- src/store/__tests__/authStore.test.ts src/services/__tests__/empresaService.test.ts src/services/__tests__/empleadoService.test.ts src/components/shared/__tests__/TablePagination.test.tsx src/router/__tests__/router.test.tsx src/pages/admin/__tests__/EmpresasPage.test.tsx src/components/empresas/__tests__/PasswordRevealDialog.test.tsx src/components/empresas/__tests__/AnaliticaPanel.test.tsx src/pages/admin/__tests__/EmpleadosPage.test.tsx src/components/empleados/__tests__/CargaMasivaWizard.test.tsx`
- `npm run lint` and `npm run build` (`tsc -b && vite build`) — the project's build was previously confirmed broken for unrelated pre-existing reasons per prior session memory; confirm this plan's files don't add NEW `tsc` errors even if the pre-existing ones remain.
- Manually smoke-test the golden path in a browser per this project's UI-change convention: log in as ADMIN, create an empresa, confirm the password modal, edit it, regenerate its password, view its analytics panel, navigate to its employees via "Ver empleados", create an employee, and run the bulk-upload wizard end-to-end against a real backend.
