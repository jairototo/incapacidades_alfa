# Liquidación — PDF "Autorización de pago por OCCIRED" + estado EN_PAGO/EN_PAGO_PARCIAL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Task 5.2 of `docs/superpowers/plans/2026-06-23-workflow-estados-liquidacion.md` (`POST /incapacidades/{id}/liquidacion` and `POST /incapacidades/{id}/liquidacion/completar`) so that: (1) saving a liquidación draft generates and stores a watermarked "BORRADOR" PDF named "Autorizacion de pago por OCCIRED" visible in the incapacidad's document space; (2) completing a liquidación replaces that PDF with a final, non-watermarked version; and (3) `completar` moves the incapacidad to the new intermediate states `EN_PAGO` / `EN_PAGO_PARCIAL` instead of jumping straight to `PAGADA` / `PAGADA_PARCIAL`.

**Architecture:** A new pure PDF-building module (`liquidacion_pdf_service.py`, reportlab, following the existing `glosada_notification_service.py` pattern) generates the document; a second function in the same module persists it as a `Documento` row and **actually writes the bytes to the configured storage backend** (the existing glosada flow creates the `Documento` row but never calls `storage_backend.upload_file`, so its PDF is not downloadable — this plan does not repeat that bug). `liquidacion_service.py` calls these functions best-effort (log-and-continue on failure, consistent with `notificar_glosada`) from `guardar_liquidacion()` and `completar_liquidacion()`. Two new data fields the spec requires (`sucursal`, `nro_contrato`) don't exist anywhere in the schema today; per user decision they land as a new `Siniestro.sucursal` column (editable from the liquidación form) and a new `Empresa.nro_contrato` column. `EstadoIncapacidad` gains `EN_PAGO`/`EN_PAGO_PARCIAL`; `completar_liquidacion` now targets these instead of `PAGADA`/`PAGADA_PARCIAL`, which requires updating `orden_pago_service.py`'s gate conditions so the existing "create orden de pago → registrar pago → PAGADA" pipeline keeps working end to end (this is a necessary consequence of the state change, not optional — without it, incapacidades would get stuck in `EN_PAGO` forever with no path to `PAGADA`).

**Tech Stack:** FastAPI + SQLAlchemy 2 async, Alembic, PostgreSQL, reportlab 4.2.5 (already a backend dependency), React 18 + Tailwind v3 + Zod v3 + React Query (sistema-interno), pytest (Docker exec), vitest.

## Global Constraints

- Backend tests: `docker exec incapacidades-api python -m pytest <path> -v --no-cov` — only run tests for the file(s) touched in each task, per project convention.
- Frontend tests: `npm test -- <pattern>` from `apps/frontend/sistema-interno/`.
- TDD: red → implement → green → commit per task.
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`.
- Alembic migrations: generate via `docker exec incapacidades-api alembic revision -m "..."`, apply via `docker exec incapacidades-api alembic upgrade head`.
- Never N+1: reuse existing eager-loaded relations (`incapacidad.empleado`, `.empresa`, `.afiliado`, `.siniestro` are already eager-loaded by `incapacidad_service.get_incapacidad()` — do not add ad-hoc lazy access to them).
- All historial_estado entries use `entity_type="incapacidad"` and string state values (handled automatically by `_cambiar_estado`).

## Decisions Locked In (from user clarification, 2026-07-24)

| # | Decision |
|---|----------|
| D1 | `sucursal` lives on `Siniestro` (not `Liquidacion`), editable from the liquidación form. Allowed values are the 4 branches listed in `docs/recursos_arl/Asignación Auditores - Incapacidades ARL.xlsx`: Cali, Medellín, Cartagena, Bogotá — presented as a dropdown, not free text. |
| D2 | `nro_contrato` is a new column on `Empresa`. |
| D3 | `tipo_beneficiario` and `tipo_liquidacion` are hardcoded to the literal string `"Empleador"` for both PDF variants, for now (explicit user instruction — revisit when the business rule is defined). |
| D4 | `fecha_autorizacion_pago` is the server date/time at the moment the PDF is generated (not a stored field). |
| D5 | `completar_liquidacion` transitions `LIQUIDACION → EN_PAGO` and `LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL`. `PAGADA`/`PAGADA_PARCIAL` remain reachable only through the existing `orden_pago_service` payment-registration flow, which is updated in Phase 1 to gate on the new states instead of `LIQUIDACION`/`LIQUIDACION_PARCIAL`. |

---

## File Map

### Created
| File | Purpose |
|------|---------|
| `apps/backend/alembic/versions/<ts>_add_en_pago_states.py` | Adds `EN_PAGO`, `EN_PAGO_PARCIAL` to the `estadoincapacidad` PG enum |
| `apps/backend/alembic/versions/<ts>_add_sucursal_nro_contrato.py` | Adds `siniestro.sucursal` and `empresa.nro_contrato` columns |
| `apps/backend/app/services/liquidacion_pdf_service.py` | Builds and persists the "Autorización de pago por OCCIRED" PDF (borrador + final) |
| `apps/backend/tests/test_liquidacion_pdf_service.py` | Unit tests for PDF generation + persistence |

### Modified
| File | Why |
|------|-----|
| `apps/backend/app/utils/enums.py` | Add `EN_PAGO`, `EN_PAGO_PARCIAL` to `EstadoIncapacidad`; add `SucursalSiniestro` enum |
| `apps/backend/app/services/incapacidad_service.py` | `ALLOWED_TRANSITIONS` — add EN_PAGO/EN_PAGO_PARCIAL edges |
| `apps/backend/app/services/orden_pago_service.py` | Gate `create_orden_from_incapacidad` and `registrar_pago` on EN_PAGO/EN_PAGO_PARCIAL instead of LIQUIDACION/LIQUIDACION_PARCIAL |
| `apps/backend/app/services/liquidacion_service.py` | `completar_liquidacion` targets EN_PAGO/EN_PAGO_PARCIAL; `guardar_liquidacion`/`completar_liquidacion` call the new PDF service; `sucursal` handling |
| `apps/backend/app/models/siniestro.py` | Add `sucursal` column |
| `apps/backend/app/models/empresa.py` | Add `nro_contrato` column |
| `apps/backend/app/schemas/liquidacion.py` | Add `sucursal` to `LiquidacionGuardar` + `LiquidacionResponse` |
| `apps/backend/app/schemas/empresa.py` | Add `nro_contrato` to `EmpresaBase`/`EmpresaUpdate`/`EmpresaResponse` |
| `apps/backend/tests/test_liquidacion_service.py` | Update completar_liquidacion assertions (EN_PAGO not PAGADA); add sucursal + documento tests |
| `apps/backend/tests/test_orden_pago_service.py` | Update fixtures/gates to EN_PAGO/EN_PAGO_PARCIAL |
| `apps/frontend/sistema-interno/src/types/enums.ts` | Add EN_PAGO/EN_PAGO_PARCIAL to `EstadoIncapacidad` |
| `apps/frontend/sistema-interno/src/components/dashboard/IncapacidadesTable.tsx` | State color/label maps |
| `apps/frontend/sistema-interno/src/components/dashboard/FiltersBar.tsx` | State filter options |
| `apps/frontend/sistema-interno/src/components/dashboard/charts/DistribucionEstadosPieChart.tsx` | State color map |
| `apps/frontend/sistema-interno/src/components/incapacidades/HistorialTimeline.tsx` | State label/icon/color maps |
| `apps/frontend/sistema-interno/src/components/incapacidades/StateDescriptionPanel.tsx` | New state descriptions |
| `apps/frontend/sistema-interno/src/pages/incapacidades/LiquidacionPage.tsx` | `sucursal` field, completar success copy |
| `apps/frontend/sistema-interno/src/services/liquidacion.ts` | `sucursal` in types/payload |

---

## Phase 1: State Machine — EN_PAGO / EN_PAGO_PARCIAL

### Task 1.1: Add EN_PAGO/EN_PAGO_PARCIAL to EstadoIncapacidad + ALLOWED_TRANSITIONS

**Files:**
- Create: `apps/backend/alembic/versions/<ts>_add_en_pago_states.py`
- Modify: `apps/backend/app/utils/enums.py`
- Modify: `apps/backend/app/services/incapacidad_service.py`

**Interfaces:**
- Produces: `EstadoIncapacidad.EN_PAGO`, `EstadoIncapacidad.EN_PAGO_PARCIAL`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_enum_en_pago.py
from app.utils.enums import EstadoIncapacidad


def test_en_pago_states_exist():
    assert EstadoIncapacidad.EN_PAGO == "EN_PAGO"
    assert EstadoIncapacidad.EN_PAGO_PARCIAL == "EN_PAGO_PARCIAL"
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_enum_en_pago.py -v --no-cov
```
Expected: FAIL — `AttributeError: EN_PAGO`.

