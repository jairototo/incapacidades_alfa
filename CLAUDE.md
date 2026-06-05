# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project Overview

**Sistema de Gestión de Incapacidades** — An end-to-end disability management platform for insurance companies handling ARL (workplace accidents) and SALUD (health) disability claims from filing to payment.

**Current Status**: Phase 1 ~85% complete
- ✅ Backend API: 100% complete, production-ready
- ✅ Portal Externo (public filing): 100% complete, 217 tests
- 🔄 Sistema Interno (admin dashboard): In development
- 📚 Comprehensive Spanish documentation in `/docs`

---

## 🛠️ Quick Start Commands

### Backend (run from `apps/backend/`)

```bash
# Setup & Development
make install              # Install deps + dev dependencies
make dev                  # uvicorn --reload on :8000 (auto-restart on code change)

# Testing
make test                 # pytest with coverage (threshold: 70%)
make test-unit            # Only unit tests
make test-integration     # Only integration tests
make lint                 # ruff + mypy
make format               # Auto-format code with ruff

# Database
make migrate msg='...'    # Create new migration
make upgrade-db           # Apply pending migrations
make downgrade-db         # Revert last migration

# Docker (8 services: api, postgres, redis, minio, rabbitmq, flower, adminer, pgadmin)
make docker-up            # Start all services (backend ready at http://localhost:8010/docs)
make docker-down          # Stop services
make docker-logs          # Follow api logs
```

**Key insight**: MinIO is **opt-in** via `docker-compose --profile minio up -d`. Default storage is filesystem.

### Frontend — Portal Externo (run from `apps/frontend/portal-externo/`)

```bash
npm run dev              # Vite dev server :5173 (proxies /api → :8010)
npm run build            # tsc -b && vite build
npm run lint             # eslint
npm test                 # vitest (threshold: 70%)
npm run test:coverage    # Coverage report
npm run test:ui          # Interactive test UI
```

### Frontend — Sistema Interno (run from `apps/frontend/sistema-interno/`)

```bash
npm run dev
npm run build
npm test
```

---

## 📁 Repository Structure

```
incapacidades_vs/
├── apps/backend/                    ✅ 100% complete
│   ├── app/
│   │   ├── api/v1/endpoints/        # 11 REST modules
│   │   ├── services/                # Business logic (clean layer)
│   │   ├── db/repositories/         # SQLAlchemy async queries
│   │   ├── models/                  # SQLAlchemy ORM (11 tables)
│   │   ├── schemas/                 # Pydantic v2 DTOs
│   │   ├── core/                    # Config, security, deps
│   │   └── utils/                   # Enums, helpers
│   ├── alembic/                     # Database migrations
│   ├── tests/                       # 87% coverage, async-native
│   ├── Makefile                     # Development commands
│   └── docker-compose.yml           # 8 containerized services
│
├── apps/frontend/
│   ├── portal-externo/              ✅ 100% complete (Phase 1)
│   │   ├── src/components/
│   │   │   ├── consulta/            # Query/search components
│   │   │   └── radicacion/          # Filing wizard (6 steps)
│   │   ├── src/services/            # API client + React Query
│   │   ├── src/schemas/             # Zod validations
│   │   └── tests/                   # 217 tests, vitest
│   │
│   └── sistema-interno/             🔄 In development (Phase 2)
│       ├── src/pages/               # Dashboard, audit, payment orders
│       ├── src/stores/              # Zustand auth/permissions
│       └── src/components/          # Shared + internal-only components
│
├── ai/                              # Non-executable AI context
│   ├── skills/                      # Domain expertise (security, frontend design, business rules)
│   ├── agents/                      # AI agent definitions
│   ├── prompts/                     # Prompt templates
│   ├── rag/                         # RAG context (archived docs)
│   └── memory/                      # Persistent memories from prior sessions
│
├── docs/                            # 14 comprehensive Spanish technical docs
│   ├── 00_RESUMEN_PROYECTO.md       # Executive summary
│   ├── 01_ARQUITECTURA.md           # Architecture & patterns
│   ├── 02_MODELO_DATOS.md           # Data model (11 tables)
│   ├── 03_API_ENDPOINTS.md          # All 66+ endpoints
│   ├── 04_FLUJO_ESTADOS.md          # State machine
│   ├── arquitectura_sistema.md       # System architecture details
│   ├── matriz_trazabilidad.md       # Traceability matrix
│   └── documentacion_cliente/       # Client delivery docs
│
├── infra/                           # Docker, nginx, deployment
├── .github/
│   ├── copilot-instructions.md      # ⭐ PRIMARY INSTRUCTION FILE (890 lines)
│   └── workflows/                   # CI/CD (GitHub Actions)
└── AGENTS.md                        # Developer commands reference

Key doc: Read `.github/copilot-instructions.md` before any significant task.
```

