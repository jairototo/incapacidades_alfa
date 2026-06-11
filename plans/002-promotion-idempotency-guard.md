# Plan 002: Add idempotency guard to pre-incapacidad promotion

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/backend/app/services/pre_incapacidad_promotion_service.py apps/backend/tests/test_pre_incapacidad_promotion_service.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

`PromotePreIncapacidadService.promote_pre_incapacidad()` is invoked fire-and-forget from a
Celery task when a citizen files a claim, and can also be triggered manually via the
internal `POST /pre-incapacidades/{id}/promover` endpoint. It has **no guard against
running twice on the same pre-incapacidad**: a second run creates a second `Incapacidad`
record, overwrites `pre_incapacidad.incapacidad_id` with the new UUID, and orphans the
first incapacidad (which has already entered the audit workflow). Celery retries, a double
task enqueue, or an operator clicking "promover" on an already-processed record all trigger
this. The fix is a small early-return guard plus tests.

## Current state

Relevant files:

- `apps/backend/app/services/pre_incapacidad_promotion_service.py` — `promote_pre_incapacidad` (lines 36–182). The guard goes right after the fetch at lines 56–68.
- `apps/backend/app/models/pre_incapacidad.py:35-40` — `estado` column, allowed values documented as `PENDIENTE | PROCESADA | RECHAZADA | ERROR | DEVUELTA`, default `PENDIENTE`. The model also has an `incapacidad_id` FK (nullable) set during promotion.
- `apps/backend/app/schemas/validation_inconsistencia.py:47-54` — `PromotionResult`: `success: bool`, `pre_incapacidad_id: UUID`, `incapacidad_id: Optional[UUID]`, `validation_summary: ValidationSummary`, `error_message: Optional[str]`, `timestamp: datetime`.
- `apps/backend/tests/test_pre_incapacidad_promotion_service.py` — DB-backed tests for this service; 317 lines, fixtures `pre_inc_valida`, `pre_inc_sin_empresa`, etc.

### Service entry — `pre_incapacidad_promotion_service.py:55-76` (exact current code)

```python
        try:
            # 1. Fetch pre-incapacidad
            pre_inc = await self.pre_inc_repo.get_by_id(self.db, pre_incapacidad_id)
            if not pre_inc:
                logger.error(f"Pre-incapacidad {pre_incapacidad_id} not found")
                return PromotionResult(
                    success=False,
                    pre_incapacidad_id=pre_incapacidad_id,
                    validation_summary=ValidationSummary(
                        total_issues=0, errors=0, warnings=0, infos=0, issues=[],
                    ),
                    error_message="Pre-incapacidad no encontrada",
                    timestamp=datetime.utcnow(),
                )

            # 2. Clear existing validation issues for idempotent re-runs
            if clear_existing_issues:
                deleted = await self.validation_repo.delete_by_pre_incapacidad(pre_incapacidad_id)
```

### How a success result is built — same file, lines 135-155 (exact current code)

```python
            counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
            validation_summary = ValidationSummary(
                total_issues=counts["total"],
                errors=counts["ERROR"],
                warnings=counts["WARNING"],
                infos=counts["INFO"],
                issues=[],
            )
            ...
            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=incapacidad_id,
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )
```

### Existing test to model after — `tests/test_pre_incapacidad_promotion_service.py:186-196` (exact current code)

```python
async def test_promote_first_call_succeeds_and_marks_procesada(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Primera llamada a promote con empresa inexistente crea incapacidad y marca PROCESADA."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result.success is True
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.estado == "PROCESADA"
    assert pre_inc_sin_empresa.incapacidad_id is not None
```

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests for this service | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py -v --no-cov"` | all pass |
| Lint | from `apps/backend/`: `make lint` | exit 0 |

(Repo convention: run backend tests inside the Docker container, and only the test files for what you changed.)

## Scope

**In scope** (the only files you should modify):
- `apps/backend/app/services/pre_incapacidad_promotion_service.py`
- `apps/backend/tests/test_pre_incapacidad_promotion_service.py`

**Out of scope** (do NOT touch, even though they look related):
- `apps/backend/app/api/v1/endpoints/pre_incapacidades.py` — the `/promover` endpoint's response handling is fine once the service is idempotent.
- `apps/backend/app/tasks/incapacidad_tasks.py` — Celery retry policy is a separate concern.
- The multi-commit transaction structure of the service — that is Plan 003; do not restructure commits here.

## Git workflow

