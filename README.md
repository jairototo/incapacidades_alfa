# Sistema de Gestión de Incapacidades - Aseguradora

**Estado**: ⚠️ **FASE 1 EN DESARROLLO** - Portal Externo 80% Funcional  
**Última actualización**: 17 de enero de 2026  
**Versión**: 0.9.0-beta

---

## 📋 Descripción del Proyecto

Sistema integral para la gestión del ciclo completo de incapacidades médicas, desde la radicación hasta el pago, con soporte diferenciado para:

- **Incapacidades ARL** (Administradora de Riesgos Laborales): Con gestión de siniestros y accidentes laborales
- **Incapacidades SALUD**: Con gestión de afiliados y pólizas de salud

### 🎯 Características Principales

- ✅ **Portal Externo - Radicación**: Wizard de 5 pasos completado (100%)
- ⏳ **Portal Externo - Consulta**: Búsqueda y detalle de incapacidades (0%)
- ⏳ **Sistema Interno**: Dashboard de auditoría con roles RBAC (en planificación)
- ✅ **Workflow de Estados**: Máquina de estados completa (RADICADA → PAGADA)
- ✅ **Gestión Documental**: Upload/download con MinIO/S3
- ✅ **Autenticación JWT**: Tokens con refresh y revocación
- ✅ **Órdenes de Pago**: Generación automática y workflow de aprobación
- ✅ **Auditoría Completa**: Historial de cambios para todas las entidades

---

## 🎯 Estado del Proyecto

### Progreso Global: 85% ⚠️

| Componente | Completado | Estado |
|------------|------------|--------|
| **Backend API** | 100% | ✅ Producción |
| **Base de Datos** | 100% | ✅ Producción |
| **Autenticación** | 100% | ✅ Producción |
| **Documentos** | 100% | ✅ Producción |
| **Frontend - Radicación** | 100% | ✅ Completado |
| **Frontend - Consulta** | 0% | ⏳ Por iniciar |
| **Frontend Fase 2** | 0% | ⏳ Planificado |

### Últimos Hitos Alcanzados

- ✅ **16 de enero**: Wizard de radicación (5 pasos) completado - 217 tests pasando
- ✅ **15 de enero**: Integración completa con backend FastAPI
- ✅ **14 de enero**: Sistema de autenticación JWT finalizado
- ✅ **12 de enero**: Módulo de documentos con MinIO operativo

### ⚠️ Pendiente para Completar Fase 1

- 🔴 **Consulta de Incapacidades** (CRÍTICO)
  - Endpoint backend para búsqueda pública
  - Componente de búsqueda por número/documento
  - Vista detallada de incapacidad
  - Timeline de estados
  - Descarga de documentos
  - Tests completos (>70% cobertura)

---

## 🏗️ Arquitectura General

### Stack Tecnológico

#### Backend (100% completado)
- **Framework**: FastAPI 0.109+ con Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async/await native)
- **Base de Datos**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Storage**: MinIO (S3-compatible)
- **Queue**: Celery + RabbitMQ
- **Auth**: JWT con refresh tokens
- **Testing**: pytest (87% cobertura)

#### Frontend (Fase 1: 80% completado)
- **Framework**: React 18 + TypeScript 5
- **Build**: Vite 5
- **Styling**: TailwindCSS 3 + Shadcn/ui
- **Forms**: React Hook Form + Zod
- **Data**: React Query (@tanstack/react-query)
- **HTTP**: Axios con interceptors
- **Testing**: Vitest + Testing Library (75% cobertura)

#### Infraestructura
- **Containerización**: Docker Compose (8 servicios)
- **Puertos**: API:8010, PostgreSQL:5442, Redis:6389, MinIO:9010/9011

---

## 🛠️ Inicio Rápido

### Prerequisitos

- Docker 24+ y Docker Compose
- Node.js 18+ (para frontend)
- Python 3.11+ (opcional, para desarrollo sin Docker)

### 1. Backend API

```bash
cd backend

# Iniciar todos los servicios (PostgreSQL, Redis, MinIO, API, Celery)
docker compose up -d

# Ver logs
docker compose logs -f api

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Crear datos de prueba (opcional)
docker compose exec api python scripts/seed_data.py
```

**Acceder a**:
- API: http://localhost:8010
- Swagger UI: http://localhost:8010/docs
- MinIO Console: http://localhost:9011 (minioadmin / minioadmin)
- RabbitMQ Management: http://localhost:15682 (guest / guest)

