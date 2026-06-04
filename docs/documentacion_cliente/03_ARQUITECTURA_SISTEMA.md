# ARQUITECTURA DEL SISTEMA

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Describir la arquitectura técnica completa del Sistema de Gestión de Incapacidades

---

## 1. VISIÓN GENERAL

El Sistema de Gestión de Incapacidades es una plataforma integral que gestiona el ciclo completo de incapacidades médicas desde la radicación hasta el pago, con soporte diferenciado para:

- **Incapacidades ARL** (Administradora de Riesgos Laborales): Gestión de siniestros/accidentes laborales vinculados a empleados
- **Incapacidades SALUD**: Gestión de afiliados con pólizas de salud

La arquitectura sigue patrones de **Clean Architecture / Hexagonal Architecture** con separación clara de capas y responsabilidades.

---

## 2. DIAGRAMA DE COMPONENTES

```mermaid
graph TB
    subgraph Cliente["🖥️ Capa Cliente"]
        PE["Portal Externo<br/>React 18 + Vite<br/>Puerto 5173"]
        SI["Sistema Interno<br/>React 18 + Vite<br/>Puerto 8080"]
    end
    
    subgraph Entrega["🌐 Capa de Entrega"]
        NG["Nginx<br/>Proxy Reverso<br/>Puerto 80/443"]
    end
    
    subgraph API["🔌 Capa API"]
        FW["FastAPI 0.109+<br/>Python 3.11+<br/>Puerto 8010"]
    end
    
    subgraph Logica["⚙️ Capa de Lógica"]
        SVC["Services<br/>Orquestación de negocio"]
        REP["Repositories<br/>Acceso a datos (batch)"]
    end
    
    subgraph Datos["💾 Capa de Datos"]
        PG["PostgreSQL 15+<br/>UUID, JSONB, Triggers<br/>Puerto 5442"]
        REDIS["Redis 7+<br/>Caché y Sesiones<br/>Puerto 6389"]
    end
    
    subgraph Storage["📦 Almacenamiento"]
        MINIO["MinIO/S3<br/>Documentos<br/>Puerto 9010"]
        FS["Filesystem<br/>Fallback"]
    end
    
    subgraph Queue["⏳ Colas de Tareas"]
        RMQ["RabbitMQ<br/>Message Broker<br/>Puerto 5682"]
        CEL["Celery<br/>Task Worker"]
        FLOWER["Flower<br/>Monitor Celery<br/>Puerto 5565"]
    end
    
    PE -->|HTTP/HTTPS| NG
    SI -->|HTTP/HTTPS| NG
    NG -->|Proxy| FW
    FW -->|Dependency Injection| SVC
    SVC -->|Query| REP
    REP -->|SQL Query| PG
    REP -->|Cache| REDIS
    FW -->|Upload/Download| MINIO
    MINIO -->|Fallback| FS
    FW -->|Publish| RMQ
    RMQ -->|Consume| CEL
    FLOWER -->|Monitor| RMQ
    CEL -->|Write| PG
```

---

## 3. FLUJO DE DATOS - DIAGRAMA DE FLUJO

```mermaid
graph LR
    A["Solicitante<br/>(Usuario Externo)"] -->|1. Completa Formulario| B["Portal Externo"]
    B -->|2. Valida Frontend| C{Validación<br/>Pydantic?}
    C -->|No| B
    C -->|Sí| D["API FastAPI<br/>POST /incapacidades/radicar"]
    D -->|3. Valida Backend| E{Cumple<br/>RN?}
    E -->|No| B
    E -->|Sí| F["Service Layer<br/>incapacidad_service"]
    F -->|4. Genera Radicado| G["Repository Layer<br/>batch_fetch()"]
    G -->|5. INSERT| H["PostgreSQL<br/>Tabla: incapacidad"]
    H -->|6. Trigger| I["Tabla: historial_estado<br/>RADICADA"]
    F -->|7. Publica Evento| J["RabbitMQ<br/>Queue: radicar_task"]
    J -->|8. Consume| K["Celery Worker"]
    K -->|9. Email/Notificación| L["Sistema de Notificaciones"]
    H -->|10. OK| M["Response JSON"]
    M -->|11. Muestra| N["Portal: Comprobante"]
    N -->|12. Consulta Pública| O["GET /incapacidades/consultar"]
    O -->|13. Redis Cache| P["CACHE HIT/MISS"]
    P -->|14. Número Radicado| Q["Estado Público"]
```

