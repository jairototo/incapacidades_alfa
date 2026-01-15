# GitHub Copilot Instructions

## Descripción General del Proyecto

**Sistema de Gestión de Incapacidades** - Plataforma integral para aseguradoras que maneja el ciclo completo de incapacidades médicas desde la radicación hasta el pago, con soporte diferenciado para:
- **Incapacidades ARL** (Administradora de Riesgos Laborales): Con gestión de siniestros/accidentes laborales
- **Incapacidades SALUD**: Con gestión de afiliados y pólizas

### Stack Tecnológico Completo

#### Backend (95% completado)
- **Framework**: FastAPI 0.109+ con Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async/await native)
- **Base de Datos**: PostgreSQL 15+ (UUID primary keys, JSONB, triggers)
- **Cache/Session**: Redis 7+
- **Storage**: MinIO/S3 compatible
- **Task Queue**: Celery + RabbitMQ
- **Migraciones**: Alembic 1.13+
- **Validación**: Pydantic v2.5+
- **Auth**: python-jose (JWT), passlib (bcrypt)
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Logging**: Loguru (structured logging)

#### Frontend (0% - Documentación completa)
- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3 + Shadcn/ui
- **Data Fetching**: React Query (@tanstack/react-query)
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **State**: Zustand (auth/UI global)
- **Tables**: TanStack Table
- **Charts**: Recharts
- **Testing**: Vitest + Testing Library + Playwright
- **Deployment**: Vercel/Netlify

#### Infraestructura
- **Containerización**: Docker 24+ con Docker Compose
- **Proxy**: Nginx 1.25+
- **CI/CD**: GitHub Actions
- **Monitoreo**: Prometheus + Grafana + Sentry

### Puertos Configurados (custom para evitar conflictos)
- **API FastAPI**: `8010`
- **PostgreSQL**: `5442`
- **Redis**: `6389`
- **MinIO API**: `9010`
- **MinIO Console**: `9011`
- **RabbitMQ AMQP**: `5682`
- **RabbitMQ Management**: `15682`
- **Flower (Celery)**: `5565`

## Arquitectura y Estructura

### Principios Arquitectónicos

1. **Clean Architecture / Hexagonal Pattern** (Backend)
   - Separación estricta de capas: API → Services → Repositories → Models
   - Dependency Injection via FastAPI dependencies
   - Domain-Driven Design (DDD) patterns

2. **Component-Driven Development** (Frontend)
   - Atomic Design con Shadcn/ui como base
   - Componentes reutilizables entre portal externo y sistema interno
   - Storybook para documentación visual

3. **Async-First** 
   - SQLAlchemy 2.0 async/await
   - FastAPI endpoints async
   - React Query para data fetching asíncrono

### Estructura Backend

```
backend/app/
├── api/v1/
│   ├── router.py                  # Router principal
│   └── endpoints/                 # 11 módulos de endpoints
│       ├── auth.py                # JWT login/logout/refresh
│       ├── incapacidades.py       # CRUD + workflow
│       ├── ordenes_pago.py        # Gestión de pagos
│       ├── usuarios.py            # CRUD usuarios + roles
│       ├── empresas.py            # CRUD empresas
│       ├── empleados.py           # CRUD empleados
│       ├── afiliados.py           # CRUD afiliados
│       ├── siniestros.py          # CRUD siniestros ARL
│       ├── documentos.py          # Upload/download MinIO
│       ├── historial_estado.py    # Auditoría de cambios
│       └── health.py              # Health checks
├── core/
│   ├── config.py                  # Settings (Pydantic v2)
│   ├── security.py                # JWT, bcrypt, RBAC
│   ├── exceptions.py              # Custom exceptions (8 tipos)
│   ├── logging.py                 # Loguru setup
│   └── events.py                  # Startup/shutdown handlers
├── db/
│   ├── session.py                 # AsyncSession factory
│   └── repositories/              # 11 repositories
│       └── base.py                # BaseRepository genérico
├── models/                        # 11 modelos SQLAlchemy 2.0
│   ├── base.py                    # BaseModel (id, timestamps)
│   ├── usuario.py                 # Auth + RBAC
│   ├── refresh_token.py           # JWT refresh tokens
│   ├── empresa.py                 # Empresas ARL
│   ├── empleado.py                # Empleados (para ARL)
│   ├── afiliado.py                # Afiliados (para SALUD)
│   ├── incapacidad.py             # Modelo polimórfico ARL/SALUD
│   ├── siniestro.py               # Accidentes laborales
│   ├── documento.py               # Archivos con hashes
│   ├── historial_estado.py        # Auditoría polimórfica
│   ├── orden_pago.py              # Órdenes de pago
│   └── auditoria_log.py           # Logs del sistema
├── schemas/                       # 11 schemas Pydantic v2
│   └── [entity].py                # Base/Create/Update/Response por modelo
├── services/                      # 11 services (lógica de negocio)
│   ├── auth_service.py            # Login, tokens, permissions
│   ├── incapacidad_service.py     # Workflow + validaciones
│   ├── orden_pago_service.py      # Generación y aprobación
│   ├── usuario_service.py         # CRUD + roles
│   ├── documento_service.py       # Upload MinIO + hashing
│   └── [entity]_service.py        # CRUD + business logic
├── tasks/                         # Celery tasks
│   ├── email_tasks.py             # Notificaciones email
│   ├── notification_tasks.py      # Notificaciones in-app
│   └── report_tasks.py            # Generación reportes PDF/Excel
├── utils/
│   └── enums.py                   # 17 enumeraciones del sistema
└── main.py                        # FastAPI app entry point
```

