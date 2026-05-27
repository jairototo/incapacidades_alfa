# PROMPT PARA SIGUIENTE PASO: Testing de Componentes de Gráficos del Dashboard

## 📋 Contexto

Acabamos de completar la implementación de **6 componentes de visualización de datos** para el Dashboard de Auditoría usando **Recharts**. Los componentes están funcionando correctamente y compilando sin errores de TypeScript, pero **no tienen tests unitarios** que validen su comportamiento.

### Estado Actual
✅ **Completado**:
- 6 componentes de gráficos (TopEmpresasChart, TopDiagnosticosChart, TopEmpleadosTable, DistribucionEstadosPieChart, DistribucionTiposDonut, TendenciaMensualLineChart)
- 1 hook customizado (useExtendedStats)
- Integración con DashboardPage
- Types TypeScript completos
- 0 errores de compilación en código de producción

❌ **Pendiente**:
- Tests unitarios para componentes de gráficos (0% cobertura)
- Tests para hook useExtendedStats
- Tests de integración en DashboardPage con gráficos

---

## 🎯 Objetivo

Implementar tests unitarios completos para los **6 componentes de gráficos** y el **hook useExtendedStats** utilizando **Vitest + React Testing Library**, logrando una cobertura mínima del **80%** en los nuevos componentes.

---

## 📝 Requerimientos Específicos

### 1. Tests para TopEmpresasChart.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/TopEmpresasChart.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar el gráfico con datos válidos
- ✅ Debe mostrar el título "Top Empresas por Incapacidades"
- ✅ Debe renderizar barras para cada empresa (verificar cantidad de `<Bar>`)
- ✅ Debe mostrar mensaje "No hay datos disponibles" cuando data está vacío
- ✅ Debe mostrar mensaje "No hay datos disponibles" cuando data es null/undefined
- ✅ Debe formatear valores numéricos en tooltips correctamente
- ✅ Debe renderizar ResponsiveContainer con width="100%" y height={300}

**Mock data**:
```typescript
const mockTopEmpresas: TopEmpresaStats[] = [
  {
    empresa_id: '1',
    razon_social: 'Empresa A S.A.',
    nit: '900123456',
    total_incapacidades: 45,
    valor_total: 15000000,
  },
  {
    empresa_id: '2',
    razon_social: 'Empresa B Ltda',
    nit: '800654321',
    total_incapacidades: 32,
    valor_total: 9800000,
  },
];
```

---

### 2. Tests para TopDiagnosticosChart.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/TopDiagnosticosChart.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar el gráfico horizontal con datos válidos
- ✅ Debe mostrar el título "Top Diagnósticos (CIE-10)"
- ✅ Debe renderizar barras horizontales (`layout="vertical"`)
- ✅ Debe mostrar códigos CIE-10 en el eje Y
- ✅ Debe mostrar empty state con array vacío
- ✅ Debe aplicar colores diferentes a cada barra (máximo 5 colores rotativos)
- ✅ Tooltip debe mostrar descripción completa del diagnóstico

**Mock data**:
```typescript
const mockTopDiagnosticos: TopCIE10Stats[] = [
  {
    codigo_cie10: 'M54.5',
    descripcion: 'Lumbago no especificado',
    total_incapacidades: 28,
    porcentaje: 35.5,
  },
  {
    codigo_cie10: 'J06.9',
    descripcion: 'Infección aguda de las vías respiratorias superiores',
    total_incapacidades: 22,
    porcentaje: 27.8,
  },
];
```

---

### 3. Tests para TopEmpleadosTable.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/TopEmpleadosTable.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar tabla con datos válidos
- ✅ Debe mostrar el título "Top Empleados con Más Incapacidades"
- ✅ Debe mostrar 6 columnas (Ranking, Documento, Nombre, Incapacidades, Días, Empresa)
- ✅ Debe renderizar badge primario para top 3
- ✅ Debe renderizar badge secundario para posiciones 4+
- ✅ Debe mostrar nombre completo concatenado (nombres + apellidos)
- ✅ Debe formatear documento en font-mono
- ✅ Debe mostrar badge outline para días totales
- ✅ Debe mostrar empty state con array vacío

**Mock data**:
```typescript
const mockTopEmpleados: TopEmpleadoStats[] = [
  {
    empleado_id: '1',
    nombres: 'Juan Carlos',
    apellidos: 'Pérez González',
    numero_documento: '1234567890',
    empresa_razon_social: 'Empresa A S.A.',
    total_dias: 120,
    total_incapacidades: 8,
  },
  {
    empleado_id: '2',
    nombres: 'María Fernanda',
    apellidos: 'Rodríguez López',
    numero_documento: '9876543210',
    empresa_razon_social: 'Empresa B Ltda',
    total_dias: 95,
    total_incapacidades: 6,
  },
];
```