---

## 4. DIAGRAMA DE SECUENCIA - PROCESO DE RADICACIÓN

```mermaid
sequenceDiagram
    participant U as Solicitante
    participant PE as Portal Externo
    participant FW as FastAPI
    participant SVC as Service Layer
    participant REP as Repository
    participant DB as PostgreSQL
    participant REDIS as Redis
    participant CEL as Celery

    U->>PE: 1. Completa wizard (6 pasos)
    PE->>PE: 2. Valida con Zod + React Hook Form
    PE->>FW: 3. POST /incapacidades/radicar + archivos
    
    activate FW
    FW->>FW: 4. Valida token JWT
    FW->>SVC: 5. radicar_incapacidad(params)
    
    activate SVC
    SVC->>SVC: 6. Valida RN-001 a RN-020
    SVC->>SVC: 7. Genera número radicado (AAAAMMNNNNNN)
    SVC->>REP: 8. create_incapacidad(incap_data)
    
    activate REP
    REP->>REP: 9. Batch fetch relacionadas (empleado, empresa)
    REP->>DB: 10. BEGIN TRANSACTION
    REP->>DB: 11. INSERT incapacidad
    REP->>DB: 12. INSERT documentos (si existen)
    REP->>DB: 13. INSERT historial_estado (RADICADA)
    REP->>DB: 14. COMMIT
    deactivate REP
    
    DB->>DB: 15. Trigger: tr_incapacidad_estado
    DB->>DB: 16. INSERT historial_estado
    
    SVC->>REDIS: 17. Invalidar cache consulta
    SVC->>CEL: 18. Publica: radicar_incapacidad_task()
    deactivate SVC
    
    FW->>PE: 19. 201 CREATED + {numero, id, timestamp}
    deactivate FW
    
    PE->>U: 20. Muestra comprobante radicación
    PE->>U: 21. Email con número radicado
    
    CEL->>CEL: 22. Ejecuta tarea asíncrona
    CEL->>DB: 23. Inserta auditoria_log
    CEL->>CEL: 24. Envía notificaciones
```

---

## 5. DIAGRAMA DE SECUENCIA - PROCESO DE AUDITORÍA

```mermaid
sequenceDiagram
    participant AUD as Auditor
    participant SI as Sistema Interno
    participant FW as FastAPI
    participant SVC as Service Layer
    participant DB as PostgreSQL
    participant HIST as Historial Estado

    AUD->>SI: 1. Dashboard: Lista incapacidades EN_AUDITORIA
    SI->>FW: 2. GET /incapacidades?estado=EN_AUDITORIA
    FW->>FW: 3. Valida token + rol=AUDITOR
    FW->>SVC: 4. list_por_auditar()
    SVC->>DB: 5. SELECT * FROM incapacidad WHERE estado='EN_AUDITORIA'
    FW->>SI: 6. 200 OK + lista completa
    
    SI->>AUD: 7. Muestra listado con filtros
    AUD->>SI: 8. Selecciona incapacidad + ver detalles
    SI->>FW: 9. GET /incapacidades/{id}/detalles
    FW->>SVC: 10. get_incapacidad_con_documentos(id)
    SVC->>DB: 11. SELECT + LEFT JOIN documentos, siniestro, empleado
    FW->>SI: 12. 200 OK + objeto incapacidad completo
    
    SI->>AUD: 13. Muestra detalles + documentos
    AUD->>AUD: 14. Revisa documentos (PDF, imágenes)
    AUD->>AUD: 15. Valida contra RN-003 a RN-015
    
    alt Aprobado
        AUD->>SI: 16. Clic: Aprobar + observaciones opcionales
        SI->>FW: 17. PATCH /incapacidades/{id}/auditar
        FW->>FW: 18. {nuevo_estado: APROBADA}
        FW->>SVC: 19. cambiar_estado(id, APROBADA)
    else Observada
        AUD->>SI: 16. Clic: Observar
        SI->>FW: 17. PATCH /incapacidades/{id}/observar
        FW->>FW: 18. {nuevo_estado: OBSERVADA, observaciones: [...]}
        FW->>SVC: 19. cambiar_estado(id, OBSERVADA)
    else Rechazada
        AUD->>SI: 16. Clic: Rechazar + motivo
        SI->>FW: 17. PATCH /incapacidades/{id}/rechazar
        FW->>FW: 18. {nuevo_estado: RECHAZADA, motivo_rechazo: '...'}
        FW->>SVC: 19. cambiar_estado(id, RECHAZADA)
    end
    
    SVC->>DB: 20. BEGIN TRANSACTION
    SVC->>DB: 21. UPDATE incapacidad SET estado='APROBADA'
    SVC->>HIST: 22. INSERT historial_estado
    SVC->>DB: 23. INSERT auditoria_datos_aprobados (si aplica)
    SVC->>DB: 24. COMMIT
    FW->>SI: 25. 200 OK + incapacidad actualizada
    SI->>AUD: 26. Confirmación visual + estado nuevo
```

