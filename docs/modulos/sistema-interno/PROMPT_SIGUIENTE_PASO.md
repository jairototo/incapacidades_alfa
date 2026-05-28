# PROMPT PARA EL SIGUIENTE PASO - Dashboard y Módulo Pendientes

**Fecha**: 26 de enero de 2026  
**Context**: Fase 2 Sistema Interno  
**Progreso actual**: Layout ✅ | Autenticación ✅ | Consulta ✅ | **Dashboard+Pendientes ⏳**

---

## 📍 CONTEXTO ACTUAL

### ✅ Completado hasta ahora:

1. **Setup inicial del proyecto** (100%)
   - React 19.2 + TypeScript 5.3 + Vite 5
   - TailwindCSS + Shadcn/ui configurados
   - Proyecto corriendo en puerto 5174

2. **Sistema de Autenticación** (100%)
   - LoginForm con validación Zod
   - authStore con Zustand + persist
   - Axios con interceptores JWT (refresh automático)
   - ProtectedRoute component
   - Tests: 26 LoginForm + 15 LoginPage + 11 ProtectedRoute

3. **Layout Principal** (100%)
   - AppShell component
   - Sidebar con menú de navegación (8 ítems, filtrado por roles)
   - Header con dropdown de usuario
   - Footer
   - Tests: 6 AppShell + 13 Router

4. **Módulo Incapacidades - Consulta** (100%)
   - ConsultaPage con tabla de resultados
   - ConsultaFilters (búsqueda múltiple)
   - DataTable component genérico
   - Integración con API backend
   - Tests: 13 pasando/5 fallando (problema userEvent + react-hook-form)

**Total de tests**: 71 tests implementados

---

## 🎯 OBJETIVO DEL SIGUIENTE PASO

Implementar **dos módulos críticos** que completarán el flujo principal del sistema interno:

### 1. **Dashboard de Auditoría** (Página principal del sistema)
Página de inicio con métricas en tiempo real y accesos rápidos a funcionalidades clave.

### 2. **Módulo de Incapacidades Pendientes** (Bandeja de entrada de auditoría)
Listado de incapacidades que requieren acción inmediata (estados: RADICADA, EN_AUDITORIA, OBSERVADA).

---

## 📋 REQUERIMIENTOS ESPECÍFICOS

### PARTE 1: Dashboard de Auditoría

#### 1.1 Crear Types para Dashboard

**Archivo**: `src/types/dashboard.ts`

```typescript
export interface EstadisticasDashboard {
  // Contadores principales
  total_incapacidades: number;
  pendientes_revision: number;
  aprobadas_mes: number;
  rechazadas_mes: number;
  
  // Por estado
  por_estado: {
    estado: EstadoIncapacidad;
    cantidad: number;
    porcentaje: number;
  }[];
  
  // Por tipo
  por_tipo: {
    tipo: 'ARL' | 'SALUD';
    cantidad: number;
    valor_total: number;
  }[];
  
  // Métricas de tiempo
  tiempo_promedio_revision: number; // horas
  antiguedad_pendiente_mas_viejo: number; // días
  
  // Top empresas
  empresas_mas_radicaciones: {
    empresa_nit: string;
    razon_social: string;
    total_radicaciones: number;
  }[];
  
  // Tendencia mensual (últimos 6 meses)
  tendencia_mensual: {
    mes: string; // formato: "2026-01"
    radicadas: number;
    aprobadas: number;
    rechazadas: number;
  }[];
}

export interface AccionRapida {
  id: string;
  tipo: 'pendiente' | 'observada' | 'alerta';
  incapacidad_numero: string;
  empleado_nombre: string;
  empresa: string;
  dias_antiguedad: number;
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
}
```

#### 1.2 Crear Dashboard Service

**Archivo**: `src/services/dashboardService.ts`

```typescript
import api from '@/lib/api';
import type { EstadisticasDashboard, AccionRapida } from '@/types/dashboard';

export const dashboardService = {
  /**
   * Obtener estadísticas generales del dashboard
   */
  async getEstadisticas(): Promise<EstadisticasDashboard> {
    const { data } = await api.get<EstadisticasDashboard>('/dashboard/estadisticas');
    return data;
  },

  /**
   * Obtener acciones rápidas (incapacidades que requieren atención)
   */
  async getAccionesRapidas(limite: number = 5): Promise<AccionRapida[]> {
    const { data } = await api.get<AccionRapida[]>('/dashboard/acciones-rapidas', {
      params: { limite },
    });
    return data;
  },
};
```

