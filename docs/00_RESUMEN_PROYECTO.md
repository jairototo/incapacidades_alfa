# Resumen del Proyecto - Sistema de Gestión de Incapacidades

**Fecha de actualización**: 9 de enero de 2026  
**Versión**: 1.0.0  
**Estado**: En desarrollo activo

---

## 📋 Descripción General

Sistema integral para la gestión del ciclo completo de incapacidades médicas para una aseguradora, abarcando tanto incapacidades de tipo **ARL** (Administradora de Riesgos Laborales) como **SALUD** (seguros de salud).

### Propósito
Automatizar y controlar el flujo de radicación, auditoría, aprobación y pago de incapacidades médicas, garantizando trazabilidad completa, cumplimiento normativo y eficiencia operativa.

---

## 🏗️ Arquitectura Técnica

### Stack Tecnológico
- **Backend**: Python 3.11+, FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0 (async)
- **Base de Datos**: PostgreSQL 15+ (UUID, JSONB, ENUMs)
- **Cache**: Redis 7+
- **Storage**: MinIO/S3
- **Queue**: Celery + RabbitMQ
- **Testing**: Pytest con pytest-asyncio

### Patrón Arquitectónico
**Clean Architecture / Hexagonal Pattern**

```
app/
├── api/v1/endpoints/       # Controladores REST (FastAPI routers)
├── models/                 # Modelos SQLAlchemy (ORM)
├── schemas/                # Schemas Pydantic (validación I/O)
├── services/               # Lógica de negocio
├── db/repositories/        # Acceso a datos (queries)
├── core/                   # Config, seguridad, excepciones
├── middleware/             # Logging, error handling
├── tasks/                  # Tareas asíncronas Celery
└── utils/                  # Enums, helpers
```

### Puertos Configurados
- API: `8010`
- PostgreSQL: `5442`
- Redis: `6389`
- MinIO: `9010` (API), `9011` (Console)
- RabbitMQ: `5682` (AMQP), `15682` (Management)
- Flower: `5565`

---

## 📊 Modelo de Datos Principal

### Entidades Core
1. **EMPRESA**: Empresas afiliadas al sistema ARL
2. **EMPLEADO**: Trabajadores vinculados a empresas
3. **AFILIADO**: Personas aseguradas independientes (pólizas de salud)
4. **INCAPACIDAD**: Registro central de incapacidades médicas
5. **SINIESTRO**: Accidentes laborales (ARL)
6. **HISTORIAL_ESTADO**: Trazabilidad de cambios de estado (polimórfico)
7. **ORDEN_PAGO**: Órdenes de pago generadas
8. **DOCUMENTO**: Archivos adjuntos (certificados, soportes)
9. **USUARIO**: Usuarios del sistema con RBAC

### Relaciones Clave
- **Incapacidad ARL**: `empleado` + `empresa` + `siniestro` (opcional)
- **Incapacidad SALUD**: `afiliado` (sin empleado/empresa)
- **Historial**: Relación polimórfica con `incapacidad` y `siniestro`

---

## 🔄 Workflows Implementados

### 1. Workflow de Incapacidades

```
RADICADA 
    ↓
EN_AUDITORIA 
    ↓
OBSERVADA / APROBADA / RECHAZADA
    ↓
EN_PAGO (solo si APROBADA)
    ↓
PAGADA
```

**Estados disponibles**:
- `RADICADA`: Incapacidad registrada
- `EN_AUDITORIA`: En revisión médica/administrativa
- `OBSERVADA`: Requiere correcciones
- `APROBADA`: Aprobada para pago
- `RECHAZADA`: Rechazada (no procede pago)
- `EN_PAGO`: Orden de pago generada
- `PAGADA`: Pago efectuado
- `CANCELADA`: Cancelada por el usuario

### 2. Workflow de Siniestros (ARL)

```
REPORTADO 
    ↓
EN_INVESTIGACION 
    ↓
CERRADO / ANULADO
```

**Estados disponibles**:
- `REPORTADO`: Siniestro reportado
- `EN_INVESTIGACION`: Investigación activa
- `CERRADO`: Investigación completada
- `ANULADO`: Siniestro anulado