---

## 6. ESTRUCTURA DEL BACKEND

```
apps/backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/          # Layer 1: Routing + Request Validation
│   │       │   ├── auth.py          (6 endpoints: login, logout, refresh, change_password, ...)
│   │       │   ├── incapacidades.py (50+ endpoints: radicar, consultar, auditar, aprobar, pagar)
│   │       │   ├── empresas.py      (CRUD + búsqueda)
│   │       │   ├── empleados.py     (CRUD + filtros)
│   │       │   ├── afiliados.py     (CRUD + sincronización)
│   │       │   ├── siniestros.py    (CRUD + relación con incapacidades)
│   │       │   ├── documentos.py    (Upload, download, delete, búsqueda)
│   │       │   ├── ordenes_pago.py  (CRUD + workflow de pago)
│   │       │   ├── usuarios.py      (Admin: CRUD, bloqueo, reseteo)
│   │       │   ├── catalogos.py     (Lectura de CIE-10, municipios, etc)
│   │       │   ├── historial_estado.py (Auditoría de cambios)
│   │       │   └── solicitantes.py  (CRUD solicitantes)
│   │       └── router.py            # Central router
│   │
│   ├── services/                    # Layer 2: Business Logic & Orchestration
│   │   ├── incapacidad_service.py   (47KB: Lógica de radicación, auditoría, pago)
│   │   ├── orden_pago_service.py    (Workflow órdenes de pago)
│   │   ├── auth_service.py          (JWT, bcrypt, token validation)
│   │   ├── documento_service.py     (Upload a MinIO/FS, virus scan, virus scan)
│   │   ├── empresa_service.py       (Sincronización externa)
│   │   ├── empleado_service.py      (Importación masiva)
│   │   ├── usuario_service.py       (RBAC, bloqueo, reseteo)
│   │   ├── historial_estado_service.py (Auditoría de cambios)
│   │   └── ...service.py
│   │
│   ├── db/
│   │   ├── repositories/            # Layer 3: Data Access (Batch fetching - NO N+1)
│   │   │   ├── base.py
│   │   │   ├── incapacidad_repo.py
│   │   │   ├── documento_repo.py
│   │   │   └── ...
│   │   ├── session.py               # Async session factory
│   │   └── session_local.py         # Local session config
│   │
│   ├── models/                      # Layer 4: SQLAlchemy ORM (NO business logic)
│   │   ├── base.py                  # BaseModel con timestamp, UUID PK
│   │   ├── usuario.py
│   │   ├── incapacidad.py           (Polimórfico: ARL o SALUD)
│   │   ├── empresa.py
│   │   ├── empleado.py
│   │   ├── afiliado.py
│   │   ├── siniestro.py
│   │   ├── documento.py
│   │   ├── orden_pago.py
│   │   ├── historial_estado.py      (Polimórfico: incapacidad, siniestro, orden_pago)
│   │   ├── auditoria_datos_aprobados.py
│   │   ├── auditoria_log.py
│   │   ├── solicitante.py
│   │   ├── catalogo_cie10.py
│   │   ├── pre_incapacidad.py       (Pre-radicación)
│   │   ├── pre_documento.py         (Documentos pre-radiación)
│   │   ├── refresh_token.py         (Tokens con SHA256 hash)
│   │   └── __init__.py
│   │
│   ├── schemas/                     # Pydantic v2 DTOs
│   │   ├── incapacidad.py           (30+ schemas: Create, Update, Response, ...)
│   │   ├── documento.py
│   │   ├── orden_pago.py
│   │   ├── usuario.py
│   │   └── ...
│   │
│   ├── middleware/
│   │   ├── auth.py                  # JWT validation
│   │   ├── rbac.py                  # Role-based access control
│   │   ├── logger.py                # Request/Response logging
│   │   └── error_handler.py         # Global exception handling
│   │
│   ├── core/
│   │   ├── config.py                # Environment variables (.env)
│   │   ├── security.py              # JWT, bcrypt, PermissionChecker
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── enums.py                 # Enums: EstadoIncapacidad, TipoIncapacidad, etc
│   │   └── logging.py               # Loguru configuration
│   │
│   ├── tasks/                       # Celery async tasks
│   │   ├── incapacidad_tasks.py    (Radicar automática, notificaciones)
│   │   ├── email_tasks.py           (Envío de emails)
│   │   └── notification_tasks.py
│   │
│   ├── utils/
│   │   ├── enums.py                 # Enumeraciones (Estado, Tipo, Prioridad)
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── validators.py            # Validación de datos
│   │   └── helpers.py
│   │
│   ├── templates/                   # Email templates (Jinja2)
│   │   ├── radicacion_confirmacion.html
│   │   └── ...
│   │
│   └── main.py                      # FastAPI app initialization
│
├── alembic/                          # Database migrations
│   ├── versions/
│   │   ├── 20260106_1000_001_initial_schema.py
│   │   ├── 20260121_0202_34cf625b8606_add_trigger_registro_radicacion.py
│   │   ├── 20260202_1923_566c94df42fa_update_estadoincapacidad_enum_add_.py
│   │   └── 20260603_1415_874da694b916_add_pre_incapacidad_pre_documento.py
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── unit/                        # Unit tests (fixtures, mocks)
│   ├── integration/                 # Integration tests (DB + API)
│   ├── conftest.py                  # Pytest configuration
│   └── ...
│
├── scripts/                         # Utility scripts
│   ├── backup.sh
│   └── ...
│
├── docker-compose.yml               # 8 services: api, postgres, redis, minio, rabbitmq, flower, nginx, celery
├── Dockerfile
├── Makefile                         # make install, make dev, make test, make docker-up
├── pytest.ini
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies (.linting, testing)
└── README.md
```