#### 1.3 Crear Stats Card Component

**Archivo**: `src/components/dashboard/StatsCard.tsx`

**Propósito**: Tarjeta reutilizable para mostrar métricas (estilo KPI card).

**Props**:
```typescript
interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ElementType;
  trend?: {
    value: number; // porcentaje de cambio
    isPositive: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}
```

**Ejemplo de uso**:
```tsx
<StatsCard
  title="Pendientes de Revisión"
  value={87}
  description="Requieren auditoría"
  icon={Clock}
  trend={{ value: 12, isPositive: false }}
  variant="warning"
/>
```

**Diseño esperado**:
- Card con padding, border, shadow-sm
- Icono en círculo (bg-blue-100, text-blue-600)
- Título en text-sm text-gray-600
- Valor en text-2xl font-bold
- Trend con flecha (↑ verde o ↓ rojo) + porcentaje
- Descripción en text-xs text-gray-500

#### 1.4 Crear Acciones Rápidas Component

**Archivo**: `src/components/dashboard/AccionesRapidas.tsx`

**Propósito**: Listar incapacidades que requieren atención inmediata.

**Features**:
- Lista de AccionRapida[]
- Cada item muestra:
  - Número de incapacidad (badge)
  - Nombre del empleado
  - Empresa
  - Días de antigüedad (badge con color según urgencia)
  - Botón "Revisar" → navega a `/incapacidades/gestionar/:id`
- Ordenado por prioridad (ALTA → MEDIA → BAJA)
- Empty state cuando no hay acciones pendientes

#### 1.5 Crear Tendencia Chart Component

**Archivo**: `src/components/dashboard/TendenciaChart.tsx`

**Propósito**: Gráfico de líneas con tendencia de incapacidades (últimos 6 meses).

**Usar**: Recharts (ya instalado en package.json)

**Ejemplo**:
```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function TendenciaChart({ data }: { data: TendenciaMensual[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="mes" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="radicadas" stroke="#3b82f6" name="Radicadas" />
        <Line type="monotone" dataKey="aprobadas" stroke="#10b981" name="Aprobadas" />
        <Line type="monotone" dataKey="rechazadas" stroke="#ef4444" name="Rechazadas" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

#### 1.6 Crear Dashboard Page

**Archivo**: `src/pages/dashboard/DashboardPage.tsx`

**Layout esperado**:
```
┌──────────────────────────────────────────────────────┐
│ Dashboard de Auditoría                               │
│ Bienvenido, Juan Pérez (AUDITOR)                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│ [StatsCard TotalIncap] [StatsCard Pendientes]       │
│ [StatsCard Aprobadas]  [StatsCard Rechazadas]       │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Grid 2 columnas (lg:grid-cols-2):                   │
│                                                      │
│ ┌─────────────────────┐  ┌─────────────────────┐   │
│ │ Acciones Rápidas    │  │ Distribución por    │   │
│ │                     │  │ Estado (Pie Chart)  │   │
│ │ [Lista 5 items]     │  │                     │   │
│ └─────────────────────┘  └─────────────────────┘   │
│                                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ Tendencia Últimos 6 Meses (Line Chart)       │   │
│ │                                               │   │
│ └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**React Query**:
```tsx
const { data: stats, isLoading } = useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => dashboardService.getEstadisticas(),
  staleTime: 60 * 1000, // 1 minuto
  refetchInterval: 5 * 60 * 1000, // Refetch cada 5 minutos
});

const { data: acciones } = useQuery({
  queryKey: ['dashboard-acciones'],
  queryFn: () => dashboardService.getAccionesRapidas(5),
  staleTime: 30 * 1000, // 30 segundos
});
```

**Loading y Error states**:
- Loading: Mostrar skeleton loaders para cada card
- Error: Alert con mensaje de error y botón "Reintentar"

---

### PARTE 2: Módulo de Incapacidades Pendientes

#### 2.1 Crear Types para Pendientes

**Archivo**: `src/types/pendientes.ts` (o agregar a `incapacidad.ts` existente)

```typescript
export interface IncapacidadPendiente extends Incapacidad {
  dias_desde_radicacion: number;
  dias_en_estado_actual: number;
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
}

export interface FiltrosPendientes {
  tipo?: 'ARL' | 'SALUD';
  prioridad?: 'ALTA' | 'MEDIA' | 'BAJA';
  empresa_nit?: string;
  dias_antiguedad_min?: number;
}
```