### 3. Workflow de Órdenes de Pago

```
GENERADA 
    ↓
APROBADA / RECHAZADA
    ↓
EN_PROCESO (si APROBADA)
    ↓
PAGADA / ANULADA
```

**Estados disponibles**:
- `GENERADA`: Orden creada automáticamente
- `APROBADA`: Aprobada para procesamiento
- `RECHAZADA`: Rechazada por validaciones
- `EN_PROCESO`: En procesamiento de pago
- `PAGADA`: Pago completado
- `ANULADA`: Orden anulada

---

## 🔐 Seguridad y Permisos

### Roles de Usuario
- **ADMIN**: Acceso total al sistema
- **AUDITOR**: Revisión y auditoría de incapacidades
- **APROBADOR**: Aprobación de pagos
- **EMPRESA**: Consulta de incapacidades de su empresa
- **EMPLEADO**: Consulta de sus propias incapacidades
- **READONLY**: Solo lectura

### Autenticación
- JWT (JSON Web Tokens)
- Tokens de acceso y refresh
- Expiración configurable
- Hash de contraseñas con bcrypt

---

## 📡 API REST

### Endpoints Principales Implementados

#### Empresas
- `GET /api/v1/empresas/` - Listar empresas
- `POST /api/v1/empresas/` - Crear empresa
- `GET /api/v1/empresas/{id}` - Obtener empresa
- `PUT /api/v1/empresas/{id}` - Actualizar empresa
- `DELETE /api/v1/empresas/{id}` - Eliminar empresa

#### Empleados
- `GET /api/v1/empleados/` - Listar empleados
- `POST /api/v1/empleados/` - Crear empleado
- `GET /api/v1/empleados/{id}` - Obtener empleado
- `PUT /api/v1/empleados/{id}` - Actualizar empleado
- `DELETE /api/v1/empleados/{id}` - Eliminar empleado

#### Afiliados
- `GET /api/v1/afiliados/` - Listar afiliados
- `POST /api/v1/afiliados/` - Crear afiliado
- `GET /api/v1/afiliados/{id}` - Obtener afiliado
- `PUT /api/v1/afiliados/{id}` - Actualizar afiliado
- `DELETE /api/v1/afiliados/{id}` - Eliminar afiliado

#### Incapacidades
- `GET /api/v1/incapacidades/` - Listar incapacidades
- `POST /api/v1/incapacidades/` - Crear incapacidad
- `GET /api/v1/incapacidades/{id}` - Obtener incapacidad
- `PUT /api/v1/incapacidades/{id}` - Actualizar incapacidad
- `POST /api/v1/incapacidades/{id}/radicar` - Radicar incapacidad
- `POST /api/v1/incapacidades/{id}/auditar` - Auditar incapacidad
- `POST /api/v1/incapacidades/{id}/aprobar` - Aprobar incapacidad
- `POST /api/v1/incapacidades/{id}/rechazar` - Rechazar incapacidad
- `POST /api/v1/incapacidades/{id}/enviar-pago` - Enviar a pago
- `POST /api/v1/incapacidades/{id}/marcar-pagada` - Marcar como pagada
- `GET /api/v1/incapacidades/{id}/historial` - **Historial de estados**

#### Siniestros
- `GET /api/v1/siniestros/` - Listar siniestros
- `POST /api/v1/siniestros/` - Crear siniestro
- `GET /api/v1/siniestros/{id}` - Obtener siniestro
- `PUT /api/v1/siniestros/{id}` - Actualizar siniestro
- `POST /api/v1/siniestros/{id}/reportar` - Reportar siniestro
- `POST /api/v1/siniestros/{id}/cerrar` - Cerrar siniestro
- `POST /api/v1/siniestros/{id}/anular` - Anular siniestro
- `GET /api/v1/siniestros/{id}/historial` - **Historial de estados**