---

## 7. ESTRUCTURA DEL FRONTEND - PORTAL EXTERNO

```
apps/frontend/portal-externo/
├── src/
│   ├── components/
│   │   ├── Atomic Design Structure
│   │   ├── atoms/                   # Botones, inputs, labels, icons
│   │   ├── molecules/               # Cards, formGroups, badges
│   │   ├── organisms/               # Headers, footers, modals, forms
│   │   └── pages/                   # Rutas principales
│   │
│   ├── pages/
│   │   ├── Home.tsx                 # Landing page + navegación
│   │   ├── Radicar.tsx              # Wizard radicación (6 pasos)
│   │   ├── Consultar.tsx            # Consulta pública
│   │   └── Layouts/
│   │       ├── MainLayout.tsx
│   │       └── ErrorLayout.tsx
│   │
│   ├── hooks/
│   │   ├── useRadicacion.ts         # Lógica wizard radicación
│   │   ├── useConsulta.ts           # Lógica consulta pública
│   │   ├── usePrevios.ts            # Pasos anteriores wizard
│   │   └── ...
│   │
│   ├── services/
│   │   ├── api.ts                   # Axios instance + interceptores
│   │   ├── incapacidadService.ts    # GET /incapacidades/*, POST /radicar
│   │   ├── documentoService.ts      # Upload, download
│   │   └── ...
│   │
│   ├── stores/
│   │   ├── useAuthStore.ts          # Zustand: token, user (opcional - puede ser localStorage)
│   │   ├── useRadicacionStore.ts    # Zustand: estado del wizard
│   │   └── ...
│   │
│   ├── utils/
│   │   ├── validators.ts            # Validación Zod
│   │   ├── formatters.ts            # Formateo de fechas, números
│   │   └── constants.ts             # Constantes (estados, tipos)
│   │
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css                    # TailwindCSS v4.1
│   └── vite-env.d.ts
│
├── tests/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   ├── vitest.config.ts
│   └── setup.ts
│
├── public/
│   ├── assets/
│   └── index.html
│
├── vite.config.ts                   # Vite + React + TypeScript
├── tsconfig.json                    # TypeScript strict mode
├── package.json                     # React 18, TailwindCSS 4, Zod, Vitest
└── tailwind.config.js               # Tailwind CSS v4 configuration

Módulos implementados:
- ✅ Wizard radicación (6 pasos) — 217 tests
- ✅ Módulo consulta pública — 141 tests
- ✅ Home + navegación
- ✅ Layout responsive
```