#### 2.2 Actualizar Incapacidad Service

**Archivo**: `src/services/incapacidadService.ts`

**Agregar método**:
```typescript
/**
 * Obtener incapacidades pendientes de auditoría
 * Estados incluidos: RADICADA, EN_AUDITORIA, OBSERVADA
 */
async listarPendientes(params?: FiltrosPendientes): Promise<PaginatedResponse<IncapacidadPendiente>> {
  const { data } = await api.get<PaginatedResponse<IncapacidadPendiente>>('/incapacidades/pendientes', {
    params,
  });
  return data;
},
```

#### 2.3 Crear Pendientes Filters Component

**Archivo**: `src/components/incapacidades/PendientesFilters.tsx`

**Filtros específicos**:
- Tipo (ARL/SALUD)
- Prioridad (ALTA/MEDIA/BAJA)
- Empresa (select con autocomplete)
- Antigüedad mínima (input number: "Más de X días")
- Botón "Limpiar filtros"

**Más simple que ConsultaFilters** (solo 4 campos vs 8).

#### 2.4 Crear Pendientes Page

**Archivo**: `src/pages/incapacidades/PendientesPage.tsx`

**Features clave**:

1. **Título con contador**:
```tsx
<h1 className="text-2xl font-bold">
  Incapacidades Pendientes 
  <Badge variant="warning" className="ml-2">
    {data?.total || 0}
  </Badge>
</h1>
```

2. **Filtros colapsables**:
```tsx
<Collapsible>
  <CollapsibleTrigger>
    <Button variant="outline">
      <Filter className="mr-2 h-4 w-4" />
      Filtros
    </Button>
  </CollapsibleTrigger>
  <CollapsibleContent>
    <PendientesFilters onSearch={handleSearch} />
  </CollapsibleContent>
</Collapsible>
```

3. **Tabla de pendientes** (columnas):
   - Número (link a detalle)
   - Tipo (badge: ARL azul, SALUD verde)
   - Solicitante + Empresa/Afiliado
   - Fecha radicación (+ días transcurridos)
   - Estado (badge)
   - Prioridad (badge con colores: ALTA rojo, MEDIA amarillo, BAJA gris)
   - Acciones (botón "Gestionar")

4. **Ordenamiento**:
   - Por defecto: prioridad DESC, dias_desde_radicacion DESC
   - Las más antiguas y urgentes primero

5. **Auto-refresh**:
```tsx
const { data } = useQuery({
  queryKey: ['incapacidades-pendientes', params],
  queryFn: () => incapacidadService.listarPendientes(params),
  staleTime: 30 * 1000,
  refetchInterval: 2 * 60 * 1000, // Refetch cada 2 minutos
});
```

6. **Empty state**:
```tsx
{data?.total === 0 && (
  <div className="text-center py-12">
    <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
    <h3 className="mt-4 text-lg font-medium">¡No hay pendientes!</h3>
    <p className="mt-2 text-gray-500">
      Todas las incapacidades están al día.
    </p>
  </div>
)}
```

#### 2.5 Actualizar Router

**Archivo**: `src/App.tsx`

**Agregar rutas**:
```tsx
<Route element={<ProtectedRoute allowedRoles={['ADMIN', 'AUDITOR']} />}>
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/incapacidades/pendientes" element={<PendientesPage />} />
</Route>
```

---

## 🧪 TESTS ESPERADOS

### Tests de Dashboard (20+ tests)

**Archivo**: `src/pages/dashboard/__tests__/DashboardPage.test.tsx`

**Grupos de tests**:

1. **Renderizado inicial** (5 tests)
   - ✅ Debe renderizar el título "Dashboard de Auditoría"
   - ✅ Debe mostrar el nombre del usuario y rol
   - ✅ Debe renderizar 4 StatsCards (total, pendientes, aprobadas, rechazadas)
   - ✅ Debe renderizar AccionesRapidas component
   - ✅ Debe renderizar TendenciaChart component

2. **Loading state** (2 tests)
   - ✅ Debe mostrar skeletons mientras carga
   - ✅ No debe renderizar contenido hasta que carguen los datos

3. **Error state** (2 tests)
   - ✅ Debe mostrar alert de error cuando falla la API
   - ✅ Debe permitir reintentar cuando hay error