---

## 🏗️ Architecture & Patterns

### Backend — Clean Layers (Hexagonal)

```
HTTP Request
    ↓
api/v1/endpoints/  ← routing + request validation only
    ↓
services/          ← business logic, orchestration
    ↓
db/repositories/   ← SQLAlchemy async queries (DISTINCT ON for latest, no N+1)
    ↓
models/            ← SQLAlchemy ORM (no business logic here)
    ↓
PostgreSQL
```

**Key principle**: Never N+1. Use `DISTINCT ON` for "latest traceability" queries. Original Laravel code had ~2500 queries for 255 rows — the fix is batch loading.

### Frontend — Component-Driven

- **Atomic Design**: Shadcn/ui base components → page-level compositions
- **React Query**: Server state with `@tanstack/react-query` (caching, refetch, background sync)
- **Zod**: Client-side validation (portal-externo uses Zod v4.3.5; sistema-interno uses v3.25.76)
- **Zustand**: Lightweight stores (auth, permissions)

---

## 🔐 Authentication & Security

### JWT Bridge (Laravel → FastAPI)

No login here — tokens are emitted by Laravel, validated by FastAPI.

**Flow**:
1. Laravel emits HS256 JWT with `JWT_SECRET` (shared env var)
2. Frontend stores token in `localStorage` as `inc_token`
3. Axios sends `Authorization: Bearer <token>` on every request
4. FastAPI validates with same `JWT_SECRET`
5. On 401 → redirect to Laravel login

**Required claims**:
| Claim | Purpose |
|-------|---------|
| `iss` | Issuer (Laravel) |
| `iat` | Issued at |
| `exp` | Expiration (15 min for access token) |
| `nbf` | Not before |
| `sub` | Subject (user ID as string) |
| `jti` | JWT ID (unique token identifier) |

**Tokens**: Access: 15 min. Refresh: 7 days (SHA256-hashed in DB).

**RBAC Roles**: `ADMIN`, `AUDITOR`, `APROBADOR`, `EMPRESA`, `EMPLEADO`, `READONLY`

---

## 📊 Data Model (11 Tables)

| Table | Purpose |
|-------|---------|
| `usuarios` | Authentication, RBAC, failed login tracking |
| `refresh_tokens` | JWT refresh tokens (SHA256 hash) |
| `empresas` | Companies (ARL) with external sync |
| `empleados` | Employees → companies (ARL claims) |
| `afiliados` | Health policy members (SALUD claims) |
| `incapacidades` | Polymorphic: ARL or SALUD, full workflow |
| `siniestros` | Work accidents (1:N with incapacidades) |
| `documentos` | Files with MD5/SHA256 hashes, MinIO storage |
| `historial_estados` | State change audit trail (polymorphic) |
| `ordenes_pago` | Payment orders (GENERADA → APROBADA → PAGADA) |
| `auditoria_logs` | System-wide audit logs |

**Workflow State Machine**:
```
RADICADA
  → EN_AUDITORIA
    → {OBSERVADA, APROBADA, RECHAZADA}
      → EN_PAGO
        → PAGADA
```

---

