# Unified Pre-Incapacidad → Incapacidad Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the pre-incapacidad → incapacidad promotion into a single background job pass — the Celery task creates a full `Incapacidad` record directly from the `PreIncapacidad`, with no separate "promote" step, and handles missing employee gracefully.

**Architecture:** The `promote_pre_incapacidad_task` Celery task is rewritten to: (1) always create a full `Incapacidad` regardless of whether the employee/company is found in the DB; (2) link `pre_incapacidad.incapacidad_id` → the new `Incapacidad`; (3) call `radicar_incapacidad()` to immediately transition to `EN_AUDITORIA`; (4) run additional audit business rules when employee IS found, recording issues as `ValidationInconsistencia` records. The "Promover manualmente" button in the management UI remains but now re-triggers the same unified job.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async, Alembic, Celery/asyncio.run pattern (psycopg2 sync engine replaced by asyncio.run + asyncpg async engine), Pydantic v2, React + Zod v3 + React Query + Tailwind v3.

**Docker commands:** All backend commands run from `/opt/apps/incapacidades_vs/apps/backend` as:
```bash
docker compose exec api sh -c "<command>"
```

---

## File Map

| File | Change |
|------|--------|
| `alembic/versions/20260609_XXXX_<hash>_unified_flow.py` | Create — DB migration |
| `app/models/incapacidad.py` | Modify — relax ARL `CheckConstraint` |
| `app/models/pre_incapacidad.py` | Modify — add `incapacidad_id` FK |
| `app/schemas/pre_incapacidad.py` | Modify — add `incapacidad_id` to response |
| `app/services/incapacidad_service.py` | Modify — add `create_from_pre_incapacidad()` |
| `app/services/pre_incapacidad_validation_service.py` | Modify — demote EMPLEADO/EMPRESA_NOT_FOUND to WARNING |
| `app/services/pre_incapacidad_promotion_service.py` | Rewrite — unified flow |
| `app/tasks/incapacidad_tasks.py` | Modify — `promote_pre_incapacidad_task` logs only |
| `app/api/v1/endpoints/pre_incapacidades.py` | Modify — update `/promover`, add `/{id}/incapacidad` |
| `apps/frontend/sistema-interno/src/types/preIncapacidad.ts` | Modify — add `incapacidad_id` |
| `apps/frontend/sistema-interno/src/services/preIncapacidadService.ts` | Modify — add `getIncapacidad()` |
| `apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx` | Modify — show linked incapacidad |
| `tests/unit/test_unified_promotion.py` | Create — unified flow tests |
| `tests/unit/test_incapacidad_from_pre_inc.py` | Create — create_from_pre_incapacidad tests |
| `docs/04_FLUJO_ESTADOS.md` | Modify — document unified flow |

---

## Task 1: DB Migration — Relax ARL Constraint + Add incapacidad_id FK

**Context:** The `incapacidad` table has a `CHECK` constraint that requires `empresa_id IS NOT NULL` for ARL. The unified flow creates `Incapacidad` records even when the company/employee isn't in the DB, so this constraint must be relaxed. Additionally, `pre_incapacidad` needs an `incapacidad_id` FK to link to the created `Incapacidad` (1-to-1).

**Files:**
- Create: `apps/backend/alembic/versions/` (file named by `make migrate`)
- Modify: `apps/backend/app/models/incapacidad.py:31-34`
- Modify: `apps/backend/app/models/pre_incapacidad.py` (add FK column after line 79)

- [ ] **Step 1: Generate migration**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "alembic revision --autogenerate -m 'unified_flow_relax_arl_constraint_add_incapacidad_fk'"
```

Expected: creates a new file in `alembic/versions/` with `_unified_flow_relax_arl_constraint_add_incapacidad_fk.py`.

- [ ] **Step 2: Update the Incapacidad model CheckConstraint**

In `apps/backend/app/models/incapacidad.py`, replace lines 31-34:

Old:
```python
        CheckConstraint(
            "(tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR "
            "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
            name="check_tipo_incapacidad_relacion"
        ),
```

New:
```python
        CheckConstraint(
            "(tipo = 'ARL' AND afiliado_id IS NULL) OR "
            "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
            name="check_tipo_incapacidad_relacion"
        ),
```

- [ ] **Step 3: Add incapacidad_id FK to PreIncapacidad model**

In `apps/backend/app/models/pre_incapacidad.py`, add these imports at the top:
```python
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
```

Then add the column after `motivo_devolucion` (around line 82):
```python
    # ── Vínculo con incapacidad creada (1-to-1, set after unified job) ──────────
    incapacidad_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id"),
        nullable=True,
        unique=True,
        index=True,
    )
```

Also add the relationship after the existing ones:
```python
    incapacidad: Mapped[Optional["Incapacidad"]] = relationship(
        "Incapacidad",
        foreign_keys=[incapacidad_id],
        lazy="select",
    )
