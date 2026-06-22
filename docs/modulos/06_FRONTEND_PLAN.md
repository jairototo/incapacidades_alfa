# Plan de Desarrollo Frontend - Sistema de Gestión de Incapacidades

> ## ⛔ DOCUMENTO HISTÓRICO / PARCIALMENTE OBSOLETO (2026-06-20)
>
> La parte de **Portal Externo** de este plan describe un portal **público sin
> autenticación** (radicación y consulta anónimas) que **ya no existe**. El Portal
> Externo es hoy un portal **autenticado solo para empresas** (rol `EMPRESA`, solo
> ARL) con radicación individual + masiva y consulta autenticada por empresa.
> Estado actual: [`docs/superpowers/PR-portal-externo-empresa-refactor.md`](../superpowers/PR-portal-externo-empresa-refactor.md).

## Visión General

Desarrollo frontend en fases para portal externo y sistema interno, siguiendo una estrategia incremental que prioriza la funcionalidad de cara al cliente.

## Fases de Desarrollo

### Fase 1: Portal Externo (PRIORITARIO - 2-3 semanas)
**Objetivo**: Demo funcional para presentación al cliente

#### Módulos
- ✅ Radicación de incapacidades (sin login) - Wizard de 5 pasos
- ✅ Consulta de incapacidades por número de radicación
- ✅ Upload de documentos adjuntos (PDF, JPG, PNG)
- ✅ Validación en tiempo real de campos
- ✅ Diseño responsive (mobile-first)

#### Stack Tecnológico
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS + Shadcn/ui
- **Data Fetching**: React Query (@tanstack/react-query)
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Date Handling**: date-fns

#### Entregables
- Formulario de radicación funcional por etapas
- Consulta por número de radicación o documento
- Preview y upload de documentos
- Validaciones de negocio (CIE-10, fechas, MIME types)
- Diseño responsive (mobile, tablet, desktop)
- Documentación de componentes
- Tests unitarios (>70% coverage)

---

### Fase 2: Sistema Interno (4-6 semanas)
**Objetivo**: Dashboard de auditoría y gestión completa

#### Módulos
- Login y autenticación JWT
- Dashboard de auditoría de incapacidades
- Gestión de incapacidades (CRUD + workflow)
- Órdenes de pago (generación, aprobación, pago)
- Gestión de usuarios y roles (RBAC)
- Gestión de empresas y empleados
- Gestión de afiliados
- Gestión de siniestros

#### Stack Adicional
- **State Management**: Zustand (para auth, UI global)
- **Tables**: TanStack Table
- **Charts**: Recharts
- **Forms Avanzados**: React Hook Form + Zod
- **Notificaciones**: Sonner

#### Entregables
- Dashboard con métricas en tiempo real
- Workflow completo de auditoría
- Gestión de órdenes de pago
- CRUD completo de todas las entidades
- Sistema de permisos por rol
- Reportes y exportación de datos

---

### Fase 3: Funcionalidades Avanzadas (2-3 semanas)
**Objetivo**: Optimización y features premium

#### Módulos
- Reportes y analytics avanzados
- Exportación masiva de datos (Excel, PDF)
- Notificaciones en tiempo real (WebSockets)
- Integración con sistemas externos
- Firma digital de documentos
- Chat de soporte en línea
- Logs de auditoría completos

#### Stack Adicional
- **WebSockets**: Socket.io client
- **PDF Generation**: jsPDF / react-pdf
- **Excel Export**: xlsx
- **Signature**: react-signature-canvas
- **Real-time**: Socket.io

---

## Estimación de Esfuerzo

| Fase | Duración | Desarrolladores | Total Horas |
|------|----------|----------------|-------------|
| Fase 1: Portal Externo | 2-3 semanas | 1 Senior + 1 Mid | 160-240h |
| Fase 2: Sistema Interno | 4-6 semanas | 2 Senior + 1 Mid | 480-720h |
| Fase 3: Avanzadas | 2-3 semanas | 1 Senior + 1 Mid | 160-240h |
| **TOTAL** | **8-12 semanas** | **2-3 devs** | **800-1200h** |

