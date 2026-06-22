# Arquitectura del Sistema - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026

---

> **Nota (2026-06-20) — Radicación del Portal Externo:** la radicación desde el
> Portal Externo (empresa autenticada, individual y masiva) **ya no pasa por
> `pre_incapacidad`**. Usa un `RadicacionPipelineService` compartido que crea la
> `Incapacidad` directamente y dispara la auditoría (`RADICADA → EN_AUDITORIA`).
> El servicio `pre_incapacidad_service` y el job `procesar_pre_incapacidades`/
> `promote_pre_incapacidad_task` descritos abajo corresponden al flujo legado de
> pre-incapacidad (aún presente en el backend), no al portal actual. Integraciones
> ServiAlfa/Sicat son **STUB**. Ver
> [`superpowers/PR-portal-externo-empresa-refactor.md`](./superpowers/PR-portal-externo-empresa-refactor.md).

---

## Visión de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      PORTAL PÚBLICO                          │
│         (React Vite - Portal Externo Radicación)            │
│                   Consulta sin login                         │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┴──────────────────┐
    │                                   │
┌───▼─────────────────┐    ┌──────────▼────────────┐
│   NGINX PROXY       │    │  SISTEMA INTERNO      │
│   (Puerto 80/443)   │    │  (React Dashboard)    │
└───┬─────────────────┘    │  (Fase 3 - Desarrollo)
    │                      └──────────┬────────────┘
    │                                 │
    └─────────────────┬───────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   FASTAPI Backend         │
        │   (Puerto 8010)           │
        │   ✅ Fase 2 Completado   │
        └─────────────┬─────────────┘
        ┌─────────────▼─────────────────────────────────┐
        │         SERVICIOS BACKEND (Python)            │
        ├────────────────────────────────────────────┤
        │ - Autenticación (JWT + RBAC)               │
        │ - Lógica de Negocio                        │
        │ - Validaciones                             │
        │ - Integración Datos                        │
        └──────┬─────────────────────────┬───────────┘
               │                         │
    ┌──────────▼────────────────┐  ┌───▼──────────────────┐
    │ PostgreSQL 15+            │  │  Redis Cache/Session │
    │ - 17 Tablas              │  │  (Puerto 6389)       │
    │ - Auditoría Completa     │  │  - Sesiones JWT      │
    │ - Relaciones Polimórficas│  │  - Caché Consultas  │
    └───────────────────────────┘  └───────────────────────┘

    ┌──────────────────────────────────────────────────────┐
    │           COMPONENTES ADICIONALES                    │
    ├──────────────────────────────────────────────────────┤
    │ - MinIO/S3: Almacenamiento Documentos               │
    │ - RabbitMQ: Message Broker (Puerto 5682)            │
    │ - Celery: Task Queue - Procesamiento Batch          │
    │ - Email Service: Notificaciones (SMTP)              │
    │ - Job Scheduler: Cron Tasks (cada 5 min, etc)      │
    └──────────────────────────────────────────────────────┘