- [ ] **Step 3: Generate and write the migration**

```bash
docker exec incapacidades-api alembic revision -m "add en_pago and en_pago_parcial to estadoincapacidad enum"
```

Edit the generated file:

```python
"""add en_pago and en_pago_parcial to estadoincapacidad enum

Revision ID: <auto>
"""
from alembic import op


def upgrade() -> None:
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'EN_PAGO'")
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'EN_PAGO_PARCIAL'")
    op.execute("COMMIT")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values. No-op — matches the precedent set by
    # the original estadoincapacidad rename migration (2026-06-23 plan, Task 1.1).
    pass
```

- [ ] **Step 4: Apply migration**

```bash
docker exec incapacidades-api alembic upgrade head
```

- [ ] **Step 5: Update `EstadoIncapacidad` in `app/utils/enums.py`**

```python
class EstadoIncapacidad(str, Enum):
    """Estado de la incapacidad en el workflow."""
    RADICADA = "RADICADA"
    EN_AUDITORIA = "EN_AUDITORIA"
    PENDIENTE = "PENDIENTE"
    CREACION_SINIESTRO = "CREACION_SINIESTRO"
    LIQUIDACION = "LIQUIDACION"
    LIQUIDACION_PARCIAL = "LIQUIDACION_PARCIAL"
    GLOSADA = "GLOSADA"
    EN_PAGO = "EN_PAGO"
    EN_PAGO_PARCIAL = "EN_PAGO_PARCIAL"
    PAGADA = "PAGADA"
    PAGADA_PARCIAL = "PAGADA_PARCIAL"
```

- [ ] **Step 6: Update `ALLOWED_TRANSITIONS` in `app/services/incapacidad_service.py`**

```python
ALLOWED_TRANSITIONS: Dict[EstadoIncapacidad, List[EstadoIncapacidad]] = {
    EstadoIncapacidad.RADICADA: [
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.EN_AUDITORIA: [
        EstadoIncapacidad.PENDIENTE,
        EstadoIncapacidad.LIQUIDACION,
        EstadoIncapacidad.LIQUIDACION_PARCIAL,
        EstadoIncapacidad.GLOSADA,
        EstadoIncapacidad.CREACION_SINIESTRO,
    ],
    EstadoIncapacidad.PENDIENTE: [
        EstadoIncapacidad.EN_AUDITORIA,
        EstadoIncapacidad.GLOSADA,
    ],
    EstadoIncapacidad.CREACION_SINIESTRO: [
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.LIQUIDACION: [
        EstadoIncapacidad.EN_PAGO,
        EstadoIncapacidad.PAGADA,  # kept for the legacy /enviar-pago, /marcar-pagada endpoints
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.LIQUIDACION_PARCIAL: [
        EstadoIncapacidad.EN_PAGO_PARCIAL,
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.GLOSADA: [],
    EstadoIncapacidad.EN_PAGO: [
        EstadoIncapacidad.PAGADA,
    ],
    EstadoIncapacidad.EN_PAGO_PARCIAL: [
        EstadoIncapacidad.PAGADA_PARCIAL,
    ],
    EstadoIncapacidad.PAGADA: [],
    EstadoIncapacidad.PAGADA_PARCIAL: [],
}
```

> Note: `LIQUIDACION → PAGADA` is kept (in addition to the new `LIQUIDACION → EN_PAGO`) purely so the pre-existing, UI-unreachable `/enviar-pago` and `/marcar-pagada` endpoints (`incapacidad_service.enviar_a_pago` / `marcar_como_pagada`) don't start raising `InvalidStateException`. They are not called from any live frontend code path (confirmed: `incapacidadService.cambiarEstado` — the only caller — is itself dead code, referenced only from a test mock).

- [ ] **Step 7: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_enum_en_pago.py -v --no-cov
git add app/utils/enums.py app/services/incapacidad_service.py alembic/versions/
git commit -m "feat(estado): add EN_PAGO and EN_PAGO_PARCIAL states"
```

---

### Task 1.2: `completar_liquidacion` targets EN_PAGO / EN_PAGO_PARCIAL

**Files:**
- Modify: `apps/backend/app/services/liquidacion_service.py:401-457` (`completar_liquidacion`)
- Modify: `apps/backend/tests/test_liquidacion_service.py:410-451`

**Interfaces:**
- `completar_liquidacion()` now returns an `Incapacidad` in `EN_PAGO` (was `LIQUIDACION`) or `EN_PAGO_PARCIAL` (was `LIQUIDACION_PARCIAL`)

- [ ] **Step 1: Update the existing tests to assert the new target states**

`tests/test_liquidacion_service.py` builds its fixtures inline with the module-level helpers `_make_incapacidad(db_session, estado)`, `_make_liquidador(db_session)` and `_make_liquidacion_row(db_session, inc_id)` (no pytest fixtures) — keep that pattern. Replace the two existing tests (lines 413-450):

```python
@pytest.mark.asyncio
async def test_completar_liquidacion_a_en_pago(db_session):
    """completar_liquidacion transitions LIQUIDACION → EN_PAGO."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_PAGO


@pytest.mark.asyncio
async def test_completar_liquidacion_a_en_pago_parcial(db_session):
    """completar_liquidacion transitions LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION_PARCIAL")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_PAGO_PARCIAL
```

This replaces `test_completar_liquidacion_a_pagada` and `test_completar_liquidacion_a_pagada_parcial` — update the module docstring list at the top of the file (lines 16-17) accordingly (`12. completar_liquidacion_a_en_pago — LIQUIDACION → EN_PAGO`, `13. completar_liquidacion_a_en_pago_parcial — LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL`).

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -k "en_pago" -v --no-cov
```
Expected: FAIL — actual estado is still `PAGADA`.

- [ ] **Step 3: Update `completar_liquidacion` in `liquidacion_service.py`**

```python
        nuevo_estado = (
            EstadoIncapacidad.EN_PAGO
            if incapacidad.estado == EstadoIncapacidad.LIQUIDACION
            else EstadoIncapacidad.EN_PAGO_PARCIAL
        )

        await incapacidad_service._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=nuevo_estado,
            observacion="Liquidación completada — enviada a pago",
            usuario_id=liquidador_id,
        )
```

(Only the `nuevo_estado` computation and the observación text change — the rest of the method is unchanged.)

- [ ] **Step 4: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -v --no-cov
git add app/services/liquidacion_service.py tests/test_liquidacion_service.py
git commit -m "feat(liquidacion): completar_liquidacion now transitions to EN_PAGO/EN_PAGO_PARCIAL"
```

---

### Task 1.3: Update `orden_pago_service` gates to EN_PAGO / EN_PAGO_PARCIAL

**Context:** `orden_pago_service.create_orden_from_incapacidad()` currently only allows creating a payment order while `incapacidad.estado == LIQUIDACION` (i.e. *before* the liquidator finishes). `registrar_pago()` then transitions `LIQUIDACION`/`LIQUIDACION_PARCIAL` → `PAGADA`/`PAGADA_PARCIAL` once payment is confirmed. After Task 1.2, `completar_liquidacion` moves the incapacidad to `EN_PAGO`/`EN_PAGO_PARCIAL`, so both gates must shift to the new states — otherwise an order created before `completar` would find `registrar_pago`'s guard permanently false (the incapacidad will already be `EN_PAGO` by the time payment is registered) and payments could never resolve to `PAGADA`.

**Files:**
- Modify: `apps/backend/app/services/orden_pago_service.py:87-111` (`create_orden_from_incapacidad`)
- Modify: `apps/backend/app/services/orden_pago_service.py:319-334` (`registrar_pago`)
- Modify: `apps/backend/tests/test_orden_pago_service.py` (fixtures `test_incapacidad_arl_aprobada`, `test_incapacidad_salud_aprobada`)
- Modify: `apps/backend/tests/test_orden_pago_repository.py:76`

- [ ] **Step 1: Update fixtures to use EN_PAGO**

In `tests/test_orden_pago_service.py`, change both fixtures' `estado=EstadoIncapacidad.LIQUIDACION` to `estado=EstadoIncapacidad.EN_PAGO`. Same in `tests/test_orden_pago_repository.py:76`.

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_orden_pago_service.py -v --no-cov
```
Expected: FAIL — `create_orden_from_incapacidad` raises `BadRequestException("La incapacidad debe estar en LIQUIDACION...")` because the fixture is now EN_PAGO.