### Estructura Frontend (Planeada)

```
frontend/
├── portal-externo/                # Fase 1: Portal público sin auth
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn/ui base
│   │   │   ├── forms/             # Wizard radicación 5 pasos
│   │   │   ├── consulta/          # Consulta por radicación
│   │   │   └── layout/            # Layout público
│   │   ├── services/
│   │   │   ├── api.ts             # Axios instance
│   │   │   └── queries/           # React Query hooks
│   │   ├── types/                 # TypeScript types
│   │   ├── utils/                 # Utilidades
│   │   └── App.tsx
│   └── package.json
├── sistema-interno/               # Fase 2: Dashboard privado con auth
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn/ui base
│   │   │   ├── auth/              # Login, guards
│   │   │   ├── dashboard/         # Dashboard widgets
│   │   │   ├── incapacidades/     # CRUD incapacidades
│   │   │   ├── ordenes-pago/      # Gestión pagos
│   │   │   ├── usuarios/          # Gestión usuarios
│   │   │   └── layout/            # Layout privado
│   │   ├── services/
│   │   │   ├── api.ts             # Axios + interceptors JWT
│   │   │   └── queries/           # React Query (15+ hooks)
│   │   ├── store/
│   │   │   └── authStore.ts       # Zustand auth state
│   │   ├── router/                # React Router v6
│   │   ├── hooks/                 # Custom hooks
│   │   └── App.tsx
│   └── package.json
└── shared-ui/                     # Fase 3: Library compartida
    ├── src/
    │   ├── components/            # Componentes reutilizables
    │   ├── hooks/                 # Custom hooks
    │   ├── utils/                 # Utilidades compartidas
    │   └── types/                 # Types compartidos
    └── package.json
```

### Modelo de Datos (11 Tablas)

#### Entidades Principales

1. **USUARIO**: Autenticación, roles RBAC (6 roles), bloqueo por intentos fallidos
2. **REFRESH_TOKEN**: Tokens JWT con hash SHA256 y versioning
3. **EMPRESA**: Empresas ARL con sincronización externa (sync_source, external_id)
4. **EMPLEADO**: Empleados vinculados a empresas (para incapacidades ARL)
5. **AFILIADO**: Afiliados con pólizas de salud (para incapacidades SALUD)
6. **INCAPACIDAD**: Modelo polimórfico (ARL o SALUD) con workflow de estados
7. **SINIESTRO**: Accidentes laborales ARL (relación 1:N con incapacidades)
8. **DOCUMENTO**: Archivos con hashes MD5/SHA256 y almacenamiento MinIO
9. **HISTORIAL_ESTADO**: Auditoría de cambios de estado (polimórfico)
10. **ORDEN_PAGO**: Órdenes de pago con workflow (GENERADA → APROBADA → PAGADA)
11. **AUDITORIA_LOG**: Logs de auditoría del sistema

#### Relaciones Clave

```
EMPRESA 1──N EMPLEADO 1──N INCAPACIDAD (ARL)
                    │1
                    └──N SINIESTRO

AFILIADO 1──N INCAPACIDAD (SALUD)

INCAPACIDAD 1──N DOCUMENTO
            1──N HISTORIAL_ESTADO
            1──1 ORDEN_PAGO

USUARIO (cambiado_por) 1──N HISTORIAL_ESTADO
USUARIO (uploaded_by) 1──N DOCUMENTO
```

### Flujo de Estados (State Machine)

**Incapacidades**:
```
RADICADA → EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA}
                              │          │
                              │          └→ EN_PAGO → PAGADA
                              │
                              └→ (responder) → EN_AUDITORIA
```