---

## 8. ESTRUCTURA DEL FRONTEND - SISTEMA INTERNO

```
apps/frontend/sistema-interno/
├── src/
│   ├── components/
│   │   ├── Atomic Design Structure
│   │   ├── Layout/
│   │   │   ├── AdminLayout.tsx
│   │   │   ├── DashboardLayout.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── Dashboard/               # Métricas, estadísticas
│   │   ├── Incapacidades/           # CRUD + listados
│   │   ├── Auditoria/               # Panel auditor
│   │   ├── Aprobacion/              # Panel aprobador
│   │   ├── Pago/                    # Panel pagador
│   │   ├── Usuarios/                # Admin management
│   │   └── Reportes/                # Reportes y exportación
│   │
│   ├── hooks/
│   │   ├── useIncapacidades.ts
│   │   ├── useAuditoria.ts
│   │   ├── usePago.ts
│   │   ├── useAuth.ts               # JWT + Zustand
│   │   └── ...
│   │
│   ├── stores/
│   │   ├── useAuthStore.ts          # Zustand: token, user, roles
│   │   ├── useIncapacidadStore.ts   # Zustand: listado, filtros
│   │   └── ...
│   │
│   ├── services/
│   │   ├── api.ts
│   │   └── ...
│   │
│   ├── types/
│   │   ├── incapacidad.ts
│   │   ├── usuario.ts
│   │   └── ...
│   │
│   └── ...
│
├── vite.config.ts
├── tsconfig.json
├── package.json                     # React 18, TailwindCSS v3, Zod v3, Vitest
└── ...

Estado: En desarrollo — Fase 2
Pendientes:
- Login screen
- Dashboard métricas
- TanStack Table para listados
- Recharts para gráficos
- RBAC enforcement
```

---

## 9. INFRAESTRUCTURA Y DESPLIEGUE

### 9.1 Docker Compose - 8 Servicios

