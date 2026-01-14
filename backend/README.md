# Sistema de Gestión de Incapacidades - Backend API

API REST para gestión integral de incapacidades en aseguradoras, desarrollado con FastAPI, PostgreSQL y arquitectura hexagonal.

## 🏗️ Arquitectura

- **Framework**: FastAPI 0.109+
- **Base de Datos**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache**: Redis 7+
- **Storage**: MinIO/S3
- **Message Queue**: Celery + RabbitMQ
- **Patrón**: Clean Architecture / Hexagonal

## 📋 Características

- ✅ API RESTful con auto-documentación (OpenAPI/Swagger)
- ✅ Autenticación JWT con refresh tokens
- ✅ RBAC (Control de acceso basado en roles)
- ✅ Workflow de estados para incapacidades
- ✅ Carga masiva de datos (CSV/Excel)
- ✅ Almacenamiento seguro de archivos
- ✅ Tareas asíncronas con Celery
- ✅ Logging estructurado
- ✅ Migraciones de BD con Alembic
- ✅ Tests unitarios e integración
- ✅ Docker y Docker Compose

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.11+
- Docker y Docker Compose
- PostgreSQL 15+ (si no usa Docker)
- Redis 7+ (si no usa Docker)

### Instalación con Docker (Recomendado)

```bash
# Clonar repositorio
git clone <repo-url>
cd backend

# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus configuraciones
nano .env

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Aplicar migraciones
docker-compose exec api alembic upgrade head

# Crear superusuario
docker-compose exec api python scripts/create_superuser.py
```

La API estará disponible en:
- API: http://localhost:8010
- Documentación: http://localhost:8010/docs
- ReDoc: http://localhost:8010/redoc
- Flower (Celery): http://localhost:5565
- MinIO Console: http://localhost:9011
- RabbitMQ Management: http://localhost:15682

### Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copiar variables de entorno
cp .env.example .env

# Editar .env
nano .env

# Crear base de datos
createdb incapacidades

# Aplicar migraciones
alembic upgrade head

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── api/                    # Endpoints de la API
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/                   # Configuración core
│   ├── db/                     # Base de datos
│   │   └── repositories/
│   ├── models/                 # Modelos SQLAlchemy
│   ├── schemas/                # Schemas Pydantic
│   ├── services/               # Lógica de negocio
│   ├── tasks/                  # Tareas Celery
│   ├── utils/                  # Utilidades
│   └── middleware/             # Middlewares
├── alembic/                    # Migraciones
├── tests/                      # Tests
├── docs/                       # Documentación
├── scripts/                    # Scripts útiles
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## 🔑 Autenticación

La API utiliza JWT (JSON Web Tokens) para autenticación.

### Obtener Token

```bash
curl -X POST "http://localhost:8010/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "your-password"
  }'
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer"
}
```

### Usar Token

```bash
curl -X GET "http://localhost:8010/api/v1/incapacidades" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 👥 Roles y Permisos

| Rol | Descripción | Permisos Principales |
|-----|-------------|---------------------|
| ADMIN | Administrador del sistema | Acceso completo |
| AUDITOR | Auditor de incapacidades | Auditar, aprobar, rechazar |
| APROBADOR | Aprobador de pagos | Aprobar órdenes de pago |
| EMPRESA | Usuario empresa | Radicar incapacidades propias |
| EMPLEADO | Usuario empleado | Ver incapacidades propias |
| READONLY | Solo lectura | Ver reportes |

## 📊 Flujo de Estados

```
RADICADA → EN_AUDITORIA → OBSERVADA → EN_AUDITORIA → APROBADA → EN_PAGO → PAGADA
                       ↓
                   RECHAZADA
```

Ver [documentación completa de estados](../docs/04_FLUJO_ESTADOS.md).

## 🔧 Comandos Útiles

### Make Commands

```bash
# Ver ayuda
make help

# Desarrollo
make dev                # Iniciar servidor desarrollo
make test               # Ejecutar tests
make lint               # Linter
make format             # Formatear código

# Base de datos
make migrate msg="descripción"  # Crear migración
make upgrade-db         # Aplicar migraciones
make downgrade-db       # Revertir migración