```

---

## Capas de Arquitectura

### 1. Presentation Layer (Frontend)

**Portal Público (React 19 + TypeScript)**:
- Radicación: Wizard 6 pasos
- Consulta: Estado incapacidad
- Responsive: Mobile-first
- Testing: Vitest 300+ tests
- Bundle: 520KB optimizado (gzip)

**Sistema Interno (React 19 - Fase 3)**:
- Dashboard: Métricas en tiempo real
- Bandeja Auditoría: Gestión incapacidades
- Bandeja Órdenes: Aprobación pagos
- Reportes: Exportación Excel/PDF
- Testing: Vitest + Testing Library

**Build & Deploy**:
- Vite: Bundling, HMR
- Docker: Contenedor Node + Nginx
- CDN: CloudFlare/AWS CloudFront (futuro)

### 2. API Layer (FastAPI)

**Routing** (Clean Architecture):
```
/api/v1/
├── auth/              # Autenticación (login, logout, refresh)
├── incapacidades/     # Gestión incapacidades
├── ordenes-pago/      # Órdenes de pago
├── documentos/        # Upload/download
├── usuarios/          # Gestión usuarios (ADMIN)
├── empresas/          # Gestión empresas
├── empleados/         # Gestión empleados
├── afiliados/         # Gestión afiliados
├── siniestros/        # Gestión siniestros
├── reportes/          # Reportes
├── estadisticas/      # Métricas
├── catalogos/         # Catálogos (CIE-10)
└── health/            # Health check
```

**Validación**:
- Pydantic v2: Schemas en request/response
- Validadores custom: Email, documento, CIE-10
- Error handling: ExceptionHandler global

**Autenticación**:
- JWT (HS256): 15 min expiry
- Refresh token: 7 días, SHA256-hashed
- RBAC: 6 roles con permisos granulares
- Rate limiting: 100 req/min por IP

### 3. Business Logic Layer (Services)

**Módulos de Servicios**:
- `auth_service`: Autenticación, validación credenciales
- `incapacidad_service`: CRUD + transiciones estado, validaciones negocio
- `orden_pago_service`: Generación, aprobación, procesamiento pagos
- `documento_service`: Upload, almacenamiento, validación
- `pre_incapacidad_service`: Procesamiento radicaciones pendientes
- `solicitante_service`: Gestión solicitantes
- `historial_estado_service`: Auditoría de transiciones
- `auditoria_service`: Logs de auditoría
- `catalogo_service`: Gestión catálogos (CIE-10)
- `usuario_service`: Gestión usuarios
- `reporte_service`: Generación reportes

**Patrones**:
- Async/await: I/O no bloqueante
- Dependency Injection: FastAPI Depends
- Error handling: Custom exceptions
- Logging: Loguru structured logs

### 4. Data Access Layer (Repositories)

**Patrones**:
- SQLAlchemy ORM 2.0: Async queries
- Type hints: Full type safety
- Batch queries: DISTINCT ON, optimizadas
- Índices: 30+ índices estratégicos
- Transactions: Acid compliance

**Repositorios**:
- `IncapacidadRepository`: Búsqueda, filtrado, estado
- `OrdenPagoRepository`: Órdenes con filtros
- `DocumentoRepository`: Archivos adjuntos
- `UsuarioRepository`: Usuarios y permisos
- `HistorialEstadoRepository`: Auditoría polimórfica

### 5. Data Layer (PostgreSQL)

**Tablas Principales** (17):
```
Usuarios:
  - USUARIO (autenticación, roles)
  - REFRESH_TOKEN (renovación sesión)

Datos Empresariales:
  - EMPRESA (ARL/SALUD)
  - EMPLEADO (empleados de empresas ARL)
  - AFILIADO (asegurados pólizas SALUD)

Incapacidades:
  - INCAPACIDAD (central - ARL/SALUD polimórfica)
  - PRE_INCAPACIDAD (radicaciones pendientes)
  - SINIESTRO (accidentes laborales ARL)

Documentos:
  - DOCUMENTO (archivos adjuntos)
  - PRE_DOCUMENTO (documentos pre-radicación)

Pagos:
  - ORDEN_PAGO (órdenes de pago)

Auditoría:
  - HISTORIAL_ESTADO (transiciones estado - polimórfico)
  - AUDITORIA_LOG (log de auditoría)
  - AUDITORIA_DATOS_APROBADOS (snapshot en aprobación)

Catálogos:
  - CATALOGO_CIE10 (diagnósticos)
  - SOLICITANTE (personas que radican)

Migraciones:
  - ALEMBIC_VERSION (control de versiones)