```yaml
version: '3.9'

services:
  # 1. Backend API
  api:
    image: incapacidades:latest
    ports:
      - "8010:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis
      - rabbitmq
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 2. PostgreSQL
  postgres:
    image: postgres:15-alpine
    ports:
      - "5442:5432"
    environment:
      POSTGRES_DB: incapacidades
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 3. Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6389:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 4. RabbitMQ
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5682:5672"
      - "15682:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 5. Celery Worker
  celery:
    image: incapacidades:latest
    command: celery -A app.tasks worker -l info
    env_file: .env
    depends_on:
      - rabbitmq
      - redis
      - postgres
    volumes:
      - ./logs:/app/logs

  # 6. Celery Flower (Monitor)
  flower:
    image: mher/flower:2.0
    command: celery --broker=amqp://guest:guest@rabbitmq:5672// flower --port=5555
    ports:
      - "5565:5555"
    depends_on:
      - rabbitmq
      - celery

  # 7. MinIO (Optional - S3 compatible)
  minio:
    image: minio/minio:latest
    ports:
      - "9010:9000"
      - "9011:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    profiles:
      - minio
    command: server /data --console-address ":9001"

  # 8. Nginx (Proxy reverso)
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  minio_data:
```

### 9.2 Puertos Configurados

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| FastAPI | 8010 | API principal |
| Portal Externo (Vite) | 5173 | Desarrollo |
| PostgreSQL | 5442 | Base de datos |
| Redis | 6389 | Cache |
| RabbitMQ AMQP | 5682 | Message broker |
| RabbitMQ Management | 15682 | UI de RabbitMQ |
| MinIO API | 9010 | Almacenamiento S3 |
| MinIO Console | 9011 | UI MinIO |
| Celery Flower | 5565 | Monitor de tareas |
| Nginx | 80/443 | Proxy reverso |

### 9.3 Variáveis de Entorno

```env
# Backend
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/incapacidades

# Cache
REDIS_URL=redis://redis:6379/0

# Storage
STORAGE_TYPE=minio  # o filesystem
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=incapacidades

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@aseguradora.com
SMTP_PASSWORD=xxx

# Auth JWT
JWT_SECRET=tu-clave-secreta-64-caracteres-minimo
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=7

# Message Queue
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend
VITE_API_URL=http://localhost:8010
VITE_APP_NAME=Incapacidades Sistema
```

---

## 10. ARQUITECTURA DE SEGURIDAD

### 10.1 Flujo de Autenticación

```mermaid
graph LR
    A["Usuario"] -->|1. Credenciales| B["POST /auth/login"]
    B -->|2. Valida| C["auth_service.authenticate()"]
    C -->|3. Bcrypt compare| D["PostgreSQL - Usuario"]
    D -->|4. Match| E["JWT Sign HS256"]
    E -->|5. Access Token + Refresh| F["Response JSON"]
    F -->|6. localStorage| G["Frontend"]
    G -->|7. Authorization: Bearer| H["Endpoint protegido"]
    H -->|8. Valida JWT| I["get_current_user"]
    I -->|9. OK| J["Acceso permitido"]
    J -->|10. Ejecuta endpoint| K["Response"]
    K -->|11. 401 Unauthorized| L["Redirecciona a login"]
```

### 10.2 Niveles de Protección

| Nivel | Mecanismo | Descripción |
|-------|-----------|-------------|
| **JWT** | HS256 (HMAC) | Claims: iss, iat, exp, nbf, sub, jti |
| **RBAC** | 6 Roles | ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY |
| **Rate Limiting** | Per IP | Límite de intentos fallidos |
| **Bloqueo de Cuenta** | After 5 failed | Bloquea cuenta por 30 minutos |
| **CORS** | Origen permitido | Solo desde dominio configurado |
| **HTTPS** | TLS 1.3 | Nginx termina SSL |
| **CSRF** | Token en cookies | Si aplica (para forms) |
| **SQL Injection** | SQLAlchemy ORM | Parametrized queries |
| **XSS** | Content-Type | application/json |
| **HASHING** | bcrypt | Min cost: 12 rounds |

### 10.3 Datos Sensibles

- **Tokens**: SHA256-hashed en BD, no almacenar en claro
- **Contraseñas**: bcrypt con cost 12+
- **Documentos**: Almacenados en MinIO con acceso restringido
- **Logs**: No registran contraseñas, tokens (redacted)

---

## 11. CAPAS DE LA ARQUITECTURA EN DETALLE