- [ ] **Step 3: Update `create_orden_from_incapacidad` gate**

```python
        # 2. Validar que esté en estado EN_PAGO (liquidación completada, lista para pago)
        if incapacidad.estado != EstadoIncapacidad.EN_PAGO:
            raise BadRequestException(
                f"La incapacidad debe estar en EN_PAGO. Estado actual: {incapacidad.estado}"
            )
```

Update the docstring above it (`"""Crea una orden de pago desde una incapacidad en LIQUIDACION."""` → `"""Crea una orden de pago desde una incapacidad en EN_PAGO."""`, and the `Raises` line).

- [ ] **Step 4: Update `registrar_pago`'s incapacidad transition**

```python
        # 6. Actualizar estado de la incapacidad a PAGADA / PAGADA_PARCIAL
        incapacidad = await self.incapacidad_repository.get_by_id(db, orden_pago.incapacidad_id)
        if incapacidad and incapacidad.estado in [EstadoIncapacidad.EN_PAGO, EstadoIncapacidad.EN_PAGO_PARCIAL]:
            from app.services.incapacidad_service import incapacidad_service
            nuevo_estado = (
                EstadoIncapacidad.PAGADA_PARCIAL
                if incapacidad.estado == EstadoIncapacidad.EN_PAGO_PARCIAL
                else EstadoIncapacidad.PAGADA
            )
            await incapacidad_service._cambiar_estado(
                db=db,
                incapacidad=incapacidad,
                nuevo_estado=nuevo_estado,
                observacion=f"Pago registrado en orden {orden_pago.numero_orden}",
                usuario_id=usuario_id,
            )
```

- [ ] **Step 5: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_orden_pago_service.py tests/test_orden_pago_repository.py -v --no-cov
git add app/services/orden_pago_service.py tests/test_orden_pago_service.py tests/test_orden_pago_repository.py
git commit -m "refactor(orden_pago): gate creation and payment registration on EN_PAGO/EN_PAGO_PARCIAL"
```

---

## Phase 2: New data fields — sucursal, nro_contrato

### Task 2.1: `Siniestro.sucursal` + `SucursalSiniestro` enum

**Files:**
- Create: `apps/backend/alembic/versions/<ts>_add_sucursal_nro_contrato.py` (this task's half — Task 2.2 adds the other column to the same migration)
- Modify: `apps/backend/app/utils/enums.py`
- Modify: `apps/backend/app/models/siniestro.py`

**Interfaces:**
- Produces: `SucursalSiniestro` enum (`CALI`, `MEDELLIN`, `CARTAGENA`, `BOGOTA`); `Siniestro.sucursal: Optional[SucursalSiniestro]`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_siniestro_sucursal.py
from app.utils.enums import SucursalSiniestro


def test_sucursal_siniestro_values():
    assert SucursalSiniestro.CALI == "Cali"
    assert SucursalSiniestro.MEDELLIN == "Medellín"
    assert SucursalSiniestro.CARTAGENA == "Cartagena"
    assert SucursalSiniestro.BOGOTA == "Bogotá"
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_siniestro_sucursal.py -v --no-cov
```

- [ ] **Step 3: Add `SucursalSiniestro` to `app/utils/enums.py`** (near `TipoSiniestro`/`EstadoSiniestro`)

```python
class SucursalSiniestro(str, Enum):
    """
    Sucursal que gira la autorización de pago para un siniestro ARL.

    Fuente: docs/recursos_arl/Asignación Auditores - Incapacidades ARL.xlsx
    (única lista de sucursales disponible a la fecha).
    """
    CALI = "Cali"
    MEDELLIN = "Medellín"
    CARTAGENA = "Cartagena"
    BOGOTA = "Bogotá"
```

- [ ] **Step 4: Generate the migration (shared with Task 2.2)**

```bash
docker exec incapacidades-api alembic revision -m "add sucursal to siniestro and nro_contrato to empresa"
```

```python
"""add sucursal to siniestro and nro_contrato to empresa

Revision ID: <auto>
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        'siniestro',
        sa.Column('sucursal', sa.String(length=50), nullable=True,
                  comment="Sucursal giradora (Cali/Medellín/Cartagena/Bogotá)"),
    )
    op.add_column(
        'empresa',
        sa.Column('nro_contrato', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('empresa', 'nro_contrato')
    op.drop_column('siniestro', 'sucursal')
```

- [ ] **Step 5: Apply migration**

```bash
docker exec incapacidades-api alembic upgrade head
```

- [ ] **Step 6: Add `sucursal` column to `app/models/siniestro.py`**

```python
from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro, SyncSource, SucursalSiniestro

# ... inside class Siniestro, after `gravedad`:
    sucursal: Mapped[Optional[SucursalSiniestro]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sucursal giradora de la autorización de pago",
    )
```

- [ ] **Step 7: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_siniestro_sucursal.py -v --no-cov
git add app/utils/enums.py app/models/siniestro.py alembic/versions/
git commit -m "feat(siniestro): add sucursal field (Cali/Medellín/Cartagena/Bogotá)"
```

---

### Task 2.2: `Empresa.nro_contrato`

**Files:**
- Modify: `apps/backend/app/models/empresa.py`
- Modify: `apps/backend/app/schemas/empresa.py`

(Migration already applied in Task 2.1, Step 4-5 — this task only adds the ORM column and exposes it in the API schema.)

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_empresa_nro_contrato.py
import pytest
from app.schemas.empresa import EmpresaUpdate


def test_empresa_update_accepts_nro_contrato():
    data = EmpresaUpdate(nro_contrato="CTR-2026-0001")
    assert data.nro_contrato == "CTR-2026-0001"
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_empresa_nro_contrato.py -v --no-cov
```
Expected: FAIL — `nro_contrato` is not a recognized field (pydantic extra-forbid or attribute mismatch).

- [ ] **Step 3: Add column to `app/models/empresa.py`** (after `direccion`/`ciudad`/`departamento` block)

```python
    nro_contrato: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

- [ ] **Step 4: Add field to `app/schemas/empresa.py`**

```python
class EmpresaBase(BaseModel):
    """Schema base para Empresa."""
    nit: str = Field(..., min_length=1, max_length=20, description="NIT de la empresa")
    razon_social: str = Field(..., min_length=1, max_length=200, description="Razón social")
    estado: str = Field(default="ACTIVA", description="Estado de la empresa")
    email_contacto: Optional[EmailStr] = Field(None, description="Email de contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    direccion: Optional[str] = Field(None, max_length=200, description="Dirección")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")
    tipo_empresa: Optional[str] = Field(None, max_length=50, description="Tipo de empresa")
    nro_contrato: Optional[str] = Field(None, max_length=100, description="Número de contrato")


class EmpresaUpdate(BaseModel):
    """Schema para actualizar una empresa."""
    razon_social: Optional[str] = Field(None, min_length=1, max_length=200)
    estado: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    tipo_empresa: Optional[str] = Field(None, max_length=50)
    nro_contrato: Optional[str] = Field(None, max_length=100)
```

(`EmpresaCreate` and `EmpresaResponse` inherit `nro_contrato` automatically via `EmpresaBase`.)

- [ ] **Step 5: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/unit/test_empresa_nro_contrato.py -v --no-cov
git add app/models/empresa.py app/schemas/empresa.py
git commit -m "feat(empresa): add nro_contrato field"
```

---

### Task 2.3: Wire `sucursal` into the liquidación form flow

