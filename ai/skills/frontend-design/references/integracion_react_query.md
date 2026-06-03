# Integración React Query + Zustand + Axios

Contexto completo: [`docs/arquitectura/10_INTEGRACION_BACKEND.md`](../../../../docs/arquitectura/10_INTEGRACION_BACKEND.md)

---

## Axios — Instancia compartida

**Archivo**: `src/lib/api.ts`

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});
```

La instancia tiene **dos interceptors preconfigurados**:

### Request interceptor — JWT injection
Lee `access_token` de `localStorage` y agrega `Authorization: Bearer <token>` a cada petición.
No es necesario configurarlo en cada servicio — es automático.

### Response interceptor — Silent refresh
Al recibir `401`:
1. Lee `refreshToken` de `useAuthStore.getState()`
2. Llama `POST /auth/refresh` con axios raw (no la instancia, evita loop)
3. Actualiza token en Zustand + localStorage con `updateAccessToken()`
4. Reintenta la petición original automáticamente
5. Si el refresh falla → `logout()` + redirect a `/login`

**Regla**: nunca crear una segunda instancia de axios. Importar siempre `api` de `@/lib/api`.

---

## Servicios

**Patrón**: plain objects con async methods que llaman `api.get/post/put/patch`.

```typescript
// src/services/incapacidadService.ts
export const incapacidadService = {
  async list(params: FiltrosIncapacidad) {
    // Limpiar params antes de enviar — regla crítica
    const filtros = Object.fromEntries(
      Object.entries(params).filter(
        ([, v]) => v !== undefined && v !== null && v !== '' && !Number.isNaN(v)
      )
    );
    const { data } = await api.get<PaginatedResponse<Incapacidad>>('/incapacidades/', { params: filtros });
    return data;
  },

  async getById(id: number) {
    const { data } = await api.get<Incapacidad>(`/incapacidades/${id}`);
    return data;
  },

  async auditar(id: number, payload: AuditoriaPayload) {
    const { data } = await api.post(`/incapacidades/${id}/auditar`, payload);
    return data;
  },
};
```

**Servicios disponibles**:

| Servicio | Endpoints cubiertos |
|---|---|
| `authService` | login (form-urlencoded), logout, logoutAll, refresh, me, changePassword |
| `incapacidadService` | list, getById, listarPendientes, radicar, auditar, getDatosAprobados, aprobar, rechazar, enviarPago, marcarPagada, getHistorial, getDocumentos, descargarDocumento, cambiarEstado |
| `dashboardService` | getIncapacidades, getStats (con fallback cliente), getExtendedStats |
| `empresaService` | list, getById, search |

**Nota**: `authService.login()` usa `application/x-www-form-urlencoded` (requerido por FastAPI OAuth2).
Todos los demás usan `application/json`.

---

## React Query — Patrones establecidos

### Configuración global de queries

```typescript
// Convención del proyecto:
staleTime: 5 * 60 * 1000   // 5 minutos — aplicar a todos los useQuery
gcTime: 10 * 60 * 1000     // 10 minutos — solo cuando se configura explícitamente
refetchOnWindowFocus: false  // deshabilitado globalmente
```

### Query keys — convención de nombres

```typescript
// Patrón: [nombre-recurso, params-objeto]
queryKey: ['incapacidades', { estado, empresa, offset, limit }]
queryKey: ['dashboard-stats']
queryKey: ['dashboard-extended-stats', params]
queryKey: ['incapacidad-detalle', id]
queryKey: ['incapacidad-historial', id]
queryKey: ['incapacidad-documentos', id]
```

La query se re-ejecuta automáticamente cuando cambia cualquier valor en el array de key.

### Queries inline en páginas (patrón del proyecto)

```typescript
// Las queries van dentro del componente de página, NO en hooks separados
// excepción: useExtendedStats (hook dedicado para el dashboard)
const { data, isLoading, isError } = useQuery({
  queryKey: ['incapacidades-pendientes', filtros],
  queryFn: () => incapacidadService.listarPendientes(filtros),
  staleTime: 5 * 60 * 1000,
});
```

### Mutations — acciones de negocio

```typescript
const { mutate: aprobar, isPending } = useMutation({
  mutationFn: (payload: AprobarPayload) => incapacidadService.aprobar(id, payload),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['incapacidad-detalle', id] });
    queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
    toast({ title: 'Incapacidad aprobada', variant: 'default' });
  },
  onError: () => {
    toast({ title: 'Error al aprobar', variant: 'destructive' });
  },
});
```

### Hook disponible: `useExtendedStats`

```typescript
import { useExtendedStats } from '@/hooks/useExtendedStats';

// Retorna data para todos los gráficos del dashboard
const { data, isLoading } = useExtendedStats({ empresa_id: empresaId });
// data incluye: top_empresas, top_diagnosticos, top_empleados,
//               distribucion_estados, distribucion_tipos, tendencia_mensual
```

---

## Zustand — Auth store

**Archivo**: `src/store/authStore.ts`

```typescript
import { useAuthStore } from '@/store/authStore';

// En componentes React:
const { user, isAuthenticated, logout } = useAuthStore();

// RBAC — verificar rol:
import { useHasRole, useCanPerform } from '@/store/authStore';
const esAuditor = useHasRole('AUDITOR');              // boolean
const esAdminOAuditor = useHasRole(['ADMIN', 'AUDITOR']);
const puedeAprobar = useCanPerform('aprobar');        // boolean

// Fuera de React (ej: en interceptor de Axios):
const { refreshToken, updateAccessToken, logout } = useAuthStore.getState();
```

**Roles disponibles**: `ADMIN | AUDITOR | APROBADOR | EMPRESA | EMPLEADO | READONLY`
(`ADMIN` tiene permiso `'*'` — puede hacer todo)

**Mapa de acciones RBAC** (definido en el store):
| Acción | Roles autorizados |
|---|---|
| `auditar` | ADMIN, AUDITOR |
| `aprobar` | ADMIN, APROBADOR |
| `rechazar` | ADMIN, APROBADOR |
| `pagar` | ADMIN, APROBADOR |
| `gestionar_usuarios` | ADMIN |

---

## Descargar documentos (blob)

```typescript
// El servicio ya tiene responseType: 'blob' configurado
const blob = await incapacidadService.descargarDocumento(docId);
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = nombreArchivo;
a.click();
URL.revokeObjectURL(url);
```

---

## Errores frecuentes

| Error | Causa | Fix |
|---|---|---|
| NaN en query params | `valueAsNumber: true` con campo vacío | `isNaN(val) ? undefined : val` |
| SelectItem `value=""` crash | Shadcn/ui no acepta string vacío | Usar `value="ALL"`, filtrar en queryFn |
| CORS 403 | Puerto 5174 vs 8010 | El proxy Vite `/api` resuelve esto — no cambiar baseURL a localhost |
| Loop infinito de refresh | Axios interceptor llama a sí mismo | Usar axios raw (`axios.post(...)`) en el refresh, no la instancia `api` |
