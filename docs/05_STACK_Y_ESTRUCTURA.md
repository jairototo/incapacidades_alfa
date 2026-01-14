# Stack Tecnológico y Estructura del Proyecto

## 1. Stack Tecnológico Recomendado

### 1.1 Backend

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Lenguaje | Python | 3.11+ | Alto rendimiento, ecosistema maduro |
| Framework Web | FastAPI | 0.109+ | Async, auto-documentación, validación |
| ORM | SQLAlchemy | 2.0+ | Potente, soporta async |
| Migraciones DB | Alembic | 1.13+ | Integración con SQLAlchemy |
| Validación | Pydantic | 2.5+ | Validación de datos robusta |
| Autenticación | python-jose, passlib | Latest | JWT, hashing seguro |
| API Client | httpx | Latest | HTTP async client |
| Tasks Queue | Celery | 5.3+ | Tareas asíncronas |
| Message Broker | RabbitMQ / Redis | Latest | Para Celery |

### 1.2 Base de Datos

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| RDBMS | PostgreSQL | 15+ | ACID, JSON, extensiones |
| Cache | Redis | 7+ | In-memory, pub/sub |
| Search | Elasticsearch | 8+ | Búsqueda full-text |

### 1.3 Storage y Archivos

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Object Storage | MinIO / S3 | Latest | Compatible S3, auto-hosted |
| Antivirus | ClamAV | Latest | Escaneo de archivos |

### 1.4 Infraestructura

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Containerización | Docker | 24+ | Portabilidad |
| Orquestación | Docker Compose / K8s | Latest | Desarrollo / Producción |
| Proxy Reverso | Nginx | 1.25+ | Load balancing, SSL |
| API Gateway | Kong / Traefik | Latest | Gateway empresarial |

### 1.5 Monitoreo y Logging

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Logging | Loguru / structlog | Latest | Logging estructurado |
| Metrics | Prometheus | Latest | Métricas time-series |
| Dashboards | Grafana | Latest | Visualización |
| APM | Sentry | Latest | Error tracking |
| Tracing | Jaeger | Latest | Distributed tracing |

### 1.6 Testing

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Testing | pytest | 7+ | Framework de testing |
| Coverage | pytest-cov | Latest | Cobertura de tests |
| HTTP Testing | httpx, pytest-asyncio | Latest | Testing async |
| Mocking | pytest-mock | Latest | Mocking |

### 1.7 DevOps

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| CI/CD | GitLab CI / GitHub Actions | Latest | Automatización |
| IaC | Terraform | 1.6+ | Infraestructura como código |
| Config Management | Ansible | Latest | Configuración servidores |

## 2. Estructura del Proyecto Backend