### Layer 1: Endpoints (Routing + Validation)

```python
# Responsabilidades:
# - Extraer parámetros (query, path, body, headers)
# - Validar contra schema Pydantic
# - Llamar service layer
# - Serializar respuesta
# - Manejar errores HTTP

@router.post("/incapacidades/radicar")
async def radicar_incapacidad(
    request: IncapacidadCreate,           # Validación Pydantic
    db: AsyncSession = Depends(get_db),   # DI
    current_user: Usuario = Depends(get_current_user),  # Auth
):
    result = await incapacidad_service.radicar(request, current_user, db)
    return {"numero_radicado": result.numero, "id": result.id}
```

**Archivos**: `apps/backend/app/api/v1/endpoints/*.py`

### Layer 2: Services (Business Logic)

```python
# Responsabilidades:
# - Aplicar reglas de negocio (RN-001 a RN-050)
# - Orquestar con múltiples repositorios
# - Publicar eventos (Celery tasks)
# - Transacciones complejas
# - Logging y auditoría

async def radicar(request: IncapacidadCreate, user: Usuario, db: AsyncSession):
    # 1. Valida RN-001: Tipos soportados
    # 2. Valida RN-002: Genera número radicado único
    # 3. Crea incapacidad con documentos en transacción
    # 4. Invalida cache
    # 5. Publica task: radicar_incapacidad_automatica_task
    # 6. Retorna comprobante
```

**Archivos**: `apps/backend/app/services/*.py`

### Layer 3: Repositories (Data Access - Batch Fetching)

```python
# Responsabilidades:
# - Ejecutar queries SQLAlchemy
# - Batch fetching (DISTINCT ON, LEFT JOIN)
# - NO N+1 queries
# - Cache en Redis si aplica
# - Transactions BEGIN/COMMIT

async def get_incapacidad_con_relacionadas(id: UUID, db: AsyncSession):
    # 1. SELECT incapacidad WHERE id
    # 2. LEFT JOIN empleado, empresa, afiliado, siniestro, documentos
    # 3. DISTINCT ON incapacidad.id (latest)
    # 4. Retorna 1 objeto con relacionadas populated
```

**Archivos**: `apps/backend/app/db/repositories/*.py`

### Layer 4: Models (SQLAlchemy ORM)

```python
# Responsabilidades:
# - Definir esquema de BD
# - Validaciones (constraints, checks)
# - Sin lógica de negocio

class Incapacidad(BaseModel):
    numero: Mapped[str] = mapped_column(String(50), unique=True)
    tipo: Mapped[TipoIncapacidad]
    estado: Mapped[EstadoIncapacidad] = mapped_column(default=EstadoIncapacidad.RADICADA)
    # ...
```

**Archivos**: `apps/backend/app/models/*.py`

---

## 12. FLUJOS PRINCIPALES DE NEGOCIO

### 12.1 Radicación

```
1. Solicitante completa wizard (6 pasos)
2. Frontend valida con Zod
3. POST /incapacidades/radicar + documentos
4. Backend valida RN-001 a RN-020
5. Genera número radicado (AAAAMMNNNNNN)
6. Crea incapacidad + documentos en transacción
7. Trigger: INSERT historial_estado (RADICADA)
8. Invalida cache
9. Publica task Celery: radicar_incapacidad_automatica_task
10. Responde 201 CREATED + número radicado
11. Celery: Inserta auditoria_log + envía notificaciones
```

### 12.2 Auditoría

```
1. Auditor accede dashboard (Sistema Interno)
2. GET /incapacidades?estado=EN_AUDITORIA
3. Selecciona incapacidad + VER DETALLES
4. GET /incapacidades/{id}/detalles (documentos, siniestro, empleado)
5. Revisa documentos (PDF, imágenes)
6. Valida contra RN-003 a RN-015 manualmente
7. Selecciona acción: Aprobar, Observar, Rechazar
8. PATCH /incapacidades/{id}/auditar con nuevo_estado
9. Backend valida transición de estado
10. UPDATE incapacidad + INSERT historial_estado en transacción
11. Si OBSERVADA: INSERT auditoria_datos_aprobados con observaciones
12. Invalida cache
13. Publica tarea Celery: Email notificación
14. Responde 200 OK
```