### 2. Frontend Portal Externo

```bash
cd frontend/portal-externo

# Instalar dependencias
npm install

# Modo desarrollo
npm run dev

# Tests
npm test

# Build producción
npm run build
```

**Acceder a**:
- Portal: http://localhost:5173

---

## 📁 Estructura del Repositorio

```
incapacidades_vs/
│
├── backend/                    # API Backend (FastAPI) ✅ 100%
│   ├── app/
│   │   ├── api/v1/endpoints/  # 11 módulos REST
│   │   ├── core/              # Config, security, logging
│   │   ├── db/repositories/   # 11 repositories
│   │   ├── models/            # 11 modelos SQLAlchemy
│   │   ├── schemas/           # 11 schemas Pydantic
│   │   ├── services/          # 11 services
│   │   └── utils/             # Enums, helpers
│   ├── alembic/               # Migraciones DB
│   ├── tests/                 # 87% cobertura
│   ├── docker-compose.yml     # 8 servicios
│   └── README.md
│
├── frontend/
│   └── portal-externo/        # Portal Público ⚠️ 80%
│       ├── src/
│       │   ├── components/    # Wizard 5 pasos ✅
│       │   │   └── consulta/  # ⏳ Por implementar
│       │   ├── services/      # API + React Query
│       │   ├── schemas/       # Validación Zod
│       │   └── types/         # TypeScript
│       ├── tests/             # 217 tests (75% cobertura)
│       └── README.md
│
├── docs/                      # Documentación técnica ✅
│   ├── 00_RESUMEN_PROYECTO.md
│   ├── 01_ARQUITECTURA.md
│   ├── 02_MODELO_DATOS.md     # 11 tablas
│   ├── 03_API_ENDPOINTS.md    # 66 endpoints
│   ├── 04_FLUJO_ESTADOS.md
│   ├── 05_STACK_Y_ESTRUCTURA.md
│   ├── 06_FRONTEND_PLAN.md    # 3 fases
│   ├── 07_FRONTEND_FASE1_PORTAL_EXTERNO.md
│   ├── 08_FRONTEND_FASE2_SISTEMA_INTERNO.md
│   ├── 09_COMPONENTES_COMPARTIDOS.md
│   └── 10_CONSULTA_INCAPACIDADES.md  # ⏳ NUEVO
│
├── ESTADO_PROYECTO.md         # Tracking detallado
├── PLAN_CONSULTA_INCAPACIDADES.md  # ⏳ NUEVO
└── README.md                  # Este archivo
```

---

## 🎯 Funcionalidades Principales

### Portal Externo

#### ✅ Radicación de Incapacidades (100% completado)

**Wizard de 5 pasos**:
- ✅ Paso 1: Selección tipo de incapacidad (ARL/SALUD)
- ✅ Paso 2: Datos personales (empleado/afiliado)
- ✅ Paso 3: Datos de la incapacidad
- ✅ Paso 4: Carga de documentos (PDF, JPG, PNG)
- ✅ Paso 5: Resumen y confirmación

**Estado**: 
- 217 tests pasando (100%)
- Build exitoso (520 KB bundle)
- Integración completa con backend
- Upload a MinIO funcional

#### ⏳ Consulta de Incapacidades (0% - PENDIENTE)

**Funcionalidad a implementar**:
- 🔴 Búsqueda por número de radicación
- 🔴 Búsqueda por documento de identidad + fecha
- 🔴 Vista detallada de incapacidad
- 🔴 Timeline de estados con historial
- 🔴 Descarga de documentos adjuntos
- 🔴 Información de contacto para soporte
- 🔴 Tests completos (>70% cobertura)

**Estimación**: 3-4 días de desarrollo

### Sistema Interno (⏳ Fase 2 - No iniciado)

1. **Autenticación**
   - Login con JWT
   - Roles RBAC (ADMIN, AUDITOR, APROBADOR, etc.)
   - Refresh tokens automático

2. **Dashboard de Auditoría**
   - Métricas en tiempo real
   - Filtros avanzados
   - Gráficos con Recharts

3. **Gestión de Incapacidades**
   - Cambio de estados con validaciones
   - Workflow completo
   - Asignación de auditores

4. **Órdenes de Pago**
   - Generación automática
   - Workflow de aprobación
   - Integración con tesorería

---

## 🔐 Seguridad