**Órdenes de Pago**:
```
GENERADA → APROBADA → EN_PROCESO → PAGADA
    │                       │
    └→ ANULADA ←───────────┘
```

**Validaciones de Transición**:
- Solo auditores pueden cambiar RADICADA → EN_AUDITORIA
- Solo aprobadores pueden cambiar EN_AUDITORIA → APROBADA
- Solo admin puede generar orden de pago (APROBADA → EN_PAGO)
- Cada transición genera registro en HISTORIAL_ESTADO automáticamente



1. **Clean Architecture**: Separar claramente las capas:
   - `api/`: Endpoints REST (FastAPI routers)
   - `models/`: Modelos SQLAlchemy (ORM)
   - `schemas/`: Schemas Pydantic (validación)
   - `services/`: Lógica de negocio
   - `db/repositories/`: Acceso a datos
   - `core/`: Configuración, seguridad, excepciones

2. **Async First**: Usar siempre funciones async/await para I/O operations:
   ```python
   async def get_incapacidad(db: AsyncSession, id: UUID) -> Incapacidad:
       result = await db.execute(select(Incapacidad).where(Incapacidad.id == id))
       return result.scalar_one_or_none()
   ```

3. **Dependency Injection**: Usar FastAPI dependencies:
   ```python
   async def endpoint(
       db: AsyncSession = Depends(get_db),
       current_user: Usuario = Depends(get_current_user)
   ):
   ```

### Modelos SQLAlchemy

1. **Heredar de BaseModel**: Todos los modelos deben heredar de `app.models.base.BaseModel`
2. **Usar Mapped y mapped_column**: SQLAlchemy 2.0 style
   ```python
   class Empresa(BaseModel):
       __tablename__ = "empresa"
       
       nit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
       razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
   ```

3. **Relaciones**: Usar `relationship` con lazy="selectin" para async
   ```python
   incapacidades: Mapped[List["Incapacidad"]] = relationship(
       back_populates="empleado",
       lazy="selectin"
   )
   ```

### Schemas Pydantic

1. **Separar por operación**:
   - `*Base`: Campos base compartidos
   - `*Create`: Para crear (POST)
   - `*Update`: Para actualizar (PUT/PATCH)
   - `*InDB`: Modelo completo con campos auto-generados
   - `*Response`: Para respuestas API

2. **Usar ConfigDict**: Pydantic v2
   ```python
   model_config = ConfigDict(from_attributes=True)
   ```

3. **Validadores**: Usar `@field_validator` de Pydantic v2
   ```python
   @field_validator('numero_siniestro')
   @classmethod
   def validate_numero_siniestro(cls, v, info):
       # validación
   ```

### Endpoints API

1. **Estructura de router**:
   ```python
   router = APIRouter()
   
   @router.get("/", response_model=ListResponse)
   async def list_items(
       skip: int = 0,
       limit: int = 100,
       db: AsyncSession = Depends(get_db)
   ):
   ```

2. **Manejo de errores**: Usar excepciones personalizadas de `app.core.exceptions`
   ```python
   from app.core.exceptions import NotFoundException
   
   if not item:
       raise NotFoundException(f"Item {id} no encontrado")
   ```

3. **Respuestas consistentes**: Usar schemas de respuesta
   ```python
   @router.get("/{id}", response_model=ItemResponse)
   async def get_item(id: UUID):
   ```

### Estado y Workflow

1. **Flujo de estados**: Seguir el diagrama en `docs/04_FLUJO_ESTADOS.md`
   - RADICADA → EN_AUDITORIA → OBSERVADA/APROBADA/RECHAZADA → EN_PAGO → PAGADA

2. **Validaciones de transición**: Implementar en services
   ```python
   ALLOWED_TRANSITIONS = {
       EstadoIncapacidad.RADICADA: [EstadoIncapacidad.EN_AUDITORIA],
       EstadoIncapacidad.EN_AUDITORIA: [
           EstadoIncapacidad.OBSERVADA,
           EstadoIncapacidad.APROBADA,
           EstadoIncapacidad.RECHAZADA
       ],
   }
   ```

3. **Registrar historial**: Cada cambio de estado debe crear registro en HISTORIAL_ESTADO

### Base de Datos

1. **Usar UUIDs**: Todos los IDs son UUID v4
2. **Timestamps automáticos**: `created_at`, `updated_at` heredados de BaseModel
3. **Soft deletes**: Usar campo `deleted_at` cuando sea necesario
4. **Índices**: Crear índices para campos de búsqueda frecuente

### Seguridad

1. **RBAC**: Usar `PermissionChecker` de `app.core.security`
   ```python
   from app.core.security import PermissionChecker, Permissions
   
   @router.post("/", dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_CREATE]))])
   ```

