# Phase 4 — Job de Auditoría sobre Incapacidad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Depends on:** Phase 2 (`enqueue_auditoria_incapacidad` no-op placeholder, pipeline), Phase 3 (`incapacidad_validation_rules`).
> **Replaces:** the temporary no-op `enqueue_auditoria_incapacidad` from Phase 2 with a real Celery enqueue.

**Goal:** After radicación, a background job evaluates every business rule directly against the `Incapacidad`, stores each rule result (name, pass/fail, detail) in a new `auditoria_resultado` table, then transitions the `Incapacidad` to `EN_AUDITORIA`.

**Architecture:** New `auditoria_resultado` table + model. A Celery task `auditar_incapacidad_task(incapacidad_id)` (sync session + `asyncio.run`, matching the existing `incapacidad_tasks.py` pattern) loads the Incapacidad, maps it to a dict, runs `validate_row` from the shared rules module, persists one `auditoria_resultado` per rule evaluated (including passes), and transitions state to `EN_AUDITORIA` via the existing historial service. `enqueue_auditoria_incapacidad` becomes `auditar_incapacidad_task.delay(str(id))`.

**Tech Stack:** Celery, SQLAlchemy async/Alembic, pytest in Docker.

---

## File Structure

- Create: `app/models/auditoria_resultado.py`
- Modify: `app/models/incapacidad.py` — `auditoria_resultados` relationship.
- Migration: `create_auditoria_resultado`.
- Create: `app/services/auditoria_service.py` — evaluate + persist + transition (async, unit-testable).
- Modify: `app/tasks/incapacidad_tasks.py` — `auditar_incapacidad_task` + `enqueue_auditoria_incapacidad`.
- Tests: `tests/test_auditoria_service.py`, `tests/test_auditar_task.py`.

---

## Task 1: Backend — `auditoria_resultado` model + migration

**Files:**
- Create: `app/models/auditoria_resultado.py`
- Modify: `app/models/incapacidad.py`, `app/models/__init__.py`
- Migration under `alembic/versions/`
- Test: `tests/test_auditoria_resultado_model.py`

- [ ] **Step 1: Create the model**

```python
# app/models/auditoria_resultado.py
"""Resultado de cada regla de auditoría evaluada sobre una Incapacidad.

A diferencia de validation_inconsistencia (solo problemas), aquí se guarda CADA regla
evaluada, incluidas las que pasan, con su booleano aprobado/no aprobado.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class AuditoriaResultado(BaseModel):
    __tablename__ = "auditoria_resultado"

    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    regla: Mapped[str] = mapped_column(String(100), nullable=False, comment="Código de la regla evaluada")
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    detalle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    incapacidad: Mapped["Incapacidad"] = relationship("Incapacidad", back_populates="auditoria_resultados")

    def __repr__(self) -> str:
        estado = "OK" if self.aprobado else "FAIL"
        return f"<AuditoriaResultado {self.regla} [{estado}] inc={self.incapacidad_id}>"
```

- [ ] **Step 2: Add the relationship + register**

```python
# app/models/incapacidad.py (add after communication_logs)
    auditoria_resultados: Mapped[list["AuditoriaResultado"]] = relationship(
        "AuditoriaResultado", back_populates="incapacidad", cascade="all, delete-orphan",
    )
```

Register `AuditoriaResultado` in `app/models/__init__.py`.

- [ ] **Step 3: Generate + apply migration**

Run: `cd apps/backend && make migrate msg='create auditoria_resultado'`
Confirm it creates `auditoria_resultado` (PK, FK→incapacidad CASCADE, index on `incapacidad_id`). Then:
Run: `docker exec incapacidades-api alembic upgrade head`

- [ ] **Step 4: Write + run model test**

