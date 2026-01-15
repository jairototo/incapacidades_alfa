# Guía de Integración Frontend-Backend

**Objetivo**: Documentación técnica completa para la integración entre aplicaciones React y API FastAPI.

---

## 🔗 Configuración de Axios

### Instancia Base

```typescript
// src/services/api.ts
import axios, { AxiosError, AxiosRequestConfig } from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Para enviar cookies (si se usan)
});

export default api;
```

### Variables de Entorno

```bash
# .env.development
VITE_API_URL=http://localhost:8010/api/v1
VITE_MINIO_URL=http://localhost:9010

# .env.staging
VITE_API_URL=https://api-staging.incapacidades.com/api/v1
VITE_MINIO_URL=https://storage-staging.incapacidades.com

# .env.production
VITE_API_URL=https://api.incapacidades.com/api/v1
VITE_MINIO_URL=https://storage.incapacidades.com
```

---

## 🔐 Interceptores de Request

### Agregar Token JWT

```typescript
// src/services/api.ts
import { getAccessToken } from '@/store/authStore';

// Request interceptor - Agregar token de autenticación
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

### Logging de Requests (desarrollo)

```typescript
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }
    return config;
  }
);
```

---

## 🔄 Interceptores de Response

### Manejo de Errores

```typescript
// src/services/api.ts
import { toast } from 'sonner';

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // 1. Error de red
    if (!error.response) {
      toast.error('Error de conexión', {
        description: 'No se pudo conectar con el servidor',
      });
      return Promise.reject(error);
    }

    const status = error.response.status;
    const data = error.response.data as any;

    // 2. Error 401 - Unauthorized (refresh token)
    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        localStorage.setItem('access_token', data.access_token);
        
        // Reintentar request original
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token expirado - logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 3. Error 403 - Forbidden
    if (status === 403) {
      toast.error('Acceso denegado', {
        description: 'No tienes permisos para realizar esta acción',
      });
    }

    // 4. Error 404 - Not Found
    if (status === 404) {
      toast.error('Recurso no encontrado', {
        description: data.detail || 'El recurso solicitado no existe',
      });
    }

    // 5. Error 422 - Validation Error (Pydantic)
    if (status === 422) {
      const validationErrors = data.detail?.map((err: any) => ({
        field: err.loc[err.loc.length - 1],
        message: err.msg,
      }));

      toast.error('Errores de validación', {
        description: validationErrors?.[0]?.message || 'Datos inválidos',
      });

      return Promise.reject({
        message: 'Errores de validación',
        errors: validationErrors,
      });
    }

    // 6. Error 500 - Internal Server Error
    if (status >= 500) {
      toast.error('Error del servidor', {
        description: 'Ha ocurrido un error interno. Intenta nuevamente.',
      });
    }

    return Promise.reject(error);
  }
);
```

---

## 🔌 React Query Setup

### Configuración Global

```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
    mutations: {
      retry: 0,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Custom Hooks por Entidad

#### Incapacidades

```typescript
// src/services/incapacidadService.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './api';

// Types
interface Incapacidad {
  id: string;
  numero: string;
  tipo: 'ARL' | 'SALUD';
  estado: string;
  // ... otros campos
}

interface CreateIncapacidadInput {
  tipo: 'ARL' | 'SALUD';
  empleado_id?: string;
  afiliado_id?: string;
  // ... otros campos
}

// GET /api/v1/incapacidades (lista)
export function useIncapacidades(filters?: {
  tipo?: string;
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['incapacidades', filters],
    queryFn: async () => {
      const { data } = await api.get('/incapacidades', { params: filters });
      return data;
    },
  });
}

// GET /api/v1/incapacidades/{id}
export function useIncapacidad(id: string) {
  return useQuery({
    queryKey: ['incapacidad', id],
    queryFn: async () => {
      const { data } = await api.get(`/incapacidades/${id}`);
      return data as Incapacidad;
    },
    enabled: !!id, // Solo ejecutar si hay ID
  });
}

// POST /api/v1/incapacidades
export function useCreateIncapacidad() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CreateIncapacidadInput) => {
      const { data } = await api.post('/incapacidades', input);
      return data;
    },
    onSuccess: () => {
      // Invalidar cache de listado
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      toast.success('Incapacidad radicada exitosamente');
    },
    onError: (error) => {
      console.error('Error creando incapacidad:', error);
    },
  });
}

// PUT /api/v1/incapacidades/{id}
export function useUpdateIncapacidad(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: Partial<Incapacidad>) => {
      const { data } = await api.put(`/incapacidades/${id}`, input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      toast.success('Incapacidad actualizada');
    },
  });
}

// POST /api/v1/incapacidades/{id}/auditar
export function useAuditarIncapacidad(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      accion: 'APROBAR' | 'RECHAZAR' | 'OBSERVAR';
      observaciones?: string;
    }) => {
      const { data: response } = await api.post(
        `/incapacidades/${id}/auditar`,
        data
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      toast.success('Auditoría registrada');
    },
  });
}

// GET /api/v1/incapacidades/{id}/historial
export function useHistorialIncapacidad(id: string) {
  return useQuery({
    queryKey: ['incapacidad-historial', id],
    queryFn: async () => {
      const { data } = await api.get(`/incapacidades/${id}/historial`);
      return data;
    },
    enabled: !!id,
  });
}
```

#### Documentos (Upload/Download)

```typescript
// src/services/documentoService.ts

// POST /api/v1/documentos/upload
export function useUploadDocumento() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      file: File;
      incapacidad_id: string;
      tipo_documento: string;
    }) => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('incapacidad_id', data.incapacidad_id);
      formData.append('tipo_documento', data.tipo_documento);

      const { data: response } = await api.post('/documentos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          console.log(`Upload: ${percentCompleted}%`);
        },
      });

      return response;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['documentos', variables.incapacidad_id],
      });
      toast.success('Documento cargado correctamente');
    },
  });
}

// GET /api/v1/documentos/{id}/download
export async function downloadDocumento(id: string, filename: string) {
  try {
    const { data } = await api.get(`/documentos/${id}/download`, {
      responseType: 'blob',
    });

    // Crear URL temporal y descargar
    const url = window.URL.createObjectURL(new Blob([data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    toast.success('Documento descargado');
  } catch (error) {
    toast.error('Error al descargar documento');
    throw error;
  }
}

// GET /api/v1/documentos (por incapacidad)
export function useDocumentos(incapacidadId: string) {
  return useQuery({
    queryKey: ['documentos', incapacidadId],
    queryFn: async () => {
      const { data } = await api.get('/documentos', {
        params: { incapacidad_id: incapacidadId },
      });
      return data;
    },
    enabled: !!incapacidadId,
  });
}
```

#### Autenticación

```typescript
// src/services/authService.ts

interface LoginInput {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    rol: string;
  };
}

// POST /api/v1/auth/login
export function useLogin() {
  return useMutation({
    mutationFn: async (credentials: LoginInput) => {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const { data } = await api.post<LoginResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      return data;
    },
    onSuccess: (data) => {
      // Guardar tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      
      // Guardar info de usuario en store
      useAuthStore.getState().setUser(data.user);
      
      toast.success('Inicio de sesión exitoso');
    },
  });
}

// POST /api/v1/auth/logout
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/auth/logout');
      return data;
    },
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      useAuthStore.getState().clearUser();
      queryClient.clear(); // Limpiar todo el cache
      toast.success('Sesión cerrada');
    },
  });
}

// POST /api/v1/auth/change-password
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: {
      current_password: string;
      new_password: string;
    }) => {
      const { data: response } = await api.post('/auth/change-password', data);
      return response;
    },
    onSuccess: () => {
      toast.success('Contraseña cambiada exitosamente');
    },
  });
}
```

#### Órdenes de Pago

```typescript
// src/services/ordenPagoService.ts

// GET /api/v1/ordenes-pago
export function useOrdenesPago(filters?: {
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}) {
  return useQuery({
    queryKey: ['ordenes-pago', filters],
    queryFn: async () => {
      const { data } = await api.get('/ordenes-pago', { params: filters });
      return data;
    },
  });
}

// POST /api/v1/ordenes-pago (generar desde incapacidad)
export function useGenerarOrdenPago() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (incapacidadId: string) => {
      const { data } = await api.post('/ordenes-pago', {
        incapacidad_id: incapacidadId,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ordenes-pago'] });
      toast.success('Orden de pago generada');
    },
  });
}

// PUT /api/v1/ordenes-pago/{id}/aprobar
export function useAprobarOrdenPago(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (observaciones?: string) => {
      const { data } = await api.put(`/ordenes-pago/${id}/aprobar`, {
        observaciones,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ordenes-pago'] });
      queryClient.invalidateQueries({ queryKey: ['orden-pago', id] });
      toast.success('Orden de pago aprobada');
    },
  });
}
```

---

## 🗂️ Manejo de Tipos TypeScript

### Generar tipos desde OpenAPI

```bash
# Instalar generador
npm install -D openapi-typescript

# Generar tipos automáticamente
npx openapi-typescript http://localhost:8010/openapi.json -o src/types/api.ts
```

### Tipos Manuales

```typescript
// src/types/incapacidad.ts
export enum TipoIncapacidad {
  ARL = 'ARL',
  SALUD = 'SALUD',
}

export enum EstadoIncapacidad {
  RADICADA = 'RADICADA',
  EN_AUDITORIA = 'EN_AUDITORIA',
  OBSERVADA = 'OBSERVADA',
  APROBADA = 'APROBADA',
  RECHAZADA = 'RECHAZADA',
  EN_PAGO = 'EN_PAGO',
  PAGADA = 'PAGADA',
  ANULADA = 'ANULADA',
}

export interface Incapacidad {
  id: string;
  numero: string;
  tipo: TipoIncapacidad;
  estado: EstadoIncapacidad;
  empleado_id?: string;
  empresa_id?: string;
  afiliado_id?: string;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico: string;
  eps: string;
  ips: string;
  nombre_medico: string;
  prioridad: 'BAJA' | 'NORMAL' | 'ALTA' | 'URGENTE';
  created_at: string;
  updated_at: string;
}

export interface IncapacidadCreateInput {
  tipo: TipoIncapacidad;
  empleado_id?: string;
  empresa_id?: string;
  afiliado_id?: string;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico: string;
  eps: string;
  ips: string;
  nombre_medico: string;
  prioridad?: 'BAJA' | 'NORMAL' | 'ALTA' | 'URGENTE';
}
```

```typescript
// src/types/api.ts
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ValidationError {
  field: string;
  message: string;
}
```

---

## 🔍 Búsqueda y Autocomplete

### Búsqueda con Debounce

```typescript
// components/shared/SearchInput.tsx
import { useState } from 'react';
import { Search } from 'lucide-react';
import { useDebounce } from '@/hooks/useDebounce';
import { useQuery } from '@tanstack/react-query';

interface SearchInputProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  endpoint: string;
}

export function SearchInput({ onSearch, placeholder, endpoint }: SearchInputProps) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);

  // Query automático con debounce
  useQuery({
    queryKey: [endpoint, 'search', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery) return [];
      const { data } = await api.get(endpoint, {
        params: { search: debouncedQuery },
      });
      return data;
    },
    enabled: debouncedQuery.length >= 3,
    onSuccess: (data) => {
      onSearch(data);
    },
  });

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md"
      />
    </div>
  );
}
```

### Autocomplete CIE-10

```typescript
// hooks/useCIE10Search.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

export function useCIE10Search(query: string) {
  return useQuery({
    queryKey: ['cie10', 'search', query],
    queryFn: async () => {
      const { data } = await api.get('/catalogos/cie10', {
        params: { search: query, limit: 20 },
      });
      return data;
    },
    enabled: query.length >= 2,
    staleTime: 10 * 60 * 1000, // Cache 10 minutos
  });
}

// Uso en componente
function DiagnosticoInput() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const { data: opciones, isLoading } = useCIE10Search(debouncedQuery);

  return (
    <AutocompleteInput
      label="Diagnóstico CIE-10"
      placeholder="Buscar diagnóstico..."
      options={opciones || []}
      onSelect={(option) => {
        setValue('diagnostico_cie10', option.value);
        setValue('descripcion_diagnostico', option.label);
      }}
      onSearch={setQuery}
      isLoading={isLoading}
    />
  );
}
```

---

## 📊 Paginación Server-Side

```typescript
// hooks/useServerPagination.ts
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';

interface UseServerPaginationProps {
  endpoint: string;
  filters?: Record<string, any>;
  itemsPerPage?: number;
}

export function useServerPagination({
  endpoint,
  filters = {},
  itemsPerPage = 10,
}: UseServerPaginationProps) {
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: [endpoint, 'paginated', currentPage, itemsPerPage, filters],
    queryFn: async () => {
      const { data } = await api.get(endpoint, {
        params: {
          skip: (currentPage - 1) * itemsPerPage,
          limit: itemsPerPage,
          ...filters,
        },
      });
      return data;
    },
  });

  const totalPages = data?.total ? Math.ceil(data.total / itemsPerPage) : 0;

  return {
    data: data?.items || [],
    total: data?.total || 0,
    currentPage,
    totalPages,
    isLoading,
    error,
    setPage: setCurrentPage,
    nextPage: () => setCurrentPage((prev) => Math.min(prev + 1, totalPages)),
    prevPage: () => setCurrentPage((prev) => Math.max(prev - 1, 1)),
  };
}

// Uso
function IncapacidadesTable() {
  const [filters, setFilters] = useState({ tipo: '', estado: '' });
  const {
    data,
    total,
    currentPage,
    totalPages,
    isLoading,
    setPage,
  } = useServerPagination({
    endpoint: '/incapacidades',
    filters,
    itemsPerPage: 20,
  });

  return (
    <>
      <DataTable data={data} columns={columns} loading={isLoading} />
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={total}
        onPageChange={setPage}
      />
    </>
  );
}
```

---

## 📤 Exportación de Datos

### Exportar a Excel

```typescript
// utils/exporters.ts
import * as XLSX from 'xlsx';

export function exportToExcel(data: any[], filename: string) {
  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Datos');

  // Ajustar ancho de columnas
  const maxWidth = 50;
  const columnWidths = Object.keys(data[0] || {}).map((key) => ({
    wch: Math.min(
      maxWidth,
      Math.max(
        key.length,
        ...data.map((row) => String(row[key] || '').length)
      )
    ),
  }));
  worksheet['!cols'] = columnWidths;

  XLSX.writeFile(workbook, `${filename}.xlsx`);
}

// Uso con API
export async function exportIncapacidades(filters: any) {
  try {
    const { data } = await api.get('/incapacidades', {
      params: { ...filters, limit: 10000 }, // Sin paginación para export
    });

    const formatted = data.items.map((item: any) => ({
      Número: item.numero,
      Tipo: item.tipo,
      Estado: item.estado,
      Solicitante: item.solicitante_nombre,
      'Fecha Inicio': formatDate(item.fecha_inicio),
      'Fecha Fin': formatDate(item.fecha_fin),
      Días: item.dias_totales,
    }));

    exportToExcel(formatted, `incapacidades_${format(new Date(), 'yyyy-MM-dd')}`);
    toast.success('Exportación completada');
  } catch (error) {
    toast.error('Error al exportar');
  }
}
```

### Exportar a PDF

```typescript
// utils/exporters.ts
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export function exportToPDF(
  data: any[],
  columns: string[],
  filename: string,
  title: string
) {
  const doc = new jsPDF();

  // Título
  doc.setFontSize(16);
  doc.text(title, 14, 20);

  // Tabla
  autoTable(doc, {
    head: [columns],
    body: data.map((row) => columns.map((col) => row[col] || '-')),
    startY: 30,
    theme: 'grid',
    styles: { fontSize: 8 },
    headStyles: { fillColor: [0, 48, 135] }, // Azul corporativo
  });

  doc.save(`${filename}.pdf`);
}
```

---

## 🧪 Testing con MSW (Mock Service Worker)

### Setup

```bash
npm install -D msw
```

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // GET /api/v1/incapacidades
  http.get('/api/v1/incapacidades', () => {
    return HttpResponse.json({
      items: [
        {
          id: '1',
          numero: 'INC-SALUD-2026-001',
          tipo: 'SALUD',
          estado: 'RADICADA',
          // ...
        },
      ],
      total: 1,
    });
  }),

  // POST /api/v1/incapacidades
  http.post('/api/v1/incapacidades', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: '2',
        numero: 'INC-SALUD-2026-002',
        ...body,
      },
      { status: 201 }
    );
  }),

  // Error 422
  http.post('/api/v1/incapacidades/invalid', () => {
    return HttpResponse.json(
      {
        detail: [
          {
            loc: ['body', 'fecha_inicio'],
            msg: 'field required',
            type: 'value_error.missing',
          },
        ],
      },
      { status: 422 }
    );
  }),
];
```

```typescript
// src/mocks/browser.ts
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);
```

```typescript
// src/main.tsx
async function enableMocking() {
  if (import.meta.env.MODE !== 'development') {
    return;
  }

  const { worker } = await import('./mocks/browser');
  return worker.start();
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
});
```

---

## 📝 Checklist de Integración

### Setup Inicial
- [x] Configurar Axios con baseURL
- [x] Variables de entorno (.env)
- [x] Request interceptor (JWT)
- [x] Response interceptor (errores)
- [x] React Query setup

### Servicios
- [x] authService (login, logout, refresh)
- [x] incapacidadService (CRUD + auditar)
- [x] documentoService (upload, download)
- [x] ordenPagoService (gestión)
- [x] empresaService, empleadoService, afiliadoService

### Tipos TypeScript
- [ ] Generar desde OpenAPI
- [x] Tipos manuales de entidades
- [x] Tipos de responses (ApiResponse, PaginatedResponse)

### Features
- [x] Búsqueda con debounce
- [x] Autocomplete (CIE-10, empresas)
- [x] Paginación server-side
- [x] Exportación (Excel, PDF)
- [x] Upload de archivos
- [x] Download de archivos

### Testing
- [ ] MSW setup
- [ ] Mocks de endpoints
- [ ] Tests de services

---

## 🔗 Recursos Adicionales

- [Axios Documentation](https://axios-http.com/docs/intro)
- [React Query Documentation](https://tanstack.com/query/latest)
- [MSW Documentation](https://mswjs.io/)
- [OpenAPI TypeScript Generator](https://github.com/drwpow/openapi-typescript)