2. **JWT**: Autenticación con tokens JWT
3. **Passwords**: Siempre usar `pwd_context.hash()` para hashear contraseñas

### Testing

1. **Usar pytest**: Tests unitarios e integración
2. **Fixtures**: Crear fixtures reutilizables
3. **Async tests**: Usar `pytest-asyncio`
   ```python
   @pytest.mark.asyncio
   async def test_create_incapacidad(db_session):
   ```

### Documentación

1. **Docstrings**: Usar Google style
   ```python
   def function(param1: str, param2: int) -> bool:
       """
       Descripción breve.
       
       Args:
           param1: Descripción del parámetro
           param2: Descripción del parámetro
           
       Returns:
           Descripción del retorno
           
       Raises:
           NotFoundException: Cuando no se encuentra
       """
   ```

2. **Type hints**: Siempre usar type hints
3. **Comentarios**: Solo cuando sea necesario explicar "por qué", no "qué"

### Nomenclatura

1. **Archivos**: `snake_case.py`
2. **Clases**: `PascalCase`
3. **Funciones/variables**: `snake_case`
4. **Constantes**: `UPPER_SNAKE_CASE`
5. **Private**: Prefijo `_` para métodos/atributos privados

### Logging

1. **Usar loguru**: Importar de `app.core.logging`
   ```python
   from app.core.logging import logger
   
   logger.info("Mensaje", extra={"user_id": str(user_id)})
   ```

2. **Niveles apropiados**:
   - `debug`: Información detallada para debugging
   - `info`: Eventos normales del sistema
   - `warning`: Advertencias, situaciones inesperadas pero manejables
   - `error`: Errores que requieren atención

### Migraciones Alembic

1. **Auto-generar**: `alembic revision --autogenerate -m "mensaje"`
2. **Revisar siempre**: Validar el SQL generado antes de aplicar
3. **Datos de prueba**: No incluir en migraciones, usar scripts separados

### Celery Tasks

1. **Decorador**: Usar `@celery_app.task`
   ```python
   @celery_app.task(name="send_notification")
   def send_notification_task(user_id: str, message: str):
   ```

2. **Idempotencia**: Las tareas deben ser idempotentes
3. **Retry**: Configurar retry para tareas críticas
   ```python
   @celery_app.task(bind=True, max_retries=3)
   def task_with_retry(self):
       try:
           # código
       except Exception as exc:
           raise self.retry(exc=exc, countdown=60)
   ```

## Referencias Rápidas

### Documentación del Proyecto
- Arquitectura: `docs/01_ARQUITECTURA.md`
- Modelo de Datos: `docs/02_MODELO_DATOS.md`
- API Endpoints: `docs/03_API_ENDPOINTS.md`
- Flujo de Estados: `docs/04_FLUJO_ESTADOS.md`
- Stack: `docs/05_STACK_Y_ESTRUCTURA.md`
- Estado del Proyecto: `ESTADO_PROYECTO.md`

### Enums Principales
Ubicación: `app/utils/enums.py` (17 enumeraciones)

**Tipos de Incapacidad**:
- `TipoIncapacidad`: ARL, SALUD
- `SubtipoIncapacidadARL`: ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO
- `SubtipoIncapacidadSalud`: ENFERMEDAD_GENERAL, MATERNIDAD, LICENCIA

**Estados y Workflow**:
- `EstadoIncapacidad`: RADICADA, EN_AUDITORIA, OBSERVADA, APROBADA, RECHAZADA, EN_PAGO, PAGADA, ANULADA
- `EstadoOrdenPago`: GENERADA, APROBADA, RECHAZADA, EN_PROCESO, PAGADA, ANULADA
- `EstadoSiniestro`: REPORTADO, EN_INVESTIGACION, CERRADO, ANULADO
- `EstadoAfiliado`: ACTIVO, INACTIVO, SUSPENDIDO

**Usuarios y Seguridad**:
- `RolUsuario`: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY
- `EstadoUsuario`: ACTIVO, INACTIVO, BLOQUEADO

**Otros**:
- `TipoDocumento`: CEDULA, PASAPORTE, CEDULA_EXTRANJERIA, etc.
- `TipoPoliza`: INDIVIDUAL, FAMILIAR, COLECTIVA
- `TipoDocumentoArchivo`: INCAPACIDAD_MEDICA, HISTORIA_CLINICA, SOPORTE_ARL, etc.
- `TipoCuenta`: AHORROS, CORRIENTE
- `AccionAuditoria`: CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.
- `Prioridad`: BAJA, NORMAL, ALTA, URGENTE