4. **Datos de estadísticas** (6 tests)
   - ✅ Debe mostrar el total de incapacidades correctamente
   - ✅ Debe mostrar el número de pendientes
   - ✅ Debe mostrar aprobadas del mes
   - ✅ Debe mostrar rechazadas del mes
   - ✅ Debe calcular tendencias correctamente (↑ verde, ↓ rojo)
   - ✅ Debe formatear valores monetarios correctamente

5. **Acciones rápidas** (3 tests)
   - ✅ Debe listar 5 acciones rápidas
   - ✅ Debe navegar al detalle al hacer clic en "Revisar"
   - ✅ Debe mostrar empty state cuando no hay acciones pendientes

6. **Refetch automático** (2 tests)
   - ✅ Debe refrescar datos cada 5 minutos
   - ✅ Debe refrescar al hacer focus en la ventana

**Archivo**: `src/components/dashboard/__tests__/StatsCard.test.tsx`

1. **Renderizado** (4 tests)
   - ✅ Debe renderizar título, valor y descripción
   - ✅ Debe renderizar el icono correctamente
   - ✅ Debe aplicar variante de color (success, warning, danger)
   - ✅ Debe mostrar trend correctamente (↑/↓ con porcentaje)

### Tests de Pendientes Page (15+ tests)

**Archivo**: `src/pages/incapacidades/__tests__/PendientesPage.test.tsx`

**Grupos de tests**:

1. **Renderizado inicial** (4 tests)
   - ✅ Debe renderizar el título con contador
   - ✅ Debe renderizar los filtros
   - ✅ Debe renderizar la tabla con columnas correctas
   - ✅ Debe mostrar loading state

2. **Filtros** (3 tests)
   - ✅ Debe filtrar por tipo (ARL/SALUD)
   - ✅ Debe filtrar por prioridad
   - ✅ Debe limpiar filtros correctamente

3. **Tabla de resultados** (4 tests)
   - ✅ Debe mostrar las pendientes en la tabla
   - ✅ Debe ordenar por prioridad y antigüedad
   - ✅ Debe mostrar badges de estado y prioridad
   - ✅ Debe mostrar días desde radicación

4. **Navegación** (2 tests)
   - ✅ Debe navegar al gestionar una incapacidad
   - ✅ Debe tener un botón "Gestionar" por cada pendiente

5. **Empty state** (1 test)
   - ✅ Debe mostrar mensaje "No hay pendientes" cuando está vacío

6. **Auto-refresh** (1 test)
   - ✅ Debe refrescar datos cada 2 minutos

---

## ✅ CRITERIOS DE ACEPTACIÓN

### Dashboard de Auditoría
- [ ] Página renderiza en ruta `/dashboard`
- [ ] 4 StatsCards visibles (Total, Pendientes, Aprobadas, Rechazadas)
- [ ] Acciones rápidas lista hasta 5 incapacidades urgentes
- [ ] Botón "Revisar" navega a página de gestión
- [ ] Gráfico de tendencia muestra últimos 6 meses
- [ ] Loading state con skeletons
- [ ] Error state con mensaje y botón reintentar
- [ ] Auto-refresh cada 5 minutos
- [ ] Solo accesible para ADMIN y AUDITOR
- [ ] Tests: 20+ tests pasando (>80% cobertura)

### Módulo Pendientes
- [ ] Página renderiza en ruta `/incapacidades/pendientes`
- [ ] Contador de pendientes visible en título
- [ ] Filtros funcionando (tipo, prioridad, empresa, antigüedad)
- [ ] Tabla ordenada por prioridad y antigüedad
- [ ] Badges de estado y prioridad con colores correctos
- [ ] Días desde radicación visible en cada fila
- [ ] Botón "Gestionar" en cada fila
- [ ] Empty state cuando no hay pendientes
- [ ] Auto-refresh cada 2 minutos
- [ ] Solo accesible para ADMIN y AUDITOR
- [ ] Tests: 15+ tests pasando (>75% cobertura)

### Integración
- [ ] Ambas rutas funcionan desde el Sidebar
- [ ] Navegación fluida entre Dashboard → Pendientes → Gestionar
- [ ] Build exitoso sin warnings
- [ ] Bundle size optimizado (<700KB)
- [ ] Tests totales del proyecto: 106+ tests (71 actuales + 35 nuevos)

---

## 🛠️ CONSIDERACIONES TÉCNICAS

