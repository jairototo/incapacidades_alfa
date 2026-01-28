# Prompt - Dashboard de Auditoría (Sistema Interno)

**Fecha**: 28 de enero de 2026  
**Contexto**: Módulo de Gestión completado (38/38 tests, 64% cobertura)  
**Objetivo**: Implementar Dashboard de Auditoría con listado, filtros y métricas

---

## CONTEXTO ACTUAL

### Estado del Proyecto
- ✅ **Backend**: 100% completo (11 módulos, API REST, JWT, MinIO, PostgreSQL)
- ✅ **Frontend Portal Externo**: 100% (Radicación + Consulta)
- ✅ **Frontend Sistema Interno - Autenticación**: 100% (Login, JWT, refresh tokens)
- ✅ **Frontend Sistema Interno - Módulo Gestión**: 100% (38/38 tests, GestionarPage + 4 componentes)
  - GestionarPage: Página de auditoría individual
  - IncapacidadDetalle: Vista detallada con 7 cards
  - DocumentosViewer: Grid de documentos con modal preview
  - HistorialTimeline: Timeline de cambios de estado
  - GestionActions: Acciones de auditoría (Aprobar/Observar/Rechazar)

### Stack Tecnológico Confirmado
- React 19.2 + TypeScript 5.3+
- Vite 5.0+
- TailwindCSS 3.4+ + Shadcn/ui
- React Query (@tanstack/react-query v5)
- Zustand (auth store implementado)
- React Router v6
- Axios (con interceptores JWT)
- Vitest + Testing Library (objetivo: >75% cobertura)

---

## OBJETIVO

Implementar el **Dashboard de Auditoría** como página principal del sistema interno, que permita:

1. Visualizar lista paginada de incapacidades
2. Filtros avanzados (tipo, estado, fecha, empresa)
3. Búsqueda por número o documento
4. Métricas en tiempo real (cards de resumen)
5. Tabla interactiva con ordenamiento
6. Navegación a GestionarPage (ya implementada)
7. Indicadores visuales de prioridad/SLA

---

## REQUERIMIENTOS ESPECÍFICOS

### 1. Estructura de Archivos a Crear

```
src/
├── pages/
│   └── dashboard/
│       ├── DashboardPage.tsx           # Página principal
│       └── __tests__/
│           └── DashboardPage.test.tsx  # Tests (>75%)
├── components/
│   └── dashboard/
│       ├── StatsCards.tsx              # Cards de métricas (4 cards)
│       ├── IncapacidadesTable.tsx      # Tabla con TanStack Table
│       ├── FiltersBar.tsx              # Barra de filtros
│       └── __tests__/                  # Tests individuales
│           ├── StatsCards.test.tsx
│           ├── IncapacidadesTable.test.tsx
│           └── FiltersBar.test.tsx
├── services/
│   └── dashboardService.ts             # Servicios API dashboard
└── types/
    └── dashboard.ts                    # Tipos específicos
```

### 2. Componentes Requeridos

#### 2.1 DashboardPage.tsx
**Responsabilidades**:
- Layout principal con header, stats, filters, table
- Gestión de estado de filtros y paginación
- Integración con React Query para data fetching
- Navegación a GestionarPage al click en fila

**Props**: Ninguna (página raíz)

**Hooks a usar**:
- `useQuery` para cargar incapacidades
- `useState` para filtros locales
- `useNavigate` para navegación
- `useAuth` para validar permisos

#### 2.2 StatsCards.tsx
**Responsabilidades**:
- Mostrar 4 métricas principales:
  1. Total Pendientes (RADICADA + EN_AUDITORIA)
  2. Auditadas Hoy
  3. Próximas a Vencer SLA (>3 días)
  4. Rechazadas/Observadas

**Props**:
```typescript
interface StatsCardsProps {
  stats: DashboardStats;
  isLoading: boolean;
}
```

**Diseño**: Grid de 4 columnas (responsive: 1 col en mobile, 2 en tablet, 4 en desktop)

#### 2.3 FiltersBar.tsx
**Responsabilidades**:
- Select tipo incapacidad (ARL/SALUD/Todas)
- Select estado (RADICADA/EN_AUDITORIA/OBSERVADA/Todos)
- DatePicker rango de fechas
- Input búsqueda por número o documento
- Autocomplete empresa (con debounce)
- Botón "Limpiar filtros"

**Props**:
```typescript
interface FiltersBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  empresas: Empresa[];
}
```

#### 2.4 IncapacidadesTable.tsx
**Responsabilidades**:
- Tabla con TanStack Table v8
- Columnas: Número, Fecha Radicación, Tipo, Solicitante, Empresa, Días, Estado, Acciones
- Ordenamiento por columna
- Paginación server-side
- Indicadores visuales:
  - Badge de estado con colores
  - Badge de tipo (ARL/SALUD)
  - Icono de prioridad si días > 7
