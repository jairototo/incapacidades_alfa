Con esa información cambia bastante la recomendación porque ahora **no estás diseñando una aseguradora desde cero**, sino una plataforma que debe respetar el manual de marca de Seguros Alfa.

De hecho, las directrices iniciales que compartiste entran en conflicto con el manual corporativo en dos puntos importantes:

1. El manual obliga a usar **Roboto**.
2. El manual ya define una identidad visual basada en **verdes corporativos**, no en una exploración estética libre.

---

# Lo que yo haría

## Mantener Roboto

Aunque normalmente recomendaría una tipografía más moderna como Plus Jakarta Sans o Manrope, aquí no hay discusión:

```text
Roboto Regular
Roboto Medium
Roboto Bold
```

son las fuentes oficiales.

La buena noticia es que Roboto sigue funcionando muy bien para aplicaciones transaccionales.

---

# Jerarquía tipográfica

Yo definiría algo así:

```css
--font-family: "Roboto", sans-serif;

--text-xs: 12px;
--text-sm: 14px;
--text-md: 16px;
--text-lg: 18px;
--text-xl: 24px;
--text-2xl: 32px;
```

Pesos:

```css
Regular: 400;
Medium: 500;
Bold: 700;
```

Uso:

| Elemento        | Peso |
| --------------- | ---- |
| Texto normal    | 400  |
| Labels          | 500  |
| Botones         | 500  |
| Menú            | 500  |
| Títulos sección | 700  |
| Dashboard cards | 700  |

---

# Paleta recomendada para la aplicación

No usaría todos los colores al mismo tiempo.

## Primarios

```css
--primary: #009B76;
--primary-dark: #005D55;
--deep-blue: #004953;
```

### Distribución

70% blanco

20% verde oscuro

10% verde claro

---

# Estados del sistema

## Éxito

```css
#009B76
```

## Advertencia

```css
#FECB00
```

## Error

```css
#D92D20;
```

(no está en la guía, pero es necesario)

## Información

```css
#0094B3
```

---

# Cómo usar el verde limón

Mucho cuidado.

```css
#7AB800
```

es un color de acento.

Yo lo usaría únicamente para:

* indicadores de progreso
* badges
* métricas positivas
* pasos completados

Por ejemplo:

```text
✓ Documentos cargados
✓ Solicitud validada
✓ En proceso de revisión
```

---

# Cómo NO usar el amarillo

Muchos equipos terminan haciendo esto:

```text
Botones amarillos
Menús amarillos
Headers amarillos
```

y la interfaz termina pareciendo una promoción comercial.

Yo lo reservaría para:

```text
Alertas
Recordatorios
Pendientes
```

---

# Propuesta de Dashboard

Visualmente algo así:

```text
┌──────────────────────────────────┐
│ LOGO ALFA                        │
├──────────────────────────────────┤
│ Hola, Juan Pérez                 │
│                                  │
│ ¿Qué deseas realizar hoy?        │
│                                  │
│ [ Radicar incapacidad ]          │
│ [ Consultar solicitud ]          │
│ [ Descargar certificados ]       │
│                                  │
├──────────────────────────────────┤
│ Solicitudes recientes            │
│                                  │
│ ● En revisión                    │
│ ● Pendiente documentos           │
│ ● Aprobada                       │
└──────────────────────────────────┘
```

---

# Aplicando las directrices de estética sin perder usabilidad

De las recomendaciones iniciales rescataría:

### Sí

✅ Fondos con gradientes muy sutiles

```css
background:
linear-gradient(
180deg,
#ffffff 0%,
#f6faf9 100%
);
```

---

✅ Microanimaciones

```css
transition: all .2s ease;
```

---

✅ Cards con profundidad

```css
box-shadow:
0 4px 20px rgba(0,0,0,.08);
```

---

✅ Aparición escalonada

Dashboard:

```text
1. Header
2. KPIs
3. Acciones rápidas
4. Tabla
```

animados suavemente.

---

### No

❌ Layouts diagonales

❌ Elementos superpuestos

❌ Tipografías experimentales

❌ Fondos con ruido

❌ Glassmorphism excesivo

❌ Animaciones largas

---

# Si fuera el arquitecto UX del proyecto de incapacidades

Para el sistema que has comentado varias veces (incapacidades, ARL, radicación de documentos y auditoría), buscaría una estética similar a:

* Portal bancario moderno.
* Portal de salud corporativo.
* Sistema gubernamental bien diseñado.

Con:

```css
Color principal: #009B76
Color secundario: #005D55
Acento: #7AB800

Fuente:
Roboto Regular
Roboto Medium
Roboto Bold

Radio:
12px

Sombras:
Suaves

Animaciones:
150ms - 250ms
```

El resultado sería una aplicación que se siente **moderna y corporativa**, alineada al manual de Seguros Alfa, sin caer en el aspecto antiguo que muchas aseguradoras todavía tienen.
