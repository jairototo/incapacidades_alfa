# Arquitectura del Sistema de Gestión de Incapacidades

## 1. Visión General

Sistema de gestión de incapacidades para aseguradora con cobertura de ARL y pólizas de salud.

## 2. Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                      │
├──────────────────────────────┬──────────────────────────────────┤
│     Portal Externo           │      Sistema Interno             │
│   (React 18 + TypeScript)    │    (React 19 + TypeScript)       │
│                              │                                  │
│  - Radicación (sin auth)     │  - Autenticación JWT             │
│  - Consulta por número       │  - Dashboard auditoría           │
│  - Upload documentos         │  - Workflow incapacidades        │
│  - Validación en tiempo real │  - Órdenes de pago               │
│                              │  - Gestión usuarios/roles        │
│                              │  - Reportes y analytics          │
│                              │  - Exportación datos             │
│                              │                                  │
│  Stack: Vite, TailwindCSS,   │  Stack: +Zustand, TanStack       │
│  React Query, Zod, Shadcn/ui │  Table, Recharts, Socket.io      │
└──────────────────────────────┴──────────────────────────────────┘
                              ▲
                              │ HTTPS/REST + WebSockets
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                               │
│                     (Kong/Nginx/Traefik)                         │
│                                                                  │
│  - Rate Limiting             - Load Balancing                   │
│  - SSL Termination           - Request Routing                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE APLICACIÓN                          │
│                      Backend API (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth Service │  │ Incapacidad  │  │  File        │          │
│  │              │  │  Service     │  │  Service     │          │
│  │ - JWT/OAuth2 │  │              │  │              │          │
│  │ - RBAC       │  │ - Validación │  │ - Upload     │          │
│  └──────────────┘  │ - Workflow   │  │ - Download   │          │
│                    │ - Estados    │  │ - Validación │          │
│  ┌──────────────┐  │ - ARL/SALUD  │  └──────────────┘          │
│  │  Empresa     │  └──────────────┘                            │
│  │  Service     │                                               │
│  │              │  ┌──────────────┐  ┌──────────────┐          │
│  │ - Sync       │  │  Pago        │  │  Audit       │          │
│  │ - Validación │  │  Service     │  │  Service     │          │
│  └──────────────┘  │              │  │              │          │
│                    │ - Generación │  │ - Logs       │          │
│  ┌──────────────┐  │ - Estados    │  │ - Trazabilidad│         │
│  │  Empleado    │  └──────────────┘  └──────────────┘          │
│  │  Service     │                                               │
│  │              │  ┌──────────────┐  ┌──────────────┐          │
│  │ - Sync       │  │ Afiliado     │  │ Integration  │          │
│  │ - Validación │  │ Service      │  │ Service      │          │
│  └──────────────┘  │              │  │              │          │
│                    │ - Pólizas    │  │ - API Sync   │          │
│                    │ - Validación │  │ - File Import│          │
│                    └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA DE DATOS                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │  PostgreSQL         │      │  Redis Cache        │          │
│  │                     │      │                     │          │
│  │  - Datos maestros   │      │  - Sesiones         │          │
│  │  - Transacciones    │      │  - Rate limiting    │          │
│  │  - Auditoría        │      │  - Cache queries    │          │
│  └─────────────────────┘      └─────────────────────┘          │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │  S3/MinIO           │      │  Elasticsearch      │          │
│  │                     │      │                     │          │
│  │  - Documentos       │      │  - Logs             │          │
│  │  - Imágenes         │      │  - Búsquedas        │          │
│  │  - Archivos CSV     │      │  - Analytics        │          │
│  └─────────────────────┘      └─────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE INTEGRACIÓN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │  Message Queue      │      │  Scheduled Jobs     │          │
│  │  (RabbitMQ/Celery)  │      │  (Celery Beat)      │          │
│  │                     │      │                     │          │
│  │  - Async tasks      │      │  - Sync empresas    │          │
│  │  - Notifications    │      │  - Sync empleados   │          │
│  │  - File processing  │      │  - Reports          │          │
│  └─────────────────────┘      └─────────────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │         Sistemas Externos                         │          │
│  │                                                   │          │
│  │  - API RRHH (Empresas/Empleados)                 │          │
│  │  - API Siniestros                                │          │
│  │  - Sistema de Pagos                              │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 2.1 Detalle de Capa de Presentación

### Portal Externo (Público)

**Propósito**: Interfaz para radicación y consulta de incapacidades sin autenticación.

**Tecnologías**:
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS + Shadcn/ui (UI framework)
- React Query (data fetching)
- React Hook Form + Zod (formularios y validación)
- React Router v6 (routing)
- Axios (HTTP client)

**Funcionalidades**:
- Wizard de radicación de incapacidades (5 pasos)
- Consulta de estado por número o documento
- Upload de documentos (PDF, JPG, PNG hasta 10MB)
- Validaciones en tiempo real
- Diseño responsive (mobile-first)

**Despliegue**: Vercel/Netlify (JAMstack)

---

### Sistema Interno (Privado)

**Propósito**: Dashboard de auditoría y gestión completa para usuarios internos.

**Tecnologías Core**:
- **React 19.2** + TypeScript 5.3+ 
- Vite 5.0+ (build tool)
- TailwindCSS 3.4+ + Shadcn/ui (UI framework)
- Zustand (state management global)
- React Query (@tanstack/react-query v5)
- TanStack Table v8 (tablas avanzadas)
- Recharts (gráficas y dashboards)
- React Hook Form + Zod (formularios y validación)
- React Router v6 (routing)
- Axios (HTTP client con interceptores)
- Socket.io client (notificaciones real-time)

**React 19 - Características Habilitadas**:
- ✅ **Actions**: `useActionState` para manejo de formularios con estado de servidor
- ✅ **use() hook**: Consumo de promesas y context de forma directa
- ✅ **Refs as props**: Sin necesidad de `forwardRef`
- ✅ **useOptimistic**: UI optimista para actualizaciones inmediatas
- ✅ **useFormStatus**: Estado de formularios en progreso
- ✅ **Concurrent Features**: Transitions automáticas y Suspense mejorado
- ✅ **Document Metadata**: Manejo nativo de `<title>` y `<meta>` tags
- ✅ **Resource Loading**: Precarga optimizada de assets
- ❌ **NO usar**: `forwardRef` (deprecado), componentes de clase (legacy)

**Estructura de Carpetas** (`frontend/sistema-interno/`):
```
src/
├── app/ # Configuración de la app
│ ├── providers.tsx # React Query, Auth, Theme providers
│ └── router.tsx # React Router v6 configuration
├── components/ # Componentes reutilizables
│ ├── ui/ # Shadcn/ui components
│ ├── forms/ # Form components con useActionState
│ ├── tables/ # TanStack Table wrappers
│ └── layouts/ # Layouts (Dashboard, Auth)
├── features/ # Módulos por funcionalidad
│ ├── auth/ # Login, permisos, guards
│ ├── incapacidades/ # CRUD + workflow incapacidades
│ ├── ordenes-pago/ # Gestión de pagos
│ ├── usuarios/ # Administración usuarios
│ └── dashboard/ # Métricas y analytics
├── hooks/ # Custom hooks
│ ├── useAuth.ts
│ ├── usePermissions.ts
│ └── useOptimisticUpdate.ts
├── lib/ # Utilidades
│ ├── api.ts # Axios instance con interceptores
│ ├── queryClient.ts # React Query config
│ └── utils.ts # Helpers generales
├── stores/ # Zustand stores
│ ├── authStore.ts # Estado de autenticación
│ └── uiStore.ts # Estado UI (sidebar, theme)
└── types/ # TypeScript types/interfaces
└── api.ts # Tipos de la API
```
**Funcionalidades Principales**:
- Autenticación JWT con refresh tokens automáticos
- Gestión completa de incapacidades (workflow de estados)
- Auditoría de incapacidades (aprobar/rechazar/observar)
- Gestión de órdenes de pago con estados
- Dashboard con métricas y KPIs en tiempo real
- CRUD de usuarios, empresas, empleados, afiliados
- Reportes personalizados con filtros avanzados
- Exportación a Excel y PDF
- Sistema de permisos RBAC por rol
- Notificaciones en tiempo real vía WebSockets
- UI optimista para mejor UX

**Patrones React 19**:
(https://react.dev/blog/2024/12/05/react-19#whats-new-in-react-19) 
```typescript
// ✅ Actions con useActionState (reemplaza useState + onSubmit)
import { useActionState } from 'react';

function LoginForm() {
  const [state, formAction, isPending] = useActionState(loginAction, null);
  
  return (
    <form action={formAction}>
      <input name="email" required />
      <input name="password" type="password" required />
      <button disabled={isPending}>
        {isPending ? 'Iniciando sesión...' : 'Ingresar'}
      </button>
      {state?.error && <p>{state.error}</p>}
    </form>
  );
}

// ✅ use() hook para promesas
import { use, Suspense } from 'react';

function IncapacidadDetail({ incapacidadPromise }) {
  const incapacidad = use(incapacidadPromise);
  return <div>{incapacidad.numero}</div>;
}

// Wrapper con Suspense
<Suspense fallback={<Loading />}>
  <IncapacidadDetail incapacidadPromise={fetchIncapacidad(id)} />
</Suspense>

// ✅ Refs as props (sin forwardRef)
function CustomInput({ ref, ...props }: { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />;
}

// ✅ useOptimistic para actualizaciones optimistas
import { useOptimistic } from 'react';

function IncapacidadEstado({ incapacidad }) {
  const [optimisticEstado, setOptimisticEstado] = useOptimistic(
    incapacidad.estado,
    (currentState, newState) => newState
  );

  async function handleChangeEstado(newEstado) {
    setOptimisticEstado(newEstado);
    await updateEstado(incapacidad.id, newEstado);
  }

  return (
    <Badge estado={optimisticEstado}>
      {optimisticEstado}
    </Badge>
  );
}
```

**Roles de Usuario**:
- ADMIN: Acceso completo
- AUDITOR: Auditoría de incapacidades, reportes
- APROBADOR: Aprobación de órdenes de pago
- EMPRESA: Consulta y radicación
- EMPLEADO: Consulta propia
- READONLY: Solo lectura

**Despliegue**: Vercel/Netlify + CDN

---

### Arquitectura de Componentes Compartidos

**Library**: `@incapacidades/ui` (monorepo en Fase 3)

**Componentes Base (Shadcn/ui)**:
- Button, Input, Select, Textarea
- Card, Dialog, Dropdown Menu
- Table, Badge, Alert, Toast

**Componentes Personalizados**:
- FileUploader (drag & drop, validación)
- AutocompleteInput (búsqueda con debounce)
- DateRangePicker
- DataTable (genérico, sortable, paginado)
- Pagination (server-side)
- StatsCard (métricas con iconos)
- LoadingSpinner, EmptyState
- TimelineEstados (historial visual)

**Custom Hooks**:
- useDebounce, usePagination
- useLocalStorage, useMediaQuery
- useAuth, usePermissions

---

### Integración Frontend-Backend

**API Communication**:
- Axios con interceptores para JWT
- React Query para cache y sincronización
- Refresh token automático en 401
- Manejo centralizado de errores (422, 403, 500)

**Validaciones**:
- Client-side: Zod (UX inmediata)
- Server-side: Pydantic (seguridad)

**File Handling**:
- Upload: FormData multipart
- Download: Blob con presigned URLs
- Progress tracking con onUploadProgress

**Real-time** (Fase 3):
- Socket.io para notificaciones
- WebSockets para actualizaciones live

---

### Performance y Optimización

**Code Splitting**:
- Lazy loading de rutas con React.lazy
- Dynamic imports para componentes pesados

**Bundle Size**:
- Initial bundle < 200KB (gzip)
- Lazy routes < 100KB cada una
- Tree-shaking automático con Vite

**Caching Strategy**:
- React Query: staleTime 5 minutos
- Service Worker para assets estáticos (Fase 3)
- CDN para imágenes y archivos públicos

**Core Web Vitals**:
- LCP < 2.5s
- FID < 100ms
- CLS < 0.1

---

### Seguridad Frontend

**Autenticación**:
- JWT almacenado en httpOnly cookies (ideal)
- Refresh token rotation
- Logout con revocación de tokens

**Validación de Inputs**:
- Sanitización de datos del usuario
- XSS protection con React (escaping automático)
- CSRF tokens en requests sensibles

**Headers de Seguridad**:
- Content Security Policy (CSP)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY

---

### Testing Frontend

**Pirámide de Testing**:
```
     /\
    /E2E\      10% - Playwright (flujos críticos)
   /------\
  /Integr.\   20% - Testing Library (componentes + API)
 /----------\
/  Unitarios \ 70% - Vitest (lógica, hooks, utils)
--------------
```

**Tools**:
- Vitest + Testing Library (unit/integration)
- Playwright (E2E)
- MSW (Mock Service Worker para APIs)
- Storybook (documentación de componentes)

**Cobertura Mínima**:
- Unitarios: 70%
- Integración: 50%
- E2E: Flujos críticos (radicación, login, auditoría)

---

### CI/CD Pipeline Frontend

```
Commit → Lint → TypeCheck → Tests → Build → E2E → Deploy
  ↓       ↓         ↓          ↓       ↓      ↓       ↓
 Git   ESLint   tsc    Vitest   Vite  Playwright Vercel
```

**Environments**:
- `feature/*` → Preview deployment
- `develop` → Staging
- `main` → Production (manual approval)

---

### Accesibilidad (A11y)

**Estándar**: WCAG 2.1 Nivel AA

**Checklist**:
- Contraste de color 4.5:1
- Navegación completa por teclado
- ARIA labels en elementos interactivos
- Focus visible en todos los controles
- Textos alternativos en imágenes
- Estructura semántica HTML5
- Soporte para screen readers

**Tools**:
- eslint-plugin-jsx-a11y (linting)
- axe-core (testing)
- Lighthouse (auditoría)

---

### Internacionalización (i18n)

**Fase 1**: Solo español (Colombia)
**Fase 3**: Español + Inglés con react-i18next

---

## 3. Patrones Arquitectónicos

### 3.1 Clean Architecture / Hexagonal Architecture (Backend)
- **Domain Layer**: Entidades de negocio, reglas de dominio
- **Application Layer**: Casos de uso, servicios de aplicación
- **Infrastructure Layer**: Implementaciones concretas (DB, APIs)
- **Presentation Layer**: Controllers, schemas de API

### 3.2 Component-Driven Development (Frontend)
- **Atomic Design**: Átomos → Moléculas → Organismos → Templates → Páginas
- **Composition over Inheritance**: Componentes reutilizables
- **Container/Presenter Pattern**: Separación lógica/presentación

### 3.3 Repository Pattern (Backend)
- Abstracción del acceso a datos
- Facilita testing y cambio de tecnología

### 3.4 Dependency Injection (Backend)
- Inversión de dependencias
- Mayor testabilidad

### 3.5 CQRS (Command Query Responsibility Segregation)
- Separación de lecturas y escrituras
- Optimización de queries complejos

## 4. Componentes Principales

### 4.1 API Gateway
- **Tecnología**: Kong / Nginx / Traefik
- **Responsabilidades**:
  - Enrutamiento de requests
  - Rate limiting
  - SSL/TLS termination
  - Load balancing
  - CORS management

### 4.2 Backend API
- **Tecnología**: FastAPI (Python 3.11+)
- **Características**:
  - Auto-documentación (OpenAPI/Swagger)
  - Validación con Pydantic
  - Async I/O
  - Alto rendimiento

### 4.3 Base de Datos
- **Principal**: PostgreSQL 15+
  - ACID compliant
  - JSON support
  - Full-text search
  - Extensiones (pg_trgm, uuid-ossp)

- **Cache**: Redis
  - Sesiones de usuario
  - Rate limiting
  - Cache de queries frecuentes

### 4.4 Storage
- **MinIO / S3**:
  - Almacenamiento de documentos
  - Versionado de archivos
  - Políticas de retención

### 4.5 Logging y Monitoreo
- **ELK Stack**:
  - Elasticsearch: Indexación y búsqueda
  - Logstash: Procesamiento de logs
  - Kibana: Visualización

- **Prometheus + Grafana**:
  - Métricas de aplicación
  - Alertas
  - Dashboards

### 4.6 Message Queue
- **Celery + RabbitMQ**:
  - Procesamiento asíncrono
  - Tareas programadas
  - Gestión de carga

## 5. Seguridad

### 5.1 Autenticación
- **JWT (JSON Web Tokens)**:
  - Access token (15 min)
  - Refresh token (7 días)
  - Almacenamiento seguro

### 5.2 Autorización
- **RBAC (Role-Based Access Control)**:
  - Roles: Admin, Auditor, Empresa, Empleado
  - Permisos granulares por endpoint
  - Middleware de autorización

### 5.3 Seguridad de Archivos
- Validación de tipo MIME
- Escaneo antivirus (ClamAV)
- Límite de tamaño
- Nombres sanitizados
- Acceso con URLs firmadas

### 5.4 Protección de Datos
- Encriptación en tránsito (TLS 1.3)
- Encriptación en reposo (DB, Storage)
- Hashing de contraseñas (bcrypt)
- Sanitización de inputs

### 5.5 Auditoría
- Log de todas las operaciones críticas
- Registro de accesos
- Trazabilidad de cambios
- Retention policies

## 6. Escalabilidad

### 6.1 Horizontal Scaling
- Múltiples instancias de API
- Load balancer con health checks
- Stateless application design
- Session storage en Redis

### 6.2 Database Scaling
- Connection pooling (PgBouncer)
- Read replicas para consultas
- Particionado por fecha
- Índices optimizados

### 6.3 Caching Strategy
- Cache de autenticación
- Cache de datos maestros
- Cache de queries frecuentes
- Invalidación inteligente

### 6.4 Async Processing
- Tareas pesadas en background
- File processing asíncrono
- Notificaciones en cola
- Batch operations

## 7. Monitoreo y Observabilidad

### 7.1 Métricas Clave
- Request rate, latency, errors (RED)
- CPU, memoria, disco (USE)
- Business metrics (incapacidades/día)
- SLA compliance

### 7.2 Logs Estructurados
- Formato JSON
- Correlation IDs
- Niveles apropiados (DEBUG, INFO, ERROR)
- Sensitive data masking

### 7.3 Tracing Distribuido
- OpenTelemetry
- Jaeger para visualización
- Análisis de performance

### 7.4 Health Checks
- Liveness probe
- Readiness probe
- Dependency checks (DB, Redis, S3)

## 8. Disaster Recovery

### 8.1 Backups
- PostgreSQL: Daily full + WAL archiving
- S3/MinIO: Replicación cross-region
- Redis: RDB snapshots
- Retention: 30 días

### 8.2 Alta Disponibilidad
- Multi-AZ deployment
- Database replication
- Failover automático
- Load balancer health checks

### 8.3 Recuperación
- RPO (Recovery Point Objective): 1 hora
- RTO (Recovery Time Objective): 4 horas
- Procedimientos documentados
- Pruebas periódicas

## 9. Entornos

### 9.1 Desarrollo (DEV)
- Datos ficticios
- Logging verbose
- Debug mode enabled

### 9.2 Testing (QA)
- Datos anonimizados
- Integraciones mock
- Automated testing

### 9.3 Staging (STG)
- Clon de producción
- Datos anonimizados recientes
- Pre-deployment validation

### 9.4 Producción (PROD)
- High availability
- Monitoring completo
- Security hardened
- Automated backups

## 10. DevOps y CI/CD

### 10.1 Control de Versiones
- Git (GitLab/GitHub)
- Branching strategy: GitFlow
- Code reviews obligatorios
- Conventional commits

### 10.2 CI/CD Pipeline
```
Commit → Lint → Tests → Build → Security Scan → Deploy
```

- **CI**: GitLab CI / GitHub Actions
- **CD**: ArgoCD / Flux
- **Tests**: pytest, coverage >80%
- **Security**: SAST, DAST, dependency scanning

### 10.3 Containerización
- Docker para aplicaciones
- Docker Compose para desarrollo
- Kubernetes para producción
- Helm charts para deployment

### 10.4 Infrastructure as Code
- Terraform para infraestructura
- Ansible para configuración
- Versionado en Git
- Automated provisioning
