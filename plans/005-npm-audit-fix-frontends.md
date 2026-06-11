# Plan 005: Patch known-vulnerable npm dependencies in both frontends

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/frontend/portal-externo/package.json apps/frontend/portal-externo/package-lock.json apps/frontend/sistema-interno/package.json apps/frontend/sistema-interno/package-lock.json`
> If lockfiles changed since planning, re-run `npm audit` first — the numbers
> below may be stale.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (Plan 004's CI makes verification durable but is not required)
- **Category**: security
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

`npm audit` at planning time reports **15 vulnerabilities in sistema-interno (2 critical,
8 high, 5 moderate)** and **14 in portal-externo (1 critical, 8 high, 5 moderate)**. The
high-severity cluster is `react-router`/`react-router-dom` 7.0.0–7.14.2 (both apps pin
`react-router-dom: ^7.12.0`): advisories include XSS, open redirect, and DoS issues fixed
in later 7.x patches. `axios`/`follow-redirects` carry moderate credential-leak advisories,
and `ws` a moderate memory-disclosure one. portal-externo is the **public** filing portal,
so its client-side stack is the exposed surface. npm reports fixes available via
`npm audit fix` (no breaking `--force` needed for the prod-dependency cluster).

## Current state

- `apps/frontend/portal-externo/` — public portal, "100% complete", 217 tests (vitest).
- `apps/frontend/sistema-interno/` — internal dashboard, in active development.
- Both: `"react-router-dom": "^7.12.0"` in `package.json`; caret ranges mean lockfile
  updates within 7.x are enough — `package.json` itself may not need edits.
- Scripts in both: `lint` = `eslint .`, `test` = `vitest` (watch mode — use
  `npx vitest run` for one-shot), `build` = `tsc -b && vite build`.
- Some reported vulnerabilities are in dev-only tooling (`vitest`/`@vitest/coverage-v8`
  beta range, `ws`); patching them is good hygiene but the priority is the production
  dependency cluster (`react-router`, `axios`, `follow-redirects`).

## Commands you will need

| Purpose | Command (run in EACH frontend dir) | Expected on success |
|---------|-----------------------------------|---------------------|
| Audit before | `npm audit` | record counts |
| Fix | `npm audit fix` | exit 0, lockfile updated |
| Audit after | `npm audit --omit=dev` | 0 critical, 0 high |
| Tests | `npx vitest run` | all pass |
| Lint | `npm run lint` | exit 0 |
| Build | `npm run build` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `apps/frontend/portal-externo/package.json` and `package-lock.json`
- `apps/frontend/sistema-interno/package.json` and `package-lock.json`

**Out of scope** (do NOT touch):
- Any source file in either frontend. If a dependency bump requires a code change, that's a STOP condition.
- `npm audit fix --force` — never. Forced major bumps (e.g. vitest 4 beta → other major) can break the test suites; report what `--force` would have done instead.
- The backend (`pip` deps) — separate concern, see plans/README.md rejected/deferred notes.
- Upgrading Zod or Tailwind majors — explicitly deferred; the two apps intentionally differ (see CLAUDE.md "Frontend Library Version Mismatch").

## Git workflow

- Branch: `bugfix/npm-audit-frontends`
- Conventional Commits, e.g. `fix: patch react-router and axios advisories in both frontends`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: portal-externo

```
cd apps/frontend/portal-externo
npm audit            # record the "before" counts
npm audit fix
npm audit --omit=dev # expect 0 critical / 0 high
npx vitest run && npm run lint && npm run build
```

If `npm audit --omit=dev` still shows high/critical after `fix`, check whether the
remaining advisory's fixed version is within the semver range; if it requires a major bump,
record it and continue (STOP condition only if it's the react-router cluster).

**Verify**: `npm audit --omit=dev` → 0 critical, 0 high; `npx vitest run` → all 217-ish tests pass; `npm run build` → exit 0.

### Step 2: sistema-interno

Same sequence in `apps/frontend/sistema-interno`.

**Verify**: `npm audit --omit=dev` → 0 critical, 0 high; `npx vitest run` → all pass; `npm run build` → exit 0.

### Step 3: Record the delta

In the commit message body (or final report), list before/after vulnerability counts per
app and the main packages bumped (read them from `git diff package-lock.json | grep '"version"'`
or npm's output).

## Test plan

No new tests. Both apps' existing suites (`npx vitest run`) plus `tsc -b` via the build
are the regression net — react-router is exercised by the routing tests and any page test
that renders a router.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `npm audit --omit=dev` reports 0 critical and 0 high in BOTH frontend dirs
- [ ] `npx vitest run` exits 0 in both
- [ ] `npm run lint` and `npm run build` exit 0 in both
- [ ] Only the four in-scope files are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `npm audit fix` cannot remediate the react-router high-severity cluster within the
  `^7.12.0` range (i.e. the fix needs a major bump or `--force`).
- Any test fails after the fix and the failure traces to a behavior change in a bumped
  package — report the package and failing test; do not patch app code in this plan.
- `npm audit fix` modifies dependencies you can't account for (lockfile churn > ~30
  packages) — show the diff summary and ask.

## Maintenance notes

- Dev-only advisories that remain (vitest beta range, `ws`) are acceptable short-term;
  note them in the report. The vitest coverage package is on a 4.x **beta** range —
  moving to a stable vitest is a separate, deliberate upgrade.
- Plan 004's CI should eventually add a scheduled `npm audit --omit=dev` job so this
  doesn't silently regress.
- The backend's Python pins (`fastapi==0.109.0`, `sqlalchemy==2.0.25`, `asyncpg==0.29.0`,
  early-2024 vintage) were flagged in the audit but deferred: run `pip-audit` before any
  production deployment and plan upgrades separately — SQLAlchemy/asyncpg bumps need real
  testing, not a lockstep audit-fix.