```

- [ ] **Step 4: Write migration body manually**

Open the generated migration file. Replace the `upgrade()` and `downgrade()` bodies with:

```python
def upgrade() -> None:
    # 1. Drop old strict ARL constraint
    op.drop_constraint("check_tipo_incapacidad_relacion", "incapacidad", type_="check")

    # 2. Add relaxed constraint (ARL no longer requires empleado_id / empresa_id NOT NULL)
    op.create_check_constraint(
        "check_tipo_incapacidad_relacion",
        "incapacidad",
        "(tipo = 'ARL' AND afiliado_id IS NULL) OR "
        "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
    )

    # 3. Add incapacidad_id FK to pre_incapacidad
    op.add_column(
        "pre_incapacidad",
        sa.Column("incapacidad_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        "incapacidad",
        ["incapacidad_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        ["incapacidad_id"],
    )
    op.create_index(
        "ix_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        ["incapacidad_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pre_incapacidad_incapacidad_id", table_name="pre_incapacidad")
    op.drop_constraint("uq_pre_incapacidad_incapacidad_id", "pre_incapacidad", type_="unique")
    op.drop_constraint("fk_pre_incapacidad_incapacidad_id", "pre_incapacidad", type_="foreignkey")
    op.drop_column("pre_incapacidad", "incapacidad_id")

    op.drop_constraint("check_tipo_incapacidad_relacion", "incapacidad", type_="check")
    op.create_check_constraint(
        "check_tipo_incapacidad_relacion",
        "incapacidad",
        "(tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR "
        "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
    )
```

Also ensure the migration imports include:
```python
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
```

- [ ] **Step 5: Apply migration**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "alembic upgrade head"
```

Expected: `Running upgrade <prev_rev> -> <new_rev>, unified_flow_relax_arl_constraint_add_incapacidad_fk`

- [ ] **Step 6: Verify migration applied**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "alembic current"
```

Expected: shows the new revision as `(head)`.

- [ ] **Step 7: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/alembic/versions/ apps/backend/app/models/incapacidad.py apps/backend/app/models/pre_incapacidad.py
git commit -m "feat: relax ARL check constraint, add incapacidad_id FK to pre_incapacidad"
```

---

## Task 2: IncapacidadService — add create_from_pre_incapacidad()

**Context:** The existing `create_incapacidad()` method calls `_validate_incapacidad_arl()` which throws `NotFoundException` when empresa/empleado are missing. The unified flow must create an `Incapacidad` even when entities aren't found. Instead of modifying the existing method, add a new bypass method `create_from_pre_incapacidad()`.

**Files:**
- Modify: `apps/backend/app/services/incapacidad_service.py` (add method after `create_incapacidad`, around line 167)

- [ ] **Step 1: Write failing test first**

Create `apps/backend/tests/unit/test_incapacidad_from_pre_inc.py`:

```python
"""Unit tests for IncapacidadService.create_from_pre_incapacidad()."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.incapacidad_service import IncapacidadService
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad


@pytest.fixture
def mock_pre_inc():
    m = MagicMock()
    m.id = uuid4()
    m.numero_radicacion = 202600042
    m.tipo = "ARL"
    m.fecha_inicio = date(2026, 1, 15)
    m.fecha_fin = date(2026, 1, 25)
    m.diagnostico_cie10 = "S62.0"
    m.descripcion_diagnostico = "Fractura muñeca"
    m.nombre_medico = "Dr. García"
    m.registro_medico = "RM12345"
    m.ips = "Clínica Norte"
    m.valor_dia = Decimal("50000.00")
    m.observaciones = None
    return m


@pytest.fixture
def mock_empleado():
    m = MagicMock()
    m.id = uuid4()
    return m


@pytest.fixture
def mock_empresa():
    m = MagicMock()
    m.id = uuid4()
    return m


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_with_empleado(mock_pre_inc, mock_empleado, mock_empresa):
    """Creates incapacidad with numero = str(pre_inc.numero_radicacion), empleado linked."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()

    with (
        patch.object(service.repository, "create", new=AsyncMock(return_value=created)),
        patch.object(service.repository, "get_by_id_with_relations", new=AsyncMock(return_value=created)),
    ):
        db = AsyncMock()
        result = await service.create_from_pre_incapacidad(
            db, mock_pre_inc, empleado=mock_empleado, empresa=mock_empresa
        )

    assert result == created
    call_args = service.repository.create.call_args[0][1]
    assert call_args["numero"] == "202600042"
    assert call_args["tipo"] == TipoIncapacidad.ARL
    assert call_args["estado"] == EstadoIncapacidad.RADICADA
    assert call_args["empleado_id"] == mock_empleado.id
    assert call_args["empresa_id"] == mock_empresa.id


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_without_empleado(mock_pre_inc):
    """Creates incapacidad with empleado_id=None, empresa_id=None — does not raise."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()

    with (
        patch.object(service.repository, "create", new=AsyncMock(return_value=created)),
        patch.object(service.repository, "get_by_id_with_relations", new=AsyncMock(return_value=created)),
    ):
        db = AsyncMock()
        result = await service.create_from_pre_incapacidad(db, mock_pre_inc)

    assert result == created
    call_args = service.repository.create.call_args[0][1]
    assert call_args["empleado_id"] is None
    assert call_args["empresa_id"] is None


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_calculates_dias_totales(mock_pre_inc):
    """dias_totales is calculated from fecha_inicio / fecha_fin."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()

    with (
        patch.object(service.repository, "create", new=AsyncMock(return_value=created)),
        patch.object(service.repository, "get_by_id_with_relations", new=AsyncMock(return_value=created)),
    ):
        db = AsyncMock()
        await service.create_from_pre_incapacidad(db, mock_pre_inc)

    call_args = service.repository.create.call_args[0][1]
    assert call_args["dias_totales"] == 11  # Jan 15–25 inclusive
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/unit/test_incapacidad_from_pre_inc.py -v --no-cov"
```

Expected: FAILED — `AttributeError: 'IncapacidadService' object has no attribute 'create_from_pre_incapacidad'`

- [ ] **Step 3: Add create_from_pre_incapacidad() to IncapacidadService**

In `apps/backend/app/services/incapacidad_service.py`, add after the `create_incapacidad()` method (after line ~167):

```python
    async def create_from_pre_incapacidad(
        self,
        db: AsyncSession,
        pre_inc: Any,
        empleado: Optional[Any] = None,
        empresa: Optional[Any] = None,
        usuario_id: Optional[UUID] = None,
    ) -> Incapacidad:
        """
        Create an Incapacidad directly from a PreIncapacidad — bypasses strict entity validation.
        Used by the unified background job to always create a record, even when empleado/empresa
        aren't in the DB yet. numero = str(pre_inc.numero_radicacion).
        """
        self._validate_fechas(pre_inc.fecha_inicio, pre_inc.fecha_fin)
        dias_totales = (pre_inc.fecha_fin - pre_inc.fecha_inicio).days + 1

        incapacidad_dict: Dict[str, Any] = {
            'numero': str(pre_inc.numero_radicacion),
            'tipo': TipoIncapacidad(pre_inc.tipo),
            'fecha_inicio': pre_inc.fecha_inicio,
            'fecha_fin': pre_inc.fecha_fin,
            'dias_totales': dias_totales,
            'diagnostico_cie10': pre_inc.diagnostico_cie10,
            'descripcion_diagnostico': pre_inc.descripcion_diagnostico,
            'nombre_medico': pre_inc.nombre_medico,
            'registro_medico': pre_inc.registro_medico,
            'ips': pre_inc.ips,
            'valor_dia': pre_inc.valor_dia,
            'observaciones': pre_inc.observaciones,
            'estado': EstadoIncapacidad.RADICADA,
            'fecha_radicacion': datetime.utcnow(),
            'empleado_id': empleado.id if empleado else None,
            'empresa_id': empresa.id if empresa else None,
        }

        if usuario_id:
            incapacidad_dict['radicado_por_id'] = usuario_id

        incapacidad = await self.repository.create(db, incapacidad_dict)
        return await self.repository.get_by_id_with_relations(db, incapacidad.id)
```

Add `Any` to the imports at the top: `from typing import List, Optional, Dict, Any`

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/unit/test_incapacidad_from_pre_inc.py -v --no-cov"
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/app/services/incapacidad_service.py apps/backend/tests/unit/test_incapacidad_from_pre_inc.py
git commit -m "feat: add IncapacidadService.create_from_pre_incapacidad() for unified promotion"
```

---

## Task 3: Relax Validation Severities + Update PreIncapacidad Schema

**Context:** Currently `EMPLEADO_NOT_FOUND` and `EMPRESA_NOT_FOUND` are `ERROR` severity — they blocked incapacidad creation. In the unified flow, these are non-blocking (`WARNING`). Also, `PreIncapacidadResponse` needs `incapacidad_id` so the frontend can detect when a linked incapacidad exists.

**Files:**
- Modify: `apps/backend/app/services/pre_incapacidad_validation_service.py:264-296`
- Modify: `apps/backend/app/schemas/pre_incapacidad.py:190-219`

- [ ] **Step 1: Change EMPLEADO_NOT_FOUND + EMPRESA_NOT_FOUND to WARNING**

In `apps/backend/app/services/pre_incapacidad_validation_service.py`:

At line 264, change `severidad="ERROR"` → `severidad="WARNING"` for the `EMPLEADO_NOT_FOUND` issue:
```python
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="INTEGRATION_CHECK",
                severidad="WARNING",
                codigo="EMPLEADO_NOT_FOUND",
                descripcion=f"Empleado {self.pre_inc.empleado_numero_documento} no encontrado en BD. La incapacidad se crea pendiente de resolución.",
                campo_afectado="empleado_id",
                valor_encontrado=self.pre_inc.empleado_numero_documento,
            ))
```

At line 289, change `severidad="ERROR"` → `severidad="WARNING"` for the `EMPRESA_NOT_FOUND` issue:
```python
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="INTEGRATION_CHECK",
                severidad="WARNING",
                codigo="EMPRESA_NOT_FOUND",
                descripcion=f"Empresa NIT {self.pre_inc.empresa_nit} no encontrada en BD. La incapacidad se crea pendiente de resolución.",
                campo_afectado="empresa_id",
                valor_encontrado=self.pre_inc.empresa_nit,
            ))