### 12.3 Aprobación y Pago

```
1. Admin revisa incapacidades APROBADAS
2. PATCH /incapacidades/{id}/aprobar_pago
3. Sistema genera OrdenPago (estado=GENERADA)
4. Aprobador revisa orden: PATCH /ordenes_pago/{id}/aprobar
5. OrdenPago estado = APROBADA
6. Pagador ejecuta pago: PATCH /ordenes_pago/{id}/pagar
7. OrdenPago estado = PAGADA
8. Incapacidad estado = EN_PAGO → PAGADA
9. INSERT historial_estado (cada transición)
10. Responda con comprobante de pago
```

---

## 13. CONSIDERACIONES TÉCNICAS

### 13.1 Performance

- **Batch Fetching**: DISTINCT ON + LEFT JOIN para evitar N+1
- **Redis Cache**: Consultas públicas (5 min TTL)
- **Índices**: En campos frecuentemente filtrados (estado, empresa_id, empleado_id)
- **Connection Pooling**: SQLAlchemy async connection pool
- **Lazy Loading**: NO — usar eager loading con relationships

### 13.2 Resiliencia

- **Retry Logic**: Celery tasks con reintentos exponenciales
- **Health Checks**: Todos los servicios tienen endpoints /health
- **Logging**: Loguru con structured logging JSON
- **Error Handling**: Custom exceptions + middleware global

### 13.3 Escalabilidad

- **Horizontal**: Multiple API instances detrás de load balancer
- **Database**: PostgreSQL read replicas para SELECT queries
- **Cache**: Redis cluster para sharding
- **Queue**: RabbitMQ con múltiples workers Celery

### 13.4 Monitoreo

- **Logs**: Loguru → archivo + stdout (Docker)
- **Métricas**: Celery Flower para tasks
- **Health Checks**: Nginx / Docker compose
- **APM**: (Future) Sentry, New Relic, Datadog

---

## 14. MATRICES DE DECISIÓN ARQUITECTÓNICA

### 14.1 ¿Por qué Clean Architecture?

| Criterio | Beneficio |
|----------|-----------|
| Separación de capas | Fácil testing, mantenimiento |
| Independencia de frameworks | Migración sin perder lógica |
| Reutilización de servicios | Frontend + Backend usan misma lógica |
| Escalabilidad | Agregar nuevos endpoints sin tocar BD |

### 14.2 ¿Por qué FastAPI?

| Criterio | Beneficio |
|----------|-----------|
| Async/await nativa | Performance en I/O |
| Type hints | IDE autocomplete + validación Pydantic |
| OpenAPI automático | Documentación interactiva Swagger |
| Velocidad | Desarrollo rápido |

### 14.3 ¿Por qué PostgreSQL?

| Criterio | Beneficio |
|----------|-----------|
| ACID transactions | Garantía de consistencia |
| UUID nativa | Escalabilidad horizontal |
| JSONB | Flexibilidad en datos |
| Triggers | Auditoría automática (historial_estado) |
| Full Text Search | Búsqueda avanzada |

---

## 15. PRÓXIMAS MEJORAS ARQUITECTÓNICAS

1. **GraphQL**: Complementar REST con GraphQL para flexibilidad
2. **Event Sourcing**: Almacenar eventos en lugar de solo estados
3. **CQRS**: Separar reads (reportes) de writes (radicación)
4. **Microservicios**: Separar dominio de auditoría en servicio independiente
5. **Message Broker Upgrade**: Kafka para streaming de eventos
6. **Caché estratégico**: Implementar invalidación más granular
7. **API Gateway**: Kong o similar para rate limiting, autenticación centralizada

---

**Documento de Referencia**: Esta arquitectura está diseñada para soportar 10,000+ usuarios simultáneos y procesar 100+ radicaciones/día con garantía de integridad de datos y seguridad.