### Backend
- ✅ Autenticación JWT (access + refresh tokens)
- ✅ Hash de contraseñas con bcrypt
- ✅ Validación de entrada con Pydantic
- ✅ CORS configurado
- ⏳ Rate limiting en login (pendiente)
- ✅ SQL injection protegido (ORM)
- ✅ XSS protegido (sanitización)

### Frontend
- ✅ Validación client-side con Zod
- ✅ Sanitización de inputs
- ⏳ HTTPS only (producción - pendiente)
- ⏳ Token storage seguro (pendiente en consulta pública)
- ⏳ Auto-logout en inactividad (pendiente)

---

## 📊 Roles del Sistema

| Rol | Permisos Principales |
|-----|---------------------|
| **ADMIN** | Acceso total, gestión usuarios, configuración |
| **AUDITOR** | Revisar incapacidades, cambiar a EN_AUDITORIA |
| **APROBADOR** | Aprobar/rechazar, observaciones |
| **EMPRESA** | Consultar incapacidades de sus empleados |
| **EMPLEADO** | Radicar y consultar propias incapacidades |
| **READONLY** | Solo consulta, sin modificaciones |

---

## 🔄 Flujo del Proceso

```
1. RADICACIÓN (Portal Externo - ✅ Completado)
   └─> RADICADA
       
2. CONSULTA (Portal Externo - ⏳ Pendiente)
   └─> Ver estado y documentos
       
3. AUDITORÍA (Sistema Interno - ⏳ No iniciado)
   └─> EN_AUDITORIA
       ├─> OBSERVADA (requiere corrección)
       ├─> APROBADA
       └─> RECHAZADA

4. PAGO (Sistema Interno - ⏳ No iniciado)
   └─> EN_PAGO
       └─> Generar Orden de Pago
           ├─> GENERADA
           ├─> APROBADA
           └─> PAGADA
       
5. FINALIZACIÓN
   └─> PAGADA
```

---

## 🧪 Testing

### Backend
```bash
cd backend

# Todos los tests
docker compose exec api pytest

# Con cobertura
docker compose exec api pytest --cov=app --cov-report=html

# Tests específicos
docker compose exec api pytest tests/test_auth_service.py -v
```

**Métricas**:
- Tests unitarios: 34 (100% passing)
- Tests de integración: 19 (100% passing)
- Cobertura global: 87%

### Frontend
```bash
cd frontend/portal-externo

# Tests
npm test

# Tests con UI
npm test -- --ui

# Cobertura
npm run test:coverage
```

**Métricas actuales**:
- Total tests: 217 (100% passing)
- Cobertura global: >75%
- Build: ✅ Exitoso (520 KB bundle)

**Métricas objetivo al completar Fase 1**:
- Total tests: ~280 (incluir 60+ tests de consulta)
- Cobertura global: >75%

---

## 📈 Métricas del Proyecto

### Backend
- **Endpoints**: 66 REST (66 implementados, 1 nuevo pendiente)
- **Modelos**: 11 tablas
- **Líneas de código**: ~15,000
- **Tests**: 87% cobertura
- **Tiempo respuesta API**: <100ms (promedio)

### Frontend Fase 1
- **Componentes**: 35+ (radicación) + ~10 pendientes (consulta)
- **Hooks personalizados**: 12 + 3 pendientes
- **Schemas Zod**: 8 + 2 pendientes
- **Tests actuales**: 217
- **Tests objetivo**: ~280
- **Bundle size**: 520 KB (gzipped)

### Base de Datos
- **Tablas**: 11
- **Índices**: 50+
- **Constraints**: 30+
- **Triggers**: 5

---

## 🚀 Deployment

### Producción con Docker

```bash
# Backend
cd backend
docker build -t incapacidades-api:latest .
docker run -d \
  -p 8010:8000 \
  --env-file .env.production \
  --name incapacidades-api \
  incapacidades-api:latest

# Frontend
cd frontend/portal-externo
npm run build
# Servir con Nginx/Vercel/Netlify
```

### Variables de Entorno Importantes