### Modelos Creados (11 modelos completos)
- ✅ `BaseModel`: Modelo base con id (UUID), created_at, updated_at
- ✅ `Usuario`: Autenticación, roles RBAC, bloqueo por intentos fallidos
- ✅ `RefreshToken`: Tokens JWT con hash SHA256 y versioning
- ✅ `Empresa`: Empresas ARL con sincronización externa
- ✅ `Empleado`: Empleados vinculados a empresas (para incapacidades ARL)
- ✅ `Afiliado`: Afiliados con pólizas de salud (para incapacidades SALUD)
- ✅ `Incapacidad`: Modelo principal con workflow polimórfico (ARL/SALUD)
- ✅ `Siniestro`: Accidentes laborales ARL
- ✅ `Documento`: Archivos con hashes MD5/SHA256 y almacenamiento MinIO
- ✅ `HistorialEstado`: Auditoría de cambios de estado (polimórfico)
- ✅ `OrdenPago`: Órdenes de pago con workflow
- ✅ `AuditoriaLog`: Logs de auditoría del sistema

### Comandos Útiles

```bash
# Desarrollo
docker compose up -d                    # Iniciar todos los servicios
docker compose logs -f api              # Ver logs de la API
docker compose restart api              # Reiniciar solo la API
docker compose down                     # Detener todos los servicios

# Base de Datos
docker compose exec postgres psql -U incapacidades_user -d incapacidades_db
# Verificar tablas creadas
docker compose exec api python scripts/check_migrations.py

# Migraciones
docker compose exec api alembic upgrade head                    # Aplicar migraciones
docker compose exec api alembic revision --autogenerate -m "..."  # Crear migración
docker compose exec api alembic current                         # Ver versión actual
docker compose exec api alembic downgrade -1                    # Rollback

# Tests
docker compose exec api pytest                                  # Todos los tests
docker compose exec api pytest test_auth_service.py       # Test específico
docker compose exec api pytest --cov=app                        # Con cobertura
docker compose exec api pytest --cov=app --cov-report=html      # Reporte HTML
docker compose exec api pytest -v -s                            # Verbose con prints

# Linting y Formateo
docker compose exec api black app/                              # Formatear código
docker compose exec api isort app/                              # Ordenar imports
docker compose exec api flake8 app/                             # Linter
docker compose exec api mypy app/                               # Type checking

# MinIO (Storage)
# Acceder a consola: http://localhost:9011
# Credenciales: minioadmin / minioadmin

# RabbitMQ (Queue)
# Acceder a management: http://localhost:15682
# Credenciales: guest / guest

# Flower (Celery Monitor)
# Acceder a UI: http://localhost:5565

# Scripts de Utilidad
docker compose exec api python scripts/seed_test_data.py        # Datos de prueba
docker compose exec api python scripts/create_admin.py          # Crear admin
```

## Estado Actual del Sistema (13 de enero de 2026)

### Progreso Global: 82% 🚀

| Componente | Completado | Pendiente | Prioridad |
|------------|------------|-----------|-----------|
| Modelos SQLAlchemy | 11/11 (100%) | - | ✅ |
| Schemas Pydantic | 11/11 (100%) | - | ✅ |
| Repositories | 8/11 (73%) | Usuario, OrdenPago, Auditoria | 🔴 Alta |
| Services | 8/11 (73%) | Usuario, OrdenPago, Auditoria | 🔴 Alta |
| API Endpoints | 9/11 (82%) | Usuarios, Órdenes de Pago | 🔴 Alta |
| Tests Unitarios | 34 tests | +50 tests | 🟡 Media |
| Tests Integración | 14 tests | +30 tests | 🟡 Media |
| Celery Tasks | Estructura | Implementación completa | 🟡 Media |
| Documentación | 90% | Docs técnicos | 🟢 Baja |

### Módulos 100% Completados ✅
1. **Autenticación JWT** (20 tests, 86-92% cobertura)
   - Login, logout, refresh, change-password
   - Token versioning y revocación
   - Bloqueo automático por intentos fallidos

2. **Gestión de Documentos** (11 tests, 78% cobertura)
   - Upload/download con MinIO
   - Validación de archivos (extensión, MIME, tamaño)
   - Hashing MD5/SHA256
   - Presigned URLs

3. **Historial de Estados** (17 tests)
   - Patrón polimórfico
   - Auto-generación en transiciones
   - Consulta de auditoría

4. **Gestión de Incapacidades** (endpoints completos)
   - CRUD completo
   - Workflow ARL/SALUD
   - Soporte polimórfico empleado/afiliado

5. **Gestión de Empresas y Empleados** (endpoints completos)
   - CRUD completo
   - Importación desde externos
   - Estadísticas