- Branch: `bugfix/promotion-idempotency-guard`
- Conventional Commits, e.g. `fix: skip promotion when pre-incapacidad already processed`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add the guard

In `promote_pre_incapacidad`, immediately after the `if not pre_inc:` early return
(i.e. right before the `# 2. Clear existing validation issues` block), add:

```python
            # Idempotency guard: never promote twice
            if pre_inc.estado == "PROCESADA" or pre_inc.incapacidad_id is not None:
                logger.info(
                    f"Pre-incapacidad {pre_incapacidad_id} already promoted "
                    f"(estado={pre_inc.estado}, incapacidad_id={pre_inc.incapacidad_id}); skipping"
                )
                counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
                return PromotionResult(
                    success=True,
                    pre_incapacidad_id=pre_incapacidad_id,
                    incapacidad_id=pre_inc.incapacidad_id,
                    validation_summary=ValidationSummary(
                        total_issues=counts["total"],
                        errors=counts["ERROR"],
                        warnings=counts["WARNING"],
                        infos=counts["INFO"],
                        issues=[],
                    ),
                    timestamp=datetime.utcnow(),
                )
```

Note `success=True`: an already-promoted record is a success from the caller's
perspective (the Celery task must not retry it). The guard performs **no writes**.

**Verify**: `grep -n "Idempotency guard" apps/backend/app/services/pre_incapacidad_promotion_service.py` → 1 match, located before the `clear_existing_issues` block.

### Step 2: Add idempotency tests

In `tests/test_pre_incapacidad_promotion_service.py`, after
`test_promote_first_call_succeeds_and_marks_procesada`, add (same style/fixtures):

1. `test_promote_second_call_is_noop` — promote `pre_inc_sin_empresa` twice; assert:
   - both results have `success is True`,
   - `result2.incapacidad_id == result1.incapacidad_id`,
   - exactly ONE `Incapacidad` row exists for this promotion: `select(func.count()).select_from(Incapacidad).where(Incapacidad.id == result1.incapacidad_id)` is 1, and a count of all Incapacidad rows created in the test equals 1 (the fixtures create none themselves — verify with a total count before/after the second call),
   - `pre_inc.estado` is still `"PROCESADA"` after refresh.
2. `test_promote_skips_when_incapacidad_id_set` — manually set `pre_inc.incapacidad_id` to the id from a first promotion but reset `estado` to `"PENDIENTE"` (simulates a crash after linking, before the estado update); promote again; assert no second Incapacidad is created and the returned `incapacidad_id` equals the pre-set one.

Import anything missing (`select`, `func`, `Incapacidad`) following the file's existing imports.

**Verify**: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py -v --no-cov"` → all pass, including the 2 new tests.

## Test plan

Covered by Step 2: double-call no-op, and the partial-crash state (`incapacidad_id` set,
estado not yet `PROCESADA`). Existing tests in the same file guard against regression of
the normal first-call flow. Pattern file: this same test module.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py -v --no-cov"` exits 0 with 2 new tests collected
- [ ] `make lint` exits 0
- [ ] The guard returns BEFORE `delete_by_pre_incapacidad` is called (no writes on the skip path) — confirm by code position
- [ ] No files outside the in-scope list modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The code at lines 55–76 no longer matches the excerpt (Plan 003 may have landed first and restructured the method — the guard is still needed, but placement must be re-derived; report and ask).
- You find an existing test that EXPECTS re-promotion of a `PROCESADA` record to create a new incapacidad (search the test file for "re-promote", "PROCESADA", "promover dos veces") — that would mean re-promotion is an intended product flow and the guard semantics need an operator decision.
- The estados `DEVUELTA` / `RECHAZADA` turn out to flow back through this service (grep callers of `promote_pre_incapacidad`): the guard above deliberately does NOT block them; if a caller relies on blocking them too, report instead of widening the guard.

## Maintenance notes

- Plan 003 (single-transaction promotion) builds directly on this guard: once promotion is
  atomic, the partial-crash state in test 2 can no longer occur, but the test remains valid.
- If a reconciliation sweeper is ever added for pre-incapacidades stuck in `PENDIENTE`
  (the radicar endpoint swallows task-enqueue failures — see `pre_incapacidades.py:71-77`),
  this guard is what makes the sweeper safe to run repeatedly.
- Reviewer should scrutinize: the guard treats `estado == "ERROR"` as retryable (no block) —
  that is intentional, `update_error` is the failure path and retries should proceed.