- Click en fila → Navegar a `/incapacidades/{id}/gestionar`

**Props**:
```typescript
interface IncapacidadesTableProps {
  data: Incapacidad[];
  isLoading: boolean;
  pagination: PaginationState;
  onPaginationChange: (pagination: PaginationState) => void;
  sorting: SortingState;
  onSortingChange: (sorting: SortingState) => void;
}
```

### 3. Servicios API (dashboardService.ts)

**Funciones requeridas**:
```typescript
// Listar incapacidades con filtros y paginación
getIncapacidades(params: GetIncapacidadesParams): Promise<PaginatedResponse<Incapacidad>>

// Obtener estadísticas del dashboard
getStats(): Promise<DashboardStats>

// Buscar empresas para autocomplete (ya existe en empresaService)
// Reutilizar: empresaService.search(query: string)
```

**Endpoints backend a consumir**:
- `GET /api/v1/incapacidades?tipo={tipo}&estado={estado}&fecha_desde={fecha}&fecha_hasta={fecha}&empresa_id={id}&search={query}&skip={skip}&limit={limit}&order_by={field}&direction={asc|desc}`
- `GET /api/v1/incapacidades/stats` (si no existe, calcular en frontend desde la lista completa)

### 4. Tipos TypeScript (dashboard.ts)

```typescript
export interface DashboardStats {
  pendientes: number;
  auditadas_hoy: number;
  proximas_vencer: number;
  rechazadas_observadas: number;
}

export interface FilterState {
  tipo: TipoIncapacidad | 'TODAS';
  estado: EstadoIncapacidad | 'TODOS';
  fecha_desde: Date | null;
  fecha_hasta: Date | null;
  empresa_id: string | null;
  search: string;
}

export interface GetIncapacidadesParams extends FilterState {
  skip: number;
  limit: number;
  order_by?: string;
  direction?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
```

### 5. Integración con Router

**Ruta a agregar en App.tsx**:
```typescript
// Ruta protegida (requiere autenticación)
<Route path="/dashboard" element={
  <ProtectedRoute roles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.APROBADOR]}>
    <DashboardLayout>
      <DashboardPage />
    </DashboardLayout>
  </ProtectedRoute>
} />
```

**Navegación desde tabla**:
```typescript
// Al hacer click en fila de tabla
navigate(`/incapacidades/${incapacidad.id}/gestionar`)
```

---

## CRITERIOS DE ACEPTACIÓN

### Funcionales
- [ ] Dashboard carga y muestra lista de incapacidades
- [ ] Stats cards muestran métricas correctas
- [ ] Filtros modifican la consulta y actualizan tabla
- [ ] Búsqueda por número retorna resultado exacto
- [ ] Búsqueda por documento retorna coincidencias
- [ ] Paginación funciona (10, 25, 50 items por página)
- [ ] Ordenamiento por columna actualiza datos
- [ ] Click en fila navega a GestionarPage
- [ ] Estados se muestran con colores distintivos:
  - RADICADA: Azul
  - EN_AUDITORIA: Amarillo
  - OBSERVADA: Naranja
  - APROBADA: Verde
  - RECHAZADA: Rojo
- [ ] Indicador de prioridad (⚠️) si días > 7
- [ ] Limpiar filtros resetea a estado inicial
- [ ] Loading states mientras carga datos
- [ ] Empty state si no hay resultados

### Técnicos
- [ ] React Query cachea datos (staleTime: 5 min)
- [ ] Filtros usan debounce de 500ms para búsqueda
- [ ] TanStack Table con virtualización si >100 items
- [ ] Responsive design (mobile-first)
- [ ] Validación de permisos por rol
- [ ] Manejo de errores con toast notifications
- [ ] URL params reflejan filtros actuales (deep linking)

### Testing
- [ ] Tests de DashboardPage (>75%)
- [ ] Tests de StatsCards (100%)
- [ ] Tests de FiltersBar (>80%)
- [ ] Tests de IncapacidadesTable (>75%)
- [ ] Coverage global del módulo >75%
- [ ] Tests de integración con React Query
- [ ] Tests de navegación

---

## CONSIDERACIONES TÉCNICAS

### React Query Patterns
- Usar `useQuery` con queryKey que incluya filtros: `['incapacidades', filters]`
- Invalidar query al volver de GestionarPage (para refrescar estado)
- Prefetch siguiente página al llegar al 80% del scroll

### Performance
- Memoizar columnas de TanStack Table con `useMemo`
- Debounce en búsqueda y autocomplete (500ms)
- Virtualización si lista > 100 items
- Lazy loading de componentes pesados

