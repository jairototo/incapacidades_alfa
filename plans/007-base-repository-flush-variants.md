# Plan 007: Add flush-only variants to BaseRepository (Plan 003 prerequisite)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/backend/app/db/repositories/base_repository.py apps/backend/app/services/incapacidad_service.py apps/backend/app/services/historial_estado_service.py`
> Expected: only Plan 001 and Plan 002 changes in other files — these three files
> should be UNCHANGED since planning commit. Any modification to them is a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: —
- **Blocks**: plans/003-promotion-single-transaction.md
- **Category**: refactor / prerequisite
- **Planned at**: commit `7958670b` (discovered during Plan 003 execution), 2026-06-10

## Why this matters

Plan 003 (atomic promotion) requires that `incapacidad_service.create_from_pre_incapacidad`
and `incapacidad_service.radicar_incapacidad` do NOT commit during a caller-managed
transaction. But both methods ultimately call `BaseRepository.create` and `BaseRepository.update`,
which unconditionally call `await db.commit()`.

This plan adds parallel `create_flushed` / `update_flushed` variants to `BaseRepository`
(flush semantics: writes are sent to the DB engine within the open transaction but NOT committed).
It also adds `flush_only=False` parameters to the three affected service methods so callers can
opt into flush-only behavior without changing the default for the ~25 other call sites.

No existing caller is modified. All existing behavior is preserved.

## Current state

### `apps/backend/app/db/repositories/base_repository.py` (lines 34–49, 131–172, 174–188)

```python
async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
    db_obj = self.model(**obj_in)
    db.add(db_obj)
    await db.commit()          # ← commits
    await db.refresh(db_obj)
    return db_obj

async def update(self, db: AsyncSession, id: UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
    update_data = {k: v for k, v in obj_in.items() if v is not None}
    if not update_data:
        return await self.get_by_id(db, id)
    stmt = (
        update(self.model)
        .where(self.model.id == id)
        .values(**update_data)
        .returning(self.model)
    )
    result = await db.execute(stmt)
    await db.commit()          # ← commits
    updated_obj = result.scalar_one_or_none()
    if updated_obj:
        await db.refresh(updated_obj)
    return updated_obj
```

### `apps/backend/app/services/incapacidad_service.py`

`create_from_pre_incapacidad` (line 207):
```python
incapacidad = await self.repository.create(db, incapacidad_dict)
return await self.repository.get_by_id_with_relations(db, incapacidad.id)
```

`radicar_incapacidad` (line 483):
```python
incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)

# Registrar en historial
await historial_estado_service.create_historial_entry(
    db=db, entity_type="incapacidad", entity_id=incapacidad_id,
    estado_anterior=estado_anterior.value if estado_anterior else None,
    estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
    observacion="Incapacidad radicada para auditoría",
    cambiado_por_id=usuario_id
)
return incapacidad_actualizada
```

### `apps/backend/app/services/historial_estado_service.py`

`create_historial_entry` (line 64):
```python
return await self.repository.create(db, obj_in=historial_data.model_dump())
```

`HistorialEstadoRepository` inherits `BaseRepository` without overriding `create`.

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Existing promotion tests | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py -v --no-cov"` | all pass |
| Lint | from `apps/backend/`: `make lint` | exit 0 |
| Count flush variants | `grep -n "def create_flushed\|def update_flushed" apps/backend/app/db/repositories/base_repository.py` | 2 definitions found |

## Scope

**In scope** (the only files you should modify):
- `apps/backend/app/db/repositories/base_repository.py`
- `apps/backend/app/services/incapacidad_service.py`
- `apps/backend/app/services/historial_estado_service.py`

**Out of scope** (do NOT touch):
- Any repository that extends `BaseRepository` — they inherit the new methods automatically.
- Any service method other than `create_from_pre_incapacidad`, `radicar_incapacidad`, and `create_historial_entry`.
- The promotion service itself — that is Plan 003's responsibility.
- Any existing test that currently passes.

## Git workflow

- Branch: `bugfix/base-repository-flush-variants`
- Conventional Commits: `feat: add flush-only variants to BaseRepository and expose in incapacidad_service`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Verify drift

```bash
git diff --stat 7958670b..HEAD -- apps/backend/app/db/repositories/base_repository.py apps/backend/app/services/incapacidad_service.py apps/backend/app/services/historial_estado_service.py
```

Expected: no output (these files are unchanged). Any modification → STOP.

### Step 2: Add `create_flushed` and `update_flushed` to `BaseRepository`

In `apps/backend/app/db/repositories/base_repository.py`, add two new methods immediately after the existing `create` and `update` methods respectively:

**After `create` (after line ~49):**
```python
async def create_flushed(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
    """Like create() but flushes instead of committing — for caller-managed transactions."""
    db_obj = self.model(**obj_in)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj
```

**After `update` (after line ~172):**
```python
async def update_flushed(
    self,
    db: AsyncSession,
    id: UUID,
    obj_in: Dict[str, Any],
) -> Optional[ModelType]:
    """Like update() but does not commit — for caller-managed transactions."""
    update_data = {k: v for k, v in obj_in.items() if v is not None}
    if not update_data:
        return await self.get_by_id(db, id)
    stmt = (
        update(self.model)
        .where(self.model.id == id)
        .values(**update_data)
        .returning(self.model)
    )
    result = await db.execute(stmt)
    updated_obj = result.scalar_one_or_none()
    if updated_obj:
        await db.refresh(updated_obj)
    return updated_obj
```

