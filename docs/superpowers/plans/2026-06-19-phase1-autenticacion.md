# Phase 1 — Autenticación EMPRESA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate `portal-externo` behind a login for `EMPRESA` users linked to a company, and replace the public landing with a 3-action dashboard.

**Architecture:** Enrich the existing `GET /auth/me` backend response with the user's `empresa_id` + company summary. On the frontend, add a Zustand auth store + JWT-aware Axios instance (mirroring the proven `sistema-interno` implementation, adapted to portal-externo's Zod v4 stack), a `LoginPage`, a `ProtectedRoute` that requires `rol === 'EMPRESA'` AND a linked company, and a dashboard. The old public `/radicar` and `/consultar` routes are retired.

**Tech Stack:** FastAPI + Pydantic v2 (backend); React 19, React Router, Zustand + persist, Axios, React Query, Zod v4, Tailwind v4 (frontend). Backend tests: pytest in Docker (`docker exec incapacidades-api`). Frontend tests: vitest.

---

## File Structure

**Backend (modify):**
- `apps/backend/app/schemas/auth.py` — add `EmpresaResumen` + `empresa_id`/`empresa` to `UserProfileResponse`.
- `apps/backend/app/api/v1/endpoints/auth.py` — `/me` already returns `UserProfileResponse`; ensure `current_user.empresa` is loaded (it is, `lazy="selectin"`).
- `apps/backend/tests/test_auth_me_empresa.py` — new test.

**Frontend (create):**
- `src/types/auth.ts` — `User`, `EmpresaResumen`, `LoginRequest`, `LoginResponse`, `AuthTokens`.
- `src/lib/api.ts` — JWT-aware Axios instance with silent refresh (auth calls).
- `src/store/authStore.ts` — Zustand store (mirror sistema-interno).
- `src/services/authService.ts` — login/logout/refresh/getCurrentUser.
- `src/schemas/loginSchema.ts` — Zod v4 login schema.
- `src/pages/LoginPage.tsx` — login form.
- `src/components/auth/ProtectedRoute.tsx` — guard.
- `src/components/auth/AccesoDenegado.tsx` — blocked screen for non-EMPRESA / unlinked.
- `src/pages/Dashboard.tsx` — 3-action dashboard.

**Frontend (modify):**
- `src/App.tsx` — new routing (login, protected dashboard + redirects).
- `src/services/api.ts` — attach the same Bearer-token request interceptor used by `src/lib/api.ts` so existing data services send auth.

---

## Task 1: Backend — expose `empresa` in `/auth/me`

**Files:**
- Modify: `apps/backend/app/schemas/auth.py`
- Test: `apps/backend/tests/test_auth_me_empresa.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_auth_me_empresa.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_me_includes_empresa(client: AsyncClient, empresa_user_token: str):
    """GET /auth/me returns empresa_id and an empresa summary for an EMPRESA user."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rol"] == "EMPRESA"
    assert body["empresa_id"] is not None
    assert body["empresa"]["nit"]
    assert body["empresa"]["razon_social"]
```

> Note: reuse/extend existing auth fixtures in `tests/conftest.py`. If no `empresa_user_token`
> fixture exists, add one that creates an `Empresa` + a `Usuario(rol="EMPRESA", empresa_id=...)`
> and logs in to obtain a token, following the pattern of existing auth fixtures.

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auth_me_empresa.py -v --no-cov`
Expected: FAIL — `KeyError: 'empresa_id'` (field not in response).

- [ ] **Step 3: Add the schema fields**

```python
# apps/backend/app/schemas/auth.py  (add near UserProfileResponse)
from uuid import UUID
from typing import Optional