### 1. **Estructura de archivos**

```
src/
├── components/
│   ├── dashboard/
│   │   ├── StatsCard.tsx                    ← CREAR
│   │   ├── AccionesRapidas.tsx              ← CREAR
│   │   ├── TendenciaChart.tsx               ← CREAR
│   │   └── __tests__/
│   │       └── StatsCard.test.tsx           ← CREAR
│   └── incapacidades/
│       ├── PendientesFilters.tsx            ← CREAR
│       └── ...existing files
├── pages/
│   ├── dashboard/
│   │   ├── DashboardPage.tsx                ← CREAR
│   │   └── __tests__/
│   │       └── DashboardPage.test.tsx       ← CREAR
│   └── incapacidades/
│       ├── PendientesPage.tsx               ← CREAR
│       └── __tests__/
│           └── PendientesPage.test.tsx      ← CREAR
├── services/
│   ├── dashboardService.ts                  ← CREAR
│   └── incapacidadService.ts                ← ACTUALIZAR (agregar método)
└── types/
    ├── dashboard.ts                         ← CREAR
    └── pendientes.ts                        ← CREAR (o agregar a incapacidad.ts)
```

### 2. **Dependencias de Recharts**

Recharts ya está instalado en `package.json`. Componentes a usar:
- `LineChart` para tendencia mensual
- `PieChart` para distribución por estado (opcional)
- `ResponsiveContainer` para hacer charts responsive

### 3. **Formateo de datos**

**Crear utilities** en `src/utils/formatters.ts`:

```typescript
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
  }).format(value);
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatRelativeDate(date: string): string {
  const now = new Date();
  const past = new Date(date);
  const diffInDays = Math.floor((now.getTime() - past.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) return 'Hoy';
  if (diffInDays === 1) return 'Ayer';
  if (diffInDays < 7) return `Hace ${diffInDays} días`;
  if (diffInDays < 30) return `Hace ${Math.floor(diffInDays / 7)} semanas`;
  return `Hace ${Math.floor(diffInDays / 30)} meses`;
}

export function getDiasDesde(fecha: string): number {
  const now = new Date();
  const past = new Date(fecha);
  return Math.floor((now.getTime() - past.getTime()) / (1000 * 60 * 60 * 24));
}
```

### 4. **Priorización de incapacidades**

**Lógica de prioridad** (implementar en el backend o frontend):

```typescript
function calcularPrioridad(incapacidad: Incapacidad): 'ALTA' | 'MEDIA' | 'BAJA' {
  const dias = getDiasDesde(incapacidad.created_at);
  
  // ALTA: Más de 7 días en RADICADA o más de 3 días en OBSERVADA
  if ((incapacidad.estado === 'RADICADA' && dias > 7) ||
      (incapacidad.estado === 'OBSERVADA' && dias > 3)) {
    return 'ALTA';
  }
  
  // MEDIA: 3-7 días en RADICADA o 1-3 días en OBSERVADA
  if ((incapacidad.estado === 'RADICADA' && dias >= 3) ||
      (incapacidad.estado === 'OBSERVADA' && dias >= 1)) {
    return 'MEDIA';
  }
  
  // BAJA: Menos de 3 días
  return 'BAJA';
}
```

### 5. **Colores de badges**

**Convención de colores**:

```typescript
// Estados
const estadoColors = {
  RADICADA: 'bg-yellow-100 text-yellow-800',
  EN_AUDITORIA: 'bg-blue-100 text-blue-800',
  OBSERVADA: 'bg-orange-100 text-orange-800',
  APROBADA: 'bg-green-100 text-green-800',
  RECHAZADA: 'bg-red-100 text-red-800',
  EN_PAGO: 'bg-purple-100 text-purple-800',
  PAGADA: 'bg-emerald-100 text-emerald-800',
};

// Prioridades
const prioridadColors = {
  ALTA: 'bg-red-100 text-red-800 border-red-300',
  MEDIA: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  BAJA: 'bg-gray-100 text-gray-800 border-gray-300',
};

// Tipos
const tipoColors = {
  ARL: 'bg-blue-100 text-blue-800',
  SALUD: 'bg-green-100 text-green-800',
};
```

### 6. **React Query - Invalidación de queries**

Cuando se gestiona una incapacidad, invalidar:
```typescript
queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
queryClient.invalidateQueries({ queryKey: ['dashboard-acciones'] });
queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
```