6. **Gestión de Afiliados** (endpoints completos)
   - CRUD con validación de pólizas
   - Búsqueda por documento/póliza

### Infraestructura Operativa ✅
- PostgreSQL 15 con 11 tablas + índices optimizados
- Redis 7 para cache y sesiones
- MinIO para almacenamiento de documentos
- RabbitMQ + Celery para tareas asíncronas
- Docker Compose con 8 servicios (7 healthy, 1 opcional)

## Prioridades Actuales (Actualizado: 13 de enero de 2026)

### ✅ Completado (82% del proyecto)
- ✅ Modelos SQLAlchemy (11/11 modelos)
- ✅ Schemas Pydantic (11/11 schemas)
- ✅ Repositories (8/11): Base, Incapacidad, Empresa, Empleado, Afiliado, Siniestro, Documento, Historial
- ✅ Services (8/11): Auth, Incapacidad, Empresa, Empleado, Afiliado, Siniestro, Documento, Historial
- ✅ Endpoints API (9/11 módulos): Auth, Incapacidades, Empresas, Empleados, Afiliados, Siniestros, Documentos, Historial, Health
- ✅ Autenticación JWT completa con refresh tokens y token versioning
- ✅ Tests (48 tests pasando: 34 unitarios + 14 integración)
- ✅ Migraciones Alembic aplicadas
- ✅ Infraestructura Docker (8 servicios)

### 🔴 Pendiente Crítico (Próximas 2 semanas)

#### 1. Completar Repositories faltantes (1 día)
- `usuario_repository.py` - CRUD + búsqueda por username/email, gestión de tokens
- `orden_pago_repository.py` - CRUD + queries por estado, búsqueda por incapacidad
- `auditoria_log_repository.py` - CRUD + filtros avanzados por fecha, usuario, acción

#### 2. Completar Services faltantes (2 días)
- `usuario_service.py` - Gestión de usuarios y roles
  - Crear/actualizar usuarios
  - Activar/desactivar cuentas
  - Asignar roles (ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY)
  - Reset de contraseña
  - Gestión de intentos fallidos

- `orden_pago_service.py` - Workflow completo de pagos
  - Generar orden desde incapacidad APROBADA
  - Aprobar orden de pago (solo ADMIN)
  - Registrar pago ejecutado
  - Anular orden de pago
  - Transiciones de estado: GENERADA → APROBADA → PAGADA/ANULADA
  - Auto-generación de número de orden
  - Integración con historial de estados

- `auditoria_log_service.py` - Logging de auditoría
  - Registrar acciones críticas
  - Filtros por usuario, acción, fecha
  - Exportación de logs

#### 3. Completar API Endpoints (2 días)
- `/api/v1/usuarios` - CRUD de usuarios (8 endpoints)
- `/api/v1/ordenes-pago` - Workflow de pagos (9 endpoints)
- `/api/v1/auditoria` - Consulta de logs (opcional)

#### 4. Implementar Tareas Celery (2-3 días)
- `email_tasks.py` - Envío de notificaciones por email
- `notification_tasks.py` - Notificaciones in-app
- `report_tasks.py` - Generación de reportes PDF/Excel
- `maintenance_tasks.py` - Limpieza y mantenimiento
- Celery Beat - Tareas programadas

#### 5. Completar Suite de Tests (3 días)
- Tests de repositories faltantes (30+ tests)
- Tests de services completos (50+ tests)
- Tests E2E de workflows (15+ tests)
- Alcanzar >80% cobertura global

#### 6. Seguridad y Optimización (1-2 días)
- Rate limiting en endpoints críticos
- Cache con Redis para queries frecuentes
- Optimización de queries (EXPLAIN ANALYZE)
- Validación exhaustiva de inputs

#### 7. Documentación Final (1 día)
- `docs/06_AUTENTICACION_JWT.md`
- `docs/07_WORKFLOW_ORDENES_PAGO.md`
- `docs/08_DEPLOYMENT.md`
- Manual de usuario por rol

## Notas Importantes

### Modelo de Datos
- **Incapacidades ARL** requieren `empleado_id` + `empresa_id` + opcional `siniestro_id`
- **Incapacidades SALUD** requieren `afiliado_id` (no empleado/empresa)
- **Workflow estricto** de estados con validaciones en cada transición
- **Auditoría completa** registrar todos los cambios en HISTORIAL_ESTADO
- **SLAs configurables** por tipo de estado
- **Integración externa** preparada para sincronización con sistema RRHH
- **Almacenamiento seguro** de documentos con validación de virus

### Cambios Arquitectónicos Importantes