```
incapacidades-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Punto de entrada FastAPI
│   │
│   ├── api/                         # Capa de API
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dependencias compartidas
│   │   │
│   │   └── v1/                      # API versión 1
│   │       ├── __init__.py
│   │       ├── router.py            # Router principal v1
│   │       │
│   │       └── endpoints/           # Endpoints por módulo
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           ├── empresas.py
│   │           ├── empleados.py
│   │           ├── incapacidades.py
│   │           ├── documentos.py
│   │           ├── ordenes_pago.py
│   │           ├── usuarios.py
│   │           ├── integraciones.py
│   │           ├── reportes.py
│   │           └── health.py
│   │
│   ├── core/                        # Configuración y utilidades core
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (Pydantic BaseSettings)
│   │   ├── security.py              # JWT, hashing, permisos
│   │   ├── logging.py               # Configuración de logs
│   │   ├── events.py                # Event handlers (startup/shutdown)
│   │   └── exceptions.py            # Excepciones personalizadas
│   │
│   ├── db/                          # Capa de base de datos
│   │   ├── __init__.py
│   │   ├── base.py                  # Base de SQLAlchemy
│   │   ├── session.py               # Sesión de DB
│   │   ├── init_db.py               # Inicialización
│   │   │
│   │   └── repositories/            # Patrón Repository
│   │       ├── __init__.py
│   │       ├── base.py              # Repository base
│   │       ├── empresa.py
│   │       ├── empleado.py
│   │       ├── incapacidad.py
│   │       ├── documento.py
│   │       ├── orden_pago.py
│   │       ├── usuario.py
│   │       └── auditoria.py
│   │
│   ├── models/                      # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── base.py                  # Base model con campos comunes
│   │   ├── empresa.py
│   │   ├── empleado.py
│   │   ├── incapacidad.py
│   │   ├── documento.py
│   │   ├── orden_pago.py
│   │   ├── usuario.py
│   │   ├── historial_estado.py
│   │   ├── auditoria_log.py
│   │   ├── tipo_documento_catalogo.py
│   │   └── parametro.py
│   │
│   ├── schemas/                     # Pydantic schemas (DTOs)
│   │   ├── __init__.py
│   │   ├── common.py                # Schemas comunes
│   │   ├── empresa.py               # EmpresaCreate, EmpresaUpdate, EmpresaInDB
│   │   ├── empleado.py
│   │   ├── incapacidad.py
│   │   ├── documento.py
│   │   ├── orden_pago.py
│   │   ├── usuario.py
│   │   ├── auth.py                  # Token, Login
│   │   └── responses.py             # Schemas de respuestas estándar
│   │
│   ├── services/                    # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── base.py                  # Service base
│   │   ├── auth_service.py
│   │   ├── empresa_service.py
│   │   ├── empleado_service.py
│   │   ├── incapacidad_service.py
│   │   ├── documento_service.py
│   │   ├── orden_pago_service.py
│   │   ├── usuario_service.py
│   │   ├── workflow_service.py      # Gestión de estados
│   │   ├── notification_service.py
│   │   ├── storage_service.py       # MinIO/S3
│   │   ├── integration_service.py   # APIs externas
│   │   └── report_service.py
│   │
│   ├── tasks/                       # Tareas Celery
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Configuración Celery
│   │   ├── empresa_tasks.py         # Sync empresas
│   │   ├── empleado_tasks.py        # Sync empleados
│   │   ├── notification_tasks.py    # Envío de notificaciones
│   │   ├── file_tasks.py            # Procesamiento archivos
│   │   └── report_tasks.py          # Generación reportes
│   │
│   ├── utils/                       # Utilidades
│   │   ├── __init__.py
│   │   ├── validators.py            # Validadores personalizados
│   │   ├── formatters.py            # Formateo de datos
│   │   ├── constants.py             # Constantes
│   │   ├── enums.py                 # Enumeraciones
│   │   ├── file_utils.py            # Utilidades de archivos
│   │   └── date_utils.py            # Utilidades de fechas
│   │
│   └── middleware/                  # Middlewares
│       ├── __init__.py
│       ├── auth_middleware.py
│       ├── logging_middleware.py
│       ├── cors_middleware.py
│       ├── rate_limit_middleware.py
│       └── error_handler.py
│
├── alembic/                         # Migraciones de DB
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── README
│
├── tests/                           # Tests
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures de pytest
│   │
│   ├── unit/                        # Tests unitarios
│   │   ├── __init__.py
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_utils/
│   │
│   ├── integration/                 # Tests de integración
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_db/
│   │
│   └── e2e/                         # Tests end-to-end
│       ├── __init__.py
│       └── test_workflows/
│
├── scripts/                         # Scripts útiles
│   ├── init_db.py                   # Inicializar DB
│   ├── create_superuser.py          # Crear admin
│   ├── import_data.py               # Importar datos
│   └── backup_db.sh                 # Backup
│
├── docs/                            # Documentación
│   ├── 01_ARQUITECTURA.md
│   ├── 02_MODELO_DATOS.md
│   ├── 03_API_ENDPOINTS.md
│   ├── 04_FLUJO_ESTADOS.md
│   ├── 05_DEPLOYMENT.md
│   └── images/
│
├── .github/                         # GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── .env.example                     # Variables de entorno ejemplo
├── .gitignore
├── .dockerignore
├── Dockerfile                       # Dockerfile para producción
├── Dockerfile.dev                   # Dockerfile para desarrollo
├── docker-compose.yml               # Compose para desarrollo
├── docker-compose.prod.yml          # Compose para producción
├── requirements.txt                 # Dependencias base
├── requirements-dev.txt             # Dependencias desarrollo
├── pyproject.toml                   # Configuración proyecto (poetry/ruff)
├── pytest.ini                       # Configuración pytest
├── alembic.ini                      # Configuración Alembic
├── README.md                        # Documentación principal
└── Makefile                         # Comandos útiles
```

## 3. Explicación de la Estructura

### 3.1 Capa de API (`app/api/`)

**Responsabilidad**: Gestión de endpoints HTTP, validación de requests, serialización de responses.