---

### 4. Tests para DistribucionEstadosPieChart.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/DistribucionEstadosPieChart.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar pie chart con datos válidos
- ✅ Debe mostrar el título "Distribución por Estados"
- ✅ Debe renderizar componente `<Pie>` de Recharts
- ✅ Debe aplicar color correcto a cada estado (ESTADO_COLORS)
- ✅ Debe mostrar labels con formato "ESTADO: XX%"
- ✅ Debe calcular cantidad total correctamente
- ✅ Debe usar porcentaje del backend (no calcular)
- ✅ Debe mostrar empty state con array vacío

**Mock data**:
```typescript
const mockDistribucionEstados: DistribucionEstados[] = [
  { estado: EstadoIncapacidad.RADICADA, cantidad: 45, porcentaje: 30.0 },
  { estado: EstadoIncapacidad.EN_AUDITORIA, cantidad: 30, porcentaje: 20.0 },
  { estado: EstadoIncapacidad.APROBADA, cantidad: 50, porcentaje: 33.3 },
  { estado: EstadoIncapacidad.RECHAZADA, cantidad: 25, porcentaje: 16.7 },
];
```

---

### 5. Tests para DistribucionTiposDonut.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/DistribucionTiposDonut.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar donut chart con datos válidos
- ✅ Debe mostrar el título "Distribución por Tipo (ARL vs SALUD)"
- ✅ Debe renderizar `<Pie>` con innerRadius y outerRadius (efecto dona)
- ✅ Debe calcular porcentaje dinámicamente
- ✅ Debe aplicar colores específicos (azul para ARL, verde para SALUD)
- ✅ Legend debe mostrar promedio de días
- ✅ Debe mostrar empty state con array vacío

**Mock data**:
```typescript
const mockDistribucionTipos: DistribucionTipos[] = [
  {
    tipo: TipoIncapacidad.ARL,
    cantidad: 120,
    valor_total: 50000000,
    promedio_dias: 15.5,
  },
  {
    tipo: TipoIncapacidad.SALUD,
    cantidad: 80,
    valor_total: 25000000,
    promedio_dias: 8.2,
  },
];
```

---

### 6. Tests para TendenciaMensualLineChart.tsx

**Archivo**: `src/components/dashboard/charts/__tests__/TendenciaMensualLineChart.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar line chart con datos válidos
- ✅ Debe mostrar el título "Tendencia Mensual de Incapacidades"
- ✅ Debe renderizar 3 líneas (radicadas, aprobadas, rechazadas)
- ✅ Debe formatear mes correctamente (Ene 2026, Feb 2026, etc.)
- ✅ Debe parsear el campo `mes` desde "2026-01"
- ✅ Debe aplicar colores correctos (morado, verde, rojo)
- ✅ Debe renderizar dots visibles en cada punto
- ✅ Debe mostrar empty state con array vacío
- ✅ Debe ocupar ancho completo (className="col-span-full")

**Mock data**:
```typescript
const mockTendenciaMensual: TendenciaMensual[] = [
  { mes: '2025-09', radicadas: 45, aprobadas: 30, rechazadas: 8, valor_total_aprobado: 12000000 },
  { mes: '2025-10', radicadas: 52, aprobadas: 38, rechazadas: 10, valor_total_aprobado: 15000000 },
  { mes: '2025-11', radicadas: 48, aprobadas: 35, rechazadas: 9, valor_total_aprobado: 14000000 },
  { mes: '2025-12', radicadas: 60, aprobadas: 45, rechazadas: 12, valor_total_aprobado: 18000000 },
  { mes: '2026-01', radicadas: 55, aprobadas: 40, rechazadas: 11, valor_total_aprobado: 16000000 },
];
```

---

### 7. Tests para useExtendedStats Hook

**Archivo**: `src/hooks/__tests__/useExtendedStats.test.ts`

**Casos de prueba**:
- ✅ Debe llamar al servicio dashboardService.getExtendedStats
- ✅ Debe usar query key `['dashboard-extended-stats', params]`
- ✅ Debe tener staleTime de 5 minutos (300000ms)
- ✅ Debe tener gcTime de 10 minutos (600000ms)
- ✅ Debe deshabilitar refetchOnWindowFocus
- ✅ Debe retornar datos correctamente cuando la API responde
- ✅ Debe manejar errores correctamente
- ✅ Debe actualizar query key cuando params cambian
- ✅ Debe funcionar sin params (opcional)

**Setup necesario**:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';

// Mock del servicio
vi.mock('@/services/dashboardService', () => ({
  dashboardService: {
    getExtendedStats: vi.fn(),
  },
}));
```

---

### 8. Tests de Integración en DashboardPage.tsx