```

Also change `categoria="FRAUD_ALERT"` → `categoria="INTEGRATION_CHECK"` for both issues.

- [ ] **Step 2: Add incapacidad_id to PreIncapacidadResponse schema**

In `apps/backend/app/schemas/pre_incapacidad.py`, add to `PreIncapacidadResponse` after `empresa_nombre`:

```python
    # Vínculo a la incapacidad creada (set after unified job runs)
    incapacidad_id: Optional[UUID] = None
```

Add `UUID` import if missing: `from uuid import UUID`

- [ ] **Step 3: Run existing promotion tests to verify they still pass after severity change**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/ -k 'promotion or validation' -v --no-cov"
```

Expected: all passing (the severity change may break tests that assert ERROR count; update those in the next task)

- [ ] **Step 4: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/app/services/pre_incapacidad_validation_service.py apps/backend/app/schemas/pre_incapacidad.py
git commit -m "feat: relax EMPLEADO/EMPRESA_NOT_FOUND to WARNING, add incapacidad_id to PreIncapacidadResponse"
```

---

## Task 4: Unified PromotePreIncapacidadService

**Context:** Rewrite `promote_pre_incapacidad()` so it: (1) always creates a full `Incapacidad` (even when entities not found); (2) links `pre_incapacidad.incapacidad_id`; (3) runs additional audit rules when employee IS found; (4) calls `radicar_incapacidad()` to move the new incapacidad immediately to `EN_AUDITORIA`; (5) always sets `pre_incapacidad.estado = PROCESADA`.

**Files:**
- Modify: `apps/backend/app/services/pre_incapacidad_promotion_service.py` (full rewrite of `promote_pre_incapacidad`)

- [ ] **Step 1: Write failing tests first**

Create `apps/backend/tests/unit/test_unified_promotion.py`:

```python
"""Tests for unified PromotePreIncapacidadService flow."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService


def make_pre_inc(estado="PENDIENTE", empresa_nit="900123456", tipo="ARL"):
    m = MagicMock()
    m.id = uuid4()
    m.numero_radicacion = 202600001
    m.tipo = tipo
    m.estado = estado
    m.empresa_nit = empresa_nit
    m.empleado_numero_documento = "12345678"
    m.fecha_inicio = date(2026, 1, 1)
    m.fecha_fin = date(2026, 1, 10)
    m.diagnostico_cie10 = "S00.0"
    m.descripcion_diagnostico = None
    m.nombre_medico = "Dr. Test"
    m.registro_medico = "RM001"
    m.ips = None
    m.valor_dia = Decimal("60000")
    m.observaciones = None
    m.incapacidad_id = None
    return m


@pytest.mark.asyncio
async def test_unified_always_creates_incapacidad_even_without_empleado():
    """Incapacidad is created even when empleado/empresa are not in the DB."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()

    mock_incapacidad = MagicMock()
    mock_incapacidad.id = uuid4()

    service.pre_inc_repo = AsyncMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.validation_repo = AsyncMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(return_value={"total": 1, "ERROR": 0, "WARNING": 1, "INFO": 0})

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=None)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=None)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)

        result = await service.promote_pre_incapacidad(pre_inc.id)

    assert result.success is True
    assert result.incapacidad_id == mock_incapacidad.id
    mock_inc_service.create_from_pre_incapacidad.assert_called_once()
    mock_inc_service.radicar_incapacidad.assert_called_once()
    service.pre_inc_repo.update_estado.assert_called_with(db, pre_inc.id, "PROCESADA")