## 🌐 Service Ports (Local Development)

| Service | Port | URL |
|---------|------|-----|
| FastAPI | 8010 | http://localhost:8010/docs (Swagger UI) |
| PostgreSQL | 5442 | `postgresql+asyncpg://postgres:postgres@localhost:5442/incapacidades` |
| Redis | 6389 | `redis://localhost:6389` |
| MinIO API | 9010 | http://localhost:9010 |
| MinIO Console | 9011 | http://localhost:9011 (minioadmin / minioadmin) |
| RabbitMQ | 5682 | amqp://guest:guest@localhost:5682 |
| RabbitMQ UI | 15682 | http://localhost:15682 |
| Flower (Celery) | 5565 | http://localhost:5565 |
| Portal Externo | 5173 | http://localhost:5173 |

---

## ⚙️ Database

**Local dev**: `postgresql+asyncpg://postgres:postgres@localhost:5442/incapacidades`

**Inside Docker**: host `postgres`, port `5432`

**Alembic config**: `apps/backend/alembic.ini`

**Async mode**: `asyncio_mode = auto` in `pytest.ini` — all tests are async-native.

**MCP connection** (opencode.json): `postgres://postgres:postgres@localhost:5442/incapacidades`

---

## 🧪 Testing Conventions

### Backend (pytest)

```bash
# Run all tests with coverage
make test                          # Coverage threshold: 70%

# Target specific tests
pytest tests/unit/test_auth.py -v
pytest tests/test_auth_service.py::test_login -v

# With coverage report
pytest --cov=app --cov-report=html
```

**Test layout**: `tests/unit/` and `tests/integration/`. All async-native.

**Current metrics**: 87% coverage (34 unit + 19 integration tests passing)

### Frontend (vitest)

```bash
# Run all tests
npm test                           # Coverage threshold: 70%

# Interactive test UI
npm run test:ui

# Watch mode
npm test -- --watch

# Coverage report
npm run test:coverage
```

**Current metrics**:
- Portal Externo: 217 tests, >75% coverage
- Sistema Interno: Separate test suite (vitest)

---

## 🐛 Known Issues & Workarounds

### 1. **Celery Event Loop Crash** (Fixed ✅)

**Issue**: asyncpg doesn't play well with Celery's event loop.

**Fix**: Use `asyncio.run()` wrapper in task payloads. See `apps/backend/app/tasks/incapacidad_tasks.py`.

**Reference**: `docs/FIX_EVENT_LOOP_CELERY.md`

### 2. **Frontend Library Version Mismatch**

**Warning**: The two frontends use different major versions of key libraries:

| Library | portal-externo | sistema-interno |
|---------|---------------|-----------------|
| Tailwind CSS | v4.1.18 (CSS variables) | v3.4.19 (config-based) |
| Zod | v4.3.5 | v3.25.76 |

**Do NOT copy styles or schema patterns between them** without checking API compatibility.

### 3. **N+1 Query Pattern (Fixed ✅)**

**Issue**: Original Laravel code had ~2500 queries for 255 rows.

**Fix**: Use batch loading in repositories with `DISTINCT ON` for "latest" queries.

**Reference**: `apps/backend/app/db/repositories/`

---

## 📝 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| API endpoints | kebab-case plural | `/incapacidades/consulta` |
| Pydantic schemas | PascalCase | `ConsultaIncapacidadParams` |
| SQLAlchemy models | PascalCase singular | `Incapacidad` |
| React components | PascalCase | `FiltrosConsulta.tsx` |
| Zustand stores | camelCase + `use` prefix | `useAuthStore` |
| Git branches | `feature/`, `bugfix/`, `hotfix/` | `feature/radicar-wizard` |
| Commits | Conventional Commits | `feat:`, `fix:`, `docs:` |

---

## 🚀 Development Workflow

### Before Starting Work

1. **Check engram memory**: Prior sessions have saved architectural decisions and patterns
2. **Read relevant skill**: `/ai/skills/` covers security, frontend design, and business rules
3. **Review copilot-instructions.md**: 890-line primary instruction file
4. **Check docs**: `/docs/` has 14 comprehensive technical documents