class EmpresaResumen(BaseModel):
    """Resumen de la empresa asociada al usuario autenticado."""
    id: UUID
    nit: str
    razon_social: str
    email_contacto: Optional[str] = None
    estado: str

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Schema para respuesta de perfil de usuario."""
    id: UUID
    username: str
    email: str
    nombre_completo: str
    rol: str
    estado: str
    empresa_id: Optional[UUID] = None
    empresa: Optional[EmpresaResumen] = None
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

> `current_user.empresa` is already loaded (`lazy="selectin"` on `Usuario.empresa`), so
> `UserProfileResponse.model_validate(current_user)` populates `empresa` automatically.
> No endpoint change needed.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_auth_me_empresa.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/schemas/auth.py apps/backend/tests/test_auth_me_empresa.py
git commit -m "feat(auth): expose empresa summary in /auth/me response"
```

---

## Task 2: Frontend — auth types

**Files:**
- Create: `apps/frontend/portal-externo/src/types/auth.ts`

- [ ] **Step 1: Create the types**

```typescript
// src/types/auth.ts
export interface EmpresaResumen {
  id: string;
  nit: string;
  razon_social: string;
  email_contacto?: string | null;
  estado: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  nombre_completo: string;
  rol: string;
  estado: string;
  empresa_id?: string | null;
  empresa?: EmpresaResumen | null;
  ultimo_acceso?: string | null;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/types/auth.ts
git commit -m "feat(auth): add auth types to portal-externo"
```

---

## Task 3: Frontend — JWT-aware Axios instance with silent refresh

**Files:**
- Create: `apps/frontend/portal-externo/src/lib/api.ts`

> Mirror `apps/frontend/sistema-interno/src/lib/api.ts`. This instance reads tokens from
> localStorage, attaches `Authorization: Bearer`, and on a 401 attempts one silent refresh
> via `/auth/refresh`, then retries; on refresh failure it clears auth and redirects to `/login`.

- [ ] **Step 1: Create the instance**

```typescript
// src/lib/api.ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let queue: Array<(token: string | null) => void> = [];

const flushQueue = (token: string | null) => {
  queue.forEach((cb) => cb(token));
  queue = [];
};

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;
    const isRefreshCall = original?.url?.includes('/auth/refresh');

    if (status !== 401 || original?._retry || isRefreshCall) {
      return Promise.reject(error);
    }
    original._retry = true;

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      forceLogout();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push((token) => {
          if (!token) return reject(error);
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/refresh`,
        { refresh_token: refreshToken },
      );
      localStorage.setItem('access_token', data.access_token);
      flushQueue(data.access_token);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    } catch (e) {
      flushQueue(null);
      forceLogout();
      return Promise.reject(e);
    } finally {
      isRefreshing = false;
    }
  },
);

function forceLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  if (window.location.pathname !== '/login') window.location.href = '/login';
}

export default api;
```

- [ ] **Step 2: Commit**

```bash
git add src/lib/api.ts
git commit -m "feat(auth): add JWT-aware axios instance with silent refresh"
```

---

## Task 4: Frontend — auth store

**Files:**
- Create: `apps/frontend/portal-externo/src/store/authStore.ts`

> Mirror `sistema-interno/src/store/authStore.ts` but add an `isEmpresaHabilitada` selector.

- [ ] **Step 1: Write the failing test**

```typescript
// src/store/__tests__/authStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import type { LoginResponse } from '@/types/auth';

const baseUser = {
  id: '1', username: 'empresa1', email: 'e@e.com', nombre_completo: 'Empresa Uno',
  rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1',
  empresa: { id: 'emp-1', nit: '900', razon_social: 'ACME', estado: 'ACTIVA' },
  created_at: '2026-01-01',
};

describe('authStore', () => {
  beforeEach(() => { useAuthStore.getState().logout(); localStorage.clear(); });

  it('stores tokens and user on login', () => {
    const resp = { access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900, user: baseUser } as LoginResponse;
    useAuthStore.getState().login(resp, baseUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(localStorage.getItem('access_token')).toBe('a');
  });

  it('clears everything on logout', () => {
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/store/__tests__/authStore.test.ts`
Expected: FAIL — module `@/store/authStore` not found.

- [ ] **Step 3: Create the store**

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@/types/auth';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => void;
  updateAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      login: (tokens, user) => {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
      },
      updateAccessToken: (token) => {
        localStorage.setItem('access_token', token);
        set({ accessToken: token });
      },
    }),
    { name: 'portal-auth-storage' },
  ),
);

/** EMPRESA logged in AND linked to a company. */
export const useIsEmpresaHabilitada = () =>
  useAuthStore((s) => s.isAuthenticated && s.user?.rol === 'EMPRESA' && !!s.user?.empresa_id);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/store/__tests__/authStore.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/store/authStore.ts src/store/__tests__/authStore.test.ts
git commit -m "feat(auth): add zustand auth store"
```

---

## Task 5: Frontend — auth service + login schema

**Files:**
- Create: `apps/frontend/portal-externo/src/services/authService.ts`
- Create: `apps/frontend/portal-externo/src/schemas/loginSchema.ts`

- [ ] **Step 1: Create the login schema (Zod v4)**

```typescript
// src/schemas/loginSchema.ts
import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'El usuario es obligatorio'),
  password: z.string().min(1, 'La contraseña es obligatoria'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
```

- [ ] **Step 2: Create the auth service**

```typescript
// src/services/authService.ts
import api from '@/lib/api';
import type { LoginRequest, LoginResponse, RefreshTokenResponse, User } from '@/types/auth';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    const { data } = await api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  async logout(refreshToken: string): Promise<void> {
    try { await api.post('/auth/logout', { refresh_token: refreshToken }); }
    catch (e) { console.error('logout error', e); }
  },
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const { data } = await api.post<RefreshTokenResponse>('/auth/refresh', { refresh_token: refreshToken });
    return data;
  },
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },
};
```

- [ ] **Step 3: Commit**

```bash
git add src/services/authService.ts src/schemas/loginSchema.ts
git commit -m "feat(auth): add auth service and login schema"
```

---

## Task 6: Frontend — LoginPage

**Files:**
- Create: `apps/frontend/portal-externo/src/pages/LoginPage.tsx`
- Test: `apps/frontend/portal-externo/src/pages/__tests__/LoginPage.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/pages/__tests__/LoginPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { authService } from '@/services/authService';

vi.mock('@/services/authService');
const renderPage = () => render(<MemoryRouter><LoginPage /></MemoryRouter>);

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows validation errors on empty submit', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/el usuario es obligatorio/i)).toBeInTheDocument();
  });

  it('blocks non-EMPRESA users with an access message', async () => {
    (authService.login as any).mockResolvedValue({
      access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900,
      user: { id: '1', username: 'aud', email: 'a@a.com', nombre_completo: 'Aud', rol: 'AUDITOR', estado: 'ACTIVO', empresa_id: null, created_at: 'x' },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText(/usuario/i), { target: { value: 'aud' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'secret12' } });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/no tiene acceso a este portal/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/__tests__/LoginPage.test.tsx`
Expected: FAIL — `LoginPage` not found.

- [ ] **Step 3: Implement LoginPage**

```tsx
// src/pages/LoginPage.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { loginSchema, type LoginFormData } from '@/schemas/loginSchema';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

export function LoginPage() {
  const navigate = useNavigate();
  const loginStore = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<LoginFormData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormData) => {
    setServerError(null);
    try {
      const resp = await authService.login(values);
      if (resp.user.rol !== 'EMPRESA' || !resp.user.empresa_id) {
        setServerError('No tiene acceso a este portal. Contacte a Servicio al Cliente.');
        return;
      }
      loginStore(resp, resp.user);
      navigate('/', { replace: true });
    } catch {
      setServerError('Usuario o contraseña inválidos.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-[#f6faf9] p-4">
      <form onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md bg-white rounded-lg shadow-sm border border-border p-8 space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Portal de Incapacidades</h1>
        <p className="text-sm text-muted-foreground">Ingrese con sus credenciales de empresa.</p>
        {serverError && (
          <div role="alert" className="rounded-md bg-red-50 text-[#D92D20] text-sm p-3">{serverError}</div>
        )}
        <div className="space-y-2">
          <Label htmlFor="username">Usuario</Label>
          <Input id="username" {...register('username')} />
          {errors.username && <p className="text-sm text-[#D92D20]">{errors.username.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Contraseña</Label>
          <Input id="password" type="password" {...register('password')} />
          {errors.password && <p className="text-sm text-[#D92D20]">{errors.password.message}</p>}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Ingresando…' : 'Ingresar'}
        </Button>
      </form>
    </div>
  );
}
```

> If `@hookform/resolvers` or `react-hook-form` are not yet installed in portal-externo, install them:
> `npm i react-hook-form @hookform/resolvers` (the radicacion wizard likely already uses them — verify first).

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/__tests__/LoginPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pages/LoginPage.tsx src/pages/__tests__/LoginPage.test.tsx
git commit -m "feat(auth): add login page with EMPRESA-only gate"
```

---

## Task 7: Frontend — ProtectedRoute + AccesoDenegado

**Files:**
- Create: `apps/frontend/portal-externo/src/components/auth/ProtectedRoute.tsx`
- Create: `apps/frontend/portal-externo/src/components/auth/AccesoDenegado.tsx`
- Test: `apps/frontend/portal-externo/src/components/auth/__tests__/ProtectedRoute.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/components/auth/__tests__/ProtectedRoute.test.tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/authStore';

const Protected = () => <div>SECRETO</div>;
const renderAt = () => render(
  <MemoryRouter initialEntries={['/']}>
    <Routes>
      <Route path="/login" element={<div>LOGIN</div>} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Protected />} />
      </Route>
    </Routes>
  </MemoryRouter>,
);

describe('ProtectedRoute', () => {
  beforeEach(() => useAuthStore.getState().logout());

  it('redirects unauthenticated users to /login', () => {
    renderAt();
    expect(screen.getByText('LOGIN')).toBeInTheDocument();
  });

  it('shows access denied for authenticated non-EMPRESA', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { id: '1', username: 'a', email: 'a', nombre_completo: 'A', rol: 'AUDITOR', estado: 'ACTIVO', empresa_id: null, created_at: 'x' } as any });
    renderAt();
    expect(screen.getByText(/no tiene acceso/i)).toBeInTheDocument();
  });

  it('renders children for EMPRESA with empresa_id', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { id: '1', username: 'e', email: 'e', nombre_completo: 'E', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1', created_at: 'x' } as any });
    renderAt();
    expect(screen.getByText('SECRETO')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/auth/__tests__/ProtectedRoute.test.tsx`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement AccesoDenegado**

```tsx
// src/components/auth/AccesoDenegado.tsx
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';

export function AccesoDenegado() {
  const logout = useAuthStore((s) => s.logout);
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-bold text-foreground">No tiene acceso a este portal</h1>
        <p className="text-sm text-muted-foreground">
          Este portal es exclusivo para usuarios de empresa vinculados a una compañía.
          Si cree que es un error, contacte a Servicio al Cliente.
        </p>
        <Button onClick={() => { logout(); window.location.href = '/login'; }}>
          Volver al inicio de sesión
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Implement ProtectedRoute**

```tsx
// src/components/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { AccesoDenegado } from './AccesoDenegado';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  if (user.rol !== 'EMPRESA' || !user.empresa_id) return <AccesoDenegado />;
  return <Outlet />;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- src/components/auth/__tests__/ProtectedRoute.test.tsx`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/components/auth/ src/components/auth/__tests__/
git commit -m "feat(auth): add ProtectedRoute and access-denied screen"
```

---

## Task 8: Frontend — Dashboard with 3 actions

**Files:**
- Create: `apps/frontend/portal-externo/src/pages/Dashboard.tsx`
- Test: `apps/frontend/portal-externo/src/pages/__tests__/Dashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/pages/__tests__/Dashboard.test.tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import { useAuthStore } from '@/store/authStore';

describe('Dashboard', () => {
  beforeEach(() => useAuthStore.setState({
    isAuthenticated: true,
    user: { id: '1', username: 'e', email: 'e', nombre_completo: 'Empresa Uno', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1', empresa: { id: 'emp-1', nit: '900', razon_social: 'ACME S.A.', estado: 'ACTIVA' }, created_at: 'x' } as any,
  }));

  it('greets the company and shows the three actions', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(screen.getByText(/ACME S\.A\./)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /radicación individual/i })).toHaveAttribute('href', '/radicar/individual');
    expect(screen.getByRole('link', { name: /radicación masiva/i })).toHaveAttribute('href', '/radicar/masiva');
    expect(screen.getByRole('link', { name: /consulta/i })).toHaveAttribute('href', '/consulta');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/__tests__/Dashboard.test.tsx`
Expected: FAIL — `Dashboard` not found.

- [ ] **Step 3: Implement Dashboard**

```tsx
// src/pages/Dashboard.tsx
import { Link } from 'react-router-dom';
import { FileText, Files, Search } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { Card } from '@/components/ui/Card';

const actions = [
  { to: '/radicar/individual', title: 'Radicación Individual', desc: 'Radique una incapacidad para un empleado.', icon: FileText },
  { to: '/radicar/masiva', title: 'Radicación Masiva', desc: 'Cargue múltiples incapacidades vía Excel.', icon: Files },
  { to: '/consulta', title: 'Consulta de Incapacidades', desc: 'Revise el estado de sus radicaciones.', icon: Search },
];

export function Dashboard() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold text-foreground">Hola, {user?.empresa?.razon_social ?? user?.nombre_completo}</h1>
        <p className="text-sm text-muted-foreground">¿Qué desea realizar hoy?</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-3">
        {actions.map(({ to, title, desc, icon: Icon }) => (
          <Link key={to} to={to} aria-label={title}
            className="group transition-all duration-200 hover:-translate-y-0.5">
            <Card className="h-full p-6 shadow-sm hover:shadow-md border-border">
              <Icon className="h-8 w-8 text-primary mb-3" />
              <h2 className="font-bold text-foreground">{title}</h2>
              <p className="text-sm text-muted-foreground mt-1">{desc}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/__tests__/Dashboard.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pages/Dashboard.tsx src/pages/__tests__/Dashboard.test.tsx
git commit -m "feat(dashboard): add 3-action EMPRESA dashboard"
```

---

## Task 9: Frontend — wire routing, retire public routes

**Files:**
- Modify: `apps/frontend/portal-externo/src/App.tsx`
- Modify: `apps/frontend/portal-externo/src/services/api.ts`

- [ ] **Step 1: Add Bearer interceptor to the existing data-services api instance**

In `src/services/api.ts`, add a request interceptor (the existing data services use this instance):

```typescript
// add inside src/services/api.ts, after `const api = axios.create({...})`
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

- [ ] **Step 2: Rewrite App.tsx routing**

```tsx
// src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { Dashboard } from '@/pages/Dashboard';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5 * 60 * 1000, retry: 1, refetchOnWindowFocus: false } },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Dashboard />} />
            {/* Phase 2 adds /radicar/individual, Phase 3 /radicar/masiva, Phase 5 /consulta */}
          </Route>
          {/* Retire old public routes */}
          <Route path="/radicar" element={<Navigate to="/login" replace />} />
          <Route path="/consultar" element={<Navigate to="/consulta" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

> Phase 2/3/5 will add their routes inside the `<ProtectedRoute />` block. For now `/radicar/*`
> and `/consulta` fall through to the catch-all redirect to `/` until their plans land.

- [ ] **Step 3: Run the full suite + build**

Run: `npm test && npm run build`
Expected: all tests PASS, build succeeds.

- [ ] **Step 4: Commit**

```bash
git add src/App.tsx src/services/api.ts
git commit -m "feat(auth): gate portal routes behind login, retire public routes"
```

---

## Self-Review Notes (coverage vs spec Phase 1 + cross-cutting)

- `/auth/me` enrichment (cross-cutting #3) → Task 1. ✅
- Own login reusing `/auth/login` (D2) → Tasks 5–6. ✅
- EMPRESA + linked-company guard (D3) → Tasks 6–7. ✅
- Dashboard 3 actions → Task 8. ✅
- Retire `/radicar` (→ login) and `/consultar` → Task 9. ✅
- `prorroga` / `communication_log` / `auditoria_resultado` migrations are NOT in this phase — they belong to Phase 2/3/4 plans (kept out here intentionally).

**Manual verification before sign-off:** `make docker-up`, log in as a seeded EMPRESA user, confirm dashboard renders with company name; log in as a non-EMPRESA user, confirm the access-denied screen; hit `/radicar` and confirm redirect to `/login`.