```python
# tests/test_auditoria_resultado_model.py
import pytest
from sqlalchemy import select
from app.models.auditoria_resultado import AuditoriaResultado


@pytest.mark.asyncio
async def test_can_persist_pass_and_fail(db_session, incapacidad_factory):
    inc = await incapacidad_factory(db_session)
    db_session.add_all([
        AuditoriaResultado(incapacidad_id=inc.id, regla="R1", categoria="BUSINESS_RULE", aprobado=True, severidad="INFO"),
        AuditoriaResultado(incapacidad_id=inc.id, regla="R2", categoria="FIELD_VALIDATION", aprobado=False, severidad="ERROR", detalle="x"),
    ])
    await db_session.flush()
    rows = (await db_session.execute(select(AuditoriaResultado).where(AuditoriaResultado.incapacidad_id == inc.id))).scalars().all()
    assert {r.aprobado for r in rows} == {True, False}
```

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_resultado_model.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/models/auditoria_resultado.py apps/backend/app/models/incapacidad.py apps/backend/app/models/__init__.py apps/backend/alembic/versions/ apps/backend/tests/test_auditoria_resultado_model.py
git commit -m "feat(db): add auditoria_resultado table"
```

---

## Task 2: Backend — auditoria service (evaluate + persist + transition)

**Files:**
- Create: `app/services/auditoria_service.py`
- Test: `tests/test_auditoria_service.py`

> Pure async function, independent of Celery, so it is fully unit-testable. The Celery task (Task 3)
> just calls it inside `asyncio.run`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auditoria_service.py
import datetime as dt
import pytest
from sqlalchemy import select
from app.services.auditoria_service import auditar_incapacidad
from app.models.auditoria_resultado import AuditoriaResultado
from app.models.incapacidad import Incapacidad
from app.utils.enums import EstadoIncapacidad


@pytest.mark.asyncio
async def test_audit_persists_results_and_transitions(db_session, incapacidad_factory):
    # incapacidad_factory should create a coherent RADICADA ARL incapacidad
    inc = await incapacidad_factory(db_session, dias_totales=999, fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5))
    await auditar_incapacidad(db_session, inc.id)

    resultados = (await db_session.execute(
        select(AuditoriaResultado).where(AuditoriaResultado.incapacidad_id == inc.id)
    )).scalars().all()
    # At least one rule recorded, with both pass and fail present (dias mismatch => fail)
    assert len(resultados) >= 1
    assert any(r.aprobado is False and r.regla == "DIAS_TOTALES_MISMATCH" for r in resultados)
    assert any(r.aprobado is True for r in resultados)

    refreshed = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == inc.id))).scalar_one()
    assert refreshed.estado == EstadoIncapacidad.EN_AUDITORIA
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_service.py -v --no-cov`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the service**

```python
# app/services/auditoria_service.py
"""Auditoría de una Incapacidad: evalúa reglas, persiste cada resultado y transiciona a EN_AUDITORIA."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.incapacidad import Incapacidad
from app.models.auditoria_resultado import AuditoriaResultado
from app.services.incapacidad_validation_rules import validate_field_level, validate_business_rules
from app.utils.enums import EstadoIncapacidad

# Reglas que SIEMPRE se evalúan (para registrar también las que pasan).
REGLAS_ESPERADAS = [
    ("EMPTY_EMPLEADO_NUMERO", "FIELD_VALIDATION"),
    ("EMPTY_DIAGNOSTICO_CIE10", "FIELD_VALIDATION"),
    ("EMPTY_NOMBRE_MEDICO", "FIELD_VALIDATION"),
    ("EMPTY_REGISTRO_MEDICO", "FIELD_VALIDATION"),
    ("INVALID_DATE_RANGE", "FIELD_VALIDATION"),
    ("DIAS_TOTALES_MISMATCH", "BUSINESS_RULE"),
    ("RETROACTIVE_BEYOND_LIMIT", "BUSINESS_RULE"),
    ("DURATION_EXCEEDS_LIMIT", "BUSINESS_RULE"),
]


def _incapacidad_to_row(inc: Incapacidad) -> dict:
    return {
        "tipo": inc.tipo.value if hasattr(inc.tipo, "value") else str(inc.tipo),
        "empleado_numero_documento": inc.empleado.numero_documento if inc.empleado else None,
        "tipo_enfermedad": inc.subtipo,
        "fecha_inicio": inc.fecha_inicio,
        "fecha_fin": inc.fecha_fin,
        "dias_totales": inc.dias_totales,
        "diagnostico_cie10": inc.diagnostico_cie10,
        "nombre_medico": inc.nombre_medico,
        "registro_medico": inc.registro_medico,
    }


async def auditar_incapacidad(db: AsyncSession, incapacidad_id: UUID) -> None:
    inc = (await db.execute(select(Incapacidad).where(Incapacidad.id == incapacidad_id))).scalar_one_or_none()
    if inc is None:
        logger.warning(f"Auditoría: incapacidad {incapacidad_id} no encontrada")
        return

    row = _incapacidad_to_row(inc)
    issues = validate_field_level(row) + validate_business_rules(row)
    failed_by_code = {i["codigo"]: i for i in issues}

    for codigo, categoria in REGLAS_ESPERADAS:
        issue = failed_by_code.get(codigo)
        db.add(AuditoriaResultado(
            incapacidad_id=inc.id,
            regla=codigo,
            categoria=categoria,
            aprobado=issue is None,
            severidad=issue["severidad"] if issue else "INFO",
            detalle=issue["descripcion"] if issue else "Regla cumplida",
        ))

    # Transición a EN_AUDITORIA (registrar historial)
    estado_anterior = inc.estado
    inc.estado = EstadoIncapacidad.EN_AUDITORIA
    await _registrar_historial(db, inc, estado_anterior)
    await db.commit()
    logger.info(f"Auditoría completa para {inc.numero}: {len(REGLAS_ESPERADAS)} reglas evaluadas → EN_AUDITORIA")


async def _registrar_historial(db: AsyncSession, inc: Incapacidad, estado_anterior) -> None:
    """Registra el cambio de estado usando el servicio de historial existente."""
    try:
        from app.services.historial_estado_service import HistorialEstadoService
        svc = HistorialEstadoService(db)
        await svc.registrar_cambio(
            incapacidad_id=inc.id,
            estado_anterior=estado_anterior,
            estado_nuevo=inc.estado,
            cambiado_por_id=None,
            observacion="Transición automática por job de auditoría",
        )
    except Exception as exc:  # historial is best-effort; never block the transition
        logger.error(f"No se pudo registrar historial para {inc.id}: {exc}")
```