#### Historial de Estados
- `GET /api/v1/historial/` - Listar todo el historial
- `GET /api/v1/historial/recent` - Cambios recientes
- `GET /api/v1/historial/{entity_type}/{entity_id}` - Historial de entidad
- `GET /api/v1/historial/{entity_type}/{entity_id}/count` - Contar cambios
- `GET /api/v1/historial/{entity_type}/{entity_id}/first` - Primer estado
- `GET /api/v1/historial/{entity_type}/{entity_id}/current` - Estado actual

---

## ✅ Módulos Completados

### 1. ✅ Módulo de Empresas
- CRUD completo
- Validaciones de negocio
- Sincronización externa
- Estados: ACTIVA, INACTIVA, SUSPENDIDA

### 2. ✅ Módulo de Empleados
- CRUD completo
- Relación con empresa
- Validación de documentos únicos
- Estados: ACTIVO, INACTIVO, RETIRADO

### 3. ✅ Módulo de Afiliados
- CRUD completo
- Gestión de pólizas de salud
- Independientes (sin empresa)
- Estados: ACTIVO, INACTIVO, SUSPENDIDO

### 4. ✅ Módulo de Incapacidades
- CRUD completo
- Workflow de estados completo (8 estados)
- Validación de tipo ARL vs SALUD
- Cálculo automático de valores
- Transiciones validadas

### 5. ✅ Módulo de Siniestros
- CRUD completo
- Workflow de estados (4 estados)
- Relación con incapacidades ARL
- Generación automática de número de siniestro
- Gravedad configurable

### 6. ✅ Módulo de Historial de Estados (NUEVO)
- **Implementación polimórfica** (entity_type + entity_id)
- **Auto-generación en transiciones** de estado
- Registro completo de cambios (estado_anterior → estado_nuevo)
- Usuario que realizó el cambio
- Observaciones y metadata
- Endpoints de consulta avanzados
- **17 tests unitarios e integración** (100% pasando)

---

## 🧪 Testing

### Cobertura Actual
- **Tests totales**: 17 tests implementados
- **Cobertura general**: ~59% (objetivo: >70%)
- **Tests pasando**: 17/17 (100%)

### Estructura de Tests
```
tests/
├── __init__.py
├── conftest.py                      # Fixtures compartidos
├── pytest.ini                       # Configuración pytest
├── test_historial_estado.py         # 12 tests unitarios
└── test_historial_integration.py    # 5 tests integración
```

### Fixtures Disponibles
- `db_engine`: Motor de base de datos de test
- `db_session`: Sesión async con rollback automático
- `client`: Cliente HTTP async (httpx)
- `test_empresa`: Empresa de prueba
- `test_empleado`: Empleado de prueba
- `test_afiliado`: Afiliado de prueba

---

## 📦 Enumeraciones del Sistema

### Tipos de Incapacidad
- `ARL`: Incapacidad laboral (requiere empleado + empresa)
- `SALUD`: Incapacidad de salud (requiere afiliado)

### Estados de Incapacidad
- `RADICADA`, `EN_AUDITORIA`, `OBSERVADA`, `APROBADA`, `RECHAZADA`, `EN_PAGO`, `PAGADA`, `CANCELADA`

### Estados de Siniestro
- `REPORTADO`, `EN_INVESTIGACION`, `CERRADO`, `ANULADO`

### Estados de Orden de Pago
- `GENERADA`, `APROBADA`, `RECHAZADA`, `EN_PROCESO`, `PAGADA`, `ANULADA`

### Roles de Usuario
- `ADMIN`, `AUDITOR`, `APROBADOR`, `EMPRESA`, `EMPLEADO`, `READONLY`

### Tipos de Siniestro
- `ACCIDENTE_TRABAJO`, `ENFERMEDAD_LABORAL`, `ACCIDENTE_TRAYECTO`

### Gravedad de Siniestro
- `LEVE`, `MODERADO`, `GRAVE`, `MORTAL`

---

## 🔧 Configuración Actual