```

**Características**:
- UUID primary keys
- TIMESTAMP with timezone
- JSONB para datos flexibles
- ENUM types PostgreSQL
- CHECK constraints para validaciones
- Foreign keys con cascadas lógicas

### 6. Storage Layer

**Tipos de Almacenamiento**:

1. **Documentos Adjuntos**:
   - MinIO/S3 compatible
   - Bucket: `incapacidades-{env}`
   - Ruta: `{tipo}/{año}/{mes}/{uuid}.{ext}`
   - Versionado: SÍ
   - Validación: SHA256 hash

2. **Archivos de Configuración**:
   - En PostgreSQL (JSONB)
   - Ejemplo: metadata_ en EMPRESA, EMPLEADO

3. **Logs de Auditoría**:
   - PostgreSQL AUDITORIA_LOG (inmutable)
   - Retención: 12 meses + archivado

### 7. Task Queue (Celery + RabbitMQ)

**Tasks Asíncronas**:
- `procesar_pre_incapacidades`: Job cada 5 min, valida y crea INCAPACIDAD
- `procesar_pagos`: Job cada 2 horas, envía a banco
- `enviar_email_notificacion`: Notificaciones evento
- `generar_reporte_excel`: Reportes grandes
- `backup_db`: Backup diario 23:00

**Configuración**:
- Broker: RabbitMQ (Puerto 5682)
- Flower UI: Monitor tasks (Puerto 5565)
- Retry: Exponential backoff
- Timeout: 10 minutos por defecto

---

## Flujos Principales

### Flujo 1: Radicación → Procesamiento

```
1. Usuario Portal → Wizard Radicación (6 pasos)
   ├─ Paso 1: Solicitante
   ├─ Paso 2: Empresa (búsqueda/ingreso)
   ├─ Paso 3: Empleado (búsqueda/ingreso)
   ├─ Paso 4: Datos Médicos (CIE-10, fechas)
   ├─ Paso 5: Upload Documentos
   └─ Paso 6: Confirmación

2. POST /api/v1/incapacidades/consulta
   ├─ Validación Pydantic
   ├─ Creación PRE_INCAPACIDAD (PENDIENTE)
   ├─ Creación PRE_DOCUMENTO
   └─ Email confirmación

3. Job: procesar_pre_incapacidades (cada 5 min)
   ├─ Select PRE_INCAPACIDAD estado=PENDIENTE
   ├─ Validación + búsqueda/creación EMPRESA, EMPLEADO, etc.
   ├─ Si OK: crear INCAPACIDAD (RADICADA) + DOCUMENTO
   ├─ Si error: PRE_INCAPACIDAD.estado=RECHAZADA/ERROR
   └─ Email resultado

4. AUDITORIA_LOG: CREATE incapacidad
5. Email: "Radicación procesada" a solicitante
```

### Flujo 2: Auditoría → Aprobación

```
1. AUDITOR: GET /api/v1/incapacidades/bandeja-auditoria
   └─ Filtra INCAPACIDAD estado IN [RADICADA, EN_AUDITORIA]

2. AUDITOR: GET /api/v1/incapacidades/{id}
   ├─ Datos completos
   ├─ Documentos adjuntos
   └─ Historial estado

3. AUDITOR: POST /api/v1/incapacidades/{id}/aprobar
   ├─ Validación: documentos validados, datos correctos
   ├─ Cambio estado: RADICADA → EN_AUDITORIA → APROBADA
   ├─ Crear AUDITORIA_DATOS_APROBADOS (snapshot)
   ├─ Registrar HISTORIAL_ESTADO
   └─ Email: "Incapacidad aprobada"

4. AUDITORIA_LOG: CAMBIO_ESTADO
5. Email: Notificación a APROBADOR
```

### Flujo 3: Generación Orden Pago → Confirmación

```
1. ADMIN: POST /api/v1/incapacidades/{id}/generar-orden-pago
   ├─ Validar INCAPACIDAD.estado = APROBADA
   ├─ Crear ORDEN_PAGO (OP-2026-000001)
   ├─ Cambio estado: APROBADA → EN_PAGO
   └─ Email: Orden generada

2. APROBADOR: GET /api/v1/ordenes-pago/bandeja
   ├─ Filtra ORDEN_PAGO estado=GENERADA
   └─ Selecciona para revisar

3. APROBADOR: POST /api/v1/ordenes-pago/{id}/aprobar
   ├─ Validaciones: beneficiario, banco, cuenta
   ├─ Cambio estado: GENERADA → APROBADA
   └─ Email: Orden aprobada

4. Job: procesar_pagos (cada 2 horas)
   ├─ SELECT ORDEN_PAGO estado=APROBADA
   ├─ Envía a banco (ACH, SPEI, etc.)
   ├─ Si OK: estado → EN_PROCESO
   └─ Si error: estado → ANULADA

5. APROBADOR: POST /api/v1/ordenes-pago/{id}/confirmar-pago
   ├─ Upload comprobante
   ├─ Cambio estado: EN_PROCESO → PAGADA
   ├─ INCAPACIDAD.estado → PAGADA
   └─ Email: "Pago completado"