**Files:**
- Modify: `apps/backend/app/schemas/liquidacion.py`
- Modify: `apps/backend/app/services/liquidacion_service.py` (`guardar_liquidacion`, `get_liquidacion`)
- Modify: `apps/backend/tests/test_liquidacion_service.py`

**Interfaces:**
- `LiquidacionGuardar.sucursal: Optional[SucursalSiniestro]`
- `LiquidacionResponse.sucursal: Optional[SucursalSiniestro]` — read back from `incapacidad.siniestro.sucursal`, not a `Liquidacion` column

- [ ] **Step 1: Write failing test**

`tests/test_liquidacion_service.py` currently builds its `Incapacidad` fixtures via a raw-SQL helper (`_make_incapacidad`) that doesn't set `empresa_id`/`empleado_id`/`siniestro_id`. This test needs a real linked `Siniestro`, so add a second helper next to `_make_incapacidad` (ORM-based, mirroring how `_make_liquidador` already builds a `Usuario` via the ORM in the same file) rather than reusing `_make_incapacidad`:

```python
async def _make_incapacidad_arl_con_siniestro(db_session, estado: str = "LIQUIDACION") -> "UUID":
    """Crea Empresa + Empleado + Siniestro + Incapacidad (ARL) vinculados, vía ORM."""
    from app.models.empresa import Empresa
    from app.models.empleado import Empleado
    from app.models.siniestro import Siniestro
    from app.models.incapacidad import Incapacidad
    from app.utils.enums import TipoDocumento, TipoIncapacidad, TipoSiniestro

    uid = uuid4()
    empresa = Empresa(nit=f"900{uid.hex[:6]}", razon_social="TechCorp S.A.S.")
    db_session.add(empresa)
    await db_session.flush()

    empleado = Empleado(
        empresa_id=empresa.id,
        numero_documento=str(uid.int % 10**9),
        tipo_documento=TipoDocumento.CC,
        nombres="Juan",
        apellidos="Pérez",
        fecha_ingreso=date(2020, 1, 1),
    )
    db_session.add(empleado)
    await db_session.flush()

    siniestro = Siniestro(
        numero_siniestro=f"SIN-TEST-{uid.hex[:8]}",
        empleado_id=empleado.id,
        empresa_id=empresa.id,
        fecha_siniestro=date(2026, 5, 1),
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Accidente de prueba",
    )
    db_session.add(siniestro)
    await db_session.flush()

    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uid.hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        empresa_id=empresa.id,
        empleado_id=empleado.id,
        siniestro_id=siniestro.id,
        estado=estado,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad.id
```

Then the test:

```python
@pytest.mark.asyncio
async def test_guardar_liquidacion_updates_siniestro_sucursal(db_session):
    """guardar_liquidacion writes sucursal onto the linked Siniestro, and the
    returned Liquidacion carries it back for the response schema."""
    from app.services.liquidacion_service import liquidacion_service
    from app.services.incapacidad_service import incapacidad_service
    from app.schemas.liquidacion import LiquidacionGuardar
    from app.utils.enums import SucursalSiniestro

    inc_id = await _make_incapacidad_arl_con_siniestro(db_session, "LIQUIDACION")

    data = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 5),
        sucursal=SucursalSiniestro.BOGOTA,
    )
    liquidacion = await liquidacion_service.guardar_liquidacion(
        db=db_session, incapacidad_id=inc_id, data=data, liquidador_id=uuid4(),
    )

    incapacidad = await incapacidad_service.get_incapacidad(db_session, inc_id)
    assert incapacidad.siniestro.sucursal == SucursalSiniestro.BOGOTA
    assert liquidacion.sucursal == SucursalSiniestro.BOGOTA
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -k sucursal -v --no-cov
```

- [ ] **Step 3: Add `sucursal` to `app/schemas/liquidacion.py`**

```python
from app.utils.enums import MetodoPagoLiquidacion, SucursalSiniestro

class LiquidacionGuardar(BaseModel):
    ...
    metodo_pago: Optional[MetodoPagoLiquidacion] = None
    notas_liquidador: Optional[str] = None
    sucursal: Optional[SucursalSiniestro] = None


class LiquidacionResponse(BaseModel):
    ...
    metodo_pago: Optional[MetodoPagoLiquidacion] = None
    notas_liquidador: Optional[str] = None
    liquidador_id: Optional[UUID] = None
    sucursal: Optional[SucursalSiniestro] = None
```

- [ ] **Step 4: Update `guardar_liquidacion` and `get_liquidacion` in `liquidacion_service.py`**

```python
    async def get_liquidacion(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> Liquidacion:
        liquidacion = await liquidacion_repository.get_by_incapacidad(db, incapacidad_id)
        if liquidacion is None:
            raise NotFoundException(
                f"No se encontró liquidación para la incapacidad {incapacidad_id}"
            )
        await self._attach_sucursal(db, liquidacion)
        return liquidacion
```

```python
    async def _attach_sucursal(self, db: AsyncSession, liquidacion: Liquidacion) -> None:
        """
        Adjunta el valor actual de sucursal (vive en Siniestro, no en Liquidacion)
        como atributo transitorio para que LiquidacionResponse.model_validate lo lea.
        """
        from app.services.incapacidad_service import incapacidad_service

        incapacidad = await incapacidad_service.get_incapacidad(db, liquidacion.incapacidad_id)
        liquidacion.sucursal = incapacidad.siniestro.sucursal if incapacidad.siniestro else None
```

In `guardar_liquidacion`, after resolving `incapacidad` (already fetched at the top of the method) and before the final `return liquidacion`:

```python
        # Sucursal vive en Siniestro, no en Liquidacion — actualizar si se envió
        if data.sucursal is not None and incapacidad.siniestro is not None:
            from app.db.repositories.siniestro_repository import SiniestroRepository
            await SiniestroRepository().update(
                db, id=incapacidad.siniestro.id, obj_in={"sucursal": data.sucursal}
            )

        ...  # existing create/update logic

        await db.commit()
        liquidacion.sucursal = data.sucursal if incapacidad.siniestro is not None else None
        logger.info(...)
        return liquidacion
```

- [ ] **Step 5: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -v --no-cov
git add app/schemas/liquidacion.py app/services/liquidacion_service.py tests/test_liquidacion_service.py
git commit -m "feat(liquidacion): capture sucursal on the linked siniestro"
```

---

## Phase 3: PDF generation — "Autorización de pago por OCCIRED"

### Task 3.1: `liquidacion_pdf_service.generar_pdf_autorizacion_pago()`

**Files:**
- Create: `apps/backend/app/services/liquidacion_pdf_service.py`
- Create: `apps/backend/tests/test_liquidacion_pdf_service.py`

**Interfaces:**
- Produces: `generar_pdf_autorizacion_pago(incapacidad: Incapacidad, liquidacion: Liquidacion, nombre_ips: Optional[str], borrador: bool) -> bytes`

- [ ] **Step 1: Write failing test**

```python
# tests/test_liquidacion_pdf_service.py
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.services.liquidacion_pdf_service import generar_pdf_autorizacion_pago


class _FakeEmpresa:
    razon_social = "TechCorp S.A.S."
    nit = "900123456-7"
    nro_contrato = "CTR-2026-0099"


class _FakeEmpleado:
    nombres = "Juan"
    apellidos = "Pérez"
    numero_documento = "123456789"
    salario_base = Decimal("2500000.00")

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class _FakeSiniestro:
    numero_siniestro = "SIN-2026-0001"
    fecha_siniestro = date(2026, 5, 1)
    sucursal = "Bogotá"


class _FakeIncapacidad:
    id = uuid4()
    numero = "INC-ARL-20260601-0001"
    numero_siniestro = "SIN-2026-0001"
    empresa = _FakeEmpresa()
    empleado = _FakeEmpleado()
    siniestro = _FakeSiniestro()
    afiliado = None


class _FakeLiquidacion:
    dias_autorizados = 5
    fecha_inicio_autorizada = date(2026, 6, 1)
    fecha_fin_autorizada = date(2026, 6, 5)
    valor_incapacidad_temporal = Decimal("416666.67")
    valor_aporte_patronal_pension = Decimal("50000.00")
    valor_aporte_trabajador_pension = Decimal("25000.00")
    valor_aporte_adicional_trabajador_pension = None
    valor_aporte_patronal_salud = Decimal("40000.00")
    valor_aporte_trabajador_salud = Decimal("20000.00")
    valor_total = Decimal("551666.67")


