# Brand Tokens — Paleta Oficial Seguros Alfa

Fuente de verdad: [Seguros Alfa Brand Book — Paleta de color](https://zeroheight.com/24509f59d/p/645c19-paleta-de-color)

Implementación en ambos frontends: `index.css` de cada app vía CSS custom properties `hsl(var(--token))`.

> **Diferencia crítica de implementación**:
> - `portal-externo` → Tailwind **v4** (`@import "tailwindcss"`) — tokens como `bg-primary`, `text-foreground`
> - `sistema-interno` → Tailwind **v3** (`@tailwind base/components/utilities`) — mismos tokens semánticos
> - La **paleta de color es idéntica** en ambos. Solo difiere la versión de Tailwind y Zod.

---

## Paleta Principal

| Nombre | Hex | Pantone | HSL | Significado |
|---|---|---|---|---|
| **Verde Claro** | `#009B76` | 334C | `166 100% 30%` | Calma y optimismo — color primario de la marca |
| **Verde Oscuro** | `#005D55` | 3292C | `175 100% 18%` | Estabilidad y energía — variante oscura del primario |
| **Azul Profundo** | `#004953` | 316C | `187 100% 16%` | Tranquilidad y equilibrio — texto oscuro institucional |
| **Verde Limón** | `#7AB800` | 376C | `80 100% 36%` | Vitalidad y contraste — acento principal |

## Paleta Secundaria

| Nombre | Hex | Pantone | HSL | Uso recomendado |
|---|---|---|---|---|
| **Amarillo** | `#FECB00` | 116C | `48 100% 50%` | Alertas, destacados, badges warning |
| **Morado** | `#6B1F7C` | 2621C | `289 60% 30%` | Estados especiales, info alternativa |
| **Azul** | `#0094B3` | 3135C | `190 100% 35%` | Información, links secundarios |

---

## Mapeo a CSS Custom Properties (Shadcn/ui)

Los dos frontends usan el sistema semántico de Shadcn/ui. La paleta Alfa se mapea así:

```css
:root {
  /* ── Primarios — Verde Alfa ──────────────────────────────── */
  --primary:            166 100% 30%;   /* #009B76 Verde Claro */
  --primary-foreground:   0   0% 100%;  /* blanco sobre verde */

  /* ── Secundario — Verde Limón (acento/contraste) ─────────── */
  --secondary:           80 100% 36%;   /* #7AB800 Verde Limón */
  --secondary-foreground: 0   0%  10%;  /* texto oscuro sobre limón */

  /* ── Acento — Amarillo ───────────────────────────────────── */
  --accent:              48 100% 50%;   /* #FECB00 Amarillo */
  --accent-foreground:  187 100% 10%;   /* texto oscuro (Azul Profundo) */

  /* ── Fondo y texto base ──────────────────────────────────── */
  --background:           0   0% 100%;  /* blanco puro */
  --foreground:         187 100% 16%;   /* #004953 Azul Profundo — texto principal */

  /* ── Cards / Popovers ────────────────────────────────────── */
  --card:                 0   0% 100%;
  --card-foreground:    187 100% 16%;

  /* ── Muted — neutros suaves ──────────────────────────────── */
  --muted:              166  30% 94%;   /* verde muy claro como fondo muted */
  --muted-foreground:   175  20% 40%;   /* texto secundario */

  /* ── Bordes e inputs ─────────────────────────────────────── */
  --border:             166  20% 88%;
  --input:              166  20% 90%;
  --ring:               166 100% 30%;   /* mismo que primary para focus rings */

  /* ── Destructive ─────────────────────────────────────────── */
  --destructive:          0  72% 51%;   /* rojo estándar */
  --destructive-foreground: 0 0% 100%;

  --radius: 0.5rem;
}
```

---

## Tokens semánticos de estado — Badges y alertas

Mapeo de estados de incapacidades a la paleta Alfa:

| Estado | Color | Token CSS | Hex |
|---|---|---|---|
| `RADICADA` | neutral/gris | `--muted` | fondo verde muy claro |
| `EN_AUDITORIA` | azul info | secundario azul | `#0094B3` |
| `OBSERVADA` | amarillo | `--accent` | `#FECB00` |
| `APROBADA` | verde claro | `--primary` | `#009B76` |
| `APROBADA_PARCIALMENTE` | verde limón | `--secondary` | `#7AB800` |
| `RECHAZADA` | rojo | `--destructive` | rojo estándar |
| `EN_PAGO` | morado | secundario morado | `#6B1F7C` |
| `PAGADA` | verde oscuro | variante dark de primary | `#005D55` |

---

## Tipografía

**Fuente**: Roboto — cargada desde Google Fonts en `index.html` de cada app.
**Fallback**: Verdana, system-ui, -apple-system, sans-serif.

### Escala (ratio 2:1 — Brand Book Alfa)

| Elemento | Tailwind v3 | Tailwind v4 | Tamaño | Peso |
|---|---|---|---|---|
| `h1` | `text-3xl font-bold` | `text-3xl font-bold` | 30–32px | 700 |
| `h2` | `text-2xl font-bold` | `text-2xl font-bold` | 24px | 700 |
| `h3` | `text-xl font-bold` | `text-xl font-bold` | 20px | 700 |
| `h4` | `text-lg font-medium` | `text-lg font-medium` | 18px | 500 |
| body / `p` | `text-base font-normal` | `text-base font-normal` | 16px | 400 |
| labels | `text-sm font-medium` | `text-sm font-medium` | 14px | 500 |
| badges | `text-xs font-medium` | `text-xs font-medium` | 12px | 500 |

**Reglas tipográficas del Brand Book:**
- Alineación: **izquierda** por defecto siempre
- Centrado: solo en CTAs o información destacada
- Justificado: exclusivamente para textos legales
- Color de títulos: `text-foreground` (Azul Profundo `#004953`)

---

## Implementación por frontend

### portal-externo (Tailwind v4)
```css
/* apps/frontend/portal-externo/src/index.css */
@import "tailwindcss";

@layer base {
  :root {
    /* tokens de la paleta Alfa aquí */
  }
}
```
Uso en clases: `bg-primary`, `text-primary`, `border-primary`, `ring-primary`

### sistema-interno (Tailwind v3)
```css
/* apps/frontend/sistema-interno/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* mismos tokens de la paleta Alfa */
  }
}
```
Uso en clases: `bg-primary`, `text-primary` — **idéntico** al portal externo gracias a la abstracción CSS vars.

---

## Colores secundarios — uso puntual

Los colores secundarios (Amarillo, Morado, Azul) se usan de forma puntual, no como sistema base:

```tsx
// Azul secundario — links informativos, badges de info
className="bg-[#0094B3] text-white"           // o via CSS var custom si se define

// Morado — badge EN_PAGO u estados especiales
className="bg-[#6B1F7C] text-white"

// Amarillo — badge OBSERVADA, alertas de atención
className="bg-[#FECB00] text-gray-900"        // texto oscuro para contraste
```

Si se usan frecuentemente, definirlos como CSS vars adicionales en `index.css`:
```css
--color-info:    190 100% 35%;   /* #0094B3 Azul */
--color-warning: 48  100% 50%;   /* #FECB00 Amarillo */
--color-special: 289  60% 30%;   /* #6B1F7C Morado */
```