### 7. **Skeleton Loaders**

**Para Dashboard**:
```tsx
{isLoading && (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="p-6 bg-white rounded-lg shadow">
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-32" />
      </div>
    ))}
  </div>
)}
```

Shadcn/ui ya incluye el componente `Skeleton`:
```bash
npx shadcn-ui@latest add skeleton
```

### 8. **Permisos por rol**

Ambas páginas solo accesibles para:
- ADMIN (acceso total)
- AUDITOR (acceso total)

Usar `ProtectedRoute`:
```tsx
<Route element={<ProtectedRoute allowedRoles={['ADMIN', 'AUDITOR']} />}>
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/incapacidades/pendientes" element={<PendientesPage />} />
</Route>
```

---

## 📊 EJEMPLO DE USO/SALIDA ESPERADA

### Dashboard Page

**URL**: `http://localhost:5174/dashboard`

**Vista esperada**:

```
┌────────────────────────────────────────────────────────────┐
│ Dashboard de Auditoría                                     │
│ Bienvenido, Juan Pérez (AUDITOR)                          │
│ Última actualización: Hace 2 minutos                       │
└────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total       │ Pendientes  │ Aprobadas   │ Rechazadas  │
│ 342         │ 87          │ 234         │ 21          │
│ ↑ 12%       │ ↓ 5%        │ ↑ 8%        │ ↓ 15%       │
└─────────────┴─────────────┴─────────────┴─────────────┘

┌──────────────────────────┬──────────────────────────┐
│ Acciones Rápidas         │ Distribución por Estado  │
│                          │                          │
│ 🔴 INC-001 (12 días)     │      [Pie Chart]         │
│    Juan Pérez            │   RADICADA: 45%          │
│    Empresa ABC           │   EN_AUDITORIA: 30%      │
│    [Revisar]             │   OBSERVADA: 15%         │
│                          │   APROBADA: 10%          │
│ 🟡 INC-045 (7 días)      │                          │
│    María López           │                          │
│    Empresa XYZ           │                          │
│    [Revisar]             │                          │
│                          │                          │
│ (+ 3 más...)             │                          │
└──────────────────────────┴──────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ Tendencia Últimos 6 Meses                              │
│                                                        │
│  [Gráfico de líneas mostrando radicadas, aprobadas,   │
│   rechazadas de agosto 2025 a enero 2026]             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Pendientes Page

**URL**: `http://localhost:5174/incapacidades/pendientes`

**Vista esperada**:

```
┌────────────────────────────────────────────────────────┐
│ Incapacidades Pendientes [87]                          │
│                                                        │
│ [🔍 Filtros]                                           │
└────────────────────────────────────────────────────────┘

┌─Tabla─────────────────────────────────────────────────┐
│ Número    │ Tipo  │ Solicitante    │ Radicación │ Pri │
├───────────┼───────┼────────────────┼────────────┼─────┤
│ INC-001   │ ARL   │ Juan Pérez     │ Hace 12d   │ 🔴  │
│           │       │ Empresa ABC    │            │ALTA │
│           │       │                │            │     │
│ [Gestionar]                                           │
├───────────┼───────┼────────────────┼────────────┼─────┤
│ INC-045   │ SALUD │ María López    │ Hace 7d    │ 🟡  │
│           │       │ Afiliado       │            │MEDIA│
│           │       │                │            │     │
│ [Gestionar]                                           │
├───────────┼───────┼────────────────┼────────────┼─────┤
│ ...       │       │                │            │     │
└───────────────────────────────────────────────────────┘

Mostrando 1-20 de 87 resultados
[← Anterior]  [Siguiente →]
```

---

## 📝 ORDEN DE IMPLEMENTACIÓN SUGERIDO

### Día 1: Dashboard Foundation
1. Crear types (`dashboard.ts`)
2. Crear `dashboardService.ts`
3. Crear `StatsCard.tsx` component
4. Crear `DashboardPage.tsx` (solo StatsCards, sin gráficos)
5. Tests de `StatsCard.test.tsx`

### Día 2: Dashboard Advanced
6. Instalar Shadcn skeleton: `npx shadcn-ui@latest add skeleton`
7. Crear `AccionesRapidas.tsx` component
8. Crear `TendenciaChart.tsx` component
9. Integrar todo en `DashboardPage.tsx`
10. Tests de `DashboardPage.test.tsx`

