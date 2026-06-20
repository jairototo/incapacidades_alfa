# feat: portal-externo authenticated EMPRESA portal (5-phase refactor)

Converts `apps/frontend/portal-externo` from a public portal into an authenticated portal for `EMPRESA` users, with individual + bulk disability filing, an audit background job, external-integration stubs, and a company-scoped inquiry.

Design + plans: `docs/superpowers/specs/2026-06-19-portal-externo-empresa-refactor-design.md` and `docs/superpowers/plans/2026-06-19-phase{1-5}-*.md`.

> **Scope note:** this branch is well ahead of `master` and includes pre-existing dev-branch work. The commits relevant to this refactor are `f54acdd8 … e6a88fa8` (+ docs `3296082a`). Every task below was implemented TDD and passed an independent spec-compliance + code-quality review.

## What changed

### Phase 1 — Authentication
- `/auth/me` enriched with `empresa_id` + company summary.
- Frontend: Zustand `authStore`, JWT axios with silent refresh, `LoginPage` (EMPRESA-only gate), `ProtectedRoute` (authenticated **and** `EMPRESA` **and** linked company), 3-action dashboard. Public `/radicar`/`/consultar` routes retired.

### Phase 2 — Individual filing
- `incapacidad.prorroga` (migration). `solicitante_resolver` (resolves/creates solicitante from the company). Shared `RadicacionPipelineService` (creates `Incapacidad` directly, validates employee↔company, savepoint+retry on numero collisions, injected audit/integration hooks). `POST /incapacidades/radicar` (multipart, EMPRESA-only, document storage, fault-isolated summary email). Frontend filing page + company-scoped employee selector.

### Phase 3 — Bulk filing
- `communication_log` + `incapacidad.numero_radicacion_servialfa` (migration). ServiAlfa/Sicat **stub** clients + `IntegracionService` (logs every attempt). Shared dict-based validation rules. Excel template / validation (robust to malformed cells/files) / ZIP-mapping endpoints. Bulk submit (server-side re-validation, reuses the pipeline, per-document failure isolation → `documentos_ignorados`, one summary email). Frontend: template modal, validation table (errors red / warnings yellow), ZIP upload, and the gated-submit page (banner + row highlight + scroll-to-first-blocking).

### Phase 4 — Audit background job
- `auditoria_resultado` (migration). `auditoria_service` evaluates every rule on the `Incapacidad`, stores each result (pass **and** fail), and transitions `RADICADA → EN_AUDITORIA` (+ historial). `auditar_incapacidad_task` (Celery) replaces the temporary no-op enqueue.

### Phase 5 — Inquiry
- `GET /incapacidades/mi-empresa` (EMPRESA-only; `empresa_id` forced from the token — a company can only ever see its own records). Frontend: filter bar, results table, and the inquiry page with a detail drawer reusing `DetalleIncapacidad`/`TimelineEstados`.

## Locked decisions
ARL-only · own login reusing `/auth/login` · unified pipeline (individual = bulk, N=1) · WARNINGs advisory (only ERROR blocks) · inquiry forced to the token's company · `auditoria_resultado` is a new table · internal `numero` now / ServiAlfa definitive number later.

## Migrations (linear, single head `07881f00b038`)
`prorroga` → `numero_radicacion_servialfa` + `communication_log` → `auditoria_resultado`.

## Testing
Backend: pytest in Docker (per-feature suites all green). Frontend: vitest targeted suites + `tsc --noEmit` clean for all new code.

> Note: the portal-externo strict `tsc -b` build has ~89 **pre-existing** errors in old wizard/consulta code (unrelated to this refactor); verification was gated on `tsc --noEmit` + targeted tests by decision.

## Follow-ups (tracked, not blocking — to address before production)
- **Harden `radicar_individual` document-upload** with the same per-doc isolation the bulk endpoint has (currently a doc-upload failure 500s after the incapacidad is already committed).
- **Scope `GET /empleados`** to the token's `empresa_id` for EMPRESA callers (currently accepts a client-supplied `empresa_id` → can enumerate other companies' employees). Should not ship to production as-is.
- `docker compose build` so `openpyxl` + `fflate` persist in fresh containers.
- Async-wrap `DocumentoService` storage I/O (currently blocks the event loop).
- `IntegrityError` guard on `resolve_solicitante_for_empresa` (concurrent same-company race).
- Replace the ServiAlfa/Sicat **stubs** with real HTTP clients when specs arrive (interfaces are ready).
- Cleanup: orphaned old wizard (`src/components/wizard/*`, `src/schemas/radicacionSchema.ts`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