6. AUDITORIA_LOG: Todos los cambios registrados
```

---

## Decisiones Arquitectónicas

### D-001: Incapacidad Polimórfica (ARL vs SALUD)
- **Justificación**: Dos flujos paralelos de negocio
- **Solución**: CHECK constraint + lógica en servicios
- **Trade-off**: Más complejidad pero cohesión de datos

### D-002: PRE_INCAPACIDAD Temporal
- **Justificación**: Desacoplar radicación del procesamiento
- **Solución**: Tabla intermedia, job procesador
- **Beneficio**: No bloquea nuevas radicaciones, retry automático

### D-003: HISTORIAL_ESTADO Polimórfico
- **Justificación**: Auditar múltiples entidades (Incapacidad, Siniestro, OrdenPago)
- **Solución**: Campos entity_type + entity_id (no FK)
- **Ventaja**: Flexibilidad, sin cambios de schema

### D-004: JWT + Token Version
- **Justificación**: Invalidación en masa sin tocar base de datos
- **Solución**: token_version en USUARIO, verificar al validar JWT
- **Ventaja**: Control fino sin eliminar tokens

### D-005: Async/Await en FastAPI
- **Justificación**: Escalabilidad con I/O no bloqueante
- **Solución**: SQLAlchemy async, Celery tasks
- **Beneficio**: Soportar 1000+ concurrentes en instancia de 2 CPU

### D-006: MinIO para Documentos
- **Justificación**: Almacenamiento escalable, no base de datos
- **Solución**: S3-compatible, metadata en PostgreSQL
- **Ventaja**: Separación responsabilidades, fácil backup

### D-007: Celery para Procesos Batch
- **Justificación**: Procesamiento asincrónico, retry automático
- **Solución**: RabbitMQ broker, Celery worker
- **Beneficio**: Desacoplamiento, resilencia

---

## Performance y Escalabilidad

### Métricas Objetivo
- API response: < 200ms (p95)
- Throughput: 1,000 req/min
- Usuarios concurrentes: 500+
- Almacenamiento: 1TB+ documentos
- Retención datos: 7+ años

### Optimizaciones Implementadas
- ✅ Índices en FK y campos búsqueda
- ✅ Conexión pooling PostgreSQL (20 connections)
- ✅ Redis caché para sesiones
- ✅ Batch queries (DISTINCT ON)
- ✅ Paginación (limit 100 máximo)
- ✅ Vite bundle minificado
- ✅ Compression gzip en Nginx

### Escalabilidad Horizontal
- Docker multi-instancia: LB con Nginx
- PostgreSQL: Read replicas (futuro)
- Redis: Sentinel/Cluster (futuro)
- RabbitMQ: Clustering (futuro)

---

## Seguridad

### Capas de Seguridad

1. **Transport**: TLS 1.3 (HTTPS)
2. **Authentication**: JWT + refresh token
3. **Authorization**: RBAC 6 roles
4. **Data validation**: Pydantic + regex
5. **SQL injection**: SQLAlchemy ORM (parametrized)
6. **CSRF**: Token en header (SPA)
7. **Rate limiting**: 100 req/min per IP
8. **Audit**: AUDITORIA_LOG completo
9. **Secrets**: Variables de entorno (.env)
10. **CORS**: Configurado por domain

### Compliance
- GDPR: Right to be forgotten (futuro)
- SOX: Auditoría inmutable
- Regulación local: AEPD Colombia

---

## Disaster Recovery

### Backup Strategy
- **Frecuencia**: Diaria 23:00
- **Retención**: 30 días local, 1 año en S3
- **RTO**: < 4 horas
- **RPO**: < 1 hora

### High Availability (Futuro)
- Multi-region deployment
- Database replication
- Redis Sentinel
- Load balancer failover

---

## Deployment

### Ambientes
- **Desarrollo**: Docker Compose local
- **Staging**: Docker + AWS ECS
- **Producción**: Kubernetes (futuro)

### CI/CD
- GitHub Actions: Tests automáticos
- Docker build: Imagen optimizada
- Pre-commit hooks: Linting, formatting
- Deployment: Manual o automático (rama main)

---

*Arquitectura sincronizada con implementación actual (Fase 2) - Junio 2026*