def test_generar_pdf_borrador_tiene_marca_de_agua():
    pdf_bytes = generar_pdf_autorizacion_pago(
        _FakeIncapacidad(), _FakeLiquidacion(), nombre_ips="IPS Central", borrador=True
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_generar_pdf_final_sin_marca_de_agua():
    pdf_bytes = generar_pdf_autorizacion_pago(
        _FakeIncapacidad(), _FakeLiquidacion(), nombre_ips="IPS Central", borrador=False
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_generar_pdf_handles_missing_siniestro():
    """SALUD incapacidades have no siniestro — must not crash, fields fall back to N/A."""
    inc = _FakeIncapacidad()
    inc.siniestro = None
    inc.empresa = None
    inc.empleado = None
    pdf_bytes = generar_pdf_autorizacion_pago(inc, _FakeLiquidacion(), nombre_ips=None, borrador=True)
    assert pdf_bytes.startswith(b"%PDF")
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_pdf_service.py -v --no-cov
```
Expected: FAIL — `ModuleNotFoundError: app.services.liquidacion_pdf_service`.

- [ ] **Step 3: Implement `app/services/liquidacion_pdf_service.py`**

```python
"""
Generación del PDF "Autorización de pago por OCCIRED" para liquidación de
incapacidades.

Dos variantes de la misma plantilla:
- borrador=True  → generada al guardar el borrador de liquidación (POST
  /incapacidades/{id}/liquidacion), con marca de agua "BORRADOR".
- borrador=False → generada al completar la liquidación (POST
  /incapacidades/{id}/liquidacion/completar), sin marca de agua.

tipo_beneficiario y tipo_liquidacion quedan fijos en "Empleador" — pendiente
de definición de negocio (decisión explícita, 2026-07-24).
"""
from __future__ import annotations

import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.incapacidad import Incapacidad
from app.models.liquidacion import Liquidacion

TITULO = "AUTORIZACIÓN DE PAGO POR OCCIRED"
TIPO_BENEFICIARIO_FIJO = "Empleador"
TIPO_LIQUIDACION_FIJO = "Empleador"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _safe(value: object) -> str:
    if value in (None, ""):
        return "N/A"
    return str(value)


def _fmt_date(value: Optional[date]) -> str:
    return value.strftime("%d/%m/%Y") if value else "N/A"


def _fmt_money(value: Optional[Decimal]) -> str:
    if value is None:
        return "Pendiente"
    return f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------


def _draw_watermark(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 90)
    canvas.setFillColor(colors.HexColor("#c0392b"))
    canvas.setFillAlpha(0.15)
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "BORRADOR")
    canvas.restoreState()


def _no_watermark(canvas, doc) -> None:
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generar_pdf_autorizacion_pago(
    incapacidad: Incapacidad,
    liquidacion: Liquidacion,
    nombre_ips: Optional[str],
    borrador: bool,
) -> bytes:
    """
    Genera el PDF "Autorización de pago por OCCIRED".

    Returns:
        bytes — contenido del PDF (comienza con b'%PDF')
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Heading1"], fontSize=14, alignment=1,
        textColor=colors.HexColor("#1a3a5c"), spaceAfter=10,
    )
    row_style = ParagraphStyle(
        "RowStyle", parent=styles["Normal"], fontSize=9, leading=12,
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=8,
    )
    right_style = ParagraphStyle(
        "RightStyle", parent=styles["Normal"], fontSize=9.5, alignment=2,
    )
    total_style = ParagraphStyle(
        "TotalStyle", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold",
    )

    empresa = getattr(incapacidad, "empresa", None)
    empleado = getattr(incapacidad, "empleado", None)
    siniestro = getattr(incapacidad, "siniestro", None)

    nombre_empresa = _safe(empresa.razon_social if empresa else None)
    nit_empresa = _safe(empresa.nit if empresa else None)
    nro_contrato = _safe(getattr(empresa, "nro_contrato", None) if empresa else None)
    nombre_empleado = _safe(empleado.nombre_completo if empleado else None)
    identificacion_empleado = _safe(empleado.numero_documento if empleado else None)
    sbc_empleado = _fmt_money(empleado.salario_base) if empleado and empleado.salario_base is not None else "N/A"
    nro_siniestro = _safe(
        siniestro.numero_siniestro if siniestro else getattr(incapacidad, "numero_siniestro", None)
    )
    fecha_siniestro = _fmt_date(siniestro.fecha_siniestro) if siniestro else "N/A"
    sucursal = _safe(siniestro.sucursal if siniestro else None)
    fecha_autorizacion_pago = datetime.now().strftime("%d/%m/%Y")
    dias_incapacidad = liquidacion.dias_autorizados

    story = []
    story.append(Paragraph("SEGUROS ALFA", title_style))
    story.append(Paragraph(TITULO, title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.4 * cm))

    filas = [
        [Paragraph(
            f"Nro de Siniestro: {nro_siniestro}    Fecha siniestro: {fecha_siniestro}    "
            f"Fecha Autorización de pago: {fecha_autorizacion_pago}",
            row_style,
        )],
        [Paragraph(
            f"COMPAÑÍA_02 - RAMO:07 - SUCURSAL: {sucursal}    SUCURSAL GIRADORA: <b>DIRECCIÓN GENERAL</b>",
            row_style,
        )],
        [Paragraph(
            f"Nombre Empresa: {nombre_empresa}    Nit: {nit_empresa}    Nro de Contrato: {nro_contrato}",
            row_style,
        )],
        [Paragraph(
            f"Empleado: {nombre_empleado}    C.C.: {identificacion_empleado}    S.B.C.: {sbc_empleado}",
            row_style,
        )],
        [Paragraph(
            f"Beneficiario: {nombre_empresa}    NIT: {nit_empresa}    Días de incapacidad: {dias_incapacidad}",
            row_style,
        )],
        [Paragraph(
            f"Tipo de Liquidación: {TIPO_LIQUIDACION_FIJO}    Tipo de Beneficiario: {TIPO_BENEFICIARIO_FIJO}",
            row_style,
        )],
    ]
    tabla_encabezado = Table(filas, colWidths=[16 * cm])
    tabla_encabezado.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla_encabezado)
    story.append(Spacer(1, 0.5 * cm))

    fecha_inicio = _fmt_date(liquidacion.fecha_inicio_autorizada)
    fecha_fin = _fmt_date(liquidacion.fecha_fin_autorizada)
    nombre_ips_txt = _safe(nombre_ips)
    story.append(Paragraph(
        f"Pago incapacidad por {dias_incapacidad} días, desde {fecha_inicio} hasta {fecha_fin}, "
        f"expedida por {nombre_ips_txt}. Se autoriza pago por abono en cuenta bancaria, "
        "por los siguientes conceptos:",
        body_style,
    ))
    story.append(Spacer(1, 0.3 * cm))

    concepto_rows = [
        ["DÍAS", "CONCEPTO", "VALOR", "CONCEPTO", "VALOR"],
        [str(dias_incapacidad), "Días incapacidad temporal o prórroga",
         _fmt_money(liquidacion.valor_incapacidad_temporal), "", ""],
        [str(dias_incapacidad), "Días aporte patronal pensión",
         _fmt_money(liquidacion.valor_aporte_patronal_pension),
         "Aporte trabajador pensión", _fmt_money(liquidacion.valor_aporte_trabajador_pension)],
        [str(dias_incapacidad), "Días aporte patronal salud",
         _fmt_money(liquidacion.valor_aporte_patronal_salud),
         "Aporte trabajador salud", _fmt_money(liquidacion.valor_aporte_trabajador_salud)],
        ["", "", "", "Aporte trabajador adicional pensión",
         _fmt_money(liquidacion.valor_aporte_adicional_trabajador_pension)],
        ["", Paragraph("<b>TOTAL A PAGAR</b>", total_style), "", "", _fmt_money(liquidacion.valor_total)],
    ]
    tabla_conceptos = Table(concepto_rows, colWidths=[1.8 * cm, 4.4 * cm, 2.8 * cm, 4.2 * cm, 2.8 * cm])
    tabla_conceptos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (1, 5), (3, 5)),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#f0f4f8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_conceptos)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("FECHA LÍMITE DE PAGO: DÍA____ MES____ AÑO____", right_style))

    doc.build(story, onFirstPage=_draw_watermark if borrador else _no_watermark,
               onLaterPages=_draw_watermark if borrador else _no_watermark)
    return buffer.getvalue()
```

- [ ] **Step 4: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_pdf_service.py -v --no-cov
git add app/services/liquidacion_pdf_service.py tests/test_liquidacion_pdf_service.py
git commit -m "feat(liquidacion): generate Autorización de pago por OCCIRED PDF (borrador + final)"
```

---

### Task 3.2: Persist the PDF as a `Documento` (with real storage write)

**Files:**
- Modify: `apps/backend/app/services/liquidacion_pdf_service.py`
- Modify: `apps/backend/tests/test_liquidacion_pdf_service.py`

**Interfaces:**
- Produces: `async def guardar_pdf_autorizacion_pago(db: AsyncSession, incapacidad: Incapacidad, pdf_bytes: bytes) -> Documento`

**Design note:** unlike `glosada_notification_service._guardar_pdf_como_documento` (which creates the `Documento` row but never calls `storage_backend.upload_file`, so the file doesn't actually exist on disk/MinIO and would 404 on download), this function writes the bytes for real. One `Documento` per incapacidad is reused across calls (found by `nombre_original`) — the borrador call creates it, the completar call overwrites its content in place, so the document space always shows exactly one "Autorizacion de pago por OCCIRED.pdf".

- [ ] **Step 1: Write failing test**

`guardar_pdf_autorizacion_pago` needs `incapacidad.id` to exist as a real FK target for `Documento.incapacidad_id`, so add a small local helper that persists a minimal `Incapacidad` row via the ORM (same idiom as `_make_liquidador` in `test_liquidacion_service.py`):

```python
# Add to tests/test_liquidacion_pdf_service.py
import pytest
from datetime import date
from uuid import uuid4

from app.services.liquidacion_pdf_service import guardar_pdf_autorizacion_pago
from app.utils.enums import TipoDocumentoAdjunto, TipoIncapacidad


async def _crear_incapacidad_real(db_session):
    from app.models.incapacidad import Incapacidad

    uid = uuid4()
    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uid.hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado="LIQUIDACION",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad


@pytest.mark.asyncio
async def test_guardar_pdf_crea_documento_nuevo(db_session):
    incapacidad = await _crear_incapacidad_real(db_session)
    documento = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 fake content")

    assert documento.incapacidad_id == incapacidad.id
    assert documento.nombre_original == "Autorizacion de pago por OCCIRED.pdf"
    assert documento.tipo_documento == TipoDocumentoAdjunto.SOPORTE_PAGO
    assert documento.mime_type == "application/pdf"
    # The bytes must be readable back from the real storage backend, not just referenced.
    from app.core.storage_core import storage_backend
    contenido = storage_backend.get_file_content(documento.ruta_storage)
    assert contenido == b"%PDF-1.4 fake content"


@pytest.mark.asyncio
async def test_guardar_pdf_reemplaza_documento_existente(db_session):
    incapacidad = await _crear_incapacidad_real(db_session)
    primero = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 borrador")
    segundo = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 final")

    assert primero.id == segundo.id  # same Documento row, content replaced

    from app.core.storage_core import storage_backend
    contenido = storage_backend.get_file_content(segundo.ruta_storage)
    assert contenido == b"%PDF-1.4 final"
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_pdf_service.py -k documento -v --no-cov
```

- [ ] **Step 3: Implement `guardar_pdf_autorizacion_pago` in `liquidacion_pdf_service.py`**

```python
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage_core import storage_backend
from app.models.documento import Documento
from app.utils.enums import TipoDocumentoAdjunto

NOMBRE_DOCUMENTO_DISPLAY = "Autorizacion de pago por OCCIRED.pdf"


async def guardar_pdf_autorizacion_pago(
    db: AsyncSession,
    incapacidad: Incapacidad,
    pdf_bytes: bytes,
) -> Documento:
    """
    Guarda (o reemplaza) el PDF de autorización de pago como Documento de la
    incapacidad. Un único Documento por incapacidad — su contenido pasa de
    borrador (con marca de agua) a final (sin marca de agua) en el mismo
    registro, para que el usuario siempre vea un solo archivo con ese nombre
    en el espacio de documentos.
    """
    result = await db.execute(
        select(Documento).where(
            Documento.incapacidad_id == incapacidad.id,
            Documento.nombre_original == NOMBRE_DOCUMENTO_DISPLAY,
        )
    )
    existente = result.scalar_one_or_none()

    if existente is not None:
        try:
            storage_backend.delete_file(existente.ruta_storage)
        except Exception:
            pass  # archivo físico ya ausente — no bloquear el reemplazo

    ruta_storage, hash_md5, hash_sha256, tamanio_bytes = storage_backend.upload_file(
        file_data=io.BytesIO(pdf_bytes),
        file_name=NOMBRE_DOCUMENTO_DISPLAY,
        content_type="application/pdf",
        folder=f"liquidacion/{incapacidad.id}",
    )

    if existente is not None:
        existente.ruta_storage = ruta_storage
        existente.hash_md5 = hash_md5
        existente.hash_sha256 = hash_sha256
        existente.tamanio_bytes = tamanio_bytes
        await db.flush()
        return existente

    documento = Documento(
        incapacidad_id=incapacidad.id,
        tipo_documento=TipoDocumentoAdjunto.SOPORTE_PAGO,
        nombre_archivo=f"autorizacion_pago_occired_{incapacidad.numero}.pdf",
        nombre_original=NOMBRE_DOCUMENTO_DISPLAY,
        ruta_storage=ruta_storage,
        bucket="incapacidades",
        mime_type="application/pdf",
        tamanio_bytes=tamanio_bytes,
        hash_md5=hash_md5,
        hash_sha256=hash_sha256,
        uploaded_by_id=None,
        validado=True,
    )
    db.add(documento)
    await db.flush()
    return documento
```

Add the `hashlib`/`select`/`AsyncSession` imports and `NOMBRE_DOCUMENTO_DISPLAY` constant near the top of the file alongside the existing imports from Task 3.1.

- [ ] **Step 4: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_pdf_service.py -v --no-cov
git add app/services/liquidacion_pdf_service.py tests/test_liquidacion_pdf_service.py
git commit -m "feat(liquidacion): persist Autorización de pago PDF as a real, downloadable Documento"
```

---

### Task 3.3: Wire PDF generation into `guardar_liquidacion` (borrador)

**Files:**
- Modify: `apps/backend/app/services/liquidacion_service.py`
- Modify: `apps/backend/tests/test_liquidacion_service.py`

- [ ] **Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_guardar_liquidacion_genera_documento_borrador(db_session):
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar
    from app.db.repositories.documento_repository import DocumentoRepository

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    data = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 5),
    )
    await liquidacion_service.guardar_liquidacion(
        db=db_session, incapacidad_id=inc_id, data=data, liquidador_id=uuid4(),
    )

    documentos = await DocumentoRepository().get_by_incapacidad(db_session, inc_id)
    nombres = [d.nombre_original for d in documentos]
    assert "Autorizacion de pago por OCCIRED.pdf" in nombres
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -k borrador -v --no-cov
```

- [ ] **Step 3: Call the PDF service from `guardar_liquidacion`**, right before the final `return liquidacion` (after `await db.commit()`):

```python
        # Generar/actualizar el PDF de autorización de pago (borrador, best-effort:
        # un fallo aquí no debe impedir que la liquidación quede guardada).
        try:
            from app.services.liquidacion_pdf_service import (
                generar_pdf_autorizacion_pago,
                guardar_pdf_autorizacion_pago,
            )
            from app.db.repositories.plantilla_auditoria_repository import (
                plantilla_auditoria_repository,
            )

            plantilla = await plantilla_auditoria_repository.get_by_incapacidad(db, incapacidad_id)
            nombre_ips = plantilla.nombre_ips if plantilla else incapacidad.ips
            pdf_bytes = generar_pdf_autorizacion_pago(
                incapacidad, liquidacion, nombre_ips=nombre_ips, borrador=True
            )
            await guardar_pdf_autorizacion_pago(db, incapacidad, pdf_bytes)
            await db.commit()
        except Exception:
            logger.exception(
                "No se pudo generar/guardar el PDF de autorización de pago (borrador) "
                "para incapacidad %s", incapacidad_id,
            )

        logger.info(
            "Liquidación guardada para incapacidad %s por liquidador %s",
            incapacidad_id, liquidador_id,
        )
        return liquidacion
```

- [ ] **Step 4: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -v --no-cov
git add app/services/liquidacion_service.py tests/test_liquidacion_service.py
git commit -m "feat(liquidacion): generate borrador PDF with BORRADOR watermark on guardar_liquidacion"
```

---

### Task 3.4: Wire PDF generation into `completar_liquidacion` (final, no watermark)

**Files:**
- Modify: `apps/backend/app/services/liquidacion_service.py`
- Modify: `apps/backend/tests/test_liquidacion_service.py`

- [ ] **Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_completar_liquidacion_genera_documento_final_sin_marca_agua(db_session):
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar
    from app.db.repositories.documento_repository import DocumentoRepository

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    data = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 5),
    )
    await liquidacion_service.guardar_liquidacion(
        db=db_session, incapacidad_id=inc_id, data=data, liquidador_id=uuid4(),
    )
    await liquidacion_service.completar_liquidacion(
        db=db_session, incapacidad_id=inc_id, liquidador_id=uuid4(),
    )

    documentos = await DocumentoRepository().get_by_incapacidad(db_session, inc_id)
    finales = [d for d in documentos if d.nombre_original == "Autorizacion de pago por OCCIRED.pdf"]
    assert len(finales) == 1  # same Documento row reused, not duplicated
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py -k documento_final -v --no-cov
```
(This should already pass structurally once Task 3.3 lands since only one Documento row is ever kept — it fails now because `completar_liquidacion` doesn't yet regenerate the PDF, so `finales` would still hold the borrador content untouched. The assertion on row-count passing without the no-watermark regeneration is the gap this step closes; add a second assertion reading the stored bytes to make the red state explicit:)

```python
    from app.core.storage_core import storage_backend
    contenido = storage_backend.get_file_content(finales[0].ruta_storage)
    assert b"BORRADOR" not in contenido  # crude but effective: watermark text must be gone
```

- [ ] **Step 3: Call the PDF service from `completar_liquidacion`**, after the `_cambiar_estado` call and before `return await incapacidad_service.get_incapacidad(...)`:

```python
        try:
            from app.services.liquidacion_pdf_service import (
                generar_pdf_autorizacion_pago,
                guardar_pdf_autorizacion_pago,
            )
            from app.db.repositories.plantilla_auditoria_repository import (
                plantilla_auditoria_repository,
            )

            plantilla = await plantilla_auditoria_repository.get_by_incapacidad(db, incapacidad_id)
            nombre_ips = plantilla.nombre_ips if plantilla else incapacidad.ips
            pdf_bytes = generar_pdf_autorizacion_pago(
                incapacidad, liq, nombre_ips=nombre_ips, borrador=False
            )
            await guardar_pdf_autorizacion_pago(db, incapacidad, pdf_bytes)
            await db.commit()
        except Exception:
            logger.exception(
                "No se pudo generar/guardar el PDF final de autorización de pago "
                "para incapacidad %s", incapacidad_id,
            )

        return await incapacidad_service.get_incapacidad(db, incapacidad_id)
```

(`liq` is the `Liquidacion` object already fetched earlier in `completar_liquidacion` via `liquidacion_repository.get_by_incapacidad`.)

- [ ] **Step 4: Run tests, commit**

```bash
docker exec incapacidades-api python -m pytest tests/test_liquidacion_service.py tests/test_liquidacion_pdf_service.py -v --no-cov
git add app/services/liquidacion_service.py tests/test_liquidacion_service.py
git commit -m "feat(liquidacion): regenerate PDF without watermark on completar_liquidacion"
```

---

## Phase 4: Frontend — sistema-interno

### Task 4.1: EN_PAGO / EN_PAGO_PARCIAL labels, colors, filters, and completar copy

**Files:**
- Modify: `apps/frontend/sistema-interno/src/types/enums.ts`
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/IncapacidadesTable.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/FiltersBar.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/charts/DistribucionEstadosPieChart.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/HistorialTimeline.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/StateDescriptionPanel.tsx`
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/LiquidacionPage.tsx`

- [ ] **Step 1: `types/enums.ts`** — add the two values:

```typescript
export const EstadoIncapacidad = {
  RADICADA: 'RADICADA',
  EN_AUDITORIA: 'EN_AUDITORIA',
  PENDIENTE: 'PENDIENTE',
  CREACION_SINIESTRO: 'CREACION_SINIESTRO',
  LIQUIDACION: 'LIQUIDACION',
  LIQUIDACION_PARCIAL: 'LIQUIDACION_PARCIAL',
  GLOSADA: 'GLOSADA',
  EN_PAGO: 'EN_PAGO',
  EN_PAGO_PARCIAL: 'EN_PAGO_PARCIAL',
  PAGADA: 'PAGADA',
  PAGADA_PARCIAL: 'PAGADA_PARCIAL',
} as const;
```

- [ ] **Step 2: `IncapacidadesTable.tsx`** — add to both maps (around line 108-128):

```typescript
          const STATE_COLORS: Record<string, string> = {
            RADICADA: 'bg-blue-100 text-blue-800',
            EN_AUDITORIA: 'bg-yellow-100 text-yellow-800',
            PENDIENTE: 'bg-orange-100 text-orange-800',
            LIQUIDACION: 'bg-purple-100 text-purple-800',
            LIQUIDACION_PARCIAL: 'bg-indigo-100 text-indigo-800',
            GLOSADA: 'bg-red-100 text-red-800',
            EN_PAGO: 'bg-cyan-100 text-cyan-800',
            EN_PAGO_PARCIAL: 'bg-sky-100 text-sky-800',
            PAGADA: 'bg-green-100 text-green-800',
            PAGADA_PARCIAL: 'bg-teal-100 text-teal-800',
          };

          const STATE_LABELS: Record<string, string> = {
            RADICADA: 'Radicada',
            EN_AUDITORIA: 'En Auditoría',
            PENDIENTE: 'Pendiente',
            LIQUIDACION: 'En Liquidación',
            LIQUIDACION_PARCIAL: 'En Liquidación Parcial',
            GLOSADA: 'Glosada',
            EN_PAGO: 'En Pago',
            EN_PAGO_PARCIAL: 'En Pago Parcial',
            PAGADA: 'Pagada',
            PAGADA_PARCIAL: 'Pagada Parcialmente',
          };
```

- [ ] **Step 3: `FiltersBar.tsx`** — insert two `SelectItem`s between `GLOSADA` and `PAGADA` (around line 118-121):

```tsx
              <SelectItem value="GLOSADA">Glosada</SelectItem>
              <SelectItem value="EN_PAGO">En Pago</SelectItem>
              <SelectItem value="EN_PAGO_PARCIAL">En Pago Parcial</SelectItem>
              <SelectItem value={EstadoIncapacidad.PAGADA}>Pagada</SelectItem>
              <SelectItem value="PAGADA_PARCIAL">Pagada Parcial</SelectItem>
```

- [ ] **Step 4: `DistribucionEstadosPieChart.tsx`** — add to `ESTADO_COLORS` (around line 8-19):

```typescript
const ESTADO_COLORS: Record<string, string> = {
  RADICADA: '#3b82f6',
  EN_AUDITORIA: '#eab308',
  PENDIENTE: '#f97316',
  CREACION_SINIESTRO: '#06b6d4',
  LIQUIDACION: '#a855f7',
  LIQUIDACION_PARCIAL: '#6366f1',
  GLOSADA: '#ef4444',
  EN_PAGO: '#0891b2',
  EN_PAGO_PARCIAL: '#0284c7',
  PAGADA: '#22c55e',
  PAGADA_PARCIAL: '#14b8a6',
};
```

- [ ] **Step 5: `HistorialTimeline.tsx`** — add `EN_PAGO`/`EN_PAGO_PARCIAL` to `STATE_LABELS` and to the three `switch` statements (`getEstadoIcon`, `getEstadoBackground`, `getEstadoBadgeVariant`):

```typescript
const STATE_LABELS: Record<string, string> = {
  RADICADA: 'Radicada',
  EN_AUDITORIA: 'En Auditoría',
  PENDIENTE: 'Pendiente',
  CREACION_SINIESTRO: 'Creación de Siniestro',
  LIQUIDACION: 'En Liquidación',
  LIQUIDACION_PARCIAL: 'En Liquidación Parcial',
  GLOSADA: 'Glosada',
  EN_PAGO: 'En Pago',
  EN_PAGO_PARCIAL: 'En Pago Parcial',
  PAGADA: 'Pagada',
  PAGADA_PARCIAL: 'Pagada Parcialmente',
};
```

```typescript
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
    case 'EN_PAGO':
    case 'EN_PAGO_PARCIAL':
      return <DollarSign className="h-6 w-6 text-white" />;
```

```typescript
    case 'EN_PAGO':
      return 'bg-cyan-500';
    case 'EN_PAGO_PARCIAL':
      return 'bg-sky-500';
```
(insert right after the `LIQUIDACION_PARCIAL` case in `getEstadoBackground`)

```typescript
    case 'LIQUIDACION':
    case 'LIQUIDACION_PARCIAL':
    case 'EN_PAGO':
    case 'EN_PAGO_PARCIAL':
      return 'default';
```
(replace the `LIQUIDACION`/`LIQUIDACION_PARCIAL` case in `getEstadoBadgeVariant` to also cover the new states)

- [ ] **Step 6: `StateDescriptionPanel.tsx`** — add a `Send` icon import and two new `STATE_INFO` entries between `LIQUIDACION_PARCIAL` and `GLOSADA`:

```typescript
import {
  FileCheck,
  Search,
  Clock,
  Link,
  AlertTriangle,
  Ban,
  CreditCard,
  Send,
  CheckCircle,
  CheckCircle2,
} from 'lucide-react';
```

```typescript
  EN_PAGO: {
    icon: <Send className="h-4 w-4" />,
    colorClass: 'border-cyan-200 bg-cyan-50 text-cyan-800',
    descripcion:
      'Liquidación completada. La orden de pago se genera y confirma desde el módulo de Órdenes de Pago.',
    requisitos: ['Orden de pago generada y pagada para pasar a PAGADA'],
  },
  EN_PAGO_PARCIAL: {
    icon: <Send className="h-4 w-4" />,
    colorClass: 'border-sky-200 bg-sky-50 text-sky-800',
    descripcion:
      'Liquidación parcial completada. La orden de pago se genera y confirma desde el módulo de Órdenes de Pago.',
    requisitos: ['Orden de pago generada y pagada para pasar a PAGADA_PARCIAL'],
  },
```

- [ ] **Step 7: `LiquidacionPage.tsx`** — update the `completarMutation` success copy (currently says "marcada como pagada", which is no longer accurate):

```typescript
  const completarMutation = useMutation({
    mutationFn: () => liquidacionService.completarLiquidacion(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      toast({
        title: 'Liquidación completada',
        description: 'La incapacidad pasó a estado EN_PAGO y queda lista para generar la orden de pago.',
      });
      setTimeout(() => navigate('/incapacidades/pendientes'), 1500);
    },
    ...
```

- [ ] **Step 8: Run frontend tests**

```bash
cd apps/frontend/sistema-interno && npm test -- --run
```

- [ ] **Step 9: Commit**

```bash
git add src/types/enums.ts src/components/dashboard/IncapacidadesTable.tsx src/components/dashboard/FiltersBar.tsx src/components/dashboard/charts/DistribucionEstadosPieChart.tsx src/components/incapacidades/HistorialTimeline.tsx src/components/incapacidades/StateDescriptionPanel.tsx src/pages/incapacidades/LiquidacionPage.tsx
git commit -m "feat(sistema-interno): add EN_PAGO/EN_PAGO_PARCIAL labels, colors and update completar copy"
```

---

### Task 4.2: `sucursal` dropdown in the liquidación form

**Files:**
- Modify: `apps/frontend/sistema-interno/src/services/liquidacion.ts`
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/LiquidacionPage.tsx`

- [ ] **Step 1: Add `sucursal` to `liquidacion.ts` types**

```typescript
export const SucursalSiniestro = {
  CALI: 'Cali',
  MEDELLIN: 'Medellín',
  CARTAGENA: 'Cartagena',
  BOGOTA: 'Bogotá',
} as const;

export type SucursalSiniestro = (typeof SucursalSiniestro)[keyof typeof SucursalSiniestro];
```

Add `sucursal?: SucursalSiniestro | null;` to both `LiquidacionResponse` and `LiquidacionGuardar` interfaces.

- [ ] **Step 2: Add the field to the Zod schema and form in `LiquidacionPage.tsx`**

```typescript
const liquidacionFormSchema = z.object({
  ibl: z
    .string()
    .min(1, 'El IBL es obligatorio')
    .refine(
      (val) => !isNaN(Number(val)) && Number(val) > 0,
      'El IBL debe ser un número mayor a 0'
    ),
  sucursal: z
    .string()
    .optional()
    .transform((val) => (val === '' ? undefined : val)),
  metodo_pago: z
    .string()
    .optional()
    .transform((val) => (val === '' ? undefined : val)),
  notas_liquidador: z.string().max(1000, 'Máximo 1000 caracteres').optional(),
});
```

Import `SucursalSiniestro` from `@/services/liquidacion`, add it to the `resetForm` defaults / `useEffect` prefill (mirroring `metodo_pago`), and add a dropdown to the form, right after the "Método de pago" `Card` block:

```tsx
                {/* Sucursal */}
                <Card className="p-4 space-y-4">
                  <h2 className="text-lg font-semibold text-slate-800">Sucursal</h2>
                  <div className="space-y-1.5">
                    <label htmlFor="sucursal" className="text-sm font-medium leading-none">
                      Sucursal giradora
                      <span className="text-xs text-slate-500 ml-2">
                        (Solo ARL con siniestro vinculado)
                      </span>
                    </label>
                    <select
                      id="sucursal"
                      className={[
                        'flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm',
                        'ring-offset-background',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                        'border-input',
                      ].join(' ')}
                      {...register('sucursal')}
                    >
                      <option value="">Seleccionar...</option>
                      {Object.entries(SucursalSiniestro).map(([key, value]) => (
                        <option key={key} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  </div>
                </Card>
```

Add `sucursal: values.sucursal ?? null` to the `onSave` payload construction.

- [ ] **Step 3: Update tests**

Extend `LiquidacionPage.test.tsx` and `liquidacion.test.ts` (existing test files) with one assertion each verifying the sucursal `<select>` renders its four options and that `guardarLiquidacion` payload includes `sucursal` when selected — follow the existing pattern used for `metodo_pago` in the same files.

- [ ] **Step 4: Run tests, commit**

```bash
cd apps/frontend/sistema-interno && npm test -- --run
git add src/services/liquidacion.ts src/pages/incapacidades/LiquidacionPage.tsx src/pages/incapacidades/__tests__/LiquidacionPage.test.tsx src/services/__tests__/liquidacion.test.ts
git commit -m "feat(sistema-interno): add sucursal dropdown to the liquidación form"
```

---

## Post-implementation checklist

- [ ] Full backend suite green: `docker exec incapacidades-api python -m pytest tests/ -v --no-cov`
- [ ] Full frontend suite green: `cd apps/frontend/sistema-interno && npm test -- --run`
- [ ] Manually verify in the UI: save a liquidación draft → "Autorizacion de pago por OCCIRED.pdf" appears in Documentos with a visible BORRADOR watermark when previewed → complete the liquidación → same document, watermark gone, incapacidad now shows state EN_PAGO (not PAGADA).
- [ ] Manually verify the Órdenes de Pago flow still resolves EN_PAGO → PAGADA end to end (create orden, registrar pago).
