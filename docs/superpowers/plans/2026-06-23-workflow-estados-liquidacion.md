# Workflow States & Liquidation Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename and restructure the Incapacidad state machine (9 states), add PENDIENTE behavior with 8-day alert, add CREACION_SINIESTRO flow for ADMINISTRADOR role, enforce siniestro validation gates, build the auditor approval template, liquidation form with year-parameterized IBL percentages, GLOSADA email+PDF notification via existing Mailtrap config, and mandatory historial observations on all transitions.

**Architecture:** All state-machine changes flow outward from `EstadoIncapacidad` in `app/utils/enums.py`; the Alembic M1 migration is the unblocking prerequisite for every other phase. New domain models (`PlantillaAuditoria`, `Liquidacion`, `IblParametros`) follow the clean-layer pattern: model → repository → service → endpoint. Frontend (sistema-interno) gains a liquidation page, auditor approval modal, and CREACION_SINIESTRO admin form; portal-externo gets label updates and GLOSADA read-only treatment.

**Tech Stack:** FastAPI + SQLAlchemy 2 async, Alembic, PostgreSQL (enum DDL), Celery (alert task), React 18 + Tailwind v3, Zod v3, React Query, Vitest, pytest (Docker exec).

## Global Constraints

- Backend tests: always `docker compose exec api sh -c "python -m pytest <path> -v --no-cov"` from `apps/backend/`
- Frontend tests: `npm test -- <pattern>` from `apps/frontend/sistema-interno/`
- TDD: red → implement → green → commit per task
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`
- Coverage threshold: 70% (backend + frontend)
- Tailwind v3 + Zod v3 in sistema-interno (do NOT import from portal-externo)
- Never N+1: use eager loading with `selectinload` in all new repositories
- All historial_estado entries use `entity_type="incapacidad"` and string state values

---

## ✅ Clarifications Applied (2026-06-23)

| # | Clarification |
|---|--------------|
| C1 | **RESOLVED** — IBL percentages provided: create `ibl_parametros` table (M4), seed 2026 row. Service reads from DB, not hardcoded. |
| C2 | **STILL PENDING** — CHEQUE/OXIRRE entity list awaiting client. `metodo_pago` field present in model; dropdown functional with no entity restriction for now. |
| C3+C4 | **RESOLVED** — No new env vars. Use existing Mailtrap config: `SMTP_HOST/PORT/USER/PASSWORD` + `EMAIL_FROM=noreply@incapacidades.com` already in `.env` and `config.py`. |
| C5 | **RESOLVED** — Replace "Claudia routing" with CREACION_SINIESTRO state (ADMINISTRADOR role). No named-user routing. See Phase 3b. |

---

## ⚠️ Migration Risk Note

The `estadoincapacidad` PostgreSQL enum cannot be altered in-place (PostgreSQL does not support `DROP VALUE`). The migration strategy is: add new values → migrate data → recreate enum by cycling through TEXT → DROP TYPE → CREATE TYPE → ALTER COLUMN. This is safe on dev/staging but must be coordinated with any production deployment (table lock on `ALTER COLUMN TYPE`). No production data exists yet.

Also update SLA field names in `config.py` (old names reference removed states):
- `SLA_OBSERVADA_DIAS` → `SLA_PENDIENTE_DIAS` (keep value 10)
- `SLA_APROBADA_DIAS` → `SLA_LIQUIDACION_DIAS` (keep value 3)
- Remove `SLA_EN_PAGO_DIAS` (state removed)

---

## File Map

### Created
| File | Purpose |
|------|---------|
| `apps/backend/app/models/plantilla_auditoria.py` | SQLAlchemy model for auditor approval template |
| `apps/backend/app/models/liquidacion.py` | SQLAlchemy model for liquidation record |
| `apps/backend/app/db/repositories/plantilla_auditoria_repository.py` | CRUD for plantilla_auditoria |
| `apps/backend/app/db/repositories/liquidacion_repository.py` | CRUD for liquidacion |
| `apps/backend/app/services/plantilla_auditoria_service.py` | Business logic for approval template |
| `apps/backend/app/services/liquidacion_service.py` | Business logic for liquidation + devolution |
| `apps/backend/app/services/glosada_notification_service.py` | Email + PDF generation on GLOSADA |
| `apps/backend/app/schemas/plantilla_auditoria.py` | Pydantic schemas |
| `apps/backend/app/schemas/liquidacion.py` | Pydantic schemas |
| `apps/backend/app/api/v1/endpoints/plantilla_auditoria.py` | REST endpoints |
| `apps/backend/app/api/v1/endpoints/liquidacion.py` | REST endpoints |
| `apps/backend/alembic/versions/<timestamp>_rename_estadoincapacidad_enum.py` | Phase 1 migration |
| `apps/backend/alembic/versions/<timestamp>_add_pendiente_desde.py` | Phase 2 migration |
| `apps/backend/alembic/versions/<timestamp>_add_plantilla_auditoria.py` | Phase 4 migration |
| `apps/backend/alembic/versions/<timestamp>_add_liquidacion.py` | Phase 5 migration |
| `apps/frontend/sistema-interno/src/pages/incapacidades/LiquidacionPage.tsx` | Liquidator work page |
| `apps/frontend/sistema-interno/src/components/incapacidades/AuditorApprovalTemplateModal.tsx` | Template modal |
| `apps/frontend/sistema-interno/src/components/incapacidades/StateDescriptionPanel.tsx` | Per-state descriptions |
| `apps/frontend/sistema-interno/src/components/incapacidades/PendienteAlertBadge.tsx` | Alert badge component |
| `apps/frontend/sistema-interno/src/services/liquidacion.ts` | API client |
| `apps/frontend/sistema-interno/src/services/plantillaAuditoria.ts` | API client |

### Modified (key files)
| File | Why |
|------|-----|
| `apps/backend/app/utils/enums.py` | Rename EstadoIncapacidad values |
| `apps/backend/app/services/incapacidad_service.py` | ALLOWED_TRANSITIONS, mandatory obs, GLOSADA hook |
| `apps/backend/app/services/auditoria_service.py` | REGLAS_ESPERADAS, add new rules |
| `apps/backend/app/services/incapacidad_validation_rules.py` | Add SINIESTRO_REQUERIDO + PRIMER_DIA_NO_PAGABLE |
| `apps/backend/app/models/incapacidad.py` | Add `pendiente_desde` column |
| `apps/backend/app/core/config.py` | Add FROM_EMAIL + BCC_EMAIL env vars |
| `apps/backend/app/api/v1/endpoints/incapacidades.py` | State refs, new endpoints for template/liquidacion/reenvio |
| `apps/backend/app/api/v1/router.py` | Register new endpoint routers |
| `apps/backend/app/schemas/incapacidad.py` | Update state literal types |
| All backend tests referencing old state names | Update assertions |
| `apps/frontend/sistema-interno/src/components/dashboard/IncapacidadesTable.tsx` | State label/color map |
| `apps/frontend/sistema-interno/src/components/dashboard/charts/DistribucionEstadosPieChart.tsx` | State color map |
| `apps/frontend/sistema-interno/src/components/dashboard/FiltersBar.tsx` | State filter options |
| `apps/frontend/sistema-interno/src/components/incapacidades/HistorialTimeline.tsx` | State cases |
| `apps/frontend/sistema-interno/src/components/incapacidades/GestionActions.tsx` | Action buttons, labels |
| `apps/frontend/portal-externo/src/components/consulta/` | Display label for PENDIENTE state |

---

## Phase 1: State Machine Rename (Foundation)

> This phase unblocks all others. Nothing referencing state names can be implemented until this migration is applied and the enum updated.

### Task 1.1: Alembic migration — rename `estadoincapacidad` enum

**Files:**
- Create: `apps/backend/alembic/versions/<timestamp>_rename_estadoincapacidad_enum.py`

**Migration strategy:** PostgreSQL cannot drop enum values; cycle via TEXT.

- [ ] **Step 1: Generate empty migration file**

```bash
cd apps/backend
make migrate msg="rename estadoincapacidad enum values for new workflow"
```

- [ ] **Step 2: Write the migration**

```python
"""rename estadoincapacidad enum values for new workflow

Revision ID: <auto>
"""
from alembic import op
import sqlalchemy as sa

old_values = (
    'RADICADA','EN_AUDITORIA','OBSERVADA','APROBADA','APROBADA_PARCIALMENTE',
    'RECHAZADA','EN_PAGO','EN_PAGO_PARCIAL','PAGADA','PAGADA_PARCIALMENTE','CANCELADA'
)
new_values = (
    'RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',
    'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA','PAGADA_PARCIAL'
)

def upgrade() -> None:
    # Add new values (PostgreSQL allows adding, not renaming)
    for v in ('PENDIENTE','CREACION_SINIESTRO','LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA_PARCIAL'):
        op.execute(f"ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS '{v}'")
    op.execute("COMMIT")

    # Migrate data: map old values to new values
    mapping = {
        'OBSERVADA': 'PENDIENTE',
        'APROBADA': 'LIQUIDACION',
        'APROBADA_PARCIALMENTE': 'LIQUIDACION_PARCIAL',
        'EN_PAGO': 'LIQUIDACION',
        'EN_PAGO_PARCIAL': 'LIQUIDACION_PARCIAL',
        'RECHAZADA': 'GLOSADA',
        'PAGADA_PARCIALMENTE': 'PAGADA_PARCIAL',
        'CANCELADA': 'GLOSADA',
    }
    for old, new in mapping.items():
        op.execute(f"UPDATE incapacidad SET estado = '{new}' WHERE estado = '{old}'")

    # Migrate historial_estado string values (stored as VARCHAR, not enum)
    for old, new in mapping.items():
        op.execute(f"UPDATE historial_estado SET estado_anterior = '{new}' WHERE estado_anterior = '{old}'")
        op.execute(f"UPDATE historial_estado SET estado_nuevo = '{new}' WHERE estado_nuevo = '{old}'")

    # Recreate enum with only new values (cycle via TEXT)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE TEXT")
    op.execute("DROP TYPE estadoincapacidad")
    op.execute(
        "CREATE TYPE estadoincapacidad AS ENUM "
        "('RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',"
        "'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA','PAGADA_PARCIAL')"
    )
    op.execute(
        "ALTER TABLE incapacidad ALTER COLUMN estado TYPE estadoincapacidad "
        "USING estado::estadoincapacidad"
    )

