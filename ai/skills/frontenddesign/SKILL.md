---
name: frontenddesign
description: >
  Skill para construir páginas y componentes en cualquiera de los dos frontends
  del sistema de incapacidades: portal-externo (React 19 + Tailwind v4) y
  sistema-interno (React 19 + Tailwind v3). Ambos usan la paleta oficial
  Seguros Alfa y el mismo Brand Book tipográfico. Úsalo siempre que crees o
  edites vistas en apps/frontend/.
---

# Frontend Design — Portales Seguros Alfa

## Dos frontends, una paleta, mismo Brand Book

| Aspecto | `portal-externo` | `sistema-interno` |
|---|---|---|
| **Audiencia** | Empresas y empleados — radicación y consulta pública | Auditores, aprobadores, admins |
| **Tailwind** | **v4** (`@import "tailwindcss"`) | **v3** (`@tailwind base/components/utilities`) |
| **Zod** | **v4** | **v3** |
| **Paleta** | Seguros Alfa (misma) | Seguros Alfa (misma) |
| **Sistema tokens** | `hsl(var(--primary))`, etc. — Shadcn/ui | `hsl(var(--primary))`, etc. — Shadcn/ui |
| **Puerto dev** | 5173 | **5174** |
| **Estado** | Fase 1 — completo (217 tests) | Fase 2 — en desarrollo |

> **Regla crítica**: NO copies schemas Zod ni clases CSS directamente entre los dos frontends
> sin verificar compatibilidad de versión. La paleta y la tipografía son iguales; la API de
> las librerías no lo es.

---

## Paleta oficial — Seguros Alfa

Colores principales definidos en el [Brand Book](https://zeroheight.com/24509f59d/p/645c19-paleta-de-color):

| Token semántico | Color | Hex | HSL |
|---|---|---|---|
| `--primary` | Verde Claro | `#009B76` | `166 100% 30%` |
| `--secondary` | Verde Limón | `#7AB800` | `80 100% 36%` |
| `--accent` | Amarillo | `#FECB00` | `48 100% 50%` |
| `--foreground` | Azul Profundo | `#004953` | `187 100% 16%` |
| `--ring` | Verde Oscuro | `#005D55` | `175 100% 18%` |

Secundarios puntuales: Azul `#0094B3`, Morado `#6B1F7C`.

Ver paleta completa con HSL, CMYK, mapeo a estados de incapacidad y reglas de contraste:
→ [`references/brand_tokens.md`](references/brand_tokens.md)

---

## Reglas del Brand Book (aplican a AMBOS portals)

1. **Fuente**: Roboto (Google Fonts). Nunca Inter ni system-ui como principal.
2. **Alineación**: izquierda por defecto. Centrado solo en CTAs. Justificado solo en textos legales.
3. **Ratio tipográfico 2:1**: h1 = 30–32px bold, body = 16px regular.
4. **Color de títulos**: `text-foreground` (Azul Profundo `#004953`).
5. **Color de acciones primarias**: `bg-primary` (Verde Claro `#009B76`).
6. **Sombras**: solo `shadow-sm` — interfaz limpia.
7. **Bordes**: `border-border` para contenedores, `border-input` para campos.
8. **Radios**: `rounded-md` para botones/inputs, `rounded-lg` para cards/tablas, `rounded-full` para badges.

---

## Librería de componentes UI

### sistema-interno — 14 componentes custom en `src/components/ui/`
Basados en `docs/ejemplos_estilos/`. Catálogo completo:
→ [`references/componentes_ui.md`](references/componentes_ui.md)

### portal-externo — Shadcn/ui primitivos
Usa directamente los primitivos de Shadcn/ui (`Button`, `Card`, `Input`, etc.) con los tokens
CSS de la paleta Alfa. Patrón: wizard de 5 pasos con `react-hook-form` + Zod v4.

---

## Patrón estándar de página (sistema-interno)

```
PageLayout
  PageHeader (título + descripción + acciones)
  [Cards de métricas — opcional]
  FilterBar (selects, búsqueda, fechas)
  DataTable (datos + loading/error/empty states)
  Pagination
```

Ver ejemplos concretos con código completo:
→ [`references/patrones_paginas.md`](references/patrones_paginas.md)

---

## Integración con React Query, Zustand y Axios (sistema-interno)

- Instancia Axios en `src/lib/api.ts` — interceptors JWT y silent refresh automáticos.
- Zustand en `src/store/authStore.ts` — `useHasRole()` y `useCanPerform()` para RBAC.
- React Query inline en páginas — `staleTime: 5min`, query keys con filtros como segundo elemento.

Ver patrones detallados:
→ [`references/integracion_react_query.md`](references/integracion_react_query.md)

---

## Estructura de carpetas

### portal-externo
```
apps/frontend/portal-externo/src/
├── components/   # wizard steps, consulta, shared
├── hooks/        # React Query hooks por feature
├── lib/          # api.ts (Axios), validations
├── pages/        # RadicarPage, ConsultaPage
├── schemas/      # Zod v4 schemas
└── types/        # TypeScript interfaces
```

### sistema-interno
```
apps/frontend/sistema-interno/src/
├── components/
│   ├── auth/          # LoginForm, ProtectedRoute
│   ├── dashboard/     # KPIs, charts (Recharts)
│   ├── incapacidades/ # AuditoriaFormulario, GestionActions, etc.
│   ├── layout/        # AppShell, Header, Sidebar
│   └── ui/            # 14 componentes del sistema de diseño
├── hooks/             # useExtendedStats, useDebounce, useToast
├── lib/               # api.ts (Axios), utils.ts
├── pages/             # auth/, dashboard/, incapacidades/
├── services/          # authService, incapacidadService, dashboardService
├── store/             # authStore.ts (Zustand persist)
├── schemas/           # Zod v3 schemas
└── types/             # TypeScript por dominio
```

---

## Gotchas críticos

| Problema | Portal | Fix |
|---|---|---|
| `<SelectItem value="">` crash | sistema-interno | Usar `value="ALL"`, filtrar en queryFn |
| `valueAsNumber` retorna NaN en campo vacío | sistema-interno | Guard con `isNaN()` antes de usar |
| Puerto 5174, no 5173 | sistema-interno | Proxy Vite `/api → http://localhost:8010` |
| Zod v4 API diferente a v3 | ambos (distintos) | No mezclar schemas entre portals |
| Tailwind v4 sin `tailwind.config.js` | portal-externo | Configurar tokens en CSS con `@theme` |

Referencias de bugs documentados:
- [`docs/modulos/sistema-interno/CORRECCION_ERRORES.md`](../../../docs/modulos/sistema-interno/CORRECCION_ERRORES.md)
- [`docs/modulos/sistema-interno/BUGFIX_NAN_FILTROS.md`](../../../docs/modulos/sistema-interno/BUGFIX_NAN_FILTROS.md)
- [`docs/modulos/sistema-interno/CORS_FIX.md`](../../../docs/modulos/sistema-interno/CORS_FIX.md)
