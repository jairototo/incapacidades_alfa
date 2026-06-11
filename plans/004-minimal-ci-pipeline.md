# Plan 004: Restore a minimal CI pipeline (lint + tests on every push/PR)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- .github/ apps/backend/Makefile apps/backend/requirements*.txt apps/frontend/sistema-interno/package.json apps/frontend/portal-externo/package.json`
> If `.github/workflows/` already contains a CI workflow, STOP — someone
> restored CI independently; reconcile instead of duplicating.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

Commit `3cd06819` ("delete pipeline github actions") removed the repo's only GitHub
Actions workflow. There is now **no automated verification of any kind**: no lint, no
tests, no build check on push or PR, and no pre-commit hooks (confirmed in `AGENTS.md`).
The project is on a branch literally named `iniciando_desarrollo_para_produccion` — heading
to production with no verification gate. Every other plan in this directory relies on
tests passing; CI is what makes that durable. This plan creates one workflow with three
jobs: backend (ruff + pytest against a Postgres service), and one lint+test+build job per
frontend.

## Current state

- `.github/workflows/` does not exist (only `.github/copilot-instructions.md` and `.github/prompts/`).
- Backend: `apps/backend/` — Python/FastAPI. `Makefile` targets exist: `test` (pytest with
  coverage, threshold 70%), `lint` (ruff + mypy), `install`. Dependencies in
  `apps/backend/requirements.txt` (check for a `requirements-dev.txt` — the Makefile's
  `install` target shows what dev deps are needed; replicate its pip commands in CI).
- Backend tests derive their DB from settings: `tests/conftest.py:21`:
  `TEST_DATABASE_URL = settings.DATABASE_URL.replace("/incapacidades", "/incapacidades_test")`.
  So CI must provide a Postgres with BOTH databases `incapacidades` (in the URL) and
  `incapacidades_test` (used by tests). The fixture (`conftest.py:33`) drops/recreates the
  schema itself, so no migrations need to run in CI.
- Backend settings come from env / `.env` (`app/core/config.py`). Required env vars are
  listed in `apps/backend/.env.example` — the critical ones for tests: `DATABASE_URL`,
  `SECRET_KEY` (≥32 chars), `ALGORITHM`, `REDIS_URL`, `CELERY_BROKER_URL`,
  `CELERY_RESULT_BACKEND`, `STORAGE_BACKEND=filesystem`, `FILESYSTEM_BASE_PATH`,
  `ENVIRONMENT`, `DEBUG`. Copy placeholder values from `.env.example`, NOT from any real `.env`.
- Frontends: `apps/frontend/portal-externo` and `apps/frontend/sistema-interno`. Scripts
  (identical in both `package.json`s): `lint` = `eslint .`, `test` = `vitest`
  (**watch mode — CI must use `npx vitest run` instead**), `build` = `tsc -b && vite build`.
  Both have `package-lock.json` (verify; if present use `npm ci`).
- Node version: check `.nvmrc` / `engines` in package.json; if absent use Node 22 LTS.
  Python version: check `apps/backend/Dockerfile` or `pyproject.toml`/`setup.cfg` for the
  pinned version; the docker image will state it (e.g. `FROM python:3.12`). Match it.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Validate workflow syntax | `gh workflow list` after push, or `actionlint .github/workflows/ci.yml` if available locally | no errors |
| Local backend test rehearsal | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/ -x -q --no-cov"` | informative — see Step 2 |
| Frontend test rehearsal | from each frontend dir: `npx vitest run` and `npm run lint` and `npm run build` | exit 0 |

## Scope

**In scope** (the only files you should create/modify):
- `.github/workflows/ci.yml` (create)
- `AGENTS.md` — update the single line claiming "No lint/test CI yet" once CI exists.

**Out of scope** (do NOT touch):
- Any application code or test code. If a test fails in CI, do not "fix" the test in this plan — report it (see STOP conditions).
- Deployment/CD, coverage upload services, pre-commit hooks, branch protection rules (mention to operator at the end; configuring GitHub settings is theirs).
- The deleted `auto-documentation.yml` workflow — do not resurrect it.

## Git workflow

- Branch: `feature/ci-pipeline`
- Conventional Commits, e.g. `feat: add CI workflow with backend and frontend gates`
- Do NOT push or open a PR unless the operator instructed it. NOTE: CI cannot be fully
  verified without pushing; ask the operator to push the branch when you reach Step 4.

## Steps

### Step 1: Rehearse each job locally

Before writing YAML, run locally and record results:

1. Frontends (host machine, from each frontend dir): `npm ci && npm run lint && npx vitest run && npm run build`.
2. Backend (inside the running container): `docker compose exec api sh -c "python -m pytest tests/ -q --no-cov"` and `docker compose exec api sh -c "ruff check app/"`.

