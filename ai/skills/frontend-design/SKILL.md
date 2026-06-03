---
name: frontend-design
description: >
  Skill para construir páginas y componentes en sistema-interno (React 19 + Tailwind v3).
  Úsalo siempre que crees o edites vistas en apps/frontend/sistema-interno/.
  Cubre el sistema de diseño Alfa, la librería de 14 componentes UI, los patrones
  de composición de páginas y la integración con React Query, Zustand y Axios.
---

# Frontend Design — Sistema Interno

## Contexto del proyecto

Sistema interno para auditores, aprobadores y admins del flujo de incapacidades.
Stack: **React 19 + Vite + TypeScript + Tailwind v3 + Shadcn/ui + React Query + Zustand**.

> **Importante**: Portal externo usa Tailwind **v4** y Zod **v4**. Sistema interno usa Tailwind **v3** y Zod **v3**.
> No copies estilos ni schemas entre frontends sin verificar compatibilidad.

Fuente de verdad visual: [`docs/ejemplos_estilos/`](../../../docs/ejemplos_estilos/)

---

## Reglas del Brand Book Alfa

1. **Fuente**: Roboto (Google Fonts). Nunca Inter, nunca system-ui como principal.
2. **Alineación**: izquierda por defecto. Centrado solo en CTAs o info destacada (`.text-cta`). Justificado solo para textos legales (`.text-legal`).
3. **Ratio tipográfico 2:1**: el título de una sección mide el doble que el cuerpo. h1=30–32px, body=16px.
4. **Jerarquía de color**: primario `brand-*` (azul institucional), acento `lime`, estado `alfa-gray-*`.
5. **Tokens de color**: ver [`references/brand_tokens.md`](references/brand_tokens.md).

---

## Librería de componentes UI

14 componentes disponibles en `src/components/ui/`. Ver catálogo completo en:
→ [`references/componentes_ui.md`](references/componentes_ui.md)

Componentes más usados:

| Componente | Uso principal |
|---|---|
| `Button` | Acciones — 5 variantes: `primary`, `secondary`, `ghost`, `danger`, `accent` |
| `DataTable<T>` | Listados paginados — tipado genérico con column defs |
| `FilterBar` | Barra de filtros responsive — 2, 3 o 4 columnas |
| `PageLayout` | Contenedor de página — ancho `narrow/default/wide/full` |
| `PageHeader` | Encabezado con título, descripción, botón volver y slot de acciones |
| `Badge` | Estado visual — `success/warning/info/error/neutral/accent` |
| `Card` | Contenedor de sección con `CardHeader`, `CardBody`, `CardFooter` |

---

## Patrón estándar de página

Toda página nueva sigue esta composición:

```
PageLayout
  PageHeader (título + descripción + acciones)
  [Cards de métricas — opcional]
  FilterBar (selects, búsqueda, fechas)
  DataTable (datos + loading/error/empty states)
  Pagination
```

Ver ejemplos concretos en → [`references/patrones_paginas.md`](references/patrones_paginas.md)

---

## Integración con React Query, Zustand y Axios

- Instancia Axios en `src/lib/api.ts` — interceptors JWT y silent refresh automáticos.
- Zustand auth store en `src/store/authStore.ts` — usar `useHasRole()` y `useCanPerform()` para RBAC.
- React Query inline en páginas — query keys siempre incluyen filtros y paginación como segundo elemento.

Ver patrones detallados en → [`references/integracion_react_query.md`](references/integracion_react_query.md)

---

## Estructura de carpetas

```
apps/frontend/sistema-interno/src/
├── components/
│   ├── auth/          # LoginForm, ProtectedRoute, PublicRoute
│   ├── dashboard/     # FiltersBar, IncapacidadesTable, StatsCards, charts/
│   ├── incapacidades/ # AuditoriaFormulario, ConsultaFilters, GestionActions, etc.
│   ├── layout/        # AppShell, Header, Sidebar, Footer
│   ├── shared/        # DataTable genérico
│   └── ui/            # 14 componentes del sistema de diseño Alfa
├── hooks/             # useExtendedStats, useDebounce, useToast
├── lib/               # api.ts (Axios), utils.ts (cn helper)
├── pages/             # auth/, dashboard/, incapacidades/
├── services/          # authService, incapacidadService, dashboardService, empresaService
├── store/             # authStore.ts (Zustand persist)
├── schemas/           # Zod v3 schemas por recurso
├── types/             # TypeScript interfaces por dominio
└── utils/             # formatters.ts
```

---

## Notas críticas

- `<SelectItem value="">` está **prohibido** en Shadcn/ui — usar `value="ALL"` y filtrar en lógica.
  Ver [`docs/modulos/sistema-interno/CORRECCION_ERRORES.md`](../../../docs/modulos/sistema-interno/CORRECCION_ERRORES.md)
- `valueAsNumber: true` en React Hook Form retorna `NaN` si el campo está vacío — siempre validar con `isNaN()`.
  Ver [`docs/modulos/sistema-interno/BUGFIX_NAN_FILTROS.md`](../../../docs/modulos/sistema-interno/BUGFIX_NAN_FILTROS.md)
- El frontend corre en puerto **5174** (no 5173). Proxy Vite `/api → http://localhost:8010`.
  Ver [`docs/modulos/sistema-interno/CORS_FIX.md`](../../../docs/modulos/sistema-interno/CORS_FIX.md)