### When Adding Features

1. **Backend**: Use clean layer pattern (endpoints → services → repositories → models)
2. **Frontend**: 
   - Validate with Zod first
   - Use React Query for server state
   - Write tests **before** implementation (TDD)
3. **Database**: Create migrations with `make migrate msg='...'`
4. **Tests**: Coverage threshold is 70% (backend) and 70% (frontend)

### When Pushing Code

1. **Lint & format**: `make lint && make format` (backend) or `npm run lint` (frontend)
2. **Tests pass**: `make test` (backend) or `npm test` (frontend)
3. **Commit message**: Use Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
4. **Create PR**: Push to feature branch, create PR against `master`

---

## 📚 Key Documentation

**Read in this order**:

1. **`.github/copilot-instructions.md`** (890 lines) — Primary instruction file covering:
   - Complete project description
   - Architectural patterns
   - API endpoints structure
   - Frontend component layout
   - Security model
   - Delivery protocol

2. **`docs/00_RESUMEN_PROYECTO.md`** — Executive summary

3. **`docs/01_ARQUITECTURA.md`** — System architecture & patterns

4. **`docs/02_MODELO_DATOS.md`** — Data model (11 tables)

5. **`docs/04_FLUJO_ESTADOS.md`** — State machine & workflow

6. **`AGENTS.md`** — This repo's developer commands reference

7. **`ai/skills/`** — Domain expertise:
   - `security/skill.md` — JWT, RBAC, validation
   - `frontend-design/SKILL.md` — Brand tokens, component patterns
   - `negocio/incapacidad_radicacion/skill.md` — Filing business rules

---

## 🎯 Common Tasks

### Add a New API Endpoint

1. Create schema in `apps/backend/app/schemas/`
2. Create endpoint in `apps/backend/app/api/v1/endpoints/`
3. Add service logic in `apps/backend/app/services/`
4. Add repository query if needed in `apps/backend/app/db/repositories/`
5. Write tests in `apps/backend/tests/`
6. Update `docs/03_API_ENDPOINTS.md`

### Add a Frontend Component

1. Create component in `apps/frontend/portal-externo/src/components/`
2. Add Zod schema if form in `apps/frontend/portal-externo/src/schemas/`
3. Use React Query for data fetching via `src/services/api.ts`
4. Write tests in `apps/frontend/portal-externo/tests/`
5. Ensure >70% coverage

### Fix a Database Issue

1. Create migration: `make migrate msg='description'`
2. Review Alembic file in `apps/backend/alembic/versions/`
3. Test: `make test-integration`
4. Apply: `make upgrade-db`

---

## 🔗 Important Files

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | ⭐ Primary instruction file (890 lines) |
| `AGENTS.md` | Developer commands reference |
| `ai/skills/security/skill.md` | Security & JWT bridge details |
| `apps/backend/Makefile` | Backend commands |
| `apps/backend/alembic.ini` | Database migration config |
| `apps/backend/pytest.ini` | Test config (async mode) |
| `apps/frontend/portal-externo/vite.config.ts` | Frontend build config |
| `docs/` | 14 comprehensive Spanish technical docs |

---

## 💡 Tips for Success

1. **Always use async/await** in backend (SQLAlchemy 2.0 is async-first)
2. **Use React Query** for server state, not local useState (caching matters)
3. **Validate early** with Zod/Pydantic (client + server)
4. **Write tests first** (TDD approach, especially frontend)
5. **Batch load queries** to avoid N+1 (check repositories for patterns)
6. **Check library versions** before copying code between frontends
7. **Run tests locally** before pushing (CI is currently docs-only)
8. **Follow Conventional Commits** for clear commit history

---

**Last updated**: 2026-06-05  
**Project Version**: 0.9.0-beta  
**Phase**: 1 (85% complete) — Portal Externo done, Sistema Interno in development
