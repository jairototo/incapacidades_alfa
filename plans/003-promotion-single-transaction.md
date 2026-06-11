# Plan 003: Make pre-incapacidad promotion atomic (single commit)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/backend/app/services/pre_incapacidad_promotion_service.py apps/backend/tests/test_pre_incapacidad_promotion_service.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding. Plan 002
> adds an idempotency guard near the top of the method — that change is
> EXPECTED and compatible; anything else is a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/007-base-repository-flush-variants.md (and plans/002-promotion-idempotency-guard.md, already merged)
- **Category**: bug
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

`promote_pre_incapacidad()` performs one logical operation — turn a pre-incapacidad into a
filed incapacidad — but commits the database transaction **eight separate times** along the
way (after clearing issues, persisting validations, creating the incapacidad, copying
documents, linking, audit rules, the state transition, and marking PROCESADA). A failure
between any two commits leaves the system in a state no code path expects: e.g. an
`Incapacidad` exists but `pre_incapacidad.estado` is still `PENDIENTE`, or documents are
copied but the link is missing. These states require manual database surgery to fix.
Collapsing to a single commit makes promotion all-or-nothing and also removes seven
round-trips per promotion.

## Current state

Relevant file: `apps/backend/app/services/pre_incapacidad_promotion_service.py`,
method `promote_pre_incapacidad` (lines 36–182 at planning commit).

Commit call sites inside the happy path (all `await self.db.commit()`):
line 73 (after clearing issues), 94 (after persisting validation issues), 103 (after
`create_from_pre_incapacidad`), 108 (after `_copy_documents`), 114 (after linking
`pre_inc.incapacidad_id`), 123 (after audit-rule issues), 128 (after
`radicar_incapacidad`), 133 (after `update_estado(..., "PROCESADA")`).

### Skeleton of the happy path (excerpt, lines 70-133)

```python
            # 2. Clear existing validation issues for idempotent re-runs
            if clear_existing_issues:
                deleted = await self.validation_repo.delete_by_pre_incapacidad(pre_incapacidad_id)
                await self.db.commit()
                await self.db.refresh(pre_inc)
            ...
            for issue_schema in issues:
                await self.validation_repo.create(issue_schema)
            await self.db.commit()
            ...
            # 5. Create Incapacidad unconditionally
            inc = await incapacidad_service.create_from_pre_incapacidad(
                self.db, pre_inc, empleado=empleado, empresa=empresa, usuario_id=usuario_id
            )
            incapacidad_id = inc.id
            await self.db.commit()

            # 5b. Copy documents from pre_incapacidad → incapacidad
            copied = await self._copy_documents(pre_inc.id, incapacidad_id, usuario_id)
            if copied:
                await self.db.commit()

            # 6. Link pre_incapacidad → incapacidad
            pre_inc.incapacidad_id = incapacidad_id
            self.db.add(pre_inc)
            await self.db.commit()
            await self.db.refresh(pre_inc)

            # 7. Run additional audit rules when empleado is found
            if empleado:
                audit_issues = await self._run_audit_business_rules(pre_inc, inc, empleado)
                for issue in audit_issues:
                    await self.validation_repo.create(issue)
                if audit_issues:
                    await self.db.commit()

            # 8. Transition to EN_AUDITORIA
            await incapacidad_service.radicar_incapacidad(self.db, incapacidad_id, usuario_id)
            await self.db.commit()

            # 9. Mark pre-incapacidad as PROCESADA
            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()
```

### Error path (excerpt, lines 157-182)

```python
        except Exception as e:
            from sqlalchemy.exc import SQLAlchemyError
            ...
            is_infra = isinstance(e, SQLAlchemyError) or (_PgError and isinstance(e, _PgError))
            if is_infra:
                raise

            logger.error(f"Error in unified promotion for {pre_incapacidad_id}: {e}")
            try:
                await self.pre_inc_repo.update_error(self.db, pre_incapacidad_id, str(e))
                await self.db.commit()
            except Exception:
                pass

            return PromotionResult(success=False, ...)
```

