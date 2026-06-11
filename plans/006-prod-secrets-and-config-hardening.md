# Plan 006: Parameterize default credentials and harden production config

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **SECRET-HANDLING RULE**: never write a real credential value into any file
> you produce (plan updates, docs, commit messages). Reference locations and
> credential types only.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/backend/docker-compose.yml apps/backend/app/main.py apps/backend/.env.example docs/`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

The repo is heading to production (branch `iniciando_desarrollo_para_produccion`) with three
config-level hazards. (1) `apps/backend/docker-compose.yml` hardcodes well-known default
credentials — Postgres `postgres/postgres`, MinIO `minioadmin/minioadmin`, RabbitMQ
`guest/guest` — fine for local dev, catastrophic if this compose file is ever the basis of
a deployment. (2) A real `backend/.env` (79 lines, including SMTP credentials and a
SECRET_KEY) was committed at `000e3063` and removed at `999109b7` — the values remain in
git history and must be treated as burned: **rotation is required regardless of any other
action**. (3) `app/main.py` exposes Swagger/ReDoc unconditionally and configures CORS with
wildcard methods/headers + credentials. This plan parameterizes the compose file with safe
dev defaults, gates docs by environment, tightens CORS, and writes a short rotation
runbook. The actual rotation of external credentials is a HUMAN action — the runbook tells
the operator exactly what to rotate.

## Current state

- `apps/backend/docker-compose.yml` — `POSTGRES_USER/POSTGRES_PASSWORD: postgres` (lines ~8–9), `MINIO_ROOT_USER/PASSWORD: minioadmin` (lines ~40–42), `RABBITMQ_DEFAULT_USER/PASS: guest` (lines ~60–62). Line numbers approximate — locate by grep.
- `apps/backend/app/main.py:23-25`:
  ```python
  openapi_url=f"{settings.API_V1_STR}/openapi.json",
  docs_url="/docs",
  redoc_url="/redoc",
  ```
- `apps/backend/app/main.py:34-40`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- `apps/backend/app/core/config.py` — pydantic Settings; has `ENVIRONMENT` and `DEBUG`
  fields (listed in `.env.example`). Check the exact field names/types before using them.
- `apps/backend/.env` exists locally, is git-ignored (verified), and contains real dev
  values — do not read values from it into any output; you only need `.env.example`.
- Git history: `git show 000e3063 --stat | grep .env` shows `backend/.env` added;
  `git show 999109b7 --stat` shows it deleted. Credential types in the burned file:
  app SECRET_KEY, SMTP (Mailtrap) user/password, MinIO keys, Postgres password.
- Frontend `.env.production` files contain only public URLs (verified — no secrets there).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Compose config still valid | from `apps/backend/`: `docker compose config -q` | exit 0 |
| Stack still boots | from `apps/backend/`: `docker compose up -d && curl -sf http://localhost:8010/api/v1/health` (endpoint per `endpoints/health.py`; adjust path if different) | HTTP 200 |
| Backend tests (smoke) | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_auth_api_simple.py -v --no-cov"` | all pass |
| Lint | from `apps/backend/`: `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify/create):
- `apps/backend/docker-compose.yml`
- `apps/backend/app/main.py`
- `apps/backend/.env.example` (add the new compose variables with DEV-ONLY placeholder values)
- `docs/SECURITY_ROTATION.md` (create — the rotation runbook)

**Out of scope** (do NOT touch):
- Rewriting git history (BFG/filter-repo) — high-blast-radius, operator-only decision; the runbook mentions it as optional since rotation makes the leaked values worthless.
- `apps/backend/.env` (the real local file) — never read or edit it.
- `infra/` deployment configs — production compose/nginx hardening is a separate effort.
- Auth code (`app/core/security.py`) and everything in Plan 001.

## Git workflow

- Branch: `feature/prod-config-hardening`
- Conventional Commits, e.g. `feat: parameterize docker-compose credentials and gate docs by environment`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Parameterize docker-compose credentials

In `apps/backend/docker-compose.yml`, replace each hardcoded credential with variable
substitution keeping the current value as the dev default, e.g.:

```yaml
POSTGRES_USER: ${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
...
MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
...
RABBITMQ_DEFAULT_USER: ${RABBITMQ_DEFAULT_USER:-guest}
RABBITMQ_DEFAULT_PASS: ${RABBITMQ_DEFAULT_PASS:-guest}
```

Also update any service URL in the same file that embeds these values (e.g. the api
service's `DATABASE_URL`, `CELERY_BROKER_URL`) to use the same variables. Add the new
variable NAMES to `.env.example` with a comment block: "override in non-dev environments;
defaults are for local development only".

**Verify**: `docker compose config -q` → exit 0, and `docker compose config | grep -c "minioadmin\|guest\|postgres"` still resolves to the dev defaults when no overrides are set (same behavior as before for local dev). Then `docker compose up -d` + health check → 200.

### Step 2: Gate API docs by environment

In `app/main.py`, make the docs URLs conditional. First check `app/core/config.py` for the
exact settings fields (`ENVIRONMENT: str` and/or `DEBUG: bool`), then:

```python
docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
```

(Use the field/value spelling actually present in config.py — e.g. if it's an Enum or
`"prod"`, match it.)

**Verify**: restart the stack (`docker compose restart api`); with the dev env, `curl -sf http://localhost:8010/docs` → 200 (dev still works). Unit-level check is enough for the production branch: `docker compose exec api sh -c "ENVIRONMENT=production python -c 'from app.main import app; assert app.docs_url is None'"` → no assertion error (if config caching prevents this one-liner, note it and verify by reading the code path instead).

### Step 3: Tighten CORS methods/headers

In the same middleware block, replace the wildcards:

```python
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
allow_headers=["Authorization", "Content-Type"],
```

Before committing, grep both frontends for custom request headers
(`grep -rn "headers" apps/frontend/*/src/services apps/frontend/*/src/lib | grep -iv "authorization\|content-type"`)
and add any legitimately used header to the list.

**Verify**: with the stack up, exercise one authed endpoint from sistema-interno dev server (or `curl -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: authorization,content-type" -X OPTIONS http://localhost:8010/api/v1/auth/login`) → preflight 200 with the requested headers allowed.

### Step 4: Write the rotation runbook

Create `docs/SECURITY_ROTATION.md` (Spanish, matching the docs convention) covering:

1. **Why**: `backend/.env` was committed at `000e3063` and removed at `999109b7`; every
   value in it is burned (visible to anyone with repo/history access).
2. **What to rotate before any production deployment** (types only, no values):
   application `SECRET_KEY` (note: rotating it invalidates all issued JWTs — coordinate
   with the Laravel side, which shares the secret), SMTP/Mailtrap credentials, MinIO
   access/secret keys, Postgres password, and any `API_RRHH_API_KEY` if it was ever real.
3. **How** (per credential: where it lives — env var name from `.env.example` — and the
   external console where it's regenerated).
4. **Optional**: history rewrite with `git filter-repo`/BFG; note it requires force-push and
   team coordination, and is redundant once rotation is done.
5. A checklist table the operator can tick.

**Verify**: file exists; `grep -ciE "(minioadmin|guest|mailtrap.{0,20}[0-9a-f]{6})" docs/SECURITY_ROTATION.md` → 0 real values leaked (naming "minioadmin" as a default to replace is acceptable — adapt the check to: no NEW secret values appear; manual read-through required).

## Test plan

No new automated tests. The verification gates are: compose config validity, the stack
booting with unchanged dev defaults, the docs-gating assertion, the CORS preflight check,
and one existing auth test file as a smoke test (Step table above).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n '\${POSTGRES_PASSWORD' apps/backend/docker-compose.yml` → ≥1 match (and same for MinIO/RabbitMQ vars)
- [ ] `docker compose config -q` exits 0
- [ ] `app/main.py` has no unconditional `docs_url="/docs"` and no `allow_methods=["*"]` / `allow_headers=["*"]`
- [ ] `docs/SECURITY_ROTATION.md` exists and contains no credential values
- [ ] `docker compose exec api sh -c "python -m pytest tests/test_auth_api_simple.py -v --no-cov"` exits 0
- [ ] No files outside the in-scope list modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `app/core/config.py` has no `ENVIRONMENT`-like field — gating needs a settings change, widen scope only after reporting.
- The CORS preflight check fails for a header either frontend actually sends — list the header and stop rather than re-widening to `*`.
- `docker compose config` shows the credential variables are ALSO consumed by services this plan didn't account for (e.g. flower, pgadmin) and changing them breaks startup twice in a row.
- You are tempted to write any real credential value anywhere — don't; re-read the secret-handling rule.

## Maintenance notes

- The runbook's rotation checklist is the gating artifact for production go-live; a
  reviewer should confirm the SECRET_KEY rotation is coordinated with the Laravel system
  (shared `JWT_SECRET` — see CLAUDE.md "JWT Bridge").
- Rate limiting on the public filing endpoints (`/pre-incapacidades/radicar`, document
  upload) was found in the audit and deliberately deferred — it's an M-effort feature
  (SlowAPI + Redis), worth its own plan before public launch.
- `infra/` production deployment (nginx TLS, backups, monitoring) remains unaddressed —
  flagged as a direction finding in plans/README.md.