**Verify**: `grep -n "def create_flushed\|def update_flushed" apps/backend/app/db/repositories/base_repository.py` → 2 lines.

### Step 3: Add `flush_only=False` to `historial_estado_service.create_historial_entry`

In `apps/backend/app/services/historial_estado_service.py`, find `create_historial_entry` (around line 26).

Add `flush_only: bool = False` as the last parameter. At the end of the method, change the `create` call:

Before:
```python
return await self.repository.create(db, obj_in=historial_data.model_dump())
```

After:
```python
if flush_only:
    return await self.repository.create_flushed(db, historial_data.model_dump())
return await self.repository.create(db, obj_in=historial_data.model_dump())
```

**Verify**: `grep -n "flush_only" apps/backend/app/services/historial_estado_service.py` → 2 lines (param + branch).

### Step 4: Add `flush_only=False` to `incapacidad_service.create_from_pre_incapacidad`

In `apps/backend/app/services/incapacidad_service.py`, find `create_from_pre_incapacidad` (around line 169).

Add `flush_only: bool = False` as the last parameter. Change the `repository.create` call at the bottom of the method:

Before (line ~207):
```python
incapacidad = await self.repository.create(db, incapacidad_dict)
return await self.repository.get_by_id_with_relations(db, incapacidad.id)
```

After:
```python
if flush_only:
    incapacidad = await self.repository.create_flushed(db, incapacidad_dict)
else:
    incapacidad = await self.repository.create(db, incapacidad_dict)
return await self.repository.get_by_id_with_relations(db, incapacidad.id)
```

**Verify**: `grep -n "flush_only" apps/backend/app/services/incapacidad_service.py` → ≥2 lines.

### Step 5: Add `flush_only=False` to `incapacidad_service.radicar_incapacidad`

Find `radicar_incapacidad` (around line 449).

Add `flush_only: bool = False` as the last parameter. Change the `repository.update` call and the historial call:

Before (lines ~483–494):
```python
incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)

await historial_estado_service.create_historial_entry(
    db=db,
    entity_type="incapacidad",
    entity_id=incapacidad_id,
    estado_anterior=estado_anterior.value if estado_anterior else None,
    estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
    observacion="Incapacidad radicada para auditoría",
    cambiado_por_id=usuario_id
)
```

After:
```python
if flush_only:
    incapacidad_actualizada = await self.repository.update_flushed(db, id=incapacidad_id, obj_in=update_data)
else:
    incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)

await historial_estado_service.create_historial_entry(
    db=db,
    entity_type="incapacidad",
    entity_id=incapacidad_id,
    estado_anterior=estado_anterior.value if estado_anterior else None,
    estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
    observacion="Incapacidad radicada para auditoría",
    cambiado_por_id=usuario_id,
    flush_only=flush_only,
)
```

**Verify**: `grep -n "flush_only" apps/backend/app/services/incapacidad_service.py` → ≥4 lines.

### Step 6: Run existing tests (no new tests needed — behavior is unchanged for default callers)

```bash
cd apps/backend && docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py tests/test_incapacidad_api.py -v --no-cov"
```

All tests must pass. If any test fails, STOP — a caller may be broken.

### Step 7: Lint

```bash
cd apps/backend && make lint
```

Must exit 0.

### Step 8: Update `plans/README.md`

Mark Plan 007 as `DONE — commit <sha>, branch bugfix/base-repository-flush-variants`.

### Step 9: Commit

```
feat: add flush-only variants to BaseRepository and expose in incapacidad_service

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -n "def create_flushed\|def update_flushed" apps/backend/app/db/repositories/base_repository.py` → 2 definitions
- [ ] `grep -c "flush_only" apps/backend/app/services/incapacidad_service.py` → ≥4
- [ ] `grep -c "flush_only" apps/backend/app/services/historial_estado_service.py` → ≥2
- [ ] `docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_promotion_service.py tests/test_pre_incapacidad_api.py tests/test_incapacidad_api.py -v --no-cov"` exits 0
- [ ] `make lint` exits 0
- [ ] No files outside the in-scope list modified

## STOP conditions

- Any of the three in-scope files has already been modified since commit `7958670b` (drift check).
- An existing test that was passing before this plan is now failing.
- `incapacidad_service.py` references `create_flushed` or `update_flushed` from a repository
  other than `self.repository` (e.g. `auditoria_datos_repository`) — those would need separate handling.

## Maintenance notes

- These variants are intentionally narrow: `create_flushed` and `update_flushed` only. Do NOT
  add a `delete_flushed` unless needed (the promotion flow doesn't delete).
- If a future service method needs flush-only semantics, it can add its own `flush_only=False`
  parameter and use these variants — the pattern is established here.
- After Plan 003 lands, the only callers of `create_flushed` / `update_flushed` are inside
  the promotion flow. If the promotion service is ever replaced or removed, these variants
  remain as a no-op in the base class (harmless).