Facts verified at planning time:

- `incapacidad_service.create_from_pre_incapacidad` and `incapacidad_service.radicar_incapacidad`
  (both in `apps/backend/app/services/incapacidad_service.py`) do **not** call `commit()`
  internally — re-verify with the grep in Step 1.
- Repository methods use `flush()`, not `commit()` (e.g. `pre_incapacidad_repository.update_estado`
  at `apps/backend/app/db/repositories/pre_incapacidad_repository.py:53-64` flushes).
- The caller is a Celery task (`apps/backend/app/tasks/incapacidad_tasks.py`,
  `promote_pre_incapacidad_task`) that opens its own session per run, and the internal
  endpoint `POST /pre-incapacidades/{id}/promover` which uses the request session.
- Tests: `tests/test_pre_incapacidad_promotion_service.py` is DB-backed (real
  `db_session` fixture from `tests/conftest.py:154`) and covers the unified flow —
  these are the characterization tests protecting this refactor.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Service tests | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py -v --no-cov"` | all pass |
| Internal-commit grep | `grep -n "commit" apps/backend/app/services/incapacidad_service.py` | inspect — see Step 1 |
| Lint | from `apps/backend/`: `make lint` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `apps/backend/app/services/pre_incapacidad_promotion_service.py`
- `apps/backend/tests/test_pre_incapacidad_promotion_service.py`

**Out of scope** (do NOT touch, even though they look related):
- `apps/backend/app/services/incapacidad_service.py` — if it turns out to commit internally inside the called methods, that's a STOP condition, not something to refactor here.
- `apps/backend/app/db/repositories/*` — repository flush semantics are correct.
- The endpoint and Celery task — their session handling is unchanged.

## Git workflow

- Branch: `bugfix/promotion-single-transaction`
- Conventional Commits, e.g. `fix: make pre-incapacidad promotion atomic with single commit`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Confirm no nested commits in the call chain

Run `grep -n "await db.commit()\|await self.db.commit()\|\.commit()" apps/backend/app/services/incapacidad_service.py`
and locate which methods contain them. Confirm that neither `create_from_pre_incapacidad`
nor `radicar_incapacidad` (nor anything they call — check `historial_estado` writes inside
`radicar_incapacidad`) commits. Commits in OTHER methods of the file are fine.

**Verify**: no `commit()` inside the two methods' bodies → proceed. Otherwise STOP.

### Step 2: Collapse the commits

**Prerequisite**: Plan 007 must already be merged. Its `flush_only=True` params on
`incapacidad_service.create_from_pre_incapacidad` and `incapacidad_service.radicar_incapacidad`
are what make this step safe. Verify with:
`grep -n "flush_only" apps/backend/app/services/incapacidad_service.py` → ≥4 lines.
If not present, STOP — execute Plan 007 first.

In `promote_pre_incapacidad`:

- Replace the commits at lines 73, 94, 103, 108, 114, 123, 128 with `await self.db.flush()`
  **only where a later step reads what was just written** (the incapacidad create at
  line 103 needs a flush so `inc.id` is populated; the link at 114 and validation-issue
  creates flush via the repos already — when in doubt, `flush()` is always safe).
- At line 119 (or wherever `create_from_pre_incapacidad` is called), add `flush_only=True`:
  ```python
  inc = await incapacidad_service.create_from_pre_incapacidad(
      self.db, pre_inc, empleado=empleado, empresa=empresa, usuario_id=usuario_id,
      flush_only=True,
  )
  ```
- At the `radicar_incapacidad` call (step 8), add `flush_only=True`:
  ```python
  await incapacidad_service.radicar_incapacidad(self.db, incapacidad_id, usuario_id, flush_only=True)
  ```
- Keep exactly ONE `await self.db.commit()` — after step 9 (`update_estado(..., "PROCESADA")`),
  before the `count_by_severidad` read.
- Move `await self.db.refresh(pre_inc)` calls as needed
  (the one after `delete_by_pre_incapacidad` can stay after a `flush()`; the one after linking
  `pre_inc.incapacidad_id` stays after a `flush()` — audit rules need the refreshed pre_inc).