# Docker
make docker-build       # Construir imagen
make docker-up          # Iniciar servicios
make docker-down        # Detener servicios
make docker-logs        # Ver logs
```

## 📦 Sistema de Almacenamiento (Storage)

El sistema soporta dos backends de almacenamiento intercambiables mediante patrón Strategy:

### FileSystem Storage (Predeterminado)

Almacena archivos en el disco local del servidor.

```bash
# Configuración en .env
STORAGE_BACKEND=filesystem
FILESYSTEM_BASE_PATH=/app/storage
FILESYSTEM_SERVE_FILES=true
```

**Estructura de carpetas**:
```
storage/
├── documentos/
│   ├── incapacidades/
│   │   ├── 2026/
│   │   │   ├── 01/
│   │   │   │   ├── abc123-def456.pdf
│   │   │   │   └── xyz789-012345.jpg
│   │   │   └── 02/
│   │   └── 2027/
│   └── siniestros/
│       └── 2026/
└── temp/
```

**Características**:
- ✅ Organización automática por año/mes
- ✅ Permisos restrictivos (644 para archivos, 755 para directorios)
- ✅ Validación de path traversal
- ✅ URLs relativas a la API (`/api/v1/storage/files/{path}`)
- ✅ Sin dependencias externas
- ✅ Ideal para desarrollo y despliegues simples

### MinIO Storage (Opcional)

Almacena archivos en MinIO/S3 compatible.

```bash
# Configuración en .env
STORAGE_BACKEND=minio
STORAGE_ENDPOINT=localhost:9010
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=incapacidades
STORAGE_SECURE=false

# Iniciar con MinIO
docker-compose --profile minio up -d
```

**Características**:
- ✅ S3-compatible (MinIO, AWS S3, DigitalOcean Spaces, etc.)
- ✅ URLs firmadas con expiración
- ✅ Escalabilidad horizontal
- ✅ Ideal para producción con múltiples instancias

### Cambiar Backend de Storage

El cambio es transparente para la aplicación:

```bash
# De FileSystem a MinIO
# 1. Actualizar .env
STORAGE_BACKEND=minio

# 2. Iniciar MinIO
docker-compose --profile minio up -d

# 3. Reiniciar API
docker-compose restart api
```

### Alembic (Migraciones)

```bash
# Crear migración automática
alembic revision --autogenerate -m "Agregar tabla X"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial
alembic history

# Ver migración actual
alembic current
```

### Celery (Tareas Asíncronas)

```bash
# Iniciar worker
celery -A app.tasks.celery_app worker --loglevel=info

# Iniciar beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info

# Iniciar Flower (monitoring)
celery -A app.tasks.celery_app flower
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Ver reporte de cobertura
open htmlcov/index.html
```

## 📝 Migraciones

### Crear Migración

```bash
alembic revision --autogenerate -m "Descripción del cambio"
```

### Aplicar Migraciones

```bash
# Aplicar todas
alembic upgrade head

# Aplicar específica
alembic upgrade +1
```

### Revertir Migración

```bash
alembic downgrade -1
```

## 🔒 Seguridad

- ✅ Hashing de contraseñas con bcrypt
- ✅ JWT con expiración configurable
- ✅ CORS configurado
- ✅ Rate limiting
- ✅ Validación de archivos
- ✅ SQL injection prevention (ORM)
- ✅ XSS prevention
- ✅ HTTPS en producción

## 📊 Monitoreo

### Health Check

```bash
curl http://localhost:8010/health
```

### Métricas (Prometheus)

```bash
curl http://localhost:8010/metrics
```

### Logs

Los logs se almacenan en:
- Consola (desarrollo)
- `logs/app.log` (producción, JSON format)

## 🚀 Deployment

### Producción con Docker

```bash
# Build
docker build -t incapacidades-api:latest .

# Run
docker run -d \
  -p 8010:8000 \
  --env-file .env.production \
  --name incapacidades-api \
  incapacidades-api:latest
```

### Variables de Entorno Importantes

```bash
# Producción
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-secret-key>
DATABASE_URL=<production-db-url>
SENTRY_DSN=<sentry-dsn>
```

## 📚 Documentación

- [Arquitectura](../docs/01_ARQUITECTURA.md)
- [Modelo de Datos](../docs/02_MODELO_DATOS.md)
- [API Endpoints](../docs/03_API_ENDPOINTS.md)
- [Flujo de Estados](../docs/04_FLUJO_ESTADOS.md)
- [Stack Tecnológico](../docs/05_STACK_Y_ESTRUCTURA.md)

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Privado - Todos los derechos reservados

## 👨‍💻 Autor

Sistema de Gestión de Incapacidades - 2026

## 📞 Soporte

Para soporte, contactar al equipo de desarrollo.