@pytest.mark.asyncio
async def test_unified_links_incapacidad_id_on_pre_inc():
    """pre_incapacidad.incapacidad_id is set after incapacidad creation."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()

    mock_incapacidad = MagicMock()
    mock_incapacidad.id = uuid4()

    service.pre_inc_repo = AsyncMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.validation_repo = AsyncMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(return_value={"total": 0, "ERROR": 0, "WARNING": 0, "INFO": 0})

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=None)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=None)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)

        await service.promote_pre_incapacidad(pre_inc.id)

    assert pre_inc.incapacidad_id == mock_incapacidad.id


@pytest.mark.asyncio
async def test_unified_runs_audit_rules_when_empleado_found():
    """When empleado is found, _run_audit_business_rules is called."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()
    mock_empresa = MagicMock(); mock_empresa.id = uuid4()
    mock_empleado = MagicMock(); mock_empleado.id = uuid4()
    mock_incapacidad = MagicMock(); mock_incapacidad.id = uuid4()

    service.pre_inc_repo = AsyncMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.validation_repo = AsyncMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(return_value={"total": 0, "ERROR": 0, "WARNING": 0, "INFO": 0})

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
        patch.object(service, "_run_audit_business_rules", new=AsyncMock(return_value=[])) as mock_audit,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=mock_empresa)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=mock_empleado)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)

        await service.promote_pre_incapacidad(pre_inc.id)

    mock_audit.assert_called_once()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/unit/test_unified_promotion.py -v --no-cov"