#### Soporte Polimórfico ARL/SALUD
- **Incapacidades ARL**: Requieren `empleado_id` + `empresa_id` + opcional `siniestro_id`
- **Incapacidades SALUD**: Requieren `afiliado_id` (no empleado/empresa)
- **Validación**: Constraint CHECK en base de datos asegura exclusividad
- **Schemas**: `IncapacidadARLCreate` vs `IncapacidadSaludCreate` separados

#### Sistema de Tokens Mejorado
- **Refresh Tokens**: Almacenados con hash SHA256 en base de datos
- **Token Versioning**: Campo `token_version` en Usuario para invalidación masiva
- **Revocación**: Campo `revoked` en RefreshToken para logout individual
- **Expiración**: Access token 15 min, Refresh token 7 días

#### Historial de Estados Polimórfico
- **Relación genérica**: Usando `entity_type` + `entity_id` (UUID genérico)
- **Soporta**: Incapacidad, Siniestro, OrdenPago (extensible)
- **Auto-generación**: Cada transición de estado crea registro automático

### Patrones de Diseño Implementados
1. **Repository Pattern**: Abstracción de acceso a datos con BaseRepository genérico
2. **Service Layer**: Lógica de negocio separada de controllers
3. **Dependency Injection**: FastAPI dependencies para DB, Auth, Permissions
4. **Factory Pattern**: Creación de entidades con validación en services
5. **Strategy Pattern**: Diferentes validadores según tipo (ARL vs SALUD)

## Notas Importantes para el Agente de desarrollo

### Principios Fundamentales
- Asegúrate de seguir la estructura de Clean Architecture en todo momento.
- Prioriza el uso de funciones asíncronas para todas las operaciones de I/O.
- Actualiza la documentación interna y los docstrings conforme avances en el desarrollo.
- Ejecuta los tests después de cada implementación significativa.
- Mantén la cobertura de tests por encima del 70%.

### Entrega de Resultados

Al finalizar cada requerimiento o tarea, SIEMPRE debes entregar:

1. **Resumen Ejecutivo**: Breve descripción de lo completado (2-3 líneas)

2. **Cambios Realizados**: Lista de archivos modificados/creados con descripción

3. **Validación**: 
   - Resultado de tests ejecutados
   - Verificación de que no se introdujeron errores
   - Confirmación de que el código sigue los estándares del proyecto

4. **Actualización Documentación**: Si aplica, se deben actualizar los README.md y ESTADO_PROYECTO.md

5. **Próximos Pasos Sugeridos**: Proporcionar 2-3 opciones de continuación lógica

6. **Prompt Estructurado**: Generar un prompt completo y detallado para el siguiente paso, siguiendo este formato:

```
### PROMPT SUGERIDO PARA EL SIGUIENTE PASO

**Contexto**: [Explicar el contexto actual y por qué este es el siguiente paso lógico]

**Objetivo**: [Describir claramente qué se debe lograr]

**Requerimientos específicos**:
- [Requerimiento 1 con detalles técnicos]
- [Requerimiento 2 con detalles técnicos]
- [Requerimiento 3 con detalles técnicos]
- [etc.]

**Criterios de aceptación**:
- [ ] [Criterio verificable 1]
- [ ] [Criterio verificable 2]
- [ ] [Criterio verificable 3]

**Consideraciones técnicas**:
- [Consideración 1: patrones, dependencias, etc.]
- [Consideración 2: validaciones requeridas]
- [Consideración 3: integración con módulos existentes]

**Tests esperados**:
- [Tipo de tests a crear y cobertura esperada]

**Ejemplo de uso/salida esperada**:
[Código de ejemplo o descripción de la funcionalidad en acción]
```

### Ejemplo de Entrega Completa