- **v1/endpoints/**: Cada archivo contiene los endpoints relacionados con un módulo específico
- **deps.py**: Dependencias compartidas (autenticación, permisos, sesión DB)
- **router.py**: Enrutador principal que agrupa todos los endpoints

### 3.2 Capa Core (`app/core/`)

**Responsabilidad**: Configuración central, seguridad, eventos del sistema.

- **config.py**: Settings con Pydantic (lee de variables de entorno)
- **security.py**: JWT, hashing de passwords, RBAC
- **logging.py**: Configuración de logging estructurado
- **events.py**: Handlers de startup/shutdown (conexiones DB, etc.)

### 3.3 Capa de Base de Datos (`app/db/`)

**Responsabilidad**: Acceso a datos mediante patrón Repository.

- **repositories/**: Implementa operaciones CRUD y queries específicas
- **session.py**: Factory de sesiones de DB (async)
- **base.py**: Configuración de SQLAlchemy

### 3.4 Modelos (`app/models/`)

**Responsabilidad**: Definición de tablas de base de datos (SQLAlchemy ORM).

- Cada archivo define un modelo/tabla
- Relaciones entre modelos
- Validaciones a nivel de DB

### 3.5 Schemas (`app/schemas/`)

**Responsabilidad**: Validación y serialización de datos (Pydantic).

- **XxxCreate**: Datos para crear entidad
- **XxxUpdate**: Datos para actualizar entidad
- **XxxInDB**: Representación completa desde DB
- **XxxResponse**: Datos para respuesta API

### 3.6 Servicios (`app/services/`)

**Responsabilidad**: Lógica de negocio, orquestación de operaciones.

- Coordinan operaciones entre múltiples repositorios
- Implementan reglas de negocio
- Gestionan transacciones
- Interactúan con servicios externos

### 3.7 Tasks (`app/tasks/`)

**Responsabilidad**: Tareas asíncronas con Celery.

- Procesamiento de archivos
- Sincronización con sistemas externos
- Envío de notificaciones
- Generación de reportes pesados

### 3.8 Middleware (`app/middleware/`)

**Responsabilidad**: Procesamiento de requests/responses.

- Autenticación
- Logging de requests
- CORS
- Rate limiting
- Manejo global de errores

## 4. Patrones de Diseño Aplicados

### 4.1 Repository Pattern

```python
# app/db/repositories/base.py
class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: UUID) -> Optional[T]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, obj_in: dict) -> T:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
```

### 4.2 Service Layer Pattern

```python
# app/services/base.py
class BaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute_in_transaction(self, func):
        async with self.db.begin():
            return await func()
```

### 4.3 Dependency Injection

```python
# app/api/deps.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    # Validar token y retornar usuario
    ...

# En endpoint
@router.get("/incapacidades")
async def list_incapacidades(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    ...
```

### 4.4 Factory Pattern

```python
# app/services/factory.py
class ServiceFactory:
    @staticmethod
    def get_incapacidad_service(db: AsyncSession) -> IncapacidadService:
        return IncapacidadService(
            repository=IncapacidadRepository(db),
            workflow_service=WorkflowService(db),
            notification_service=NotificationService()
        )
```

## 5. Configuración de Entorno

### 5.1 Variables de Entorno (.env.example)

```bash
# Application
APP_NAME=Incapacidades API
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/incapacidades
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Storage (MinIO/S3)
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=incapacidades
STORAGE_SECURE=false

# Celery
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@incapacidades.com
SMTP_PASSWORD=
SMTP_TLS=true
EMAIL_FROM=noreply@incapacidades.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Sentry
SENTRY_DSN=

# External APIs
API_RRHH_BASE_URL=https://api.rrhh.com
API_RRHH_API_KEY=
```

## 6. Comandos Útiles (Makefile)

```makefile
.PHONY: help install dev test lint format migrate upgrade-db run docker-build

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make migrate       - Create migration"
	@echo "  make upgrade-db    - Apply migrations"
	@echo "  make run           - Run production server"
	@echo "  make docker-build  - Build Docker image"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	ruff check app/
	mypy app/

format:
	ruff format app/
	ruff check --fix app/

migrate:
	alembic revision --autogenerate -m "$(msg)"

upgrade-db:
	alembic upgrade head

downgrade-db:
	alembic downgrade -1

run:
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

docker-build:
	docker build -t incapacidades-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

shell:
	python -m app.db.init_db

create-superuser:
	python scripts/create_superuser.py
```

## 7. Dependencias Principales

### requirements.txt

```txt
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
psycopg2-binary==2.9.9

# Redis
redis==5.0.1
hiredis==2.3.2

# Pydantic
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP Client
httpx==0.26.0

# Celery
celery==5.3.4
flower==2.0.1

# Storage
minio==7.2.3
boto3==1.34.23

# Email
fastapi-mail==1.4.1

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# Logging
loguru==0.7.2
```

### requirements-dev.txt

```txt
# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0

# Linting & Formatting
ruff==0.1.14
mypy==1.8.0
black==24.1.0

# Type stubs
types-python-dateutil==2.8.19.20240106
types-pytz==2023.3.1.1

# Development
ipython==8.20.0
ipdb==0.13.13
```