```

Expected: FAILED — tests fail because the service doesn't yet implement the unified flow.

- [ ] **Step 3: Rewrite promote_pre_incapacidad() in PromotePreIncapacidadService**

Replace `apps/backend/app/services/pre_incapacidad_promotion_service.py` with:

```python
"""
Servicio de promoción unificada: pre-incapacidad → incapacidad en un solo paso.

El job siempre crea una Incapacidad, incluso si empleado/empresa no se encuentran en BD.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pre_incapacidad import PreIncapacidad
from app.db.repositories.pre_incapacidad_repository import PreIncapacidadRepository
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.schemas.validation_inconsistencia import (
    ValidationSummary,
    PromotionResult,
    ValidationInconsistenciaCreate,
)


class PromotePreIncapacidadService:
    """Servicio para promoción unificada de pre-incapacidades a incapacidades."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pre_inc_repo = PreIncapacidadRepository()
        self.validation_repo = ValidationInconsistenciaRepository(db)

    async def promote_pre_incapacidad(
        self,
        pre_incapacidad_id: UUID,
        clear_existing_issues: bool = True,
        usuario_id: Optional[UUID] = None,
    ) -> PromotionResult:
        """
        Flujo unificado — siempre crea Incapacidad, maneja empleado faltante sin error.

        1. Fetch pre-incapacidad
        2. Clear existing issues (default: True)
        3. Resolve empresa + empleado (may be None)
        4. Run all validations — EMPLEADO/EMPRESA_NOT_FOUND now WARNING, not ERROR
        5. Create Incapacidad via create_from_pre_incapacidad()
        6. Link pre_incapacidad.incapacidad_id
        7. If empleado found: run audit business rules
        8. Transition incapacidad RADICADA → EN_AUDITORIA via radicar_incapacidad()
        9. Set pre_incapacidad.estado = PROCESADA
        """
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
                await self.db.commit()
                await self.db.refresh(pre_inc)
                if deleted:
                    logger.info(f"Cleared {deleted} existing issues for {pre_incapacidad_id}")

            # 3. Resolve entities (may be None — no longer blocking)
            empresa = None
            empleado = None
            if pre_inc.empresa_nit:
                empresa = await empresa_repository.get_by_nit(self.db, pre_inc.empresa_nit)
            if pre_inc.tipo == "ARL" and empresa:
                empleado = await empleado_repository.get_by_documento(
                    self.db, pre_inc.empleado_numero_documento, empresa.id
                )

            # 4. Run all validations (EMPLEADO/EMPRESA_NOT_FOUND are now WARNING)
            validation_service = PreIncapacidadValidationService(pre_inc, empleado, empresa)
            issues = await validation_service.validate_all()

            for issue_schema in issues:
                await self.validation_repo.create(issue_schema)
            await self.db.commit()
            logger.debug(f"Persisted {len(issues)} validation issues for {pre_incapacidad_id}")

            # 5. Create Incapacidad unconditionally
            from app.services.incapacidad_service import incapacidad_service
            incapacidad = await incapacidad_service.create_from_pre_incapacidad(
                self.db, pre_inc, empleado=empleado, empresa=empresa, usuario_id=usuario_id
            )
            incapacidad_id = incapacidad.id
            logger.info(f"Created incapacidad {incapacidad_id} from pre-incapacidad {pre_incapacidad_id}")
            await self.db.commit()

            # 6. Link pre_incapacidad → incapacidad
            pre_inc.incapacidad_id = incapacidad_id
            self.db.add(pre_inc)
            await self.db.commit()
            await self.db.refresh(pre_inc)

            # 7. Run additional audit rules when empleado is found
            if empleado:
                audit_issues = await self._run_audit_business_rules(pre_inc, incapacidad, empleado)
                for issue in audit_issues:
                    await self.validation_repo.create(issue)
                if audit_issues:
                    await self.db.commit()
                    logger.info(f"Added {len(audit_issues)} audit rule issues for {pre_incapacidad_id}")

            # 8. Transition to EN_AUDITORIA
            await incapacidad_service.radicar_incapacidad(self.db, incapacidad_id, usuario_id)
            await self.db.commit()
            logger.info(f"Incapacidad {incapacidad_id} transitioned to EN_AUDITORIA")

            # 9. Mark pre-incapacidad as PROCESADA
            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()

            counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
            validation_summary = ValidationSummary(
                total_issues=counts["total"],
                errors=counts["ERROR"],
                warnings=counts["WARNING"],
                infos=counts["INFO"],
                issues=[],
            )

            logger.success(
                f"Unified promotion complete for {pre_incapacidad_id}. "
                f"Incapacidad: {incapacidad_id}. Issues: {counts}"
            )

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=incapacidad_id,
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            from sqlalchemy.exc import SQLAlchemyError
            try:
                from asyncpg import PostgresError as _PgError
            except ImportError:
                _PgError = None
            is_infra = isinstance(e, SQLAlchemyError) or (_PgError and isinstance(e, _PgError))
            if is_infra:
                raise

            logger.error(f"Error in unified promotion for {pre_incapacidad_id}: {e}")
            try:
                await self.pre_inc_repo.update_error(self.db, pre_incapacidad_id, str(e))
                await self.db.commit()
            except Exception:
                pass

            return PromotionResult(
                success=False,
                pre_incapacidad_id=pre_incapacidad_id,
                validation_summary=ValidationSummary(
                    total_issues=0, errors=0, warnings=0, infos=0, issues=[],
                ),
                error_message=f"Error durante promoción unificada: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def _run_audit_business_rules(
        self,
        pre_inc: PreIncapacidad,
        incapacidad: object,
        empleado: object,
    ) -> List[ValidationInconsistenciaCreate]:
        """
        Additional audit checks from ai/skills/negocio/auditoria_liquidacion/ — only run when
        the employee record exists in the DB. Issues are INFO/WARNING, never blocking.

        Checks implemented:
        - RN008/VAL018: overlapping incapacidad periods for same employee
        - RN009/VAL017: duplicate incapacidad (same employee, CIE10, same month)
        """
        issues = []
        incapacidad_id = getattr(incapacidad, 'id', None)
        empleado_id = getattr(empleado, 'id', None)
        if not empleado_id:
            return issues

        try:
            from sqlalchemy import select
            from app.models.incapacidad import Incapacidad
            from app.utils.enums import EstadoIncapacidad

            # RN008/VAL018 — overlapping periods
            overlap_query = select(Incapacidad).where(
                Incapacidad.empleado_id == empleado_id,
                Incapacidad.id != incapacidad_id,
                Incapacidad.estado != EstadoIncapacidad.CANCELADA,
                Incapacidad.fecha_inicio <= pre_inc.fecha_fin,
                Incapacidad.fecha_fin >= pre_inc.fecha_inicio,
            )
            overlap_result = await self.db.execute(overlap_query)
            overlapping = overlap_result.scalars().all()

            if overlapping:
                numeros = ", ".join(str(i.numero) for i in overlapping)
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=pre_inc.id,
                    incapacidad_id=incapacidad_id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="OVERLAPPING_PERIOD",
                    descripcion=f"Período se traslapa con incapacidades existentes: {numeros}",
                    campo_afectado="fecha_inicio,fecha_fin",
                    valor_encontrado=f"{pre_inc.fecha_inicio} al {pre_inc.fecha_fin}",
                ))

            # RN009/VAL017 — duplicate (same employee + CIE10 + same month)
            from app.models.incapacidad import Incapacidad
            from sqlalchemy import extract
            duplicate_query = select(Incapacidad).where(
                Incapacidad.empleado_id == empleado_id,
                Incapacidad.id != incapacidad_id,
                Incapacidad.diagnostico_cie10 == pre_inc.diagnostico_cie10,
                extract('year', Incapacidad.fecha_inicio) == pre_inc.fecha_inicio.year,
                extract('month', Incapacidad.fecha_inicio) == pre_inc.fecha_inicio.month,
            )
            dup_result = await self.db.execute(duplicate_query)
            duplicates = dup_result.scalars().all()

            if duplicates:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=pre_inc.id,
                    incapacidad_id=incapacidad_id,
                    categoria="FRAUD_ALERT",
                    severidad="WARNING",
                    codigo="POSSIBLE_DUPLICATE",
                    descripcion=f"Posible duplicado: mismo empleado + CIE10 en el mismo mes",
                    campo_afectado="diagnostico_cie10",
                    valor_encontrado=pre_inc.diagnostico_cie10,
                ))

        except Exception as e:
            logger.warning(f"Audit rule check failed for {pre_inc.id}: {e}")

        return issues