### Día 3: Módulo Pendientes
11. Crear types (`pendientes.ts`)
12. Actualizar `incapacidadService.ts` (método `listarPendientes`)
13. Crear `PendientesFilters.tsx`
14. Crear `PendientesPage.tsx`
15. Tests de `PendientesPage.test.tsx`

### Día 4: Testing y Refinamiento
16. Completar tests faltantes
17. Incrementar cobertura a >80%
18. Corregir errores de linting
19. Optimizar performance (memoización, lazy loading)
20. Actualizar documentación

---

## 🚀 COMANDOS DE VALIDACIÓN

```bash
# Desarrollo
cd /opt/apps/incapacidades_vs/frontend/sistema-interno
npm run dev

# Tests
npm run test                    # Todos los tests
npm run test:watch             # Watch mode
npm run test -- DashboardPage   # Test específico
npm run test:coverage          # Reporte de cobertura

# Build
npm run build                   # Build de producción
npm run preview                # Preview del build

# Linting
npm run lint                    # ESLint check
npm run lint:fix               # ESLint fix automático

# Type checking
npx tsc --noEmit               # Verificar tipos
```

---

## 📤 ENTREGABLES ESPERADOS

Al finalizar este paso, deberás proporcionar:

### 1. **Resumen Ejecutivo** (2-3 líneas)
Breve descripción de lo completado.

### 2. **Archivos Creados/Modificados**
Lista completa con descripción:
```
CREADOS (13 archivos):
- src/types/dashboard.ts
- src/types/pendientes.ts
- src/services/dashboardService.ts
- src/components/dashboard/StatsCard.tsx
- src/components/dashboard/AccionesRapidas.tsx
- src/components/dashboard/TendenciaChart.tsx
- src/components/dashboard/__tests__/StatsCard.test.tsx
- src/components/incapacidades/PendientesFilters.tsx
- src/pages/dashboard/DashboardPage.tsx
- src/pages/dashboard/__tests__/DashboardPage.test.tsx
- src/pages/incapacidades/PendientesPage.tsx
- src/pages/incapacidades/__tests__/PendientesPage.test.tsx
- src/utils/formatters.ts

MODIFICADOS (2 archivos):
- src/services/incapacidadService.ts (agregar método listarPendientes)
- src/App.tsx (agregar rutas dashboard y pendientes)
```

### 3. **Tests Ejecutados**
```bash
npm run test:coverage

# Resultado esperado:
# - 106+ tests pasando (71 actuales + 35 nuevos)
# - Cobertura global: >80%
# - 0 errores de TypeScript
# - 0 warnings de linting
```

### 4. **Build Exitoso**
```bash
npm run build

# Resultado esperado:
# - dist/ generado correctamente
# - Bundle size: <700KB (optimizado)
# - 0 warnings
```

### 5. **Screenshots/Evidence**
- Dashboard renderizado con datos de prueba
- Pendientes page con tabla funcional
- Test runner mostrando todos los tests pasando

### 6. **Documento de Completación**
Crear archivo: `DASHBOARD_Y_PENDIENTES_COMPLETADO.md`

**Contenido**:
- Resumen de implementación
- Detalles de componentes creados
- Resultados de tests
- Capturas de pantalla
- Problemas encontrados y soluciones
- Métricas finales (tests, cobertura, bundle size)

### 7. **Próximos Pasos Sugeridos**
Proporcionar 2-3 opciones para continuar:
- Opción A: Módulo de Gestión de Incapacidad (detalle + acciones)
- Opción B: Optimizaciones y mejoras de UX
- Opción C: Módulo de Órdenes de Pago

---

## 🎯 CRITERIO DE ÉXITO FINAL

**Este paso se considerará completado exitosamente cuando**:

✅ Dashboard Page renderiza con 4 StatsCards + Acciones Rápidas + Gráfico  
✅ Pendientes Page renderiza con filtros + tabla + badges de prioridad  
✅ 35+ nuevos tests pasando (total: 106+ tests)  
✅ Cobertura de tests: >80% en módulos nuevos  
✅ Build exitoso sin warnings (<700KB)  
✅ Navegación fluida: Sidebar → Dashboard → Pendientes  
✅ Auto-refresh funcionando en ambas páginas  
✅ Documento DASHBOARD_Y_PENDIENTES_COMPLETADO.md creado  

---

**¿Listo para comenzar? Procede con la implementación siguiendo el orden sugerido. ¡Adelante!** 🚀