**Backend** (.env.production):
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-secret-key>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
MINIO_ENDPOINT=s3.amazonaws.com
SENTRY_DSN=<sentry-dsn>
```

**Frontend** (.env.production):
```bash
VITE_API_URL=https://api.incapacidades.com/api/v1
VITE_ENV=production
```

---

## 📚 Documentación Completa

### General (11 documentos)
- [Resumen del Proyecto](docs/00_RESUMEN_PROYECTO.md)
- [Arquitectura](docs/01_ARQUITECTURA.md)
- [Modelo de Datos](docs/02_MODELO_DATOS.md)
- [API Endpoints](docs/03_API_ENDPOINTS.md)
- [Flujo de Estados](docs/04_FLUJO_ESTADOS.md)
- [Stack Tecnológico](docs/05_STACK_Y_ESTRUCTURA.md)
- [Plan Frontend](docs/06_FRONTEND_PLAN.md)
- [Fase 1 - Portal Externo](docs/07_FRONTEND_FASE1_PORTAL_EXTERNO.md)
- [Fase 2 - Sistema Interno](docs/08_FRONTEND_FASE2_SISTEMA_INTERNO.md)
- [Componentes Compartidos](docs/09_COMPONENTES_COMPARTIDOS.md)
- [Consulta de Incapacidades](docs/10_CONSULTA_INCAPACIDADES.md) ⏳ NUEVO

### Backend Específica
- [Backend README](backend/README.md)
- [Migraciones Alembic](backend/alembic/README.md)
- [Scripts de Utilidades](backend/scripts/README.md)

### Frontend Específica
- [Portal Externo README](frontend/portal-externo/README.md)
- [Wizard Paso 1 - Completado](frontend/portal-externo/WIZARD_PASO1_COMPLETADO.md)
- [Wizard Paso 2 - Completado](frontend/portal-externo/WIZARD_PASO2_COMPLETADO.md)
- [Wizard Paso 3 - Completado](frontend/portal-externo/WIZARD_PASO3_COMPLETADO.md)
- [Wizard Paso 4 - Completado](frontend/portal-externo/WIZARD_PASO4_COMPLETADO.md)
- [Wizard Paso 5 - Completado](frontend/portal-externo/WIZARD_PASO5_COMPLETADO.md)
- [Consulta - Plan de Implementación](frontend/portal-externo/PLAN_CONSULTA.md) ⏳ NUEVO

### Estado y Tracking
- [Estado del Proyecto](ESTADO_PROYECTO.md)
- [Resumen Visual Completo](RESUMEN_VISUAL_COMPLETO.md)
- [Sesión Resumen Frontend Fase 1](SESION_RESUMEN_FRONTEND_FASE1.md)
- [Plan Consulta Incapacidades](PLAN_CONSULTA_INCAPACIDADES.md) ⏳ NUEVO

---

## 🎯 Roadmap

### ⚠️ Fase 1: Portal Externo (85% COMPLETADO)
- ✅ Wizard de radicación (100%)
- ⏳ Consulta de incapacidades (0%) **← SIGUIENTE TAREA CRÍTICA**
- ⏳ Upload de documentos en consulta (0%)
- ⏳ Integración completa con backend (80%)

**Tiempo estimado restante**: 3-4 días

### ⏳ Fase 2: Sistema Interno (0% - 2-4 semanas)
- Autenticación JWT en frontend
- Dashboard de auditoría
- CRUD de incapacidades
- Gestión de órdenes de pago
- Gestión de usuarios y roles

### 📅 Fase 3: Funcionalidades Avanzadas (2-3 semanas)
- Notificaciones en tiempo real (WebSockets)
- Analytics avanzados
- Firma digital de documentos
- Integración con sistemas externos
- App móvil (opcional)

---

## 🤝 Contribución

### Convenciones

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Branches**: `feature/`, `bugfix/`, `hotfix/`
- **Code Style**: 
  - Backend: Black + isort + flake8
  - Frontend: Prettier + ESLint
- **Tests**: Obligatorios para nuevas features (>70% cobertura)

### Flujo de Trabajo

1. Fork el proyecto
2. Crear branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'feat: add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📝 Licencia

Privado - Todos los derechos reservados

---

## 📞 Contacto

**Equipo de Desarrollo**:
- Repositorio: https://github.com/Imaginesas/incapacidades_alfa
- Documentación: `/docs`
- API Swagger: http://localhost:8010/docs
- Issues: GitHub Issues

---

## 🏆 Reconocimientos

- **FastAPI**: Framework web moderno y rápido
- **React**: Librería UI con gran ecosistema
- **Shadcn/ui**: Componentes accesibles y customizables
- **PostgreSQL**: Base de datos robusta y confiable
- **MinIO**: Almacenamiento compatible S3

---

**Última actualización**: 17 de enero de 2026  
**Versión**: 0.9.0-beta  
**Estado**: ⚠️ **FASE 1 EN DESARROLLO - CONSULTA PENDIENTE**

**Próxima tarea crítica**: Implementar módulo de consulta de incapacidades (3-4 días estimados)