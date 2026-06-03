# AGENTS.md — Incapacidades VS

Primary AI instruction file: `.github/copilot-instructions.md` (890 lines). Read it before starting any significant task.

---

## Repo Structure

Monorepo — three separate apps, each with its own `node_modules` / venv:

```
apps/backend/              FastAPI + SQLAlchemy 2.0 async
apps/frontend/portal-externo/   React 19 public portal (Phase 1 — complete)
apps/frontend/sistema-interno/  React internal dashboard (in development)
docs/                      ~80 .md architecture/business docs
infra/docker, nginx, …
ai/                        prompts, skills, RAG, memory (non-executable)
```

No Turborepo/Nx — each app is independent. Run commands from the app's own directory.

---

## Developer Commands

### Backend (run from `apps/backend/`)

```bash
make install          # install deps (requirements.txt + requirements-dev.txt)
make dev              # uvicorn --reload on :8000
make test             # pytest -v --cov=app (threshold: 70%)
make test-unit        # pytest tests/unit/ -v
make test-integration # pytest tests/integration/ -v
make lint             # ruff check app/ && mypy app/
make format           # ruff format app/ && ruff check --fix app/
make migrate msg='…'  # alembic revision --autogenerate -m "…"
make upgrade-db       # alembic upgrade head
make downgrade-db     # alembic downgrade -1
make docker-up        # docker-compose up -d (all 8 services)
make docker-logs      # docker-compose logs -f api
```

MinIO is **opt-in**: `docker-compose --profile minio up -d`. Default storage is `filesystem`.

### Frontend — Portal Externo (run from `apps/frontend/portal-externo/`)

```bash
npm run dev           # Vite dev server :5173, proxies /api → http://localhost:8010
npm run build         # tsc -b && vite build
npm run lint          # eslint
npm test              # vitest (threshold: 70% lines/functions/branches/statements)
npm run test:coverage
```

### Frontend — Sistema Interno (run from `apps/frontend/sistema-interno/`)

```bash
npm run dev
npm run build
npm run lint
npm test              # vitest
npm run test:ui       # vitest --ui
npm run test:coverage
```

---

## Ports

| Service | Host port |
|---------|-----------|
| FastAPI (`api`) | 8010 |
| PostgreSQL | 5442 |
| Redis | 6389 |
| RabbitMQ AMQP | 5682 |
| RabbitMQ UI | 15682 |
| MinIO API | 9010 |
| MinIO Console | 9011 |
| Celery Flower | 5565 |
| Portal externo (Vite) | 5173 |

---

## Database

- Local dev: `postgresql+asyncpg://postgres:postgres@localhost:5442/incapacidades`
- Inside Docker containers: host `postgres`, port `5432`
- MCP (opencode.json): `postgres://postgres:postgres@localhost:5442/incapacidades`
- Alembic config: `apps/backend/alembic.ini`
- `asyncio_mode = auto` in `pytest.ini` — all tests are async-native

---

## Frontend Version Quirks

**The two frontends use different major versions of two libraries:**

| Library | portal-externo | sistema-interno |
|---------|---------------|-----------------|
| Tailwind CSS | v4.1.18 | v3.4.19 |
| Zod | v4.3.5 | v3.25.76 |

Do not copy schema or style patterns between them without checking API compatibility.

Portal-externo uses Tailwind v4 CSS variable colors (`hsl(var(--...))`). Sistema-interno uses Tailwind v3 with standard config.

---

## Architecture — Clean Layers (Backend)

```
api/v1/endpoints/  →  services/  →  db/repositories/  →  models/
```

- Endpoints: routing + request validation only
- Services: business logic, orchestration
- Repositories: SQLAlchemy async queries (batch — never N+1)
- Models: SQLAlchemy ORM (no business logic)
- Schemas: Pydantic v2 DTOs

Use `DISTINCT ON` for "latest traceability" queries. The original Laravel code had ~2500 queries for 255 rows; the fix is batch loading in repositories.

---

## Auth

JWT bridge from Laravel → FastAPI. Do **not** implement login/2FA here.

- Laravel emits HS256 JWT with `JWT_SECRET`
- Frontend stores token in `localStorage` as `inc_token`
- Axios sends `Authorization: Bearer <token>`
- FastAPI validates with same `JWT_SECRET`
- On 401 → redirect to Laravel login

Claims required: `iss`, `iat`, `exp`, `nbf`, `sub` (user ID), `jti`.

Access token: 15 min. Refresh token: 7 days, SHA256-hashed in DB.

---

## Enums / Constants

 """Estado de la incapacidad en el workflow."""
    RADICADA = "RADICADA"
    EN_AUDITORIA = "EN_AUDITORIA"
    OBSERVADA = "OBSERVADA"
    APROBADA = "APROBADA"
    APROBADA_PARCIALMENTE = "APROBADA_PARCIALMENTE"  # Estado para aprobación parcial
    RECHAZADA = "RECHAZADA"
    EN_PAGO = "EN_PAGO"
    EN_PAGO_PARCIAL = "EN_PAGO_PARCIAL"  # Estado para pago parcial
    PAGADA = "PAGADA"
    PAGADA_PARCIALMENTE = "PAGADA_PARCIALMENTE"  # Estado para pago parcial completado
    CANCELADA = "CANCELADA"

State machine: `RADICADA → EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA} → EN_PAGO → PAGADA`

RBAC roles: `ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY`

---

## Naming Conventions

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

## CI

Single workflow: `.github/workflows/auto-documentation.yml`
- Triggers on push/PR to `master`
- Auto-commits doc updates (`docs/`, `README.md`, `CHANGELOG.md`)
- No lint/test CI yet — run checks locally before merging

No pre-commit hooks configured.

---

## Delivery Protocol

Per `.github/copilot-instructions.md`, every task completion should include:
1. Executive summary of changes
2. List of changed files
3. Test results (or why tests weren't run)
4. Docs update if needed
5. Structured "next step prompt"
