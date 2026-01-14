# Arquitectura del Sistema de Gestión de Incapacidades

## 1. Visión General

Sistema de gestión de incapacidades para aseguradora con cobertura de ARL y pólizas de salud.

## 2. Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                      │
├──────────────────────────────┬──────────────────────────────────┤
│     Portal Externo           │      Sistema Interno             │
│   (React/Vue/Angular)        │    (React/Vue/Angular)           │
│                              │                                  │
│  - Radicación                │  - Auditoría                     │
│  - Consultas                 │  - Aprobación/Rechazo            │
│  - Adjuntar docs             │  - Órdenes de pago               │
│                              │  - Control de roles              │
└──────────────────────────────┴──────────────────────────────────┘
                              ▲
                              │ HTTPS/REST
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

## 3. Patrones Arquitectónicos

### 3.1 Clean Architecture / Hexagonal Architecture
- **Domain Layer**: Entidades de negocio, reglas de dominio
- **Application Layer**: Casos de uso, servicios de aplicación
- **Infrastructure Layer**: Implementaciones concretas (DB, APIs)
- **Presentation Layer**: Controllers, schemas de API

### 3.2 Repository Pattern
- Abstracción del acceso a datos
- Facilita testing y cambio de tecnología

### 3.3 Dependency Injection
- Inversión de dependencias
- Mayor testabilidad

### 3.4 CQRS (Command Query Responsibility Segregation)
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