- In the **non-infra error path**: add `await self.db.rollback()` BEFORE
  `update_error(...)` + `commit()`, so the failed partial work is discarded and only the
  ERROR estado lands. In the **infra path** (`is_infra: raise`), add a
  `await self.db.rollback()` before `raise` so the Celery task doesn't retry on a dirty session.

**Verify**: `grep -c "await self.db.commit()" apps/backend/app/services/pre_incapacidad_promotion_service.py` → exactly 2 in `promote_pre_incapacidad` (one happy-path, one in the error handler). The idempotency-guard path from Plan 002 contains none.

### Step 3: Add a failure-atomicity test

In `tests/test_pre_incapacidad_promotion_service.py` add
`test_promote_failure_leaves_no_partial_state`: use `unittest.mock.patch` to make
`incapacidad_service.radicar_incapacidad` raise `ValueError("boom")` (a non-infra error),
promote `pre_inc_valida`, then assert:

- `result.success is False`,
- NO `Incapacidad` row exists for this pre-incapacidad (count == 0 — this is the key
  assertion that used to fail under the 8-commit version),
- `pre_inc.estado == "ERROR"` after refresh and `pre_inc.incapacidad_id is None`.

Model the mocking style on existing patches in the test file or
`tests/unit/test_unified_promotion.py` (heavily mocked — use only its patch style, not
its structure).

**Verify**: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py -v --no-cov"` → all pass, including the new test.

### Step 4: Run the wider promotion-related suites

**Verify**: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py tests/test_validaciones_endpoint.py -v --no-cov"` → all pass. `make lint` → exit 0.

## Test plan

- New: `test_promote_failure_leaves_no_partial_state` (Step 3) — the regression this plan exists to prevent.
- Existing DB-backed tests in `test_pre_incapacidad_promotion_service.py` (document copy, PROCESADA marking, validation counts) act as characterization tests — they must pass unchanged. If any of them asserts on intermediate-commit visibility, treat as a STOP condition rather than rewriting the assertion.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "flush_only" apps/backend/app/services/incapacidad_service.py` → ≥4 lines (Plan 007 landed)
- [ ] Exactly one happy-path `commit()` in `promote_pre_incapacidad` (plus one in the error handler)
- [ ] `rollback()` present in both error branches (infra re-raise and `update_error` path)
- [ ] `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py tests/test_validaciones_endpoint.py -v --no-cov"` exits 0
- [ ] `make lint` exits 0
- [ ] No files outside the in-scope list modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- Step 1 finds a `commit()` inside `create_from_pre_incapacidad` or `radicar_incapacidad`
  (or in a service/repo they call). Restructuring those is out of scope.
- An existing test fails because it depends on intermediate commits being visible
  (e.g. it opens a second session mid-promotion). That implies a concurrent reader
  depends on partial state — needs an operator decision.
- Plan 002's guard is NOT present in the method (execute plans in order; this plan's
  error-path rollback assumes the guard exists for safe retries).
- The new failure test still finds a persisted `Incapacidad` after your refactor and you
  cannot explain why within two attempts — the session/transaction model may differ from
  the plan's assumption (e.g. autobegin quirks); report findings.

## Maintenance notes

- After this lands, promotion is all-or-nothing: a reviewer should check that the Celery
  task's retry policy (if any is later added) is compatible — retries are now safe thanks
  to Plan 002's guard plus atomicity.
- If a future change adds an external side effect inside the flow (e.g. sending an email,
  writing to MinIO), it must happen AFTER the single commit, or be compensated on rollback —
  the document copy step copies DB metadata only (verified at planning time), which is why
  it can sit inside the transaction.
- Deferred (out of scope here): the radicar endpoint swallowing task-enqueue failures
  (`pre_incapacidades.py:71-77`) still leaves pre-incapacidades stuck in `PENDIENTE` with
  no retry mechanism; a periodic reconciliation sweep is the natural follow-up.