**Archivo**: `src/pages/dashboard/__tests__/DashboardPage-Charts.test.tsx`

**Casos de prueba**:
- ✅ Debe renderizar sección "Análisis y Tendencias"
- ✅ Debe mostrar skeletons mientras carga (isLoadingExtended = true)
- ✅ Debe renderizar los 6 componentes de gráficos cuando hay datos
- ✅ Debe mostrar alert de error cuando extendedError existe
- ✅ Debe aplicar filtros al hook useExtendedStats
- ✅ Debe pasar top_limit de 10 por defecto
- ✅ Debe convertir fecha_desde y fecha_hasta a undefined si son null
- ✅ Debe convertir tipo a undefined si es 'TODAS'
- ✅ Grid debe tener clase "grid grid-cols-1 lg:grid-cols-2 gap-6"
- ✅ TendenciaMensualLineChart debe tener clase "col-span-full"

**Mock estrategia**:
```typescript
// Mock de useExtendedStats
vi.mock('@/hooks/useExtendedStats', () => ({
  useExtendedStats: vi.fn(),
}));

// Mock de componentes de gráficos (para aislar pruebas)
vi.mock('@/components/dashboard/charts', () => ({
  TopEmpresasChart: () => <div data-testid="top-empresas-chart">Mock Chart</div>,
  TopDiagnosticosChart: () => <div data-testid="top-diagnosticos-chart">Mock Chart</div>,
  // ... resto de mocks
}));
```

---

## 🔨 Consideraciones Técnicas

### Setup de Testing con Recharts

**Problema conocido**: Recharts usa `ResizeObserver` que no está disponible en JSDOM.

**Solución**: Mock global de ResizeObserver en setupTests.ts

```typescript
// src/setupTests.ts
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
```

### Mock de Recharts (Opcional)

Si los tests son lentos o inestables, mockear Recharts:

```typescript
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  Cell: () => <div data-testid="cell" />,
  // ... resto de componentes
}));
```

### Testing Library Queries

**Usar estrategia de queries**:
1. `getByRole` (preferido para accesibilidad)
2. `getByText` (para títulos y textos visibles)
3. `getByTestId` (último recurso)

**Ejemplo**:
```typescript
// ✅ Preferido
expect(screen.getByRole('heading', { name: /Top Empresas/i })).toBeInTheDocument();

// ✅ Aceptable
expect(screen.getByText(/No hay datos disponibles/i)).toBeInTheDocument();

// ⚠️ Último recurso
expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
```

### Assertions para Recharts

**Verificar que componentes de Recharts se renderizan**:
```typescript
// Verificar que ResponsiveContainer existe
const container = screen.getByText((content, element) => 
  element?.tagName.toLowerCase() === 'div' && 
  element?.className.includes('recharts-responsive-container')
);

// O usar data-testid en ResponsiveContainer
<ResponsiveContainer data-testid="chart-container" width="100%" height={300}>
```

---

## ✅ Criterios de Aceptación

### Cobertura de Tests
- [ ] **TopEmpresasChart**: ≥80% cobertura (7 tests mínimo)
- [ ] **TopDiagnosticosChart**: ≥80% cobertura (7 tests mínimo)
- [ ] **TopEmpleadosTable**: ≥80% cobertura (9 tests mínimo)
- [ ] **DistribucionEstadosPieChart**: ≥80% cobertura (8 tests mínimo)
- [ ] **DistribucionTiposDonut**: ≥80% cobertura (7 tests mínimo)
- [ ] **TendenciaMensualLineChart**: ≥80% cobertura (9 tests mínimo)
- [ ] **useExtendedStats**: ≥90% cobertura (9 tests mínimo)
- [ ] **DashboardPage integración**: ≥70% cobertura (10 tests mínimo)

### Calidad de Tests
- [ ] Todos los tests pasan sin errores ni warnings
- [ ] No hay tests marcados como `.skip` o `.todo` sin justificación
- [ ] Cada test tiene descripción clara (debe/should pattern)
- [ ] Se usan mock data realistas y consistentes
- [ ] Se valida tanto happy path como edge cases
- [ ] Se valida empty states explícitamente
- [ ] Se valida error states cuando aplique

### Ejecución
- [ ] `npm run test` ejecuta todos los tests sin errores
- [ ] `npm run test:coverage` muestra >80% en componentes nuevos
- [ ] Tests se ejecutan en <10 segundos (total)
- [ ] No hay memory leaks ni timeouts

---

## 📦 Estructura de Archivos Esperada