### Variables de Entorno Clave
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/incapacidades
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
```

### Base de Datos
- **Producción**: `incapacidades`
- **Testing**: `incapacidades_test`
- **Migraciones**: Alembic (5 migraciones aplicadas)

---

## 📈 Estado del Proyecto

### Completado ✅
1. Arquitectura base (Clean Architecture)
2. Modelos SQLAlchemy completos
3. Schemas Pydantic con validaciones
4. Repositorios base y especializados
5. Services con lógica de negocio
6. Endpoints REST (CRUD + Transiciones)
7. Workflow de estados con validaciones
8. Historial de estados polimórfico
9. Sistema de autenticación JWT
10. Middleware de logging y error handling
11. Migraciones Alembic
12. Tests unitarios e integración

### En Progreso 🔄
1. Módulo de Documentos (upload MinIO)
2. Módulo de Órdenes de Pago (workflow completo)
3. Módulo de Usuarios (CRUD + permisos)
4. Sistema de notificaciones (email/webhook)
5. Auditoría completa (AUDITORIA_LOG)
6. Incrementar cobertura de tests (>70%)

### Pendiente 📋
1. Dashboard de métricas
2. Reportes (PDF/Excel)
3. Integración con sistemas externos RRHH
4. Validación de virus en documentos
5. SLAs configurables por estado
6. Sistema de alertas y notificaciones
7. API GraphQL (opcional)
8. WebSockets para actualizaciones en tiempo real

---

## 🎯 Próximos Pasos Recomendados

### Paso 1: Módulo de Documentos
**Descripción**: Implementar upload, download y gestión de documentos adjuntos con almacenamiento en MinIO.

**Prompt sugerido**:
```
Implementar el módulo de Documentos con las siguientes características:
- Upload de archivos a MinIO/S3
- Validación de tipos permitidos (PDF, JPG, PNG, DOCX)
- Generación de hash MD5 para integridad
- Relación con incapacidades y siniestros
- Endpoints: POST /upload, GET /download/{id}, DELETE /{id}
- Validación de tamaño máximo (10MB)
- Seguir el patrón de Clean Architecture usado en HistorialEstado
```

### Paso 2: Completar Módulo de Órdenes de Pago
**Descripción**: Implementar workflow completo de órdenes de pago con validaciones y estados.

**Prompt sugerido**:
```
Completar el módulo de Órdenes de Pago con:
- CRUD completo de órdenes de pago
- Workflow de estados (GENERADA → APROBADA → EN_PROCESO → PAGADA)
- Generación automática desde incapacidades aprobadas
- Validaciones de datos bancarios
- Integración con historial de estados
- Cálculo de valores y descuentos
- Tests unitarios e integración
```

### Paso 3: Módulo de Usuarios Completo
**Descripción**: Finalizar gestión de usuarios con RBAC completo.

**Prompt sugerido**:
```
Implementar gestión completa de usuarios:
- CRUD de usuarios
- Asignación de roles (ADMIN, AUDITOR, APROBADOR, etc.)
- Sistema de permisos granulares (PermissionChecker)
- Cambio de contraseña con validaciones
- Activación/desactivación de usuarios
- Auditoría de acciones de usuario
- Login/logout con JWT tokens
- Tests de autenticación y autorización
```

---

## 📚 Documentación Disponible

- [01_ARQUITECTURA.md](./01_ARQUITECTURA.md) - Arquitectura detallada del sistema
- [02_MODELO_DATOS.md](./02_MODELO_DATOS.md) - Modelo de datos completo
- [03_API_ENDPOINTS.md](./03_API_ENDPOINTS.md) - Documentación de API
- [04_FLUJO_ESTADOS.md](./04_FLUJO_ESTADOS.md) - Workflows y transiciones
- [05_STACK_Y_ESTRUCTURA.md](./05_STACK_Y_ESTRUCTURA.md) - Stack técnico

---

## 👥 Contribución

### Estándares de Código
- **Python**: PEP 8, type hints obligatorios
- **Async**: Usar async/await para I/O operations
- **Imports**: Ordenados con isort
- **Formato**: Black para formateo automático
- **Docstrings**: Google style
- **Tests**: Pytest con coverage >70%

### Convenciones de Nombres
- **Archivos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones/variables**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Private**: Prefijo `_` para métodos/atributos privados

---

**Última actualización**: 9 de enero de 2026  
**Responsable**: Equipo de Desarrollo
