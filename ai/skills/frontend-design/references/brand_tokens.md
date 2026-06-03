# Brand Tokens — Sistema Interno

Fuente de verdad: [`docs/ejemplos_estilos/index.css`](../../../../docs/ejemplos_estilos/index.css)

Sistema de diseño: **Seguros Alfa Brand Book**. Implementado con Tailwind v3 + tokens custom en `tailwind.config.js`.

---

## Paleta de color

### brand-* — Azul institucional (color primario)

| Token | Uso |
|---|---|
| `brand-50` | Hover muy suave (filas de tabla, fondos de ghost) |
| `brand-100` | Badge success background |
| `brand-500` | Focus rings (`focus:ring-brand-500`) |
| `brand-600` | Botón primary, links, label de formularios (`text-brand-600`) |
| `brand-700` | Hover de botón primary (`hover:bg-brand-700`) |
| `brand-800` | Active de botón primary |
| `brand-900` | Texto de títulos (h1–h5), color dominante del texto |

### alfa-gray-* — Escala de grises Alfa

| Token | Uso |
|---|---|
| `alfa-gray-100` | Fondos alternativos, separadores suaves |
| `alfa-gray-500` | Texto secundario, placeholders |
| `alfa-gray-900` | Color base del body (`color: theme('colors.alfa-gray.900')`) |

### Colores semánticos

| Token | Valor base | Uso |
|---|---|---|
| `lime` | Verde limón | Botón `accent`, badge `accent` (En Pago) |
| `alfa-yellow-light` | Amarillo | Badge `warning` background (`/30` de opacidad) |
| `alfa-blue` | Azul info | Badge `info` background (`/15` de opacidad) |
| `alfa-blue-dark` | Azul oscuro | Badge `info` texto |
| `red-100` / `red-600` / `red-700` | Rojo estándar Tailwind | Badges error, botón danger |

---

## Tipografía

**Fuente**: Roboto (cargada desde Google Fonts en `index.html`)
**Fallback**: Verdana, system-ui, -apple-system, sans-serif

### Escala (ratio 2:1)

| Elemento | Clase Tailwind | Tamaño | Peso |
|---|---|---|---|
| `h1` | `text-3xl font-bold text-brand-900 leading-tight` | 30–32px | bold |
| `h2` | `text-2xl font-bold text-brand-900 leading-snug` | 24px | bold |
| `h3` | `text-xl font-bold text-brand-900 leading-snug` | 20px | bold |
| `h4` | `text-lg font-medium text-brand-900` | 18px | medium |
| `h5/h6` | `text-base font-medium text-brand-900` | 16px | medium |
| `p` / body | `text-base font-normal leading-relaxed` | 16px | regular |
| Labels form | `text-sm font-medium text-brand-900` | 14px | medium |
| Badges / captions | `text-xs font-medium` | 12px | medium |

### Clases especiales de alineación

```css
.text-legal { @apply text-justify text-sm leading-relaxed; }  /* textos legales */
.text-cta   { @apply text-center; }                            /* CTAs o info destacada */
/* Por defecto: text-align left (brand book) */
```

---

## Clases utilitarias de componentes (CSS layer `components`)

Estas clases están en `index.css` y pueden usarse directamente o servir de referencia:

```css
/* Botones */
.btn-primary    → bg-brand-600 text-white + hover/active/focus/disabled
.btn-secondary  → border brand-600 bg-white + hover/active/focus/disabled
.btn-danger     → bg-red-600 text-white + hover/active/focus/disabled

/* Badges de estado */
.badge-success  → bg-brand-100 text-brand-700
.badge-warning  → bg-alfa-yellow-light/30 text-amber-800
.badge-info     → bg-alfa-blue/15 text-alfa-blue-dark
.badge-error    → bg-red-100 text-red-700

/* Contenedores */
.card           → bg-white rounded-lg border border-gray-200 shadow-sm p-6

/* Formularios */
.form-input     → block w-full rounded-md border border-gray-300 px-3 py-2 + focus:ring-brand-500
.form-label     → block text-sm font-medium text-brand-900 mb-1
```

---

## Reglas de diseño

1. **Alineación**: siempre izquierda excepto `.text-cta` (centrado) y `.text-legal` (justificado).
2. **Ratio 2:1**: el título de una sección mide el doble que el texto de cuerpo.
3. **Sombras**: usar solo `shadow-sm` (brand book prefiere interfaz limpia, sin sombras pesadas).
4. **Bordes**: `border-gray-200` para contenedores, `border-gray-300` para inputs.
5. **Radios**: `rounded-md` para botones e inputs, `rounded-lg` para cards y tablas, `rounded-full` para badges.
6. **Transiciones**: siempre `transition-colors duration-150` en elementos interactivos.