```markdown
## ✅ Resumen Ejecutivo
Se implementó el módulo de Historial de Estados con patrón polimórfico, 
incluyendo auto-generación en transiciones y 17 tests (100% passing).

## 📝 Cambios Realizados
- **Modificados** (7 archivos):
  - `app/models/historial_estado.py`: Relación polimórfica con Usuario
  - `app/services/incapacidad_service.py`: Auto-generación de historial (6 métodos)
  - `app/services/siniestro_service.py`: Auto-generación de historial (3 métodos)
  - `app/api/v1/endpoints/incapacidades.py`: Endpoint GET /{id}/historial
  - `app/api/v1/endpoints/siniestros.py`: Endpoint GET /{id}/historial
  - `app/schemas/historial_estado.py`: validation_alias para metadata
  - `tests/conftest.py`: Corrección de fixtures

- **Creados** (4 archivos):
  - `tests/__init__.py`: Package marker
  - `tests/conftest.py`: Fixtures compartidos (177 líneas)
  - test_historial_estado.py: 12 tests unitarios (254 líneas)
  - test_historial_integration.py: 5 tests integración (240 líneas)
  - `pytest.ini`: Configuración de pytest

## ✅ Validación
- Tests ejecutados: 17/17 pasando (100%)
- Cobertura actual: 59% (objetivo: >70%)
- Sin errores de linting
- Endpoints funcionando correctamente

## 🎯 Próximos Pasos Sugeridos

### Opción 1: Módulo de Documentos (Recomendado)
Upload/download de archivos con MinIO, validación de virus, generación de hash MD5.

### Opción 2: Completar Módulo de Órdenes de Pago
Workflow completo, generación automática desde incapacidades aprobadas.

### Opción 3: Incrementar Cobertura de Tests
Agregar tests para módulos existentes (Empresas, Empleados, Afiliados).

---

### PROMPT SUGERIDO PARA EL SIGUIENTE PASO

**Contexto**: El sistema ya cuenta con gestión completa de incapacidades, 
siniestros e historial de estados. El siguiente paso lógico es permitir 
la carga y descarga de documentos adjuntos (certificados médicos, soportes, etc.) 
con almacenamiento seguro en MinIO/S3.

**Objetivo**: Implementar el módulo completo de Documentos siguiendo el patrón 
de Clean Architecture usado en HistorialEstado, con upload a MinIO, validaciones 
de seguridad y gestión de metadatos.

**Requerimientos específicos**:
- Modelo `Documento` con campos: incapacidad_id, siniestro_id, tipo_documento, 
  nombre_archivo, ruta_storage, mime_type, tamanio_bytes, hash_md5, uploaded_by_id
- Schema Pydantic con validación de tipo de archivo permitido (PDF, JPG, PNG, DOCX)
- Repository con métodos: create, get_by_id, list_by_incapacidad, list_by_siniestro, delete
- Service con lógica de upload a MinIO, cálculo de hash MD5, validación de tamaño (<10MB)
- Endpoints REST:
  - POST /api/v1/documentos/upload
  - GET /api/v1/documentos/{id}
  - GET /api/v1/documentos/{id}/download
  - DELETE /api/v1/documentos/{id}
  - GET /api/v1/incapacidades/{id}/documentos
  - GET /api/v1/siniestros/{id}/documentos

**Criterios de aceptación**:
- [ ] Upload de archivos funcional con almacenamiento en MinIO
- [ ] Validación de tipos MIME permitidos
- [ ] Generación automática de hash MD5 para integridad
- [ ] Download de archivos con URL firmada (presigned URL)
- [ ] Soft delete de documentos (no eliminación física)
- [ ] Relación many-to-one con Incapacidad y Siniestro
- [ ] Tests unitarios para service (mocking MinIO)
- [ ] Tests de integración para endpoints (upload/download)
- [ ] Cobertura de tests >70% para el módulo

**Consideraciones técnicas**:
- Usar `minio` library para interacción con MinIO/S3
- Configurar bucket en startup (create_bucket si no existe)
- Generar nombres únicos de archivo con UUID + extensión original
- Validar extensión contra whitelist: ['.pdf', '.jpg', '.jpeg', '.png', '.docx']
- Límite de tamaño: 10MB (configurable en settings)
- Presigned URLs con expiración de 1 hora para downloads
- Integrar con historial de estados (AccionAuditoria.UPLOAD_FILE, DOWNLOAD_FILE)

**Tests esperados**:
- tests/test_documento_service.py: 8-10 tests unitarios (mock MinIO)
- tests/test_documento_api.py: 6-8 tests de integración
- Fixtures: test_documento, mock_minio_client
- Cobertura: >75% para módulo de documentos

**Ejemplo de uso/salida esperada**:
```python
# Upload
POST /api/v1/documentos/upload
Content-Type: multipart/form-data

file: certificado.pdf
incapacidad_id: "uuid"
tipo_documento: "INCAPACIDAD_MEDICA"

Response 201:
{
  "id": "uuid",
  "nombre_archivo": "certificado.pdf",
  "tipo_documento": "INCAPACIDAD_MEDICA",
  "mime_type": "application/pdf",
  "tamanio_bytes": 245680,
  "hash_md5": "5d41402abc4b2a76b9719d911017c592",
  "created_at": "2026-01-09T16:00:00Z"
}

# Download
GET /api/v1/documentos/{id}/download

Response 200:
{
  "url": "https://minio:9000/bucket/documento.pdf?X-Amz-Signature=...",
  "expires_in": 3600
}
```
```