```
src/
├── components/
│   └── dashboard/
│       └── charts/
│           ├── __tests__/
│           │   ├── TopEmpresasChart.test.tsx           ✅ CREAR
│           │   ├── TopDiagnosticosChart.test.tsx       ✅ CREAR
│           │   ├── TopEmpleadosTable.test.tsx          ✅ CREAR
│           │   ├── DistribucionEstadosPieChart.test.tsx ✅ CREAR
│           │   ├── DistribucionTiposDonut.test.tsx     ✅ CREAR
│           │   └── TendenciaMensualLineChart.test.tsx  ✅ CREAR
│           ├── TopEmpresasChart.tsx                    (existente)
│           ├── TopDiagnosticosChart.tsx                (existente)
│           ├── TopEmpleadosTable.tsx                   (existente)
│           ├── DistribucionEstadosPieChart.tsx         (existente)
│           ├── DistribucionTiposDonut.tsx              (existente)
│           ├── TendenciaMensualLineChart.tsx           (existente)
│           └── index.ts                                (existente)
├── hooks/
│   ├── __tests__/
│   │   └── useExtendedStats.test.ts                    ✅ CREAR
│   └── useExtendedStats.ts                             (existente)
├── pages/
│   └── dashboard/
│       ├── __tests__/
│       │   └── DashboardPage-Charts.test.tsx           ✅ CREAR
│       └── DashboardPage.tsx                           (existente)
└── setupTests.ts                                        ⚠️ MODIFICAR (agregar ResizeObserver)
```

---

## 🚀 Ejemplo de Salida Esperada

### Reporte de Tests
```bash
$ npm run test

 ✓ src/components/dashboard/charts/__tests__/TopEmpresasChart.test.tsx (7 tests)
 ✓ src/components/dashboard/charts/__tests__/TopDiagnosticosChart.test.tsx (7 tests)
 ✓ src/components/dashboard/charts/__tests__/TopEmpleadosTable.test.tsx (9 tests)
 ✓ src/components/dashboard/charts/__tests__/DistribucionEstadosPieChart.test.tsx (8 tests)
 ✓ src/components/dashboard/charts/__tests__/DistribucionTiposDonut.test.tsx (7 tests)
 ✓ src/components/dashboard/charts/__tests__/TendenciaMensualLineChart.test.tsx (9 tests)
 ✓ src/hooks/__tests__/useExtendedStats.test.ts (9 tests)
 ✓ src/pages/dashboard/__tests__/DashboardPage-Charts.test.tsx (10 tests)

 Test Files  8 passed (8)
      Tests  66 passed (66)
   Duration  8.42s
```

### Reporte de Cobertura
```bash
$ npm run test:coverage

File                                        | % Stmts | % Branch | % Funcs | % Lines
--------------------------------------------|---------|----------|---------|--------
components/dashboard/charts/
  TopEmpresasChart.tsx                      |   95.45 |    91.67 |     100 |   94.74
  TopDiagnosticosChart.tsx                  |   93.10 |    87.50 |     100 |   92.86
  TopEmpleadosTable.tsx                     |   96.77 |    93.75 |     100 |   96.55
  DistribucionEstadosPieChart.tsx           |   94.44 |    89.29 |     100 |   93.94
  DistribucionTiposDonut.tsx                |   92.86 |    85.71 |     100 |   92.31
  TendenciaMensualLineChart.tsx             |   95.24 |    90.91 |     100 |   94.87
hooks/
  useExtendedStats.ts                       |   100.00 |   100.00 |     100 |  100.00
pages/dashboard/
  DashboardPage.tsx                         |   78.26 |    72.73 |   71.43 |   77.78
--------------------------------------------|---------|----------|---------|--------
All files                                   |   93.89 |    88.95 |   96.43 |   93.26
```

---

## 📚 Referencias

### Documentación
- [Vitest Docs](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Recharts API](https://recharts.org/en-US/api)

### Archivos de Referencia
- `src/components/incapacidades/__tests__/` - Ejemplos de tests existentes
- `src/setupTests.ts` - Configuración global de tests
- `vitest.config.ts` - Configuración de Vitest

---

## 🎯 Entregables

Al finalizar, debes proporcionar:

1. **8 archivos de tests nuevos** con total de ~66 tests
2. **setupTests.ts modificado** con mock de ResizeObserver
3. **Reporte de ejecución** (`npm run test`)
4. **Reporte de cobertura** (`npm run test:coverage`)
5. **Documento resumen** (DASHBOARD_TESTING_COMPLETADO.md) con:
   - Tests implementados
   - Cobertura lograda
   - Issues encontrados (si los hay)
   - Ejemplos de tests más significativos
   - Próximos pasos sugeridos

---

**Este prompt está diseñado para ser ejecutado por un agente de desarrollo autónomo o un desarrollador humano. Incluye todos los detalles necesarios para completar la tarea sin ambigüedades.**

**Tiempo estimado**: 4-6 horas  
**Dificultad**: Media  
**Prioridad**: Alta (afecta calidad y mantenibilidad del código)