### UX Considerations
- Skeleton loaders durante carga inicial
- Mantener filtros al volver de GestionarPage (persist en URL)
- Toast de éxito/error al aplicar filtros
- Highlight de fila al hover
- Cursor pointer en filas clickeables

### Accesibilidad
- Tabla con roles ARIA apropiados
- Labels en filtros para screen readers
- Navegación por teclado en tabla
- Focus visible en elementos interactivos

---

## TESTS ESPERADOS

### DashboardPage.test.tsx (~12 tests)
1. Renderiza correctamente con datos mock
2. Muestra loading state mientras carga
3. Muestra error state si falla la carga
4. Aplica filtro de tipo y actualiza tabla
5. Aplica filtro de estado y actualiza tabla
6. Búsqueda por número encuentra incapacidad
7. Paginación cambia de página correctamente
8. Ordenamiento por columna funciona
9. Click en fila navega a GestionarPage
10. Limpiar filtros resetea estado
11. Mantiene filtros en URL params
12. Valida permisos por rol

### StatsCards.test.tsx (~6 tests)
1. Renderiza 4 cards con datos correctos
2. Muestra skeleton durante loading
3. Formatea números correctamente (1,234)
4. Usa iconos apropiados por métrica
5. Usa colores distintivos por card
6. Responsive: 1/2/4 columnas según viewport

### FiltersBar.test.tsx (~10 tests)
1. Renderiza todos los controles de filtro
2. Select tipo cambia valor correctamente
3. Select estado cambia valor correctamente
4. DatePicker actualiza rango de fechas
5. Input búsqueda dispara callback con debounce
6. Autocomplete empresa carga opciones
7. Limpiar filtros resetea todos los valores
8. Valida formato de fecha
9. Previene fechas futuras
10. Callback onFiltersChange recibe objeto correcto

### IncapacidadesTable.test.tsx (~12 tests)
1. Renderiza tabla con datos mock
2. Muestra todas las columnas esperadas
3. Badge de estado usa color correcto
4. Badge de tipo muestra ARL/SALUD
5. Muestra icono prioridad si días > 7
6. Click en fila navega a GestionarPage
7. Paginación muestra controles correctos
8. Cambiar página llama callback
9. Ordenamiento por columna funciona
10. Muestra empty state sin resultados
11. Formatea fechas correctamente (DD/MM/YYYY)
12. Tooltip en hover muestra info adicional

---

## SALIDA ESPERADA

Al finalizar este módulo, el usuario podrá:

1. Acceder a `/dashboard` después de autenticarse
2. Ver métricas en tiempo real de incapacidades pendientes
3. Filtrar incapacidades por tipo, estado, fecha, empresa
4. Buscar por número de incapacidad o documento
5. Ordenar por cualquier columna de la tabla
6. Navegar entre páginas de resultados
7. Hacer click en una incapacidad para ir a GestionarPage
8. Visualizar estados con códigos de color intuitivos
9. Identificar incapacidades prioritarias (>7 días)

**Entregables**:
- ✅ 4 archivos de componentes (.tsx)
- ✅ 1 archivo de servicio (dashboardService.ts)
- ✅ 1 archivo de tipos (dashboard.ts)
- ✅ 4 archivos de tests (.test.tsx)
- ✅ Integración en router (App.tsx)
- ✅ >75% cobertura de tests
- ✅ Build sin errores ni warnings

**Tiempo estimado**: 6-8 horas de desarrollo + 2-3 horas de testing

---

## REFERENCIAS

### Documentación del Proyecto
- `.github/copilot-instructions.md` - Estándares y convenciones
- `docs/01_ARQUITECTURA.md` - Arquitectura frontend (línea 150+)
- `docs/08_FRONTEND_FASE2_SISTEMA_INTERNO.md` - RF-011 Dashboard de Auditoría
- `docs/04_API_ENDPOINTS.md` - Endpoints disponibles

### Componentes Existentes a Reutilizar
- `src/components/incapacidades/GestionarPage.tsx` - Página de destino
- `src/components/ui/` - Shadcn/ui components (Button, Card, Badge, Select, Input)
- `src/services/incapacidadService.ts` - Servicio base de incapacidades
- `src/store/authStore.ts` - Store de autenticación
- `src/hooks/useAuth.ts` - Hook de autenticación

### Bibliotecas Clave
- TanStack Table v8: https://tanstack.com/table/latest
- React Query v5: https://tanstack.com/query/latest
- Shadcn/ui: https://ui.shadcn.com/docs/components

---

**NOTA IMPORTANTE**: Este módulo NO requiere modificar el backend (todos los endpoints ya existen). Enfocarse exclusivamente en frontend.