def downgrade() -> None:
    # Recreate old enum
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE TEXT")
    op.execute("DROP TYPE estadoincapacidad")
    op.execute(
        "CREATE TYPE estadoincapacidad AS ENUM "
        "('RADICADA','EN_AUDITORIA','OBSERVADA','APROBADA','APROBADA_PARCIALMENTE',"
        "'RECHAZADA','EN_PAGO','EN_PAGO_PARCIAL','PAGADA','PAGADA_PARCIALMENTE','CANCELADA')"
    )
    op.execute(
        "ALTER TABLE incapacidad ALTER COLUMN estado TYPE estadoincapacidad "
        "USING estado::estadoincapacidad"
    )
```

- [ ] **Step 3: Apply migration**

```bash
docker compose exec api sh -c "alembic upgrade head"
```
Expected: no error; `\dT+ estadoincapacidad` in psql shows 8 values.

- [ ] **Step 4: Commit**

```bash
git add alembic/versions/
git commit -m "chore(db): rename estadoincapacidad enum — OBSERVADA→PENDIENTE, APROBADA→LIQUIDACION, RECHAZADA→GLOSADA"
```

---

### Task 1.2: Update Python enum and transition matrix

**Files:**
- Modify: `apps/backend/app/utils/enums.py:13-25`
- Modify: `apps/backend/app/services/incapacidad_service.py:43-86`

**Interfaces:**
- Produces: `EstadoIncapacidad` with values RADICADA, EN_AUDITORIA, PENDIENTE, LIQUIDACION, LIQUIDACION_PARCIAL, GLOSADA, PAGADA, PAGADA_PARCIAL

- [ ] **Step 1: Write failing import test**

```python
# tests/unit/test_enum_estados.py
from app.utils.enums import EstadoIncapacidad

def test_new_state_values_exist():
    assert EstadoIncapacidad.PENDIENTE
    assert EstadoIncapacidad.LIQUIDACION
    assert EstadoIncapacidad.LIQUIDACION_PARCIAL
    assert EstadoIncapacidad.GLOSADA
    assert EstadoIncapacidad.PAGADA_PARCIAL

def test_old_state_values_removed():
    assert not hasattr(EstadoIncapacidad, 'OBSERVADA')
    assert not hasattr(EstadoIncapacidad, 'APROBADA')
    assert not hasattr(EstadoIncapacidad, 'RECHAZADA')
    assert not hasattr(EstadoIncapacidad, 'CANCELADA')
    assert not hasattr(EstadoIncapacidad, 'EN_PAGO')
    assert not hasattr(EstadoIncapacidad, 'EN_PAGO_PARCIAL')
    assert not hasattr(EstadoIncapacidad, 'PAGADA_PARCIALMENTE')
```

- [ ] **Step 2: Run to verify it fails**

```bash
docker compose exec api sh -c "python -m pytest tests/unit/test_enum_estados.py -v --no-cov"
```
Expected: FAILED (PENDIENTE not found).

- [ ] **Step 3: Update `app/utils/enums.py`**

```python
class EstadoIncapacidad(str, Enum):
    RADICADA = "RADICADA"
    EN_AUDITORIA = "EN_AUDITORIA"
    PENDIENTE = "PENDIENTE"                   # was OBSERVADA — auditor hold, awaiting info
    CREACION_SINIESTRO = "CREACION_SINIESTRO" # ADMINISTRADOR links external siniestro number
    LIQUIDACION = "LIQUIDACION"               # was APROBADA — liquidator works here
    LIQUIDACION_PARCIAL = "LIQUIDACION_PARCIAL"  # was APROBADA_PARCIALMENTE
    GLOSADA = "GLOSADA"               # was RECHAZADA — terminal
    PAGADA = "PAGADA"                 # terminal
    PAGADA_PARCIAL = "PAGADA_PARCIAL" # was PAGADA_PARCIALMENTE — terminal