---

## Arquitectura Frontend

### Estructura de Proyectos

```
frontend/
├── portal-externo/          # Fase 1 - Portal público
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── sistema-interno/         # Fase 2 - Sistema privado
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
└── shared-ui/              # Library de componentes compartidos
    ├── src/
    │   ├── components/
    │   ├── hooks/
    │   ├── utils/
    │   └── types/
    ├── package.json
    └── tsconfig.json
```

### Decisiones Arquitectónicas

#### ¿Monorepo o Multirepo?
**Decisión**: Multirepo inicialmente, migración a monorepo en Fase 3

**Justificación**:
- Fase 1 necesita deployment independiente
- Menor complejidad inicial
- Posibilidad de equipos separados
- Migración a Turborepo/Nx en Fase 3 si es necesario

#### Estado Global vs Local
**Decisión**: Mixto

- **Estado Local**: React Query (server state)
- **Estado Global**: Zustand (auth, UI preferences)
- **Estado de Formularios**: React Hook Form

#### Routing
**Decisión**: React Router v6

- Routing declarativo
- Lazy loading de rutas
- Protected routes para sistema interno

---

## Estándares de Código

### Nomenclatura
- **Componentes**: PascalCase (`FormularioRadicacion.tsx`)
- **Hooks**: camelCase con prefijo `use` (`useRadicacion.ts`)
- **Utilities**: camelCase (`formatDate.ts`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Types/Interfaces**: PascalCase (`IncapacidadResponse`)

### Estructura de Componentes
```typescript
// Imports
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// Types
interface Props {
  id: string;
  onSuccess?: () => void;
}

// Component
export function MiComponente({ id, onSuccess }: Props) {
  // Hooks
  const [estado, setEstado] = useState(false);
  const { data, isLoading } = useQuery(...);

  // Handlers
  const handleSubmit = () => {
    // ...
  };

  // Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

### Git Workflow
- **Branches**: `feature/`, `bugfix/`, `hotfix/`
- **Commits**: Conventional Commits
  - `feat: añadir wizard de radicación`
  - `fix: corregir validación de fechas`
  - `docs: actualizar README`
  - `test: añadir tests para FormularioConsulta`

---

## Testing Strategy

### Pirámide de Testing

```
     /\
    /E2E\      10% - Playwright (flujos críticos)
   /------\
  /Integr.\   20% - Testing Library (componentes con API)
 /----------\
/  Unitarios \ 70% - Vitest (lógica, hooks, utils)
--------------
```

### Cobertura Mínima
- **Unitarios**: 70%
- **Integración**: 50%
- **E2E**: Flujos críticos (radicación, consulta, login)

### Tools
- **Unit/Integration**: Vitest + Testing Library
- **E2E**: Playwright
- **Coverage**: Vitest coverage (v8)
- **Mocking**: MSW (Mock Service Worker)

---

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  Commit (feature/*)                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Lint & Format (ESLint, Prettier)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Type Check (TypeScript)                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Unit Tests (Vitest)                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Build (Vite)                                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  E2E Tests (Playwright) - Solo en main                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Deploy (AWS/Vercel/Netlify)                                │
│  - DEV: feature/* → preview                             │
│  - STG: develop → staging                               │
│  - PROD: main → production                              │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Budget

### Métricas Core Web Vitals

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| **LCP** (Largest Contentful Paint) | < 2.5s | < 4s |
| **FID** (First Input Delay) | < 100ms | < 300ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | < 0.25 |
| **FCP** (First Contentful Paint) | < 1.8s | < 3s |
| **TTI** (Time to Interactive) | < 3.8s | < 7.3s |

### Bundle Size
- **Initial Bundle**: < 200KB (gzip)
- **Lazy Routes**: < 100KB (gzip) cada una
- **Third-party**: < 50KB total

### Optimizaciones
- Code splitting por ruta
- Lazy loading de componentes pesados
- Image optimization (WebP, lazy load)
- CDN para assets estáticos
- Service Worker (Fase 3)

---

## Accesibilidad (A11y)

### Estándar: WCAG 2.1 Nivel AA

#### Checklist Mínimo
- [ ] Contraste de color 4.5:1 (texto normal)
- [ ] Contraste de color 3:1 (texto grande)
- [ ] Navegación por teclado completa
- [ ] Labels en todos los inputs
- [ ] ARIA labels cuando sea necesario
- [ ] Focus visible en todos los elementos interactivos
- [ ] Sin dependencia exclusiva de color
- [ ] Textos alternativos en imágenes
- [ ] Estructura semántica HTML5

#### Tools
- **Linting**: eslint-plugin-jsx-a11y
- **Testing**: jest-axe, axe-core
- **Manual**: Lighthouse, WAVE

---

## Internacionalización (i18n)

### Fase 1: Solo Español
- Textos hardcodeados en español (Colombia)

### Fase 3: Multilenguaje
- **Library**: react-i18next
- **Idiomas**: ES (Español), EN (Inglés)
- **Formato**: JSON por namespace

```typescript
// es/common.json
{
  "radicacion": {
    "titulo": "Radicar Incapacidad",
    "paso1": "Tipo de Incapacidad",
    "paso2": "Datos del Solicitante"
  }
}
```

---

## Deployment

### Ambientes

| Ambiente | URL | Branch | Auto-deploy |
|----------|-----|--------|-------------|
| **Development** | dev.incapacidades.com | feature/* | ✅ Preview |
| **Staging** | staging.incapacidades.com | develop | ✅ Auto |
| **Production** | incapacidades.com | main | Manual |

### Hosting
- **Opción 1**: AWS S3 + CloudFront
- **Opción 2**: Vercel (recomendado para Vite+React)
- **Opción 3**: Netlify

---

## Monitoreo y Observabilidad

### Error Tracking
- **Tool**: Sentry
- **Eventos**: Errores JS, API failures, performance issues
- **Alertas**: Slack/Email en producción

### Analytics
- **Tool**: Google Analytics 4 + Plausible (privacy-focused)
- **Eventos**: Radicaciones, consultas, downloads
- **Dashboards**: Conversión, tiempos, errores

### Performance
- **Tool**: Vercel Analytics / Lighthouse CI
- **Métricas**: Core Web Vitals en tiempo real
- **Alertas**: Degradación de performance

---

## Seguridad Frontend

### Buenas Prácticas
- ✅ HTTPS obligatorio
- ✅ Content Security Policy (CSP)
- ✅ XSS Protection headers
- ✅ Sanitización de inputs
- ✅ No almacenar datos sensibles en localStorage
- ✅ Tokens JWT en httpOnly cookies (sistema interno)
- ✅ CORS configurado correctamente
- ✅ Dependencies audit regular (`npm audit`)

### Validación
- **Client-side**: Zod (UX)
- **Server-side**: Pydantic (seguridad)
- **Regla**: Nunca confiar en validación del cliente


---

## Documentación Relacionada

- [07_FRONTEND_FASE1_PORTAL_EXTERNO.md](./07_FRONTEND_FASE1_PORTAL_EXTERNO.md) - Detalle completo Fase 1
- [08_FRONTEND_FASE2_SISTEMA_INTERNO.md](./08_FRONTEND_FASE2_SISTEMA_INTERNO.md) - Detalle completo Fase 2
- [09_COMPONENTES_COMPARTIDOS.md](./09_COMPONENTES_COMPARTIDOS.md) - Library de componentes
- [10_INTEGRACION_BACKEND.md](./10_INTEGRACION_BACKEND.md) - Guía de integración con API
- [03_API_ENDPOINTS.md](./03_API_ENDPOINTS.md) - Documentación de endpoints backend

---

## Contacto y Soporte

### Equipo Frontend
- **Tech Lead**: TBD
- **Senior Dev**: TBD
- **Mid Dev**: TBD