If the full backend suite fails locally TODAY, note which tests fail — CI should initially
run exactly what passes; a pre-broken gate teaches people to ignore CI (see STOP conditions).

**Verify**: a written list of the passing commands and any failures, included in your final report.

### Step 2: Write `.github/workflows/ci.yml`

Three jobs, triggered on `push` to all branches and `pull_request` to `master`:

```yaml
name: CI
on:
  push:
  pull_request:
    branches: [master]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: apps/backend } }
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: incapacidades
        ports: ['5432:5432']
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10
      redis:
        image: redis:7
        ports: ['6379:6379']
    env:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/incapacidades
      REDIS_URL: redis://localhost:6379/0
      CELERY_BROKER_URL: redis://localhost:6379/1
      CELERY_RESULT_BACKEND: redis://localhost:6379/2
      SECRET_KEY: ci-only-secret-key-not-used-anywhere-real-0123456789
      ALGORITHM: HS256
      STORAGE_BACKEND: filesystem
      FILESYSTEM_BASE_PATH: /tmp/ci-storage
      ENVIRONMENT: test
      DEBUG: 'false'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12', cache: pip }   # match the Dockerfile's version
      - run: pip install -r requirements.txt -r requirements-dev.txt  # mirror `make install`
      - run: psql postgresql://postgres:postgres@localhost:5432/postgres -c 'CREATE DATABASE incapacidades_test'
      - run: ruff check app/
      - run: python -m pytest tests/ -q --no-cov   # tighten to coverage gate later

  frontend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [portal-externo, sistema-interno]
    defaults: { run: { working-directory: apps/frontend/${{ matrix.app }} } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: apps/frontend/${{ matrix.app }}/package-lock.json }
      - run: npm ci
      - run: npm run lint
      - run: npx vitest run
      - run: npm run build
```

Adjust to reality discovered in Step 1: exact Python version from the backend Dockerfile,
dev-requirements file name from the Makefile `install` target, whether `mypy` passes
(add it only if it passes locally), whether any extra env var is demanded by
`app/core/config.py` (it will raise a validation error naming the missing field — add that
field with the `.env.example` placeholder). If `pytest tests/ --no-cov` fails on specific
tests in Step 1, scope the CI run to the passing set explicitly (e.g. `--ignore=...`) and
list the exclusions in a YAML comment with a TODO.

**Verify**: YAML parses — `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"` → no error (run from repo root).

### Step 3: Update AGENTS.md

Replace the "No lint/test CI yet — run checks locally before merging" line with a short
description of the new workflow and its three jobs.

**Verify**: `grep -n "No lint/test CI" AGENTS.md` → no matches.

### Step 4: Hand off for push

Ask the operator to push the branch and confirm the workflow goes green in the Actions tab.
Report the run URL or the failure log verbatim.

## Test plan

CI is itself the test infrastructure; the verification is a green run on GitHub. Local
rehearsal in Step 1 is the proxy. No application tests are added or changed by this plan.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `.github/workflows/ci.yml` exists, parses as YAML, and contains a backend job (postgres+redis services, `CREATE DATABASE incapacidades_test`, ruff, pytest) and a frontend matrix job using `npx vitest run` (NOT `npm test`)
- [ ] Every env var the backend job sets uses placeholder/CI-only values — `grep -ci "minioadmin\|mailtrap" .github/workflows/ci.yml` → 0
- [ ] AGENTS.md no longer claims there is no CI
- [ ] Local rehearsal results documented in the final report
- [ ] No files outside the in-scope list modified (`git status`)
- [ ] `plans/README.md` status row updated (use `BLOCKED: awaiting push` if the operator hasn't pushed yet)

## STOP conditions

Stop and report back (do not improvise) if:

- The backend suite has >5 failing tests locally in Step 1 — the repo's baseline is redder
  than this plan assumes; report the list so failures become their own findings.
- `app/core/config.py` requires a credential CI cannot fake (e.g. a real external API key
  validated at startup) — report which field.
- `requirements-dev.txt` (or equivalent) doesn't exist and the Makefile installs dev deps
  some other way you cannot replicate in two attempts.
- A workflow already exists under `.github/workflows/` (drift check).

## Maintenance notes

- Coverage gates are deliberately off (`--no-cov`) for the first green run; the follow-up
  is to re-enable `make test`'s 70% threshold once the team sees CI stay green for a week.
- When Plan 001 (auth) and Plans 002/003 (promotion) land, their test files run here
  automatically — that's the point.
- Operator follow-ups outside the executor's reach: enable branch protection on `master`
  requiring the CI checks; consider adding `pip-audit` and `npm audit --omit=dev` as a
  scheduled (not gating) job.