> **Verify before coding:** open `app/services/historial_estado_service.py` and adapt `_registrar_historial`
> to the real method name/signature (it is polymorphic per CLAUDE.md). Do not invent a method.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_service.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/auditoria_service.py apps/backend/tests/test_auditoria_service.py
git commit -m "feat(auditoria): evaluate rules on Incapacidad, persist results, transition to EN_AUDITORIA"
```

---

## Task 3: Backend — Celery task + real enqueue

**Files:**
- Modify: `app/tasks/incapacidad_tasks.py`
- Test: `tests/test_auditar_task.py`

> Replace the Phase 2 no-op `enqueue_auditoria_incapacidad` with a real `.delay()`. The task follows
> the existing sync-session + `asyncio.run` pattern in this file.

- [ ] **Step 1: Write the failing test (task runs eagerly)**

```python
# tests/test_auditar_task.py
import pytest
from app.tasks.incapacidad_tasks import auditar_incapacidad_task, enqueue_auditoria_incapacidad


def test_enqueue_calls_delay(monkeypatch):
    called = {}
    monkeypatch.setattr(auditar_incapacidad_task, "delay", lambda iid: called.setdefault("id", iid))
    enqueue_auditoria_incapacidad("abc-123")
    assert called["id"] == "abc-123"
```

> A full integration test of the task running against the DB belongs to manual/CI verification with a
> live worker; here we assert the enqueue contract. The audit logic itself is covered by Task 2.

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditar_task.py -v --no-cov`
Expected: FAIL — `auditar_incapacidad_task` not defined.

- [ ] **Step 3: Implement the task + enqueue**

```python
# app/tasks/incapacidad_tasks.py  (add; mirror the asyncio.run pattern already used by promote_pre_incapacidad_task)
import asyncio
from uuid import UUID
from app.tasks import celery_app
from app.db.session import get_async_session_factory  # use the same async session factory the file already uses


@celery_app.task(name="auditar_incapacidad", bind=True, max_retries=3)
def auditar_incapacidad_task(self, incapacidad_id: str):
    from app.services.auditoria_service import auditar_incapacidad

    async def run():
        SessionFactory = get_async_session_factory()
        async with SessionFactory() as db:
            await auditar_incapacidad(db, UUID(incapacidad_id))

    try:
        asyncio.run(run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


def enqueue_auditoria_incapacidad(incapacidad_id) -> None:
    """Hook usado por RadicacionPipelineService (reemplaza el no-op de Phase 2)."""
    auditar_incapacidad_task.delay(str(incapacidad_id))
```

> **Verify before coding:** match the real async session factory import used elsewhere in this file
> (the file already builds sessions for `promote_pre_incapacidad_task`). Reuse that exact mechanism.
> Remove the temporary no-op `enqueue_auditoria_incapacidad` added in Phase 2.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditar_task.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Regression — pipeline + endpoints still green**

Run: `docker exec incapacidades-api python -m pytest tests/test_radicacion_pipeline.py tests/test_radicar_endpoint.py tests/test_bulk_submit.py -v --no-cov`
Expected: PASS (the real enqueue now fires; with the eager/broker config in tests it should not raise).

> If the test environment has no broker, ensure `task_always_eager=True` in the test Celery config,
> or keep `enqueue_auditoria_incapacidad` resilient (the pipeline already wraps the enqueue in try/except).

- [ ] **Step 6: Commit**

```bash
git add apps/backend/app/tasks/incapacidad_tasks.py apps/backend/tests/test_auditar_task.py
git commit -m "feat(auditoria): add celery audit task and wire real enqueue into pipeline"
```

---

## Self-Review Notes (coverage vs spec Phase 4)

- Replaces `_run_audit_business_rules`, operating on `Incapacidad` (FK) not pre_incapacidad → Task 2. ✅
- For each rule: name + passed/failed + detail stored → `auditoria_resultado` rows incl. passes (Task 2). ✅
- After evaluation → transition to `EN_AUDITORIA` (+ historial) → Task 2. ✅
- Background job → Celery task (Task 3), enqueued by the shared pipeline (Phase 2/3). ✅

**Type consistency:** `enqueue_auditoria_incapacidad(incapacidad_id)` signature matches the Phase 2
pipeline injection; `auditar_incapacidad(db, incapacidad_id)` matches the task call.

**Manual verification:** with a running worker (`make docker-up`, flower at :5565), file an incapacidad
with `dias_totales` deliberately wrong; confirm `auditoria_resultado` rows (passes + the `DIAS_TOTALES_MISMATCH`
fail) and the Incapacidad in `EN_AUDITORIA`.