```

- [ ] **Step 4: Update `ALLOWED_TRANSITIONS` in `incapacidad_service.py:43-86`**

```python
ALLOWED_TRANSITIONS: Dict[EstadoIncapacidad, List[EstadoIncapacidad]] = {
    EstadoIncapacidad.RADICADA: [
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.EN_AUDITORIA: [
        EstadoIncapacidad.PENDIENTE,
        EstadoIncapacidad.CREACION_SINIESTRO,  # ADMINISTRADOR only — no siniestro linked
        EstadoIncapacidad.LIQUIDACION,
        EstadoIncapacidad.LIQUIDACION_PARCIAL,
        EstadoIncapacidad.GLOSADA,
    ],
    EstadoIncapacidad.PENDIENTE: [
        EstadoIncapacidad.EN_AUDITORIA,   # info arrived / deadline passed → continue audit
        EstadoIncapacidad.GLOSADA,         # info never provided → glosa
    ],
    EstadoIncapacidad.CREACION_SINIESTRO: [
        EstadoIncapacidad.EN_AUDITORIA,    # siniestro linked → return to auditor
    ],
    EstadoIncapacidad.LIQUIDACION: [
        EstadoIncapacidad.PAGADA,          # liquidator completes payment
        EstadoIncapacidad.EN_AUDITORIA,    # liquidator devolution (wrong data)
    ],
    EstadoIncapacidad.LIQUIDACION_PARCIAL: [
        EstadoIncapacidad.PAGADA_PARCIAL,
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.GLOSADA: [],
    EstadoIncapacidad.PAGADA: [],
    EstadoIncapacidad.PAGADA_PARCIAL: [],
}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
docker compose exec api sh -c "python -m pytest tests/unit/test_enum_estados.py -v --no-cov"
```

- [ ] **Step 6: Commit**

```bash
git add app/utils/enums.py app/services/incapacidad_service.py
git commit -m "feat: update EstadoIncapacidad enum and ALLOWED_TRANSITIONS for new workflow"
```

---

### Task 1.3: Update all remaining backend references to old state names

**Files:**
- Modify: `apps/backend/app/services/incapacidad_service.py` (all `OBSERVADA`, `APROBADA`, `RECHAZADA`, `CANCELADA`, `EN_PAGO`, `PAGADA_PARCIALMENTE` references)
- Modify: `apps/backend/app/services/auditoria_service.py`
- Modify: `apps/backend/app/schemas/incapacidad.py`
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py`
- Modify: `apps/backend/app/api/v1/endpoints/ordenes_pago.py`
- Modify: `apps/backend/app/db/repositories/incapacidad_repository.py`

Key mechanical changes:

In `incapacidad_service.py`:
```python
# listar_pendientes() — update estados_pendientes
estados_pendientes = [
    EstadoIncapacidad.RADICADA,
    EstadoIncapacidad.EN_AUDITORIA,
    EstadoIncapacidad.PENDIENTE,    # was OBSERVADA
]

# update_incapacidad() — estados_editables
estados_editables = [
    EstadoIncapacidad.RADICADA,
    EstadoIncapacidad.PENDIENTE,    # was OBSERVADA
]

# auditar_incapacidad() — accion mapping
if accion == "SOLICITAR_INFORMACION":
    nuevo_estado = EstadoIncapacidad.PENDIENTE    # was OBSERVADA
elif accion == "APROBAR_PARA_PAGO":
    nuevo_estado = EstadoIncapacidad.LIQUIDACION  # was APROBADA
elif accion == "APROBAR_PARA_PAGO_PARCIAL":
    nuevo_estado = EstadoIncapacidad.LIQUIDACION_PARCIAL  # was APROBADA_PARCIALMENTE
elif accion == "RECHAZAR":
    nuevo_estado = EstadoIncapacidad.GLOSADA      # was RECHAZADA
```

In `auditoria_service.py`:
```python
# Transition RADICADA → EN_AUDITORIA (unchanged, no rename needed here)
# _registrar_historial uses EstadoIncapacidad.EN_AUDITORIA (no change)
```

In `_sanitize_incapacidad_publica` in `incapacidad_service.py:1262`:
```python
# Replace "OBSERVADA" string with "PENDIENTE"
if estado_actual == "PENDIENTE" and historial:
```

In `ordenes_pago.py`: any references to APROBADA state that gated orden_pago creation must reference LIQUIDACION instead.

- [ ] **Step 1: Run full test suite to establish baseline failures**

```bash
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov 2>&1 | grep -E 'FAILED|ERROR' | head -30"
```

- [ ] **Step 2: Do the mechanical renames** (as described above in all files)

- [ ] **Step 3: Run full test suite — must all pass**

```bash
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov"
```

- [ ] **Step 4: Commit**

```bash
git add app/
git commit -m "refactor: update all backend references from old to new EstadoIncapacidad values"
```

---

### Task 1.4: Update frontend state references (sistema-interno)

**Files:**
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/IncapacidadesTable.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/charts/DistribucionEstadosPieChart.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/dashboard/FiltersBar.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/HistorialTimeline.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/GestionActions.tsx`

The `EstadoIncapacidad` TypeScript enum/type must be updated. Find it:
```bash
grep -rn "EstadoIncapacidad" apps/frontend/sistema-interno/src --include="*.ts" --include="*.tsx" | grep -v test | head -20
```

New state color/label maps:

```typescript
// In IncapacidadesTable.tsx and HistorialTimeline.tsx
const STATE_COLORS: Record<string, string> = {
  RADICADA: 'bg-blue-100 text-blue-800',
  EN_AUDITORIA: 'bg-yellow-100 text-yellow-800',
  PENDIENTE: 'bg-orange-100 text-orange-800',       // was OBSERVADA
  LIQUIDACION: 'bg-purple-100 text-purple-800',     // was APROBADA
  LIQUIDACION_PARCIAL: 'bg-indigo-100 text-indigo-800',
  GLOSADA: 'bg-red-100 text-red-800',               // was RECHAZADA
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
  PAGADA: 'Pagada',
  PAGADA_PARCIAL: 'Pagada Parcialmente',
};
```

In `GestionActions.tsx`, rename action buttons:
- "Aprobar" → triggers LIQUIDACION (opens PlantillaAuditoria modal — Task 4.4)
- "Poner en Pendiente" → triggers PENDIENTE (was "Solicitar Información" → OBSERVADA)
- "Glosar" → triggers GLOSADA (was "Rechazar")

In `FiltersBar.tsx`, update SelectItem values:
```tsx
<SelectItem value="PENDIENTE">Pendiente</SelectItem>
<SelectItem value="LIQUIDACION">En Liquidación</SelectItem>
<SelectItem value="LIQUIDACION_PARCIAL">Liquidación Parcial</SelectItem>
<SelectItem value="GLOSADA">Glosada</SelectItem>
<SelectItem value="PAGADA">Pagada</SelectItem>
<SelectItem value="PAGADA_PARCIAL">Pagada Parcial</SelectItem>
```

- [ ] **Step 1: Update TypeScript type definitions**
- [ ] **Step 2: Update all state maps/switch statements**
- [ ] **Step 3: Run frontend tests**

```bash
cd apps/frontend/sistema-interno && npm test -- --run
```

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: update sistema-interno state labels and colors for new workflow"
```

---

### Task 1.5: Update portal-externo state display

**Files:**
- Modify: `apps/frontend/portal-externo/src/components/consulta/` (public query components)

The public consulta shows `estado` as a label. Update the label map:
- PENDIENTE label: "Pendiente de información" (the observation note is shown, so stakeholders understand)
- GLOSADA label: "Glosada"
- Remove labels for OBSERVADA, APROBADA, RECHAZADA, CANCELADA

Also update `_sanitize_incapacidad_publica` condition in backend (Task 1.3 already did this).

- [ ] **Step 1: Find all state string references in portal-externo**

```bash
grep -rn "OBSERVADA\|APROBADA\|RECHAZADA" apps/frontend/portal-externo/src --include="*.tsx" --include="*.ts"
```

- [ ] **Step 2: Update label maps**
- [ ] **Step 3: Run portal-externo tests**

```bash
cd apps/frontend/portal-externo && npm test -- --run
```

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: update portal-externo state labels for new workflow"
```

---

## Phase 2: PENDIENTE State Behavior

### Task 2.1: Add `pendiente_desde` column + enforce mandatory observation

**Files:**
- Create: `apps/backend/alembic/versions/<timestamp>_add_pendiente_desde.py`
- Modify: `apps/backend/app/models/incapacidad.py`
- Modify: `apps/backend/app/services/incapacidad_service.py` (auditar_incapacidad, _validate_state_transition)

**Interfaces:**
- Produces: `Incapacidad.pendiente_desde: Optional[datetime]` — set when entering PENDIENTE, cleared when leaving

- [ ] **Step 1: Write failing test for mandatory observation on PENDIENTE transition**

```python
# tests/test_pendiente_behavior.py
import pytest
from app.core.exceptions import BadRequestException

@pytest.mark.asyncio
async def test_pendiente_requires_observation(db_session, incapacidad_en_auditoria):
    from app.services.incapacidad_service import incapacidad_service
    with pytest.raises(BadRequestException, match="observaci"):
        await incapacidad_service.auditar_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad_en_auditoria.id,
            accion="SOLICITAR_INFORMACION",
            observaciones="",  # empty — must be rejected
        )

@pytest.mark.asyncio
async def test_pendiente_sets_pendiente_desde(db_session, incapacidad_en_auditoria):
    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.auditar_incapacidad(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria.id,
        accion="SOLICITAR_INFORMACION",
        observaciones="Falta la historia clínica del evento",
    )
    assert result.pendiente_desde is not None

@pytest.mark.asyncio
async def test_leaving_pendiente_clears_pendiente_desde(db_session, incapacidad_pendiente):
    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.retornar_a_auditoria(
        db=db_session,
        incapacidad_id=incapacidad_pendiente.id,
        observaciones="Documentos recibidos, retomando auditoría",
    )
    assert result.pendiente_desde is None
```

- [ ] **Step 2: Run to verify failure**

```bash
docker compose exec api sh -c "python -m pytest tests/test_pendiente_behavior.py -v --no-cov"
```

- [ ] **Step 3: Create Alembic migration**

```python
def upgrade() -> None:
    op.add_column('incapacidad', sa.Column('pendiente_desde', sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('incapacidad', 'pendiente_desde')
```

- [ ] **Step 4: Add column to `Incapacidad` model**

```python
# In app/models/incapacidad.py, after fecha_rechazo:
pendiente_desde: Mapped[Optional[datetime]] = mapped_column(
    nullable=True,
    comment="Timestamp de cuando la incapacidad entró en estado PENDIENTE (para cálculo de alerta de 8 días)"
)
```

- [ ] **Step 5: Enforce mandatory observation + set/clear `pendiente_desde` in `auditar_incapacidad()`**

```python
# In incapacidad_service.py — auditar_incapacidad(), before estado assignment:
if not observaciones or not observaciones.strip():
    raise BadRequestException(
        "La observación es obligatoria para todas las transiciones de auditoría"
    )

if accion == "SOLICITAR_INFORMACION":
    nuevo_estado = EstadoIncapacidad.PENDIENTE
    update_data['pendiente_desde'] = datetime.utcnow()
# When leaving PENDIENTE (e.g. via retornar_a_auditoria):
elif accion == "RETORNAR_A_AUDITORIA":
    nuevo_estado = EstadoIncapacidad.EN_AUDITORIA
    update_data['pendiente_desde'] = None
```

Add new action `RETORNAR_A_AUDITORIA` to the accion dispatcher.

- [ ] **Step 6: Run tests, all pass**

```bash
docker compose exec api sh -c "python -m pytest tests/test_pendiente_behavior.py -v --no-cov"
```

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(pendiente): add pendiente_desde column, mandatory observation, RETORNAR_A_AUDITORIA action"
```

---

### Task 2.2: PENDIENTE 8-day alert — Celery task + auditor queue indicator

**Files:**
- Create or modify: `apps/backend/app/tasks/incapacidad_tasks.py` (add beat task)
- Modify: `apps/backend/app/core/config.py` (add `PENDIENTE_ALERT_DAYS: int = 8`)
- Modify: `apps/backend/app/db/repositories/incapacidad_repository.py` (add `get_pendientes_vencidos()`)

**Interfaces:**
- Produces: `incapacidad_repository.get_pendientes_vencidos(db, dias) -> List[Incapacidad]`
- The task queries incapacidades where `estado = PENDIENTE` AND `pendiente_desde < now() - interval 'N days'`
- Does NOT auto-transition; only flags (the auditor decides the next action)

- [ ] **Step 1: Add repository query**

```python
# In incapacidad_repository.py
async def get_pendientes_vencidos(
    self, db: AsyncSession, dias: int = 8
) -> list[Incapacidad]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=dias)
    result = await db.execute(
        select(Incapacidad)
        .options(selectinload(Incapacidad.empleado), selectinload(Incapacidad.empresa))
        .where(
            Incapacidad.estado == EstadoIncapacidad.PENDIENTE,
            Incapacidad.pendiente_desde <= cutoff,
        )
    )
    return result.scalars().all()
```

- [ ] **Step 2: Add Celery beat task**

```python
# In app/tasks/incapacidad_tasks.py
@celery_app.task(name="tasks.check_pendientes_alert")
def check_pendientes_alert() -> None:
    """Runs daily. Logs (and in future notifies) incapacidades stuck in PENDIENTE > N days."""
    import asyncio
    from app.core.config import settings
    asyncio.run(_check_pendientes_alert_async(settings.PENDIENTE_ALERT_DAYS))

async def _check_pendientes_alert_async(dias: int) -> None:
    from app.db.session import AsyncSessionLocal
    from app.db.repositories.incapacidad_repository import incapacidad_repository
    async with AsyncSessionLocal() as db:
        vencidas = await incapacidad_repository.get_pendientes_vencidos(db, dias)
        for inc in vencidas:
            logger.warning(f"PENDIENTE alerta: {inc.numero} lleva >{dias} días sin respuesta")
        # Future: trigger push notification or email to auditor queue
```

Register in Celery beat schedule (in `celery_config.py` or `config.py`):
```python
"check-pendientes-alert": {
    "task": "tasks.check_pendientes_alert",
    "schedule": crontab(hour=8, minute=0),  # daily at 8am
},
```

- [ ] **Step 3: Frontend — `PendienteAlertBadge` component**

A small badge rendered in `PendientesPage.tsx` / `GestionarPage.tsx` next to records in PENDIENTE state with `dias_en_estado_actual >= 8`:

```tsx
// src/components/incapacidades/PendienteAlertBadge.tsx
interface Props { diasEnPendiente: number }
export function PendienteAlertBadge({ diasEnPendiente }: Props) {
  if (diasEnPendiente < 8) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
      ⚠ {diasEnPendiente} días sin respuesta
    </span>
  );
}
```

The `listar_pendientes` endpoint already returns `dias_en_estado_actual` — use that value.

- [ ] **Step 4: Write test for `get_pendientes_vencidos`**

```python
@pytest.mark.asyncio
async def test_get_pendientes_vencidos_returns_only_old_ones(db_session):
    # Create one PENDIENTE with pendiente_desde = 9 days ago, one = 3 days ago
    # Assert only the old one is returned
    ...
```

- [ ] **Step 5: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k pendiente -v --no-cov"
git commit -m "feat(pendiente): add 8-day alert Celery task and PendienteAlertBadge UI"
```

---

## Phase 3: Siniestro Validation Gates

### Task 3.0 (new): CREACION_SINIESTRO state — ADMINISTRADOR links external siniestro

**Context:** When an ARL incapacidad reaches EN_AUDITORIA with no siniestro linked, the auditor cannot approve or glosa. An ADMINISTRADOR enters the external `numero_siniestro`, a Celery task fetches the full siniestro record from the external system and populates the local `siniestro` table, then transitions the incapacidad back to EN_AUDITORIA.

**No new DB columns required** — `incapacidad.numero_siniestro` (String(50)) and `siniestro.numero_siniestro` + `siniestro.external_id` already exist.

**Files:**
- Modify: `apps/backend/app/utils/enums.py` (CREACION_SINIESTRO already added in Task 1.2)
- Modify: `apps/backend/app/services/incapacidad_service.py` (add `iniciar_creacion_siniestro()`, restrict to ADMINISTRADOR via role check in endpoint)
- Create: `apps/backend/app/tasks/siniestro_tasks.py` (`vincular_siniestro_externo_task`)
- Create: `apps/backend/app/api/v1/endpoints/creacion_siniestro.py`
- Create: `apps/frontend/sistema-interno/src/pages/incapacidades/CreacionSiniestroPage.tsx`

**Interfaces:**
- `POST /incapacidades/{id}/creacion-siniestro` — ADMINISTRADOR enters `numero_siniestro`; sets state = CREACION_SINIESTRO, saves `incapacidad.numero_siniestro`, enqueues task
- Celery task `vincular_siniestro_externo_task(incapacidad_id, numero_siniestro)`: queries external API (`settings.API_RRHH_BASE_URL`), creates/finds `Siniestro`, sets `incapacidad.siniestro_id`, transitions → EN_AUDITORIA

- [ ] **Step 1: Write failing test for state transition (ADMINISTRADOR only)**

```python
# tests/test_creacion_siniestro.py
@pytest.mark.asyncio
async def test_iniciar_creacion_siniestro_sets_state(db_session, incapacidad_en_auditoria):
    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.iniciar_creacion_siniestro(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria.id,
        numero_siniestro_externo="SINX-2026-001",
        usuario_id=uuid4(),
        observacion="Vinculando siniestro externo SINX-2026-001",
    )
    assert result.estado == EstadoIncapacidad.CREACION_SINIESTRO
    assert result.numero_siniestro == "SINX-2026-001"

@pytest.mark.asyncio
async def test_vincular_siniestro_task_transitions_to_en_auditoria(db_session, incapacidad_creacion_siniestro):
    from app.tasks.siniestro_tasks import _vincular_siniestro_async
    await _vincular_siniestro_async(
        incapacidad_id=incapacidad_creacion_siniestro.id,
        numero_siniestro="SINX-2026-001",
    )
    await db_session.refresh(incapacidad_creacion_siniestro)
    assert incapacidad_creacion_siniestro.estado == EstadoIncapacidad.EN_AUDITORIA
    assert incapacidad_creacion_siniestro.siniestro_id is not None
```

- [ ] **Step 2: Add `iniciar_creacion_siniestro()` to `incapacidad_service.py`**

```python
async def iniciar_creacion_siniestro(
    self,
    db: AsyncSession,
    incapacidad_id: UUID,
    numero_siniestro_externo: str,
    usuario_id: UUID,
    observacion: str,
) -> Incapacidad:
    incapacidad = await self.get_incapacidad(db, incapacidad_id)
    if incapacidad.tipo != TipoIncapacidad.ARL:
        raise BadRequestException("CREACION_SINIESTRO solo aplica a incapacidades ARL")
    return await self._cambiar_estado(
        db, incapacidad,
        nuevo_estado=EstadoIncapacidad.CREACION_SINIESTRO,
        observacion=observacion,
        usuario_id=usuario_id,
        extra_update={"numero_siniestro": numero_siniestro_externo},
    )
```

- [ ] **Step 3: Create Celery task `siniestro_tasks.py`**

```python
# app/tasks/siniestro_tasks.py
@celery_app.task(name="tasks.vincular_siniestro_externo")
def vincular_siniestro_externo_task(incapacidad_id: str, numero_siniestro: str) -> None:
    import asyncio
    asyncio.run(_vincular_siniestro_async(UUID(incapacidad_id), numero_siniestro))

async def _vincular_siniestro_async(incapacidad_id: UUID, numero_siniestro: str) -> None:
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # 1. Fetch siniestro data from external API
        siniestro_data = await _fetch_external_siniestro(numero_siniestro)
        
        # 2. Find or create Siniestro record
        from app.db.repositories.siniestro_repository import SiniestroRepository
        repo = SiniestroRepository()
        siniestro = await repo.get_by_numero(db, numero_siniestro)
        if not siniestro:
            siniestro = await repo.create(db, siniestro_data)
        
        # 3. Link to incapacidad and return to EN_AUDITORIA
        from app.db.repositories.incapacidad_repository import incapacidad_repository
        inc = await incapacidad_repository.get_by_id(db, incapacidad_id)
        if inc and inc.estado == EstadoIncapacidad.CREACION_SINIESTRO:
            from app.services.incapacidad_service import incapacidad_service
            await incapacidad_service._cambiar_estado(
                db, inc,
                nuevo_estado=EstadoIncapacidad.EN_AUDITORIA,
                observacion=f"Siniestro {numero_siniestro} vinculado automáticamente",
                usuario_id=None,
                extra_update={"siniestro_id": siniestro.id},
            )
            await db.commit()

async def _fetch_external_siniestro(numero_siniestro: str) -> dict:
    """Calls API_RRHH_BASE_URL to retrieve siniestro data. Returns stub if unreachable."""
    from app.core.config import settings
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.API_RRHH_BASE_URL}/siniestros/{numero_siniestro}",
                headers={"X-Api-Key": settings.API_RRHH_API_KEY},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"External siniestro fetch failed: {e} — using stub")
    # Stub: return minimal record so the flow completes even if external API is down
    return {
        "numero_siniestro": numero_siniestro,
        "descripcion": f"Siniestro {numero_siniestro} (pendiente de sincronización)",
        "sync_source": "API",
        "external_id": numero_siniestro,
        # Note: empleado_id, empresa_id, fecha_siniestro, tipo_siniestro, gravedad
        # must be resolved from the incapacidad if the external call fails.
        # The task caller should pass these as fallback context.
    }
```

- [ ] **Step 4: Create endpoint `creacion_siniestro.py`**

```python
@router.post("/incapacidades/{incapacidad_id}/creacion-siniestro")
async def iniciar_creacion_siniestro(
    incapacidad_id: UUID,
    body: CreacionSiniestroRequest,  # {numero_siniestro: str, observacion: str}
    current_user: Usuario = Depends(require_roles([RolUsuario.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    inc = await incapacidad_service.iniciar_creacion_siniestro(
        db, incapacidad_id, body.numero_siniestro, current_user.id, body.observacion
    )
    vincular_siniestro_externo_task.delay(str(incapacidad_id), body.numero_siniestro)
    return inc
```

- [ ] **Step 5: Frontend `CreacionSiniestroPage.tsx`** — minimal form:
  - Read-only incapacidad header (employee, company, dates)
  - Input: "Número de siniestro externo" (texto libre, required)
  - Textarea: "Observación" (required)
  - Submit: "Vincular siniestro" → POST → success shows "Siniestro en proceso de vinculación, la incapacidad volverá a EN_AUDITORIA automáticamente"
  - Visible only to ADMIN role

- [ ] **Step 6: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/test_creacion_siniestro.py -v --no-cov"
git commit -m "feat(siniestro): add CREACION_SINIESTRO state, admin endpoint, and Celery vincular task"
```

---

### Task 3.1: Add `SINIESTRO_REQUERIDO` business rule + check existing routing

**Files:**
- Modify: `apps/backend/app/services/incapacidad_validation_rules.py`
- Modify: `apps/backend/app/services/auditoria_service.py` (REGLAS_ESPERADAS)
- Modify: `apps/backend/app/services/incapacidad_service.py` (gate in `auditar_incapacidad`)

> **C5 check:** Before implementing, verify in `app/tasks/incapacidad_tasks.py` and `auditoria_service.py` whether "Claudia" queue routing (assigning incapacidades sin siniestro to a specific user) already exists from Phase 4. It does NOT appear to exist currently — flag this as a future feature in a `# TODO: route to designated auditor (Claudia)` comment.

**Interfaces:**
- New rule: `SINIESTRO_REQUERIDO` — triggered when `incapacidad.siniestro_id is None` and `tipo == ARL`
- Rule is in `validate_business_rules()` (same pure-function pattern as existing rules)
- In `auditar_incapacidad()`: before allowing → LIQUIDACION / LIQUIDACION_PARCIAL / GLOSADA, check that `SINIESTRO_REQUERIDO` is not blocking (it's an ERROR, not WARNING)

- [ ] **Step 1: Write failing test**

```python
# tests/test_siniestro_validation.py
def test_siniestro_requerido_fires_when_no_siniestro():
    from app.services.incapacidad_validation_rules import validate_business_rules
    row = {
        "tipo": "ARL",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": None,
    }
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)
    assert next(i for i in issues if i["codigo"] == "SINIESTRO_REQUERIDO")["severidad"] == "ERROR"

def test_siniestro_requerido_does_not_fire_when_linked():
    from app.services.incapacidad_validation_rules import validate_business_rules
    import uuid
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 5, 15),
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)

def test_siniestro_requerido_not_checked_for_salud():
    from app.services.incapacidad_validation_rules import validate_business_rules
    row = {
        "tipo": "SALUD",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": None,
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)
```

- [ ] **Step 2: Run to verify failure**

```bash
docker compose exec api sh -c "python -m pytest tests/test_siniestro_validation.py -v --no-cov"
```

- [ ] **Step 3: Add rule to `validate_business_rules()` in `incapacidad_validation_rules.py`**

```python
# Add to validate_business_rules():
if row.get("tipo") == "ARL" and not row.get("siniestro_id"):
    issues.append(_issue(
        "SINIESTRO_REQUERIDO", "BUSINESS_RULE", "ERROR",
        "Esta incapacidad ARL no tiene un siniestro asociado. "
        "Debe crear o vincular el siniestro antes de aprobar o glosar.",
        "siniestro_id"
    ))
    # TODO: route to designated auditor (Claudia) — pending queue routing feature
```

- [ ] **Step 4: Add `SINIESTRO_REQUERIDO` to `REGLAS_ESPERADAS` in `auditoria_service.py`**

```python
REGLAS_ESPERADAS = [
    # existing rules ...
    ("SINIESTRO_REQUERIDO", "BUSINESS_RULE"),
    ("PRIMER_DIA_NO_PAGABLE", "BUSINESS_RULE"),  # added in Task 3.2
]
```

Update `_incapacidad_to_row()` to include `siniestro_id` and `fecha_siniestro`:
```python
def _incapacidad_to_row(inc: Incapacidad) -> dict:
    return {
        # existing fields ...
        "siniestro_id": inc.siniestro_id,
        "fecha_siniestro": inc.siniestro.fecha_accidente if inc.siniestro else None,
    }
```

Update `auditar_incapacidad()` eager load to include siniestro:
```python
select(Incapacidad)
.options(
    selectinload(Incapacidad.empleado),
    selectinload(Incapacidad.siniestro),  # add this
)
```

- [ ] **Step 5: Gate transition in `incapacidad_service.auditar_incapacidad()`**

```python
# After resolving nuevo_estado and before calling _validate_state_transition:
if nuevo_estado in (
    EstadoIncapacidad.LIQUIDACION,
    EstadoIncapacidad.LIQUIDACION_PARCIAL,
    EstadoIncapacidad.GLOSADA,
):
    if incapacidad.tipo == TipoIncapacidad.ARL and not incapacidad.siniestro_id:
        raise BadRequestException(
            "Esta incapacidad no tiene un siniestro asociado. "
            "Debe crear o vincular el siniestro antes de continuar."
        )
```

- [ ] **Step 6: Run all tests**

```bash
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov"
```

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(auditoria): add SINIESTRO_REQUERIDO rule and transition gate"
```

---

### Task 3.2: Add `PRIMER_DIA_NO_PAGABLE` rule — force LIQUIDACION_PARCIAL

**Files:**
- Modify: `apps/backend/app/services/incapacidad_validation_rules.py`
- Modify: `apps/backend/app/services/incapacidad_service.py`

**Business rule:** If `fecha_inicio == fecha_siniestro` (same day), the first day is NOT payable, so full LIQUIDACION must be blocked — only LIQUIDACION_PARCIAL is allowed.

- [ ] **Step 1: Write failing test**

```python
def test_primer_dia_no_pagable_fires_when_dates_match():
    from app.services.incapacidad_validation_rules import validate_business_rules
    import uuid
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 6, 1),  # same as fecha_inicio
    }
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)

def test_primer_dia_no_pagable_does_not_fire_when_dates_differ():
    from app.services.incapacidad_validation_rules import validate_business_rules
    import uuid
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 2),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 9,
        "fecha_siniestro": date(2026, 6, 1),  # different
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)
```

- [ ] **Step 2: Implement rule in `validate_business_rules()`**

```python
# After SINIESTRO_REQUERIDO:
if (
    row.get("tipo") == "ARL"
    and row.get("siniestro_id")
    and row.get("fecha_inicio")
    and row.get("fecha_siniestro")
    and row["fecha_inicio"] == row["fecha_siniestro"]
):
    issues.append(_issue(
        "PRIMER_DIA_NO_PAGABLE", "BUSINESS_RULE", "ERROR",
        "El primer día de incapacidad coincide con la fecha del siniestro: "
        "ese día no es pagable. Solo se puede aprobar liquidación parcial.",
        "fecha_inicio"
    ))
```

- [ ] **Step 3: Enforce in `auditar_incapacidad()` — block LIQUIDACION if rule fires**

```python
if accion == "APROBAR_PARA_PAGO":
    # Check if primer_dia_no_pagable applies
    if (
        incapacidad.tipo == TipoIncapacidad.ARL
        and incapacidad.siniestro
        and incapacidad.fecha_inicio == incapacidad.siniestro.fecha_accidente
    ):
        raise BadRequestException(
            "El primer día coincide con la fecha del siniestro: "
            "debe usar aprobación parcial (APROBAR_PARA_PAGO_PARCIAL)."
        )
    nuevo_estado = EstadoIncapacidad.LIQUIDACION
```

- [ ] **Step 4: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k "siniestro or primer_dia" -v --no-cov"
git commit -m "feat(auditoria): add PRIMER_DIA_NO_PAGABLE rule — forces LIQUIDACION_PARCIAL"
```

---

## Phase 4: Auditor Approval Template (Plantilla de Auditoría)

### Task 4.1: `plantilla_auditoria` table + repository + service + endpoint

**Files:**
- Create: `apps/backend/app/models/plantilla_auditoria.py`
- Create: `apps/backend/app/schemas/plantilla_auditoria.py`
- Create: `apps/backend/app/db/repositories/plantilla_auditoria_repository.py`
- Create: `apps/backend/app/services/plantilla_auditoria_service.py`
- Create: `apps/backend/app/api/v1/endpoints/plantilla_auditoria.py`
- Create: Alembic migration

**Interfaces:**
- Produces: `POST /api/v1/incapacidades/{id}/plantilla-auditoria` — create/update approval template
- Produces: `GET /api/v1/incapacidades/{id}/plantilla-auditoria` — retrieve template
- Produces: `GET /api/v1/incapacidades/{id}/plantilla-auditoria/texto-copiable` — plain text for Arpis paste

- [ ] **Step 1: Write failing test for schema validation**

```python
# tests/unit/test_plantilla_auditoria_schema.py
from app.schemas.plantilla_auditoria import PlantillaAuditoriaCreate

def test_schema_requires_canal_recepcion():
    with pytest.raises(Exception):
        PlantillaAuditoriaCreate()  # missing fields
```

- [ ] **Step 2: Create Alembic migration**

```python
def upgrade() -> None:
    op.create_table(
        'plantilla_auditoria',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('incapacidad_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('incapacidad.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('canal_recepcion', sa.String(100), nullable=False,
                  comment="Portal / Imaginex / Onbase"),
        sa.Column('nombre_ips', sa.String(255), nullable=True),
        sa.Column('fecha_emision_incapacidad', sa.Date, nullable=True),
        sa.Column('dias_autorizados', sa.Integer, nullable=False),
        sa.Column('fecha_inicio_autorizada', sa.Date, nullable=False),
        sa.Column('fecha_fin_autorizada', sa.Date, nullable=False),
        sa.Column('diagnostico_cie10', sa.String(10), nullable=True),
        sa.Column('descripcion_cie10', sa.Text, nullable=True),
        sa.Column('nombre_medico', sa.String(200), nullable=True),
        sa.Column('especialidad_medico', sa.String(100), nullable=True),
        sa.Column('linea_autorizacion', sa.Text, nullable=True,
                  comment="Auto-generated: Se autoriza pago por X días desde ... hasta ..."),
        # For partial approval:
        sa.Column('dias_documento', sa.Integer, nullable=True,
                  comment="Total días en el documento físico"),
        sa.Column('rango_pagado_inicio', sa.Date, nullable=True),
        sa.Column('rango_pagado_fin', sa.Date, nullable=True),
        sa.Column('auditado_por_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('usuario.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
```

- [ ] **Step 3: Create model `app/models/plantilla_auditoria.py`**

```python
class PlantillaAuditoria(BaseModel):
    __tablename__ = "plantilla_auditoria"
    incapacidad_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"), nullable=False, unique=True)
    canal_recepcion: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_ips: Mapped[Optional[str]] = mapped_column(String(255))
    fecha_emision_incapacidad: Mapped[Optional[date]] = mapped_column(Date)
    dias_autorizados: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio_autorizada: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin_autorizada: Mapped[date] = mapped_column(Date, nullable=False)
    diagnostico_cie10: Mapped[Optional[str]] = mapped_column(String(10))
    descripcion_cie10: Mapped[Optional[str]] = mapped_column(Text)
    nombre_medico: Mapped[Optional[str]] = mapped_column(String(200))
    especialidad_medico: Mapped[Optional[str]] = mapped_column(String(100))
    linea_autorizacion: Mapped[Optional[str]] = mapped_column(Text)
    dias_documento: Mapped[Optional[int]] = mapped_column(Integer)
    rango_pagado_inicio: Mapped[Optional[date]] = mapped_column(Date)
    rango_pagado_fin: Mapped[Optional[date]] = mapped_column(Date)
    auditado_por_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    incapacidad: Mapped["Incapacidad"] = relationship("Incapacidad", back_populates="plantilla_auditoria")
```

Add to `Incapacidad` model:
```python
plantilla_auditoria: Mapped[Optional["PlantillaAuditoria"]] = relationship(
    "PlantillaAuditoria", back_populates="incapacidad", uselist=False, cascade="all, delete-orphan"
)
```

- [ ] **Step 4: Create Pydantic schemas (`app/schemas/plantilla_auditoria.py`)**

```python
class PlantillaAuditoriaCreate(BaseModel):
    canal_recepcion: str
    nombre_ips: Optional[str] = None
    fecha_emision_incapacidad: Optional[date] = None
    dias_autorizados: int = Field(gt=0)
    fecha_inicio_autorizada: date
    fecha_fin_autorizada: date
    diagnostico_cie10: Optional[str] = None
    descripcion_cie10: Optional[str] = None
    nombre_medico: Optional[str] = None
    especialidad_medico: Optional[str] = None
    dias_documento: Optional[int] = None
    rango_pagado_inicio: Optional[date] = None
    rango_pagado_fin: Optional[date] = None

    @model_validator(mode='after')
    def compute_linea_autorizacion(self) -> 'PlantillaAuditoriaCreate':
        self.linea_autorizacion = (
            f"Se autoriza pago por {self.dias_autorizados} días "
            f"desde {self.fecha_inicio_autorizada.isoformat()} "
            f"hasta {self.fecha_fin_autorizada.isoformat()}"
        )
        return self

class PlantillaAuditoriaResponse(PlantillaAuditoriaCreate):
    id: UUID
    incapacidad_id: UUID
    linea_autorizacion: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 5: Create service and endpoint**

`plantilla_auditoria_service.py`: `create_or_update(db, incapacidad_id, data, usuario_id)` — upsert on `incapacidad_id`.

`plantilla_auditoria.py` endpoint:
```python
@router.post("/incapacidades/{incapacidad_id}/plantilla-auditoria", response_model=PlantillaAuditoriaResponse)
async def create_plantilla(incapacidad_id: UUID, data: PlantillaAuditoriaCreate, ...): ...

@router.get("/incapacidades/{incapacidad_id}/plantilla-auditoria", response_model=PlantillaAuditoriaResponse)
async def get_plantilla(incapacidad_id: UUID, ...): ...

@router.get("/incapacidades/{incapacidad_id}/plantilla-auditoria/texto-copiable", response_model=dict)
async def get_texto_copiable(incapacidad_id: UUID, ...):
    # Returns {"texto": "Se autoriza pago por X días... CIE-10: ... Médico: ..."}
    # Pre-formatted for pasting into Arpis
```

- [ ] **Step 6: Write integration test**

```python
@pytest.mark.asyncio
async def test_create_plantilla_auditoria(client, auth_token_auditor, incapacidad_en_auditoria):
    resp = await client.post(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria.id}/plantilla-auditoria",
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 10,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-10",
        },
        headers={"Authorization": f"Bearer {auth_token_auditor}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Se autoriza pago por 10 días" in data["linea_autorizacion"]
```

- [ ] **Step 7: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k plantilla -v --no-cov"
git commit -m "feat(auditoria): add plantilla_auditoria table, service, and endpoints"
```

---

### Task 4.2: Frontend — AuditorApprovalTemplateModal

**Files:**
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/AuditorApprovalTemplateModal.tsx`
- Create: `apps/frontend/sistema-interno/src/services/plantillaAuditoria.ts`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/GestionActions.tsx`

The modal opens when the auditor clicks "Liquidar" or "Liquidar Parcial". It pre-fills data from the Incapacidad and lets the auditor adjust before submitting.

```tsx
// AuditorApprovalTemplateModal.tsx (structure — implement fully)
interface Props {
  incapacidad: Incapacidad;
  accion: 'LIQUIDACION' | 'LIQUIDACION_PARCIAL';
  onConfirm: (template: PlantillaAuditoriaCreate, observacion: string) => void;
  onCancel: () => void;
}

// Fields pre-filled from incapacidad:
// - diagnostico_cie10, nombre_medico
// - fecha_inicio, fecha_fin → fecha_inicio_autorizada, fecha_fin_autorizada
// - dias_totales → dias_autorizados
// - ips → nombre_ips
// Fields auditor fills:
// - canal_recepcion (select: Portal / Imaginex / Onbase)
// - especialidad_medico
// - dias_autorizados (editable — auditor may adjust)
// Computed / read-only:
// - linea_autorizacion (auto-updated as dias/dates change)
// - texto-copiable textarea (for Arpis paste)
```

In `GestionActions.tsx`, replace the direct "Aprobar" action dispatch with opening this modal first.

- [ ] **Step 1: Write vitest test for modal rendering**

```tsx
// tests/AuditorApprovalTemplateModal.test.tsx
it('pre-fills CIE-10 and medico from incapacidad', () => {
  render(<AuditorApprovalTemplateModal incapacidad={mockInc} accion="LIQUIDACION" ... />)
  expect(screen.getByDisplayValue('M545')).toBeInTheDocument()
})
it('updates linea_autorizacion when dias_autorizados changes', async () => { ... })
```

- [ ] **Step 2: Build the modal (see field list above)**
- [ ] **Step 3: Run tests, commit**

```bash
cd apps/frontend/sistema-interno && npm test -- AuditorApprovalTemplateModal --run
git commit -m "feat(ui): add AuditorApprovalTemplateModal for structured approval"
```

---

## Phase 5: Liquidation Form (LIQUIDACION / LIQUIDACION_PARCIAL)

### Task 5.0 (new): `ibl_parametros` table — year-parameterized IBL percentages

**Files:**
- Create: added to M4 migration (same Alembic file as `liquidacion`)
- Create: `apps/backend/app/models/ibl_parametros.py`
- Create: `apps/backend/app/db/repositories/ibl_parametros_repository.py` (simple `get_by_ano`)

**Purpose:** The liquidation service reads percentages from this table for the current year rather than hardcoding them. The DBA or admin can `INSERT` a new row each year without any code change.

**2026 seed values:**
- `aporte_patronal_pension`: 12.0%
- `aporte_patronal_salud`: 8.5%
- `aporte_trabajador_pension`: 4.0%
- `aporte_trabajador_salud`: 4.0%

```python
# Added to M4 upgrade():
op.create_table(
    'ibl_parametros',
    sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
    sa.Column('ano', sa.Integer, nullable=False, unique=True),
    sa.Column('aporte_patronal_pension', sa.Numeric(5, 2), nullable=False,
              comment="Porcentaje aporte patronal pensión, e.g. 12.00"),
    sa.Column('aporte_patronal_salud', sa.Numeric(5, 2), nullable=False,
              comment="Porcentaje aporte patronal salud, e.g. 8.50"),
    sa.Column('aporte_trabajador_pension', sa.Numeric(5, 2), nullable=False,
              comment="Porcentaje aporte trabajador pensión, e.g. 4.00"),
    sa.Column('aporte_trabajador_salud', sa.Numeric(5, 2), nullable=False,
              comment="Porcentaje aporte trabajador salud, e.g. 4.00"),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
)
# Seed 2026 row
op.execute("""
    INSERT INTO ibl_parametros
      (id, ano, aporte_patronal_pension, aporte_patronal_salud,
       aporte_trabajador_pension, aporte_trabajador_salud)
    VALUES
      (gen_random_uuid(), 2026, 12.00, 8.50, 4.00, 4.00)
""")
```

**Model:**
```python
class IblParametros(BaseModel):
    __tablename__ = "ibl_parametros"
    ano: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    aporte_patronal_pension: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    aporte_patronal_salud: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    aporte_trabajador_pension: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    aporte_trabajador_salud: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
```

**Usage in `liquidacion_service.py`:**
```python
async def _get_parametros(db: AsyncSession, ano: int) -> IblParametros:
    params = await ibl_parametros_repository.get_by_ano(db, ano)
    if not params:
        raise BadRequestException(f"No hay parámetros IBL configurados para el año {ano}")
    return params

# In calcular_breakdown():
ano = fecha_inicio.year
params = await _get_parametros(db, ano)
valor_patronal_pension = ibl * dias * (params.aporte_patronal_pension / 100)
valor_trabajador_pension = ibl * dias * (params.aporte_trabajador_pension / 100)
valor_patronal_salud = ibl * dias * (params.aporte_patronal_salud / 100)
valor_trabajador_salud = ibl * dias * (params.aporte_trabajador_salud / 100)
valor_incapacidad_temporal = ibl * dias  # 100% IBC per RN-010
valor_total = (
    valor_incapacidad_temporal
    + valor_patronal_pension + valor_trabajador_pension
    + valor_patronal_salud + valor_trabajador_salud
    # aporte_adicional_trabajador_pension: formula TBD (legal review pending) — stored as None
)
```

- [ ] **Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_ibl_parametros_seed_exists(db_session):
    from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository
    params = await ibl_parametros_repository.get_by_ano(db_session, 2026)
    assert params is not None
    assert params.aporte_patronal_pension == Decimal("12.00")
    assert params.aporte_trabajador_pension == Decimal("4.00")

def test_calcular_breakdown_uses_db_parametros():
    from decimal import Decimal
    ibl = Decimal("3_500_000")  # example monthly IBL
    dias = 10
    # 12% patronal pension: 3_500_000 * 10 * 0.12 = 4_200_000
    # 4% trabajador pension: 3_500_000 * 10 * 0.04 = 1_400_000
    # (formula verified against seed values)
    ...
```

- [ ] **Step 2: Implement model, repo, seed in migration, wire into service**
- [ ] **Step 3: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k ibl -v --no-cov"
git commit -m "feat(liquidacion): add ibl_parametros table with 2026 seed — service reads percentages from DB"
```

---

### Task 5.1: `liquidacion` table + migration

**Files:**
- Create: Alembic migration
- Create: `apps/backend/app/models/liquidacion.py`

**Note on C2:** The `metodo_pago` (CHEQUE/OXIRRE) field is present in the model. The entity list (which companies pay by cheque vs Oxirre) is pending from client — dropdown is shown, but no validation against an entity list yet. IBL formulas are **fully implemented** via `ibl_parametros` table (Task 5.0).

```python
def upgrade() -> None:
    op.execute("CREATE TYPE metodopagoliquidacion AS ENUM ('CHEQUE', 'OXIRRE')")
    op.create_table(
        'liquidacion',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incapacidad_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('incapacidad.id', ondelete='CASCADE'), nullable=False, unique=True),
        # IBL
        sa.Column('ibl', sa.Numeric(15, 2), nullable=True,
                  comment="Ingreso Base de Liquidación — promedio IBC 6 meses previos"),
        sa.Column('periodo_ibl_inicio', sa.Date, nullable=True),
        sa.Column('periodo_ibl_fin', sa.Date, nullable=True),
        # Authorized period (from plantilla_auditoria)
        sa.Column('dias_autorizados', sa.Integer, nullable=False),
        sa.Column('fecha_inicio_autorizada', sa.Date, nullable=False),
        sa.Column('fecha_fin_autorizada', sa.Date, nullable=False),
        # Breakdown (TODO: formula percentages — confirm with Helen)
        sa.Column('valor_incapacidad_temporal', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_aporte_patronal_pension', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_aporte_trabajador_pension', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_aporte_adicional_trabajador_pension', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_aporte_patronal_salud', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_aporte_trabajador_salud', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_total', sa.Numeric(15, 2), nullable=True),
        # Payment
        sa.Column('metodo_pago', postgresql.ENUM('CHEQUE', 'OXIRRE', name='metodopagoliquidacion'),
                  nullable=True, comment="Pending client entity list (C2)"),
        sa.Column('notas_liquidador', sa.Text, nullable=True),
        sa.Column('liquidador_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('usuario.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
```

Add to `Incapacidad` model:
```python
liquidacion: Mapped[Optional["Liquidacion"]] = relationship(
    "Liquidacion", back_populates="incapacidad", uselist=False, cascade="all, delete-orphan"
)
```

- [ ] **Commit:** `git commit -m "chore(db): add liquidacion table and metodopagoliquidacion enum"`

---

### Task 5.2: Liquidation service + endpoints + IBL placeholder

**Files:**
- Create: `apps/backend/app/services/liquidacion_service.py`
- Create: `apps/backend/app/schemas/liquidacion.py`
- Create: `apps/backend/app/api/v1/endpoints/liquidacion.py`

**IBL note:** The IBL must come from Imaginex (external system). Until the integration spec is available, `ibl` is stored as a manually entered value. The service exposes a `POST /incapacidades/{id}/liquidacion/calcular-ibl` stub that logs the call and returns `{"ibl": null, "nota": "Integración con Imaginex pendiente de especificación"}`.

**Formula constants:** All percentage constants are in a single dict marked with `# TODO: confirm with Helen before enabling formula`:

```python
# liquidacion_service.py
# TODO(C1): Confirm all percentages with Helen before enabling formula calculation
_PORCENTAJES_PLACEHOLDER: dict = {
    "incapacidad_temporal_pct": None,        # e.g. 1.0 (100% IBC) — pending
    "aporte_patronal_pension_pct": None,     # pending
    "aporte_trabajador_pension_pct": None,   # pending
    "aporte_adicional_trabajador_pension_pct": None,  # pending
    "aporte_patronal_salud_pct": None,       # pending
    "aporte_trabajador_salud_pct": None,     # pending
}

def _calcular_breakdown(ibl: Decimal, dias: int) -> dict:
    """Placeholder formula. All values return None until C1 confirmed."""
    if any(v is None for v in _PORCENTAJES_PLACEHOLDER.values()):
        return {k.replace("_pct", ""): None for k in _PORCENTAJES_PLACEHOLDER}
    # When percentages are confirmed, uncomment:
    # valor_it = ibl * dias * Decimal(_PORCENTAJES_PLACEHOLDER["incapacidad_temporal_pct"])
    # ...
    return {}
```

**Devolution to EN_AUDITORIA:**

```python
async def devolver_a_auditoria(
    self,
    db: AsyncSession,
    incapacidad_id: UUID,
    observacion: str,
    liquidador_id: UUID,
) -> Incapacidad:
    if not observacion or not observacion.strip():
        raise BadRequestException("La observación es obligatoria para la devolución")
    incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id)
    if incapacidad.estado not in (EstadoIncapacidad.LIQUIDACION, EstadoIncapacidad.LIQUIDACION_PARCIAL):
        raise InvalidStateException("Solo se puede devolver desde LIQUIDACION o LIQUIDACION_PARCIAL")
    await incapacidad_service._validate_state_transition(
        incapacidad.estado, EstadoIncapacidad.EN_AUDITORIA
    )
    await incapacidad_repository.update(db, id=incapacidad_id, obj_in={"estado": EstadoIncapacidad.EN_AUDITORIA})
    await historial_estado_service.create_historial_entry(
        db=db, entity_type="incapacidad", entity_id=incapacidad_id,
        estado_anterior=incapacidad.estado.value,
        estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
        observacion=f"Devolución por liquidador: {observacion}",
        cambiado_por_id=liquidador_id,
    )
    await db.commit()
    return await incapacidad_service.get_incapacidad(db, incapacidad_id)
```

**Endpoints:**
- `GET /incapacidades/{id}/liquidacion` — retrieve
- `POST /incapacidades/{id}/liquidacion` — create/update
- `POST /incapacidades/{id}/liquidacion/calcular-ibl` — IBL stub
- `POST /incapacidades/{id}/liquidacion/devolver` — devolution to EN_AUDITORIA
- `POST /incapacidades/{id}/liquidacion/completar` — transition to PAGADA/PAGADA_PARCIAL

- [ ] **Step 1: Write failing test for devolution**

```python
@pytest.mark.asyncio
async def test_devolucion_requiere_observacion(db_session, incapacidad_liquidacion):
    with pytest.raises(BadRequestException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=incapacidad_liquidacion.id,
            observacion="",
            liquidador_id=uuid4(),
        )
```

- [ ] **Step 2: Implement service and endpoints**
- [ ] **Step 3: Run tests**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k liquidacion -v --no-cov"
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(liquidacion): add liquidacion service, endpoints, and devolution flow (IBL and formulas pending C1/C2)"
```

---

### Task 5.3: Frontend — LiquidacionPage

**Files:**
- Create: `apps/frontend/sistema-interno/src/pages/incapacidades/LiquidacionPage.tsx`
- Create: `apps/frontend/sistema-interno/src/services/liquidacion.ts`
- Modify: `apps/frontend/sistema-interno/src/router/index.tsx` (add `/liquidacion/:id` route, restricted to APROBADOR + ADMIN)

The page shows:
1. **Read-only panel**: Incapacidad detail + audit template (from `PlantillaAuditoria`) + all documents (same document access as GestionarPage — do not reduce)
2. **IBL section**: Shows the IBL call result (stub note until Imaginex integrated); manually editable for now
3. **Breakdown table**: All 7 line items, each showing "Pendiente de configuración" until C1 confirmed
4. **Payment method**: Dropdown CHEQUE / OXIRRE (pending C2 entity list)
5. **Action buttons**: "Completar liquidación" (→ PAGADA/PAGADA_PARCIAL) + "Devolver a auditoría" (opens mandatory observation dialog)

```tsx
// Breakdown table rows (all show N/A until percentages confirmed):
const BREAKDOWN_ROWS = [
  { label: 'Días y valor incapacidad temporal', key: 'valor_incapacidad_temporal' },
  { label: 'Días y valor aporte patronal pensión', key: 'valor_aporte_patronal_pension' },
  { label: 'Días y valor aporte trabajador pensión', key: 'valor_aporte_trabajador_pension' },
  { label: 'Días y valor aporte adicional trabajador pensión', key: 'valor_aporte_adicional_trabajador_pension' },
  { label: 'Días y valor aporte patronal salud', key: 'valor_aporte_patronal_salud' },
  { label: 'Días y valor aporte trabajador salud', key: 'valor_aporte_trabajador_salud' },
];
```

- [ ] **Step 1: Write vitest test for page render + devolution dialog**
- [ ] **Step 2: Implement page with all sections**
- [ ] **Step 3: Run tests**

```bash
cd apps/frontend/sistema-interno && npm test -- LiquidacionPage --run
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(ui): add LiquidacionPage with IBL, breakdown, devolution flow"
```

---

## Phase 6: GLOSADA Notification

### Task 6.1: Email + PDF generation service for GLOSADA

**Files:**
- Create: `apps/backend/app/services/glosada_notification_service.py`
- Modify: `apps/backend/app/core/config.py` (add env vars)
- Modify: `apps/backend/app/services/incapacidad_service.py` (hook into GLOSADA transition)

**Email config:** Use existing Mailtrap setup — `settings.SMTP_HOST`, `settings.SMTP_PORT`, `settings.SMTP_USER`, `settings.SMTP_PASSWORD`, `settings.EMAIL_FROM` are all populated from `.env`. No new env vars needed.

`glosada_notification_service.py`:
```python
async def notificar_glosada(
    db: AsyncSession,
    incapacidad: Incapacidad,
    motivo_glosa: str,
) -> None:
    """
    1. Generate glosa PDF (simple HTML→PDF via reportlab or weasyprint).
    2. Store PDF as Documento on the Incapacidad (tipo OTROS, nombre "glosa_{numero}.pdf").
    3. Send email via existing Mailtrap SMTP config (settings.EMAIL_FROM, settings.SMTP_*).
       Recipient: incapacidad.empresa.email_contacto.
    """
    pdf_bytes = _generar_pdf_glosa(incapacidad, motivo_glosa)
    await _guardar_pdf_como_documento(db, incapacidad, pdf_bytes)
    await _enviar_email_glosa(incapacidad, motivo_glosa, pdf_bytes)

def _generar_pdf_glosa(incapacidad: Incapacidad, motivo: str) -> bytes:
    # Use reportlab (check requirements.txt — add if not present) or weasyprint
    # Content: Seguros Alfa letterhead, case number, employee name, glosa reason, date
    ...

async def _enviar_email_glosa(incapacidad: Incapacidad, motivo: str, pdf_bytes: bytes) -> None:
    # Use existing email task infrastructure (send_incapacidad_radicada_email_task pattern)
    # Recipient: incapacidad.empresa.email_contacto
    # FROM: settings.EMAIL_FROM  (noreply@incapacidades.com via Mailtrap)
    # Attach: pdf_bytes as glosa_{incapacidad.numero}.pdf
    ...
```

Wire into `incapacidad_service.auditar_incapacidad()`:
```python
elif accion == "RECHAZAR":  # now maps to GLOSADA
    nuevo_estado = EstadoIncapacidad.GLOSADA
    # After state update, fire notification (best-effort, non-blocking)
    try:
        await glosada_notification_service.notificar_glosada(db, incapacidad, observaciones)
    except Exception as e:
        logger.error(f"GLOSADA notification failed for {incapacidad_id}: {e}")
```

Add `POST /incapacidades/{id}/reenviar-notificacion-glosada` endpoint (for "Reenviar notificación" button, restricted to ADMIN + AUDITOR).

- [ ] **Step 1: Write test for PDF generation (unit — no DB needed)**

```python
def test_generar_pdf_glosa_returns_bytes():
    from app.services.glosada_notification_service import _generar_pdf_glosa
    mock_inc = Mock(numero="INC-ARL-20260601-0001", fecha_inicio=date(2026,6,1), ...)
    pdf = _generar_pdf_glosa(mock_inc, "Documentación insuficiente")
    assert isinstance(pdf, bytes)
    assert len(pdf) > 100
    assert pdf[:4] == b'%PDF'  # PDF magic bytes
```

- [ ] **Step 2: Implement service**
- [ ] **Step 3: Write integration test for `reenviar` endpoint**
- [ ] **Step 4: Run tests, commit**

```bash
docker compose exec api sh -c "python -m pytest tests/ -k glosada -v --no-cov"
git commit -m "feat(glosada): add email+PDF notification, BCC, PDF stored as documento, reenviar endpoint"
```

---

### Task 6.2: Frontend — "Reenviar notificación" button

**Files:**
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx`

Add "Reenviar notificación de glosa" button, visible only when `incapacidad.estado === 'GLOSADA'` and user role is ADMIN or AUDITOR. Shows confirmation dialog before firing.

```tsx
{estado === 'GLOSADA' && (isAdmin || isAuditor) && (
  <Button variant="outline" onClick={() => setShowReenviarDialog(true)}>
    Reenviar notificación de glosa
  </Button>
)}
```

- [ ] **Step 1: Write vitest test for button visibility**
- [ ] **Step 2: Implement button + dialog**
- [ ] **Step 3: Commit**

```bash
git commit -m "feat(ui): add reenviar notificación glosa button in GestionarPage"
```

---

## Phase 6b: portal-externo — GLOSADA read-only treatment

### Task 6.3: Enforce read-only display for GLOSADA state in portal-externo

**Files:**
- Modify: `apps/frontend/portal-externo/src/components/consulta/` (detail/drawer component)
- Modify: Any portal-externo component that renders action buttons or document upload slots

**Rule:** When `incapacidad.estado === 'GLOSADA'`:
- Show the record and all its documents (including the glosa PDF) — fully readable
- Do NOT render document upload slots, action buttons, or any UI element that implies further processing
- Show a clear banner: "Esta incapacidad ha sido glosada. El motivo fue comunicado por correo electrónico a la empresa."

```tsx
// In the consulta detail component:
{estado === 'GLOSADA' && (
  <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
    Esta incapacidad ha sido glosada. El motivo fue comunicado por correo electrónico a la empresa.
    Los documentos adjuntos están disponibles para consulta.
  </div>
)}
{estado !== 'GLOSADA' && <DocumentUploadSlots ... />}
{estado !== 'GLOSADA' && <ActionButtons ... />}
```

- [ ] **Step 1: Write vitest test asserting upload slots are absent in GLOSADA state**

```tsx
it('does not render upload slots or action buttons when GLOSADA', () => {
  render(<IncapacidadDetail incapacidad={{ ...mockInc, estado: 'GLOSADA' }} />)
  expect(screen.queryByTestId('upload-slot')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /radicar|adjuntar|enviar/i })).not.toBeInTheDocument()
  expect(screen.getByText(/glosada/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Apply conditional rendering**
- [ ] **Step 3: Run portal-externo tests**

```bash
cd apps/frontend/portal-externo && npm test -- --run
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(portal-externo): show GLOSADA state as read-only — no upload slots or action buttons"
```

---

## Phase 7: State Descriptions in UI

### Task 7.1: `StateDescriptionPanel` component

**Files:**
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/StateDescriptionPanel.tsx`
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx`

The panel renders below the state badge in `GestionarPage`. Each state has a description of what it means and what must be fulfilled to advance.

```tsx
// StateDescriptionPanel.tsx
const STATE_INFO: Record<string, { descripcion: string; requisitos: string[] }> = {
  RADICADA: {
    descripcion: 'Incapacidad registrada. El sistema ejecutó la validación automática de campos y reglas de negocio.',
    requisitos: [
      'Documentación mínima presente (incapacidad médica)',
      'Empleado activo vinculado a la empresa',
      'Diagnóstico CIE-10 válido en el catálogo',
      'Tipo de enfermedad registrado (Accidente de Trabajo / Enfermedad Laboral / Accidente de Trayecto)',
    ],
  },
  EN_AUDITORIA: {
    descripcion: 'En proceso de revisión por el auditor. Las reglas de negocio ya se evaluaron automáticamente.',
    requisitos: [
      'Siniestro vinculado (obligatorio antes de aprobar o glosar)',
      'Si fecha_inicio == fecha_siniestro: usar aprobación parcial',
      'Revisar resultados de reglas en la pestaña de Auditoría',
    ],
  },
  PENDIENTE: {
    descripcion: 'En espera de información adicional solicitada por el auditor. Motivo registrado en el historial.',
    requisitos: [
      'La empresa tiene hasta la fecha indicada para responder',
      'Después de 8 días sin respuesta se genera una alerta',
      'El auditor puede devolver a EN_AUDITORIA o glosar directamente',
    ],
  },
  LIQUIDACION: {
    descripcion: 'Aprobada por el auditor. El liquidador debe calcular el valor y autorizar el pago a la empresa.',
    requisitos: [
      'IBL calculado (promedio IBC 6 meses previos a la incapacidad)',
      'Desglose de liquidación diligenciado',
      'Método de pago seleccionado (Cheque / Oxirre)',
      'Completar para pasar a PAGADA, o devolver a auditoría si hay un error',
    ],
  },
  LIQUIDACION_PARCIAL: {
    descripcion: 'Aprobada parcialmente. El primer día no es pagable (coincide con el siniestro) o el auditor ajustó los días.',
    requisitos: [
      'Mismos requisitos que LIQUIDACION',
      'El rango de días pagados está especificado en la plantilla de auditoría',
    ],
  },
  GLOSADA: {
    descripcion: 'Caso cerrado — la incapacidad fue glosada. Se notificó a la empresa por correo electrónico.',
    requisitos: ['Notificación PDF generada y adjunta al expediente', 'Estado terminal — no admite más transiciones'],
  },
  PAGADA: {
    descripcion: 'Pago completo completado.',
    requisitos: ['Estado terminal'],
  },
  PAGADA_PARCIAL: {
    descripcion: 'Pago parcial completado.',
    requisitos: ['Estado terminal'],
  },
};

export function StateDescriptionPanel({ estado, auditoriaResultados }: Props) {
  const info = STATE_INFO[estado];
  if (!info) return null;
  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm space-y-2">
      <p className="text-gray-700">{info.descripcion}</p>
      <ul className="space-y-1 list-disc list-inside text-gray-600">
        {info.requisitos.map(r => <li key={r}>{r}</li>)}
      </ul>
      {estado === 'RADICADA' && auditoriaResultados && (
        <AuditoriaResultadosList resultados={auditoriaResultados} />
      )}
      {estado === 'PENDIENTE' && (
        <p className="text-orange-700 font-medium">
          ⚠ Si han pasado 8+ días sin respuesta, puede glosar directamente o devolver a auditoría.
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 1: Write vitest test for each state description**
- [ ] **Step 2: Build component**
- [ ] **Step 3: Wire into `GestionarPage.tsx`**
- [ ] **Step 4: Run tests, commit**

```bash
git commit -m "feat(ui): add StateDescriptionPanel with per-state descriptions and requisitos"
```

---

## Phase 8: Mandatory Historial Observations on All Transitions

### Task 8.1: Enforce non-empty `observacion` on every state transition

**Files:**
- Modify: `apps/backend/app/services/incapacidad_service.py`
- Modify: `apps/backend/app/services/historial_estado_service.py`

Per the spec, every state transition (including forward ones) must record an observation. Enforcement is in the service layer, not the repository.

Strategy: create a single internal `_cambiar_estado()` helper in `incapacidad_service.py` that all transition methods call, which enforces the non-empty observation:

```python
async def _cambiar_estado(
    self,
    db: AsyncSession,
    incapacidad: Incapacidad,
    nuevo_estado: EstadoIncapacidad,
    observacion: str,
    usuario_id: Optional[UUID],
    extra_update: Optional[dict] = None,
) -> Incapacidad:
    if not observacion or not observacion.strip():
        raise BadRequestException(
            f"La observación es obligatoria para la transición a {nuevo_estado.value}"
        )
    await self._validate_state_transition(incapacidad.estado, nuevo_estado)
    update_data = {"estado": nuevo_estado, **(extra_update or {})}
    estado_anterior = incapacidad.estado
    updated = await self.repository.update(db, id=incapacidad.id, obj_in=update_data)
    await historial_estado_service.create_historial_entry(
        db=db,
        entity_type="incapacidad",
        entity_id=incapacidad.id,
        estado_anterior=estado_anterior.value,
        estado_nuevo=nuevo_estado.value,
        observacion=observacion,
        cambiado_por_id=usuario_id,
    )
    return updated
```

Refactor `auditar_incapacidad()`, `radicar_incapacidad()`, `rechazar_incapacidad()`, `aprobar_incapacidad()`, `enviar_a_pago()`, `marcar_como_pagada()` to go through `_cambiar_estado()`.

- [ ] **Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_radicar_requires_observacion(db_session, incapacidad_radicada):
    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.radicar_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad_radicada.id,
            usuario_id=None,
            observacion="",  # empty
        )
```

Note: `radicar_incapacidad()` currently does not take `observacion` — add it as a required parameter.

- [ ] **Step 2: Add `observacion` param to all public transition methods, route through `_cambiar_estado()`**
- [ ] **Step 3: Update all callers (endpoints, radicacion_pipeline_service, tests)**
- [ ] **Step 4: Run full test suite**

```bash
docker compose exec api sh -c "python -m pytest tests/ -v --no-cov"
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(historial): enforce non-empty observacion on all state transitions via _cambiar_estado()"
```

---

## Execution Summary

### Phases in dependency order

```
Phase 1 (State Rename — 9 values) — MUST complete first; unblocks everything
  ↓
Phase 2 (PENDIENTE)   Phase 3 (CREACION_SINIESTRO + Siniestro gates)   [parallel after Phase 1]
  ↓                         ↓
Phase 8 (Mandatory Obs)  Phase 4 (Approval Template)
                                ↓
                          Phase 5 (IBL Params + Liquidacion form)
                                ↓
                          Phase 6 (GLOSADA email+PDF)
                          Phase 6b (portal-externo GLOSADA read-only)   [parallel with 6]
                                ↓
                          Phase 7 (State Descriptions)
```

### Alembic migrations (in apply order)

| # | Migration | Contents | Phase |
|---|-----------|----------|-------|
| M1 | Rename `estadoincapacidad` enum | 9 new values (incl. CREACION_SINIESTRO, PENDIENTE) + data migration + recreate type | 1.1 |
| M2 | `incapacidad.pendiente_desde` | DateTime nullable | 2.1 |
| M3 | `plantilla_auditoria` table | 1:1 with incapacidad, approval template fields | 4.1 |
| M4 | `liquidacion` + `ibl_parametros` | `metodopagoliquidacion` enum, liquidation fields, IBL% table + 2026 seed | 5.0–5.1 |

**No migration needed for CREACION_SINIESTRO** — `incapacidad.numero_siniestro` (String 50) and `siniestro.numero_siniestro` + `siniestro.external_id` already exist in the schema.

### Remaining client confirmation item

| ID | What | Who | Blocks |
|----|------|-----|--------|
| C2 | CHEQUE/OXIRRE entity list (which companies pay by which method) | Client | Validation of `metodo_pago` selection in Phase 5 — dropdown works, entity-specific enforcement pending |