```

- [ ] **Step 4: Run unified promotion tests**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/unit/test_unified_promotion.py -v --no-cov"
```

Expected: 3 tests PASSED

- [ ] **Step 5: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/app/services/pre_incapacidad_promotion_service.py apps/backend/tests/unit/test_unified_promotion.py
git commit -m "feat: rewrite PromotePreIncapacidadService as unified single-pass flow"
```

---

## Task 5: Backend API — Update /promover + Add /{id}/incapacidad Endpoint

**Context:** The `POST /promover` endpoint still works (it re-triggers the unified job manually). Add `GET /{pre_incapacidad_id}/incapacidad` to return the linked incapacidad.

**Files:**
- Modify: `apps/backend/app/api/v1/endpoints/pre_incapacidades.py`

- [ ] **Step 1: Add GET /{id}/incapacidad endpoint**

In `apps/backend/app/api/v1/endpoints/pre_incapacidades.py`, add after the `actualizar_pre_incapacidad` endpoint (after line 256) and before the `devolver` endpoint:

```python
@router.get(
    "/{pre_incapacidad_id}/incapacidad",
    summary="[Interno] Obtener incapacidad vinculada",
    description="Retorna la incapacidad creada por el job unificado para esta pre-incapacidad.",
)
async def get_incapacidad_vinculada(
    pre_incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    from app.core.exceptions import NotFoundException
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.pre_incapacidad import PreIncapacidad
    from app.models.incapacidad import Incapacidad

    result = await db.execute(
        select(PreIncapacidad).where(PreIncapacidad.id == pre_incapacidad_id)
    )
    pre_inc = result.scalar_one_or_none()
    if not pre_inc:
        raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")

    if not pre_inc.incapacidad_id:
        raise NotFoundException(
            f"Pre-incapacidad {pre_incapacidad_id} aún no tiene incapacidad vinculada"
        )

    from app.services.incapacidad_service import incapacidad_service
    incapacidad = await incapacidad_service.get_incapacidad(db, pre_inc.incapacidad_id)
    return incapacidad
```

This reuses the existing `IncapacidadService.get_incapacidad()` which already returns the full object with relations (including validation_inconsistencias via the incapacidad → pre_incapacidad chain).

- [ ] **Step 2: Manually test the endpoints with curl**

First ensure the backend is running:
```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose ps
```

Test that the endpoint is registered (without auth for schema check):
```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -c \"from app.api.v1.endpoints.pre_incapacidades import router; print([r.path for r in router.routes])\""
```

Expected: output includes `/{pre_incapacidad_id}/incapacidad`

- [ ] **Step 3: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/app/api/v1/endpoints/pre_incapacidades.py
git commit -m "feat: add GET /pre-incapacidades/{id}/incapacidad endpoint"
```

---

## Task 6: Frontend — Type + Service + GestionarPreIncapacidadPage

**Context:** The management page needs to: (1) show the linked incapacidad when `pre_inc.incapacidad_id` is set; (2) show validation alerts (already shown via `validation_inconsistencias`); (3) show a "Empleado no encontrado" alert banner when the INTEGRATION_CHECK WARNING is present; (4) show an "Incapacidad Vinculada" section with status and a navigation link.

**Files:**
- Modify: `apps/frontend/sistema-interno/src/types/preIncapacidad.ts`
- Modify: `apps/frontend/sistema-interno/src/services/preIncapacidadService.ts`
- Modify: `apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx`

- [ ] **Step 1: Add incapacidad_id to PreIncapacidadDetalle type**

In `apps/frontend/sistema-interno/src/types/preIncapacidad.ts`, in the `PreIncapacidadDetalle` interface, add after `motivo_devolucion`:

```typescript
  incapacidad_id: string | null;
```

- [ ] **Step 2: Add getIncapacidad() to preIncapacidadService**

In `apps/frontend/sistema-interno/src/services/preIncapacidadService.ts`, add a method to the service class:

```typescript
  async getIncapacidad(preIncapacidadId: string): Promise<IncapacidadDetalle> {
    const res = await api.get<IncapacidadDetalle>(`/pre-incapacidades/${preIncapacidadId}/incapacidad`);
    return res.data;
  }
```

Add `IncapacidadDetalle` import: `import type { IncapacidadDetalle } from '@/types/incapacidad';`

- [ ] **Step 3: Update GestionarPreIncapacidadPage to show incapacidad section**

In `apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx`:

**3a.** Add new import at the top:
```typescript
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, UserX } from 'lucide-react';
```
(Note: `useQuery` and `useMutation` are already imported — just add `ExternalLink, UserX` to the lucide import)

**3b.** Add the incapacidad query after the existing `preInc` query (around line 73):
```typescript
  const { data: incapacidad } = useQuery({
    queryKey: ['pre-incapacidad-incapacidad', id, preInc?.incapacidad_id],
    queryFn: () => preIncapacidadService.getIncapacidad(id!),
    enabled: !!id && !!preInc?.incapacidad_id,
  });
```

**3c.** Add a helper to detect missing-employee warning. After the `canDevolver` line (around line 136):
```typescript
  const empleadoNoEncontrado = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPLEADO_NOT_FOUND'
  );
```

**3d.** Replace the "Processed notice" card (lines 203-210) with an "Incapacidad Vinculada" section that:
- Shows when `preInc.incapacidad_id` exists
- Displays the incapacidad number and estado
- Shows a "Ver incapacidad" link
- Shows an alert if `empleadoNoEncontrado`

```tsx
      {/* Incapacidad vinculada (shown after unified job completes) */}
      {preInc.incapacidad_id && (
        <Card className="p-4 border-blue-200 bg-blue-50 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-blue-900 text-sm font-semibold flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Incapacidad N°{preInc.numero_radicacion} creada en el sistema
            </p>
            {incapacidad && (
              <Badge variant={incapacidad.estado === 'EN_AUDITORIA' ? 'default' : 'secondary'}>
                {incapacidad.estado}
              </Badge>
            )}
          </div>
          {empleadoNoEncontrado && (
            <div className="flex items-start gap-2 rounded bg-yellow-50 border border-yellow-200 p-3 text-yellow-800 text-xs">
              <UserX className="h-4 w-4 mt-0.5 shrink-0" />
              <span>
                <strong>Empleado no encontrado en BD.</strong> La incapacidad fue creada pero
                requiere resolución manual antes de poder procesar el pago.
              </span>
            </div>
          )}
        </Card>
      )}
```

**3e.** Update `estadoBadgeVariant` to include a success-style for `PROCESADA`:
```typescript
    case 'PROCESADA': return 'secondary';
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno
npm run build 2>&1 | head -40
```

Expected: Build succeeds (no TypeScript errors)

- [ ] **Step 5: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/frontend/sistema-interno/src/types/preIncapacidad.ts apps/frontend/sistema-interno/src/services/preIncapacidadService.ts apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx
git commit -m "feat: show linked incapacidad and empleado-not-found alert in gestión page"
```

---

## Task 7: Fix Broken Tests + Run Full Test Suite

**Context:** The validation severity change (EMPLEADO_NOT_FOUND: ERROR → WARNING) may break tests that assert error counts. Also, the existing promotion service tests may need updating for the new unified flow.

**Files:**
- Modify: `apps/backend/tests/` (any test that asserts `severidad="ERROR"` for EMPLEADO/EMPRESA_NOT_FOUND or `has_errors=True` for missing-entity scenarios)

- [ ] **Step 1: Run full test suite and identify failures**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov 2>&1 | tail -50"
```

Note all FAILED tests.

- [ ] **Step 2: Fix tests that assert EMPLEADO_NOT_FOUND/EMPRESA_NOT_FOUND as ERROR**

For each failing test that asserts `severidad == "ERROR"` for missing-entity validation issues, change the assertion to `severidad == "WARNING"`.

Example: in `tests/test_validation_inconsistencia_*.py`, find:
```python
assert issue.severidad == "ERROR"
assert issue.codigo == "EMPLEADO_NOT_FOUND"
```
Change to:
```python
assert issue.severidad == "WARNING"
assert issue.codigo == "EMPLEADO_NOT_FOUND"
```

Similarly for `EMPRESA_NOT_FOUND`.

- [ ] **Step 3: Fix promotion service tests that assert success=False for missing entities**

The old promotion service returned `success=False` when `has_errors=True` (including EMPLEADO_NOT_FOUND ERROR). Now those cases return `success=True`. Find tests like:
```python
result = await service.promote_pre_incapacidad(pre_inc.id)
assert result.success is False  # because empleado not found
```
Change to:
```python
assert result.success is True
assert result.incapacidad_id is not None
```

- [ ] **Step 4: Run full test suite again**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov 2>&1 | tail -30"
```

Expected: All tests PASSED (or only pre-existing failures that are unrelated to this plan)

- [ ] **Step 5: Check coverage is still above 70%**

```bash
cd /opt/apps/incapacidades_vs/apps/backend
docker compose exec api sh -c "python -m pytest tests/ --cov=app --cov-report=term-missing 2>&1 | grep -E 'TOTAL|PASSED|FAILED'"
```

Expected: `TOTAL` line shows ≥70% coverage.

- [ ] **Step 6: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add apps/backend/tests/
git commit -m "fix: update tests for unified flow (EMPLEADO_NOT_FOUND is now WARNING)"
```

---

## Task 8: Docs Update

**Context:** The state machine and API endpoint docs need to reflect the unified flow.

**Files:**
- Modify: `docs/04_FLUJO_ESTADOS.md`
- Modify: `docs/03_API_ENDPOINTS.md`

- [ ] **Step 1: Update 04_FLUJO_ESTADOS.md**

Open `docs/04_FLUJO_ESTADOS.md` and add a section describing the unified flow:

```markdown
## Flujo Unificado Pre-Incapacidad → Incapacidad (desde 2026-06-09)

El job de Celery `promote_pre_incapacidad_task` crea directamente una `Incapacidad` completa
desde la `PreIncapacidad` en un solo paso:

1. **Portal externo** radica `PreIncapacidad` → estado `PENDIENTE`
2. **Celery job** (`promote_pre_incapacidad_task`) se ejecuta:
   a. Resuelve empresa (por NIT) y empleado (por documento + empresa_id) — pueden no encontrarse
   b. Corre `PreIncapacidadValidationService.validate_all()` — guarda issues en `validation_inconsistencia`
   c. Crea `Incapacidad` directamente (sin restricción de empleado/empresa) con `numero = str(pre_inc.numero_radicacion)`
   d. Vincula `pre_incapacidad.incapacidad_id = incapacidad.id`
   e. Si empleado encontrado: corre reglas RN008/RN009 de auditoría (traslapes + duplicados)
   f. Llama `radicar_incapacidad()` → `Incapacidad` pasa a `EN_AUDITORIA`
   g. Actualiza `PreIncapacidad.estado = PROCESADA`
3. **Gestión interna** navega a `/pre-incapacidades/{id}/gestionar`:
   - Muestra `validation_inconsistencias` (incluyendo alertas de empleado/empresa no encontrado como WARNING)
   - Muestra "Incapacidad N°XXX creada" con vínculo a la incapacidad
   - Permite "Promover manualmente" para re-ejecutar el job si se corrigieron datos

### Manejo de empleado/empresa no encontrado

Cuando el empleado o la empresa no se encuentran en la BD:
- Se crea la incapacidad con `empleado_id = NULL` y/o `empresa_id = NULL`
- Se registra un WARNING `EMPLEADO_NOT_FOUND` / `EMPRESA_NOT_FOUND` en `validation_inconsistencia`
- La incapacidad pasa a `EN_AUDITORIA` y el auditor puede resolver manualmente

### Constraint DB relajado (desde migración unified_flow_*)

```sql
-- Nuevo constraint (ARL no requiere empleado_id / empresa_id NOT NULL)
(tipo = 'ARL' AND afiliado_id IS NULL) OR
(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
```
```

- [ ] **Step 2: Update 03_API_ENDPOINTS.md**

Add the new endpoint to the pre-incapacidades section:

```markdown
### GET /pre-incapacidades/{id}/incapacidad
**Auth:** JWT requerido
**Description:** Retorna la incapacidad completa vinculada a esta pre-incapacidad.
**Response:** `IncapacidadRead` (incluyendo empleado, empresa, documentos)
**404:** Si la pre-incapacidad no existe o no tiene incapacidad vinculada
```

- [ ] **Step 3: Commit**

```bash
cd /opt/apps/incapacidades_vs
git add docs/04_FLUJO_ESTADOS.md docs/03_API_ENDPOINTS.md
git commit -m "docs: document unified pre-incapacidad flow and new API endpoint"
```

---

## Self-Review Checklist

### Spec Coverage

| Requirement | Task |
|-------------|------|
| Portal-externo: NO changes | ✅ No portal-externo files touched |
| Background Job creates full `incapacidad` record directly | Task 4 (PromotePreIncapacidadService) |
| DB constraint: remove empresa_id requirement for ARL | Task 1 (migration + model) |
| Keep PreIncapacidad, link 1-to-1 with Incapacidad | Task 1 (incapacidad_id FK) |
| Reuse numero_radicacion | Task 2 (create_from_pre_incapacidad sets `numero = str(pre_inc.numero_radicacion)`) |
| Relax NotFoundException in create_incapacidad | Task 2 (new method bypasses validation) |
| Run audit/liquidation rules when empleado found | Task 4 (_run_audit_business_rules: RN008/RN009) |
| Call radicar_incapacidad() → RADICADA→EN_AUDITORIA | Task 4 (step 8 in promote) |
| Management view shows incapacidad directly | Task 6 (incapacidad query + section in page) |
| Handle missing empleado gracefully | Tasks 3+6 (WARNING severity + banner in UI) |
| Display validation alerts in EN_AUDITORIA | Task 6 (ValidationInconsistenciasList already shows them) |
| Fix all broken tests | Task 7 |
| Update docs | Task 8 |

### Type Consistency

- `ValidationInconsistenciaCreate.pre_incapacidad_id: UUID` — set in all issue creation calls ✅
- `ValidationInconsistenciaCreate.incapacidad_id: Optional[UUID]` — set in `_run_audit_business_rules` ✅
- `PreIncapacidadDetalle.incapacidad_id: string | null` — matches backend `PreIncapacidadResponse.incapacidad_id: Optional[UUID]` ✅
- `IncapacidadService.create_from_pre_incapacidad()` uses `incapacidad_dict` dict (not `IncapacidadCreate` schema) — bypasses validator ✅
- `PromotionResult.success: bool` — always `True` in unified flow (no ERROR-based blocking) ✅
